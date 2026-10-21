import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
class WebhookServer:
    def __init__(self,handler,host='127.0.0.1',port=8765): self.ingest_handler=handler; self.host=host; self.requested_port=port; self.httpd=None; self.thread=None
    @property
    def port(self): return self.httpd.server_address[1] if self.httpd else self.requested_port
    def start(self):
        ingest=self.ingest_handler
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path in ('/health','/avito/health'): self._reply(200,{'ok':True,'service':'AVITO AI COMBINE webhook'})
                else: self._reply(404,{'ok':False})
            def do_POST(self):
                if self.path!='/avito/webhook': return self._reply(404,{'ok':False})
                try:
                    n=int(self.headers.get('Content-Length','0')); payload=json.loads(self.rfile.read(n) or b'{}'); result=ingest.ingest(payload); self._reply(200,result)
                except Exception as exc: self._reply(400,{'ok':False,'error':type(exc).__name__})
            def _reply(self,status,payload):
                body=json.dumps(payload,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
            def log_message(self,*args): pass
        self.httpd=ThreadingHTTPServer((self.host,self.requested_port),H); self.thread=threading.Thread(target=self.httpd.serve_forever,name='avito-webhook',daemon=True); self.thread.start(); return self
    def stop(self):
        if self.httpd: self.httpd.shutdown(); self.httpd.server_close(); self.httpd=None
        if self.thread and self.thread.is_alive(): self.thread.join(timeout=2)
