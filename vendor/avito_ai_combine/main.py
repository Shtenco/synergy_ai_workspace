import argparse,json,os
from pathlib import Path
from avito_ai_combine.ui.app import AvitoAICombineApp
from avito_ai_combine.app.bootstrap import build_live_runtime
from avito_ai_combine.services.connection import ConnectionService

def main(argv=None):
    p=argparse.ArgumentParser(prog='AVITO AI COMBINE')
    p.add_argument('--check',action='store_true'); p.add_argument('--check-live',action='store_true')
    p.add_argument('--data-dir',default=str(Path.home()/'.avito_ai_combine'))
    p.add_argument('--client-id',default=os.getenv('AVITO_CLIENT_ID',''))
    p.add_argument('--client-secret',default=os.getenv('AVITO_CLIENT_SECRET',''))
    a=p.parse_args(argv)
    app=AvitoAICombineApp(a.data_dir)
    if a.check: print(json.dumps(app.health(),ensure_ascii=False)); return 0
    if a.check_live:
        if not a.client_id or not a.client_secret:
            print(json.dumps({'ok':False,'reason':'not_configured','message':'Set AVITO_CLIENT_ID and AVITO_CLIENT_SECRET or pass CLI values.'},ensure_ascii=False)); return 2
        try:
            rt=build_live_runtime(a.data_dir,client_id=a.client_id,client_secret=a.client_secret,acquire_token=True)
            result=ConnectionService(rt.account_client,rt.capabilities).check(); print(json.dumps(result,ensure_ascii=False)); return 0
        except Exception as exc:
            print(json.dumps({'ok':False,'reason':'connection_failed','error':str(exc)},ensure_ascii=False)); return 1
    app.run(); return 0
if __name__=='__main__': raise SystemExit(main())
