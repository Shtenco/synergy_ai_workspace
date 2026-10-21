#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
PAGES=["workspaces.html","studio.html","lead-radar.html","caseflow.html"]
DEPS=["smm/smm26-workspace.css","smm/mission-v93.js","smm/studio.js","smm/workspace-pro.js","smm/caseflow.js","assets/pages-runtime.js"]
for rel in ["smm/"+p for p in PAGES]+DEPS:
    p=ROOT/"upstream"/rel
    if not p.is_file() or p.stat().st_size < 100:
        sys.exit("MISSING "+str(p))
    data=p.read_bytes()
    print(rel,len(data),hashlib.sha256(data).hexdigest())
    if rel.endswith(".html") and b"<html" not in data.lower():
        sys.exit("INVALID_HTML "+rel)
print("SMM SOURCE AND DEPENDENCIES VERIFIED")
