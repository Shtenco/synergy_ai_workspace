from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent
source=ROOT/'vendor'/'synergy.github.io'/'smm'
dest=ROOT/'desktop'/'public'/'original-smm'
manifest=ROOT/'desktop'/'public'/'smm-provenance.json'
if not manifest.exists():raise SystemExit('Original SMM import missing; no ready status')
data=json.loads(manifest.read_text())
for rel,digest in data['files'].items():
 s=(source/rel).resolve();d=(dest/rel).resolve()
 if not s.is_relative_to(source.resolve()) or not d.is_relative_to(dest.resolve()):raise SystemExit('Unsafe manifest path: '+rel)
 if not s.is_file() or not d.is_file() or hashlib.sha256(s.read_bytes()).hexdigest()!=digest or s.read_bytes()!=d.read_bytes():
  raise SystemExit('Source integrity failure: '+rel)
print('PASS provenance verified:',len(data['files']),'original files')
