from pathlib import Path
from avito_ai_combine.app.bootstrap import build_local_runtime
from avito_ai_combine.services.connection import ConnectionManager
from avito_ai_combine.services.messaging import PersistentMessagingService
from avito_ai_combine.ai.gateway import AIGateway, AIResult
from avito_ai_combine.ai.knowledge import KnowledgeEntry

class FakeAuth:
    def client_credentials(self, cid, secret):
        from avito_ai_combine.avito.auth import TokenSet
        return TokenSet('tok','Bearer',3600,scopes=frozenset(('messenger:read','messenger:write')))
class FakeTransport:
    def request(self, method, path, **kwargs):
        if path == '/core/v1/accounts/self': return {'id': 777, 'name':'Test'}
        if path.endswith('/chats'): return {'chats':[{'id':'c1','context':{'value':{'id':55,'title':'Visa Spain'}},'users':[{'id':9,'name':'Ivan'}]}]}
        if '/messages/' in path: return {'messages':[{'id':'m1','author_id':9,'created':1,'content':{'text':'Хочу визу в Испанию'}}]}
        if path.endswith('/messages') and method=='POST': return {'id':'out1'}
        return {}
class Provider:
    def generate(self, req): return AIResult('Здравствуйте! Помогу разобраться.', False)

def test_credentials_survive_runtime_restart(tmp_path):
    rt=build_local_runtime(tmp_path)
    mgr=ConnectionManager(rt, auth_client=FakeAuth(), transport=FakeTransport())
    mgr.save_credentials('cid','secret')
    rt2=build_local_runtime(tmp_path)
    assert rt2.config.client_id=='cid'
    assert rt2.vault.get('client_secret')=='secret'

def test_connection_check_persists_account_and_capabilities(tmp_path):
    rt=build_local_runtime(tmp_path)
    mgr=ConnectionManager(rt, auth_client=FakeAuth(), transport=FakeTransport())
    mgr.save_credentials('cid','secret')
    result=mgr.check_live()
    assert result['account']['id']==777
    assert result['capabilities']['messenger_read'] is True
    assert rt.account_id=='777'

def test_messenger_sync_persists_chat_message_lead_and_draft(tmp_path):
    rt=build_local_runtime(tmp_path)
    mgr=ConnectionManager(rt, auth_client=FakeAuth(), transport=FakeTransport()); mgr.save_credentials('cid','secret'); mgr.check_live()
    svc=PersistentMessagingService(rt, gateway=AIGateway(Provider()))
    rt.knowledge.add(KnowledgeEntry('Помогаем с визами Испании',profile='visa_residence',approved=True))
    summary=svc.sync()
    assert summary['chats']==1 and summary['messages']==1 and summary['leads']==1
    chats=svc.list_local_chats(); assert chats[0]['chat_id']=='c1'
    msgs=svc.list_local_messages('c1'); assert msgs[0]['text']=='Хочу визу в Испанию'
    lead=svc.get_lead_for_chat('c1'); assert lead and lead['source_listing']=='55'
    draft=svc.draft_reply('c1','visa_residence'); assert draft['text']

def test_webhook_duplicate_is_idempotent(tmp_path):
    rt=build_local_runtime(tmp_path)
    payload={'id':'evt1','payload':{'value':{'chat_id':'c1','id':'m2','author_id':9,'content':{'text':'Цена?'}}}}
    a=rt.webhook_handler.ingest(payload); b=rt.webhook_handler.ingest(payload)
    assert a['duplicate'] is False and b['duplicate'] is True
    assert rt.db.scalar("select count(*) from message_events where external_id='evt1'")==1

def test_webhook_incoming_creates_message_and_lead(tmp_path):
    rt=build_local_runtime(tmp_path); rt.account_id='777'
    payload={'id':'evt-live','payload':{'value':{'chat_id':'c9','id':'m9','author_id':123,'content':{'text':'Нужна квартира в Турции'},'context':{'value':{'id':999}}}}}
    rt.webhook_handler.ingest(payload)
    assert rt.db.scalar("select count(*) from messages where external_id='m9'")==1
    assert rt.db.scalar("select count(*) from leads where external_id='123'")==1
