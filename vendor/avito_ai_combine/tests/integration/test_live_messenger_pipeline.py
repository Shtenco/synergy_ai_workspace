from avito_ai_combine.avito.messenger import MessengerClient
from avito_ai_combine.services.messaging import MessagingService
from avito_ai_combine.webhooks.handlers import WebhookIngestor

def test_messenger_routes_versions_and_supports_images_voice_blacklist():
    class T:
        def __init__(self): self.calls=[]
        def request(self,*a,**kw): self.calls.append((a,kw)); return {'ok':True}
    t=T(); c=MessengerClient(t,'tok','42')
    c.list_chats(); c.list_messages('c1'); c.send_text('c1','hello','k1'); c.send_image('c1','img1','k2'); c.get_voice_files(['v1']); c.blacklist('99')
    paths=[x[0][1] for x in t.calls]
    assert paths[0]=='/messenger/v2/accounts/42/chats'
    assert '/messenger/v3/' in paths[1]
    assert '/messenger/v1/' in paths[2]
    assert paths[3].endswith('/messages/image')
    assert 'getVoiceFiles' in paths[4]
    assert paths[5].endswith('/blacklist')

def test_webhook_duplicate_and_out_of_order_event_are_safe():
    ing=WebhookIngestor()
    older={'id':'e1','timestamp':100,'payload':{'chat_id':'c','message_id':'m1'}}
    newer={'id':'e2','timestamp':200,'payload':{'chat_id':'c','message_id':'m2'}}
    assert ing.ingest(newer)['duplicate'] is False
    assert ing.ingest(older)['duplicate'] is False
    assert ing.ingest(newer)['duplicate'] is True
    assert len(ing.events)==2

def test_messaging_service_blocks_duplicate_logical_send():
    class C:
        def __init__(self): self.n=0
        def send_text(self,*a): self.n+=1; return {'id':self.n}
    c=C(); s=MessagingService(c)
    a=s.send_text('c','x','same'); b=s.send_text('c','x','same')
    assert a==b and c.n==1
