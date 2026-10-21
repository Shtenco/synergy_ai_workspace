"""CI-only release gate: authentic upstream files required before EXE build."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'vendor/synergy.github.io/smm'
DST=ROOT/'desktop/public/original-smm'
M=ROOT/'desktop/public/smm-provenance.json'
P=ROOT/'source-provenance.json'
required=['workspaces.html','studio.html','lead-radar.html','ai-studio.html','caseflow.html','cabinet.html']
assert M.is_file() and P.is_file(),'SOURCE_NOT_IMPORTED'
manifest=json.loads(M.read_text(encoding='utf-8'))
provenance=json.loads(P.read_text(encoding='utf-8'))
assert {'smm','autopilot-python','autopilot-desktop'}.issubset({p['source'] for p in provenance})
assert all(manifest['cabinet_status'].get(name) for name in required),'MISSING_ORIGINAL_CABINET'
for rel,expected in manifest['files'].items():
    src=(SRC/rel).resolve(); dest=(DST/rel).resolve()
    assert src.is_relative_to(SRC.resolve()) and dest.is_relative_to(DST.resolve()),'PATH_TRAVERSAL'
    assert src.is_file() and dest.is_file()
    assert src.read_bytes()==dest.read_bytes()
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==expected
print('RELEASE GATE PASSED',len(manifest['files']),'authentic SMM assets')
