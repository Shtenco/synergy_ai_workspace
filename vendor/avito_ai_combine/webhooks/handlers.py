import json, hashlib
class WebhookHandler:
    def __init__(self,db,event_bus=None,account_id_getter=None): self.db=db; self.event_bus=event_bus; self.account_id_getter=account_id_getter or (lambda:'')
    def ingest(self,payload):
        raw=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')); event_id=str(payload.get('id') or payload.get('event_id') or hashlib.sha256(raw.encode()).hexdigest())
        try:
            with self.db.transaction() as c: c.execute('insert into message_events(external_id,data) values (?,?)',(event_id,raw))
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e): return {'accepted':True,'duplicate':True,'event_id':event_id}
            raise
        self._project_message(payload)
        if self.event_bus: self.event_bus.publish('avito.webhook',payload)
        return {'accepted':True,'duplicate':False,'event_id':event_id}
    def _project_message(self,payload):
        value=((payload.get('payload') or {}).get('value') or {})
        chat_id=value.get('chat_id') or ((value.get('chat') or {}).get('id') if isinstance(value.get('chat'),dict) else None)
        message_id=value.get('id') or value.get('message_id'); author=value.get('author_id') or value.get('user_id')
        if not chat_id or not message_id:return
        account_id=str(self.account_id_getter() or '')
        content=value.get('content') or {}; text=content.get('text') or value.get('text') or ''
        data=dict(value); data.update({'chat_id':str(chat_id),'text':str(text)})
        listing=((value.get('context') or {}).get('value') or {}).get('id')
        with self.db.transaction() as c:
            c.execute('insert or ignore into chats(external_id,account_id,data) values (?,?,?)',(str(chat_id),account_id,json.dumps({'id':chat_id,'context':value.get('context') or {}},ensure_ascii=False)))
            c.execute('insert or ignore into messages(external_id,account_id,data) values (?,?,?)',(str(message_id),account_id,json.dumps(data,ensure_ascii=False)))
            if author is not None and str(author)!=account_id:
                lead={'chat_id':str(chat_id),'source_listing':str(listing) if listing is not None else None,'status':'NEW','intent':'general'}
                c.execute('insert into leads(external_id,account_id,data) values (?,?,?) on conflict(external_id,account_id) do update set data=excluded.data',(str(author),account_id,json.dumps(lead,ensure_ascii=False)))

class WebhookIngestor:
    def __init__(self): self.events=[]; self._ids=set()
    def ingest(self,payload):
        eid=str(payload.get('id') or hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest())
        if eid in self._ids:return {'duplicate':True,'event_id':eid}
        self._ids.add(eid); self.events.append(payload); return {'duplicate':False,'event_id':eid}
