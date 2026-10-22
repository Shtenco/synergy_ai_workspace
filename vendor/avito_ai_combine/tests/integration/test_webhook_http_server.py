import json, urllib.request
from avito_ai_combine.app.bootstrap import build_local_runtime
from avito_ai_combine.webhooks.server import WebhookServer

def test_webhook_server_accepts_and_deduplicates(tmp_path):
    rt=build_local_runtime(tmp_path); server=WebhookServer(rt.webhook_handler,host='127.0.0.1',port=0); server.start()
    try:
        url=f'http://127.0.0.1:{server.port}/avito/webhook'; data=json.dumps({'id':'e-http'}).encode()
        def post():
            req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'},method='POST')
            return json.loads(urllib.request.urlopen(req,timeout=2).read())
        assert post()['duplicate'] is False
        assert post()['duplicate'] is True
    finally: server.stop()
