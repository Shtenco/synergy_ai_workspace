import json, uuid
from avito_ai_combine.avito.messenger import MessengerClient
from avito_ai_combine.ai.sales_agent import SalesAgent
from avito_ai_combine.ai.gateway import AIGateway
class MessagingService:
    def __init__(self,client): self.client=client; self.sent={}
    def send_text(self,chat_id,text,idempotency_key):
        if idempotency_key in self.sent: return self.sent[idempotency_key]
        r=self.client.send_text(chat_id,text,idempotency_key); self.sent[idempotency_key]=r; return r
class PersistentMessagingService:
    def __init__(self,runtime,gateway=None): self.rt=runtime; self.gateway=gateway or AIGateway()
    def _client(self):
        if not self.rt.token or not self.rt.account_id: raise RuntimeError('Avito is not connected')
        return MessengerClient(self.rt.transport,self.rt.token.access_token,self.rt.account_id)
    @staticmethod
    def _items(payload,key):
        if isinstance(payload,list): return payload
        if isinstance(payload,dict): return payload.get(key) or payload.get('result') or []
        return []
    @staticmethod
    def _listing(chat):
        value=((chat.get('context') or {}).get('value') or {}) if isinstance(chat,dict) else {}
        return str(value.get('id') or value.get('item_id') or '') or None
    @staticmethod
    def _peer(chat,account_id):
        for u in chat.get('users') or []:
            if str(u.get('id'))!=str(account_id): return str(u.get('id') or u.get('name') or 'unknown')
        return str(chat.get('id'))
    @staticmethod
    def _text(msg):
        content=msg.get('content') or {}; return str(content.get('text') or msg.get('text') or '')
    def sync(self):
        client=self._client(); chats=self._items(client.list_chats(limit=100),'chats'); counts={'chats':0,'messages':0,'leads':0}
        for chat in chats:
            chat_id=str(chat.get('id')); listing=self._listing(chat); peer=self._peer(chat,self.rt.account_id)
            with self.rt.db.transaction() as c:
                c.execute('insert into chats(external_id,account_id,data) values (?,?,?) on conflict(external_id,account_id) do update set data=excluded.data',(chat_id,self.rt.account_id,json.dumps(chat,ensure_ascii=False)))
                before=c.execute('select count(*) from leads where external_id=? and account_id=?',(peer,self.rt.account_id)).fetchone()[0]
                lead_data={'chat_id':chat_id,'source_listing':listing,'status':'NEW','intent':'general'}
                c.execute('insert into leads(external_id,account_id,data) values (?,?,?) on conflict(external_id,account_id) do update set data=excluded.data',(peer,self.rt.account_id,json.dumps(lead_data,ensure_ascii=False)))
                if not before: counts['leads']+=1
            counts['chats']+=1
            msgs=self._items(client.list_messages(chat_id,limit=100),'messages')
            for msg in msgs:
                mid=str(msg.get('id')); data=dict(msg); data['chat_id']=chat_id; data['text']=self._text(msg)
                with self.rt.db.transaction() as c:
                    cur=c.execute('insert or ignore into messages(external_id,account_id,data) values (?,?,?)',(mid,self.rt.account_id,json.dumps(data,ensure_ascii=False)))
                    counts['messages']+=max(cur.rowcount,0)
        return counts
    def list_local_chats(self):
        rows=self.rt.db.query('select external_id,data from chats where account_id=? order by id desc',(self.rt.account_id,)); out=[]
        for r in rows:
            d=json.loads(r['data']); out.append({'chat_id':r['external_id'],'title':(((d.get('context') or {}).get('value') or {}).get('title') or r['external_id']),'raw':d})
        return out
    def list_local_messages(self,chat_id):
        rows=self.rt.db.query('select data from messages where account_id=? order by id',(self.rt.account_id,)); out=[]
        for r in rows:
            d=json.loads(r['data'])
            if str(d.get('chat_id'))==str(chat_id): out.append({'id':str(d.get('id')),'text':d.get('text',''),'author_id':d.get('author_id'),'raw':d})
        return out
    def get_lead_for_chat(self,chat_id):
        for r in self.rt.db.query('select external_id,data from leads where account_id=?',(self.rt.account_id,)):
            d=json.loads(r['data'])
            if d.get('chat_id')==chat_id: return {'identity':r['external_id'],**d}
        return None
    def draft_reply(self,chat_id,profile='general'):
        msgs=self.list_local_messages(chat_id); request='\n'.join(m['text'] for m in msgs[-8:] if m['text'])
        return SalesAgent(self.gateway,self.rt.knowledge).draft_reply(profile,request)
    def send_text(self,chat_id,text):
        key=f'gui:{chat_id}:{uuid.uuid4().hex}'; result=self._client().send_text(chat_id,text,key)
        return result
