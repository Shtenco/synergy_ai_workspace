"""Copy pristine original SMM web assets into Tauri/Vite public content.
No HTML rewrites, no fabricated screens. Run after import_original_sources.py.
"""
from pathlib import Path
import shutil, json, hashlib
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'vendor'/'synergy.github.io'/'smm'
DEST=ROOT/'desktop'/'public'/'original-smm'
CABINETS=('workspaces.html','studio.html','lead-radar.html','ai-studio.html','caseflow.html','cabinet.html')
def sync():
 if not SOURCE.is_dir() or not (SOURCE/'index.html').is_file():
  raise SystemExit('Original SMM source unavailable: run python import_original_sources.py first')
 DEST.parent.mkdir(parents=True,exist_ok=True)
 if DEST.exists(): shutil.rmtree(DEST)
 shutil.copytree(SOURCE,DEST,dirs_exist_ok=False,symlinks=False)
 files=[p for p in SOURCE.rglob('*') if p.is_file()]
 manifest={'upstream':'Shtenco/synergy.github.io','branch':'main','files':{},'cabinet_status':{n:(SOURCE/n).is_file() for n in CABINETS}}
 for p in files:
  manifest['files'][p.relative_to(SOURCE).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 (DEST.parent/'smm-provenance.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print(f'Synced {len(files)} original SMM assets; wrote provenance manifest')
 return manifest
if __name__=='__main__':sync()
