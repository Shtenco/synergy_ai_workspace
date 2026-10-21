"""V0.7 provider preflight. No network access, no external side effects.
Read-only capability discovery with explicit sandbox receipts and identity gates.
"""
from __future__ import annotations
import json, hashlib, os
from pathlib import Path
from workspace import service

KNOWN={
 'avito':{'capabilities':['avito.message','avito.listing_update'],'auth':'OAuth2', 'transport':'not_configured'},
 'vk':{'capabilities':['smm.post','smm.message'],'auth':'OAuth2','transport':'not_configured'},
 'telegram':{'capabilities':['smm.post','smm.message'],'auth':'Bot Token','transport':'not_configured'},
 'instagram':{'capabilities':['smm.post'],'auth':'Meta OAuth','transport':'not_configured'},
}

def inventory():
 return {'mode':'dry_run_only','providers':{k:{**v,'status':'NOT_VERIFIED','live_writes':False} for k,v in KNOWN.items()}}

def source_manifest():
 root=service.BASE;paths={
 'smm_workspaces':'vendor/synergy.github.io/smm/workspaces.html',
 'smm_studio':'vendor/synergy.github.io/smm/studio.html',
 'smm_lead_radar':'vendor/synergy.github.io/smm/lead-radar.html',
 'smm_caseflow':'vendor/synergy.github.io/smm/caseflow.html',
 'autopilot_python':'vendor/python-runtime/src/agi_autopilot/app.py',
 'autopilot_tauri':'vendor/desktop-integration/apps/desktop/src/App.tsx',
 'avito_original':'vendor/avito_ai_combine/main.py'}
 entries={}
 for name,rel in paths.items():
  p=root/rel
  entries[name]={'path':rel,'present':p.is_file(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None}
 return {'modules':entries, 'source_integrity':'sha256-of-current-files-not-upstream-proof'}

def dry_run_dispatch(action_id:int,provider:str,operator:str,request_id:str)->dict:
 if provider not in KNOWN: raise ValueError('UNKNOWN_PROVIDER')
 if not isinstance(operator,str) or not operator.strip():raise ValueError('OPERATOR_REQUIRED')
 if not isinstance(request_id,str) or not (1<=len(request_id)<=100):raise ValueError('REQUEST_ID_REQUIRED')
 with service.LOCK,service.connect() as db:
  row=db.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone()
  if row is None:raise LookupError('action')
  row=dict(row)
  if row['status']!='approved':
   service.emit(db,'provider.dry_run_denied',str(action_id),{'reason':'APPROVAL_REQUIRED','provider':provider,'operator':operator})
   return {'status':'denied','reason':'APPROVAL_REQUIRED','external_effects':False}
  if row['kind'] not in KNOWN[provider]['capabilities']:
   service.emit(db,'provider.dry_run_denied',str(action_id),{'reason':'CAPABILITY_MISMATCH','provider':provider,'operator':operator})
   return {'status':'denied','reason':'CAPABILITY_MISMATCH','external_effects':False}
  prior=db.execute('SELECT detail FROM audit WHERE action=? AND resource=? ORDER BY id DESC',('provider.dry_run',str(action_id))).fetchall()
  for old in prior:
   r=json.loads(old['detail'])
   if r.get('request_id')==request_id:
    return {'status':'simulated','receipt':r,'replayed':True,'external_effects':False}
  receipt={'action_id':action_id,'provider':provider,'operator':operator,'request_id':request_id,'kind':row['kind'],'delivery':'NOT_SENT','transport':'MOCK','payload_sha256':hashlib.sha256(row['draft'].encode('utf8')).hexdigest()}
  service.emit(db,'provider.dry_run',str(action_id),receipt)
 return {'status':'simulated','receipt':receipt,'replayed':False,'external_effects':False}
