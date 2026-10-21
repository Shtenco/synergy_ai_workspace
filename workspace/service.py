"""Local-only SYNERGY control plane; side-effect-free except explicit local CRUD."""
from __future__ import annotations
import json, os, sqlite3, secrets, threading, time, urllib.parse, urllib.request
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from workspace import adapters

BASE=Path(__file__).resolve().parents[1]
DB=Path(os.environ.get('SYNERGY_DB',str(BASE/'runtime'/'workspace.sqlite3')))
TOKEN=os.environ.get('SYNERGY_TOKEN') or secrets.token_urlsafe(32)
LOCK=threading.RLock()

class ClosingConnection(sqlite3.Connection):
 def __exit__(self, exc_type, exc_val, exc_tb):
  try:
   return super().__exit__(exc_type,exc_val,exc_tb)
  finally:
   self.close()

def connect():
 DB.parent.mkdir(parents=True,exist_ok=True)
 db=sqlite3.connect(DB,timeout=12,factory=ClosingConnection)
 db.row_factory=sqlite3.Row
 db.execute('PRAGMA journal_mode=WAL')
 db.execute('PRAGMA busy_timeout=12000')
 db.executescript('''CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, title TEXT NOT NULL, module TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY,name TEXT NOT NULL,source TEXT NOT NULL,stage TEXT NOT NULL DEFAULT 'new',notes TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT NOT NULL,resource TEXT NOT NULL,detail TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);''')
 db.executescript("""CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL REFERENCES leads(id),task_id INTEGER NOT NULL REFERENCES tasks(id),channel TEXT NOT NULL,kind TEXT NOT NULL,draft TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'draft',approved_at TEXT,executed_at TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
 CREATE INDEX IF NOT EXISTS idx_actions_lead ON actions(lead_id);""")
 db.execute('PRAGMA foreign_keys=ON')
 return db

def emit(db,action,resource,detail):
 db.execute('INSERT INTO audit(action,resource,detail) VALUES (?,?,?)',(action,resource,json.dumps(detail,ensure_ascii=False)))

