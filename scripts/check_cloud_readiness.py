"""Source-only readiness check. Never uses cloud credentials or network."""
from pathlib import Path
import sys
r=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
required=[r/"workspace"/"service.py",r/"workspace"/"capital_engine.py"]
for p in required: print("OK" if p.exists() else "MISSING",p.relative_to(r))
if not all(p.exists() for p in required):sys.exit(1)
if "('127.0.0.1',8129)" not in required[0].read_text(encoding="utf-8"):
 print("NO-GO: re-review local bind");sys.exit(2)
print("SOURCE-ONLY PASS; cloud authorization/deployment not verified.")
