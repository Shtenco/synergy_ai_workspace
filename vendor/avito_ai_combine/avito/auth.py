from dataclasses import dataclass
from time import time
from urllib.parse import urlencode
import json, urllib.request, urllib.error
from avito_ai_combine.app.exceptions import AuthError, TransientAvitoError

TOKEN_URL='https://api.avito.ru/token/'

@dataclass(frozen=True)
class TokenSet:
    access_token: str
    token_type: str='Bearer'
    expires_in: int=0
    refresh_token: str|None=None
    scopes: frozenset[str]=frozenset()
    obtained_at: float=0.0
    @property
    def expires_at(self): return self.obtained_at + max(0,self.expires_in)
    def expired(self, skew=60): return bool(self.expires_in) and time() >= self.expires_at-skew

class AuthClient:
    def __init__(self, token_url=TOKEN_URL, timeout=20, opener=None):
        self.token_url=token_url; self.timeout=timeout; self.opener=opener or urllib.request.urlopen
    def _post(self, fields):
        data=urlencode(fields).encode()
        req=urllib.request.Request(self.token_url,data=data,headers={'Accept':'application/json','Content-Type':'application/x-www-form-urlencoded'},method='POST')
        try:
            with self.opener(req,timeout=self.timeout) as r: payload=json.loads(r.read() or b'{}')
        except urllib.error.HTTPError as e: raise AuthError(f'Avito OAuth HTTP {e.code}') from e
        except (TimeoutError,urllib.error.URLError,OSError) as e: raise TransientAvitoError('Avito OAuth network failure') from e
        if not payload.get('access_token'): raise AuthError('Avito OAuth response has no access_token')
        scope=payload.get('scope') or payload.get('scopes') or ''
        scopes=frozenset(scope.split() if isinstance(scope,str) else scope)
        return TokenSet(payload['access_token'],payload.get('token_type','Bearer'),int(payload.get('expires_in') or 0),payload.get('refresh_token'),scopes,time())
    def client_credentials(self, client_id, client_secret):
        return self._post({'grant_type':'client_credentials','client_id':client_id,'client_secret':client_secret})
    def authorization_code(self, client_id, client_secret, code, redirect_uri):
        return self._post({'grant_type':'authorization_code','client_id':client_id,'client_secret':client_secret,'code':code,'redirect_uri':redirect_uri})
    def refresh(self, client_id, client_secret, refresh_token):
        return self._post({'grant_type':'refresh_token','client_id':client_id,'client_secret':client_secret,'refresh_token':refresh_token})
