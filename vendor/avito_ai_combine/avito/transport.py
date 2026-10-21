import json, urllib.request, urllib.error, uuid
from avito_ai_combine.app.exceptions import *
class AvitoTransport:
    def __init__(self,base_url='https://api.avito.ru',timeout=20,opener=None): self.base_url=base_url.rstrip('/'); self.timeout=timeout; self.opener=opener or urllib.request.urlopen
    def request(self,method,path,*,token=None,params=None,json_body=None,idempotency_key=None):
        from urllib.parse import urlencode
        correlation_id=str(uuid.uuid4())
        url=self.base_url+path+('?' + urlencode(params,doseq=True) if params else '')
        headers={'Accept':'application/json','X-Correlation-ID':correlation_id}
        if token: headers['Authorization']='Bearer '+token
        if idempotency_key: headers['Idempotency-Key']=idempotency_key
        data=None
        if json_body is not None: data=json.dumps(json_body).encode(); headers['Content-Type']='application/json'
        req=urllib.request.Request(url,data=data,headers=headers,method=method)
        try:
            with self.opener(req,timeout=self.timeout) as r:
                raw=r.read(); return json.loads(raw or b'{}')
        except urllib.error.HTTPError as e:
            m={400:ValidationError,401:AuthError,403:PermissionError,404:NotFoundError,409:ConflictError,429:RateLimitError}
            cls=m.get(e.code,TransientAvitoError if e.code>=500 else PermanentAvitoError)
            exc=cls(f'Avito HTTP {e.code} [correlation_id={correlation_id}]'); exc.correlation_id=correlation_id; exc.status_code=e.code
            retry_after=e.headers.get('Retry-After') if e.headers else None
            exc.retry_after=retry_after
            raise exc from e
        except (TimeoutError,urllib.error.URLError,OSError) as e:
            exc=TransientAvitoError(f'Avito network failure [correlation_id={correlation_id}]'); exc.correlation_id=correlation_id
            raise exc from e
