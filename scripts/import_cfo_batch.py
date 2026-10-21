#!/usr/bin/env python3
"""Import a reviewed AI CFO JSON batch into the private Workspace service.

Requires a local workspace operator Bearer token supplied through SYNERGY_TOKEN.
Makes exactly one loopback POST. Never sends data to GitHub Pages or remote APIs.
"""
from __future__ import annotations
import argparse,json,os,sys,urllib.request,urllib.error
from pathlib import Path

ENDPOINT="http://127.0.0.1:8129/v1/capital/import"
def main(argv=None):
    cli=argparse.ArgumentParser(description="SYNERGY CFO -> Workspace local finance import")
    cli.add_argument("file",help="reviewed JSON file exported by AI CFO")
    args=cli.parse_args(argv)
    token=os.environ.get("SYNERGY_TOKEN","")
    if not token or len(token)<12:
        cli.error("Set SYNERGY_TOKEN to your LOCAL Workspace token before importing.")
    path=Path(args.file).expanduser()
    if not path.is_file() or path.stat().st_size>2_000_000:
        cli.error("Source JSON file not found or larger than 2 MB.")
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload,dict) or payload.get("operator_reviewed") is not True:
            cli.error("Only operator-reviewed CFO packages are accepted")
        # The server deliberately ignores browser-supplied 'verified_by_bank' claims.
        data={k:payload[k] for k in ("source_id","currency","period_start","period_end","entries")}
    except (UnicodeError,ValueError,KeyError) as e:
        cli.error("Invalid CFO export package: "+str(e))
    req=urllib.request.Request(ENDPOINT,data=json.dumps(data,ensure_ascii=False).encode(),
       headers={"Authorization":"Bearer "+token,"Content-Type":"application/json","Accept":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=10) as response:
            out=json.load(response)
    except urllib.error.HTTPError as e:
        print("Import refused by Workspace (HTTP "+str(e.code)+")",file=sys.stderr)
        return 1
    except (OSError,ValueError) as e:
        print("Workspace local service unavailable or invalid response",file=sys.stderr)
        return 1
    print(json.dumps({k:out.get(k) for k in ("source_id","status","sha256","imported","external_effects")},ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":sys.exit(main())
