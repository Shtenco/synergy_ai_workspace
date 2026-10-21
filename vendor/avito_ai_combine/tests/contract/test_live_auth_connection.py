import json
import io
import urllib.error
from avito_ai_combine.avito.auth import AuthClient, TokenSet
from avito_ai_combine.avito.transport import AvitoTransport
from avito_ai_combine.avito.scopes import CapabilityResolver
from avito_ai_combine.services.connection import ConnectionService

class Response:
    def __init__(self, payload, status=200): self.payload=payload; self.status=status
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def read(self): return json.dumps(self.payload).encode()

def test_client_credentials_posts_form_and_parses_token():
    seen={}
    def opener(req, timeout=0):
        seen['url']=req.full_url; seen['method']=req.method; seen['data']=req.data.decode(); seen['auth']=req.headers.get('Authorization')
        return Response({'access_token':'AT','token_type':'Bearer','expires_in':3600,'scope':'messenger:read messenger:write'})
    auth=AuthClient(opener=opener)
    token=auth.client_credentials('client-id','client-secret')
    assert isinstance(token, TokenSet)
    assert token.access_token=='AT'
    assert token.scopes==frozenset({'messenger:read','messenger:write'})
    assert 'client_id=client-id' in seen['data'] and 'client_secret=client-secret' in seen['data']
    assert seen['auth'] is None

def test_transport_returns_correlation_id_on_auth_error():
    def opener(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url,401,'unauthorized',{},io.BytesIO(b'{"error":"invalid_token"}'))
    t=AvitoTransport(opener=opener)
    try: t.request('GET','/core/v1/accounts/self',token='secret')
    except Exception as exc:
        assert getattr(exc,'correlation_id',None)
        assert 'secret' not in str(exc)
    else: raise AssertionError('expected auth error')

def test_connection_check_derives_capabilities_from_scopes_and_probe_results():
    class Account:
        def get_self(self): return {'id':123,'name':'Test'}
    resolver=CapabilityResolver(scopes={'messenger:read','messenger:write'}, flags={'listings:read'})
    result=ConnectionService(Account(),resolver).check()
    assert result['ok'] is True
    assert result['account']['id']==123
    assert result['capabilities']['messenger_read'] is True
    assert result['capabilities']['messenger_write'] is True
    assert result['capabilities']['listings_read'] is True