def list_data(table,limit=100):
 if table not in ('tasks','leads','audit','actions'):raise ValueError('table')
 with LOCK,connect() as db:return [dict(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY id DESC LIMIT ?', (max(1,min(500,int(limit))),))]

def create_task(title,module):
 if not isinstance(title,str) or not title.strip() or len(title)>240:raise ValueError('title')
 if module not in ('autopilot','smm','avito'):raise ValueError('module')
 with LOCK,connect() as db:
  c=db.execute('INSERT INTO tasks(title,module) VALUES (?,?)',(title.strip(),module));emit(db,'task.create',str(c.lastrowid),{'module':module});return c.lastrowid

def update_task(id,status):
 if status not in ('draft','review','approved','cancelled','done'):raise ValueError('status')
 with LOCK,connect() as db:
  row=db.execute('SELECT status FROM tasks WHERE id=?',(id,)).fetchone()
  if not row:raise LookupError('task')
  allowed={'draft':{'review','cancelled'},'review':{'approved','cancelled'},'approved':{'done','cancelled'},'done':set(),'cancelled':set()}
  if status not in allowed[row['status']]:raise ValueError('transition')
  db.execute('UPDATE tasks SET status=? WHERE id=?',(status,id));emit(db,'task.transition',str(id),{'from':row['status'],'to':status})

def create_lead(name,source,notes=''):
 if not isinstance(name,str) or not name.strip() or len(name)>240:raise ValueError('name')
 if source not in ('smm','avito','manual'):raise ValueError('source')
 if not isinstance(notes,str) or len(notes)>4000:raise ValueError('notes')
 with LOCK,connect() as db:
  c=db.execute('INSERT INTO leads(name,source,notes) VALUES (?,?,?)',(name.strip(),source,notes));emit(db,'lead.create',str(c.lastrowid),{'source':source});return c.lastrowid

def prepare_action(lead_id:int,kind:str,draft:str):
 """Builds an attributable action draft, never performs an external operation."""
 if kind not in ('avito.message','avito.listing_update','smm.post','smm.message'):raise ValueError('unsupported capability')
 if not isinstance(draft,str) or not draft.strip() or len(draft)>10000:raise ValueError('draft')
 if not isinstance(lead_id,int) or isinstance(lead_id,bool):raise ValueError('lead_id')
 channel=kind.split('.')[0]
 with LOCK,connect() as db:
  lead=db.execute('SELECT * FROM leads WHERE id=?',(lead_id,)).fetchone()
  if not lead:raise LookupError('lead')
  module='avito' if channel=='avito' else 'smm'
  cur=db.execute('INSERT INTO tasks(title,module,status) VALUES (?,?,?)',(f'{kind}: {lead["name"]}',module,'review'))
  task_id=cur.lastrowid
  cur=db.execute('INSERT INTO actions(lead_id,task_id,channel,kind,draft) VALUES (?,?,?,?,?)',(lead_id,task_id,channel,kind,draft.strip()))
  action_id=cur.lastrowid
  emit(db,'action.prepare',str(action_id),{'lead_id':lead_id,'task_id':task_id,'kind':kind})
 return {'id':action_id,'task_id':task_id,'status':'draft','external_effects':False}

def approve_action(action_id:int):
 with LOCK,connect() as db:
  row=db.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone()
  if not row:raise LookupError('action')
  if row['status']!='draft':raise ValueError('invalid approval transition')
  task=db.execute('SELECT status FROM tasks WHERE id=?',(row['task_id'],)).fetchone()
  if task['status']!='review':raise ValueError('task not in review')
  db.execute("UPDATE actions SET status='approved', approved_at=CURRENT_TIMESTAMP WHERE id=?",(action_id,))
  db.execute("UPDATE tasks SET status='approved' WHERE id=?",(row['task_id'],))
  emit(db,'action.approve',str(action_id),{'task_id':row['task_id'],'external_effects':False})
 return {'id':action_id,'status':'approved','external_effects':False}

def execute_action(action_id:int):
 """Intentionally fail closed: no provider-backed write adapter verified."""
 with LOCK,connect() as db:
  row=db.execute('SELECT status,kind FROM actions WHERE id=?',(action_id,)).fetchone()
  if not row:raise LookupError('action')
  emit(db,'action.execute_denied',str(action_id),{'kind':row['kind'],'reason':'NO_VERIFIED_PROVIDER_ADAPTER','approved':row['status']=='approved'})
 return {'id':action_id,'status':'blocked','code':'NO_VERIFIED_PROVIDER_ADAPTER','external_effects':False}

def status():
 v=BASE/'vendor'
 return {'service':'ok','database':'local','avito_source':(v/'avito_ai_combine'/'main.py').exists(),'smm_source':(v/'synergy.github.io'/'smm'/'index.html').exists(),'smm_embedded':(BASE/'desktop'/'public'/'original-smm'/'index.html').exists(),'autopilot_desktop_source':(v/'desktop-integration'/'apps'/'desktop'/'src'/'App.tsx').exists(),'autopilot_python_source':(v/'python-runtime'/'src'/'agi_autopilot'/'app.py').exists(),'integration':'local-control-plane','external_actions':'disabled','version':'0.8.0'}

class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,code,obj):
  raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');origin=self.headers.get('Origin','');self.send_header('Access-Control-Allow-Origin',origin if origin in ('http://tauri.localhost','tauri://localhost','http://127.0.0.1:1420','http://localhost:1420') else 'http://tauri.localhost');self.send_header('Vary','Origin');self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type');self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS');self.end_headers();self.wfile.write(raw)
 def auth(self):
  if not secrets.compare_digest(self.headers.get('Authorization',''), 'Bearer '+TOKEN):self.send(401,{'error':'unauthorized'});return False
  return True
 def do_OPTIONS(self):
  if self.headers.get('Origin','') not in ('http://tauri.localhost','tauri://localhost','http://127.0.0.1:1420','http://localhost:1420'):return self.send(403,{'error':'origin_denied'})
  self.send(200,{'ok':True})
 def do_GET(self):
  if not self.auth():return
  p=urllib.parse.urlparse(self.path).path
  if p=='/health':return self.send(200,status())
  if p=='/v1/integrations':return self.send(200,adapters.inventory())
  if p=='/v1/providers':
   from workspace.provider_runtime import inventory
   return self.send(200,inventory())
  if p=='/v1/sources':
   from workspace.provider_runtime import source_manifest
   return self.send(200,source_manifest())
  if p=='/v1/capital/summary':
   from workspace import capital_engine
   query=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
   try:return self.send(200,capital_engine.summary(query['currency'][0],query['start'][0],query['end'][0]))
   except (KeyError,IndexError,ValueError):return self.send(400,{'error':'invalid capital query'})
  if p=='/v1/orchestration/capabilities':
   from workspace import meta_orchestrator
   return self.send(200,meta_orchestrator.list_capabilities())
  for table in ('tasks','leads','audit','actions'):
   if p=='/v1/'+table:return self.send(200,{'items':list_data(table)})
  self.send(404,{'error':'not_found'})
 def do_POST(self):
  if not self.auth():return
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size>100000:raise ValueError('payload too large')
   obj=json.loads(self.rfile.read(size)) if size else {}
   p=urllib.parse.urlparse(self.path).path
   if p.startswith('/v1/actions/') and p.endswith('/provider-dry-run'):
    from workspace.provider_runtime import dry_run_dispatch
    return self.send(200,dry_run_dispatch(int(p.split('/')[3]),obj.get('provider'),obj.get('operator'),obj.get('request_id')))
   if p=='/v1/capital/import':
    from workspace import capital_engine
    return self.send(201,capital_engine.import_entries(obj))
   if p=='/v1/capital/allocate/plan':
    from workspace import capital_engine
    return self.send(201,capital_engine.allocation_plan(obj.get('currency'),obj.get('start'),obj.get('end'),obj.get('reserve_pct'),obj.get('investment_pct'),obj.get('minimum_buffer','0')))
   if p=='/v1/orchestration/run':
    from workspace import meta_orchestrator
    try:return self.send(200,meta_orchestrator.run(obj.get('steps')))
    except PermissionError:return self.send(403,{'error':'CAPABILITY_DENIED'})
   if p=='/v1/avito/score':
    result=adapters.avito_score(obj);
    with LOCK,connect() as db:emit(db,'avito.score','local',{'value':result['value']})
    return self.send(200,result)
   if p=='/v1/autopilot/smm/plan':
    result=adapters.autopilot_plan(obj);
    with LOCK,connect() as db:emit(db,'autopilot.smm.plan','local',{'count':len(result.get('items',[]))})
    return self.send(200,result)
   if p=='/v1/workflows/lead-plan':
    from workspace.integration_v06 import prepare_lead_workflow
    return self.send(201,prepare_lead_workflow(obj.get('lead_id'),obj.get('kind'),obj.get('request',{})))
   if p.startswith('/v1/actions/') and p.endswith('/simulate'):
    from workspace.integration_v06 import simulate_provider
    return self.send(200,simulate_provider(int(p.split('/')[3])))
   if p=='/v1/actions/prepare':return self.send(201,prepare_action(obj.get('lead_id'),obj.get('kind'),obj.get('draft')))
   if p.startswith('/v1/actions/') and p.endswith('/approve'):
    return self.send(200,approve_action(int(p.split('/')[3])))
   if p.startswith('/v1/actions/') and p.endswith('/execute'):
    return self.send(409,execute_action(int(p.split('/')[3])))
   if p=='/v1/tasks':return self.send(201,{'id':create_task(obj.get('title'),obj.get('module'))})
   if p=='/v1/leads':return self.send(201,{'id':create_lead(obj.get('name'),obj.get('source'),obj.get('notes',''))})
   if p.startswith('/v1/tasks/') and p.endswith('/transition'):
    idx=int(p.split('/')[3]);update_task(idx,obj.get('status'));return self.send(200,{'ok':True})
   self.send(404,{'error':'not_found'})
  except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:self.send(400,{'error':str(e)})
  except FileNotFoundError as e:self.send(409,{'error':str(e),'code':'SOURCE_NOT_IMPORTED'})
  except LookupError:self.send(404,{'error':'not_found'})

def main():
 connect().close()
 server=ThreadingHTTPServer(('127.0.0.1',8129),Handler)
 print('SYNERGY local service http://127.0.0.1:8129',flush=True)
 print('Session token:',TOKEN,flush=True)
 print('Token is local only; do not share it or paste into untrusted pages.',flush=True)
 server.serve_forever()
if __name__=='__main__':main()
