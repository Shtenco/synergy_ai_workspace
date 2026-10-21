"""Import ORIGINAL GitHub content; never replace with mock screens.
Run on a machine with Git and github.com access. Preserves provenance via pin hashes.
"""
from pathlib import Path
import argparse, subprocess, json, hashlib, shutil, os
ROOT=Path(__file__).resolve().parent
SOURCES={
 'smm':('https://github.com/Shtenco/synergy.github.io.git','main',ROOT/'vendor'/'synergy.github.io'),
 'autopilot-python':('https://github.com/Shtenco/synergy_agi_autopilot.git','feat/capability-runtime-v1',ROOT/'vendor'/'python-runtime'),
 'autopilot-desktop':('https://github.com/Shtenco/synergy_agi_autopilot.git','integration/synergy-ai-autopilot-v1',ROOT/'vendor'/'desktop-integration'),
}
def run(*args):return subprocess.check_output(list(args),text=True,stderr=subprocess.STDOUT).strip()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--only',choices=[*SOURCES,'all'],default='all'); a=ap.parse_args()
 out=[]
 for key,(url,branch,dst) in SOURCES.items():
  if a.only not in ('all',key):continue
  if dst.exists() and (dst/'.git').exists():
   run('git','-C',str(dst),'fetch','--depth','1','origin',branch)
   run('git','-C',str(dst),'checkout','-B','synergy-import','FETCH_HEAD')
  elif dst.exists():
   raise SystemExit('REFUSING to overwrite existing source: '+str(dst))
  else:
   dst.parent.mkdir(parents=True,exist_ok=True)
   run('git','clone','--single-branch','--branch',branch,'--depth','1',url,str(dst))
  sha=run('git','-C',str(dst),'rev-parse','HEAD')
  dirty=bool(run('git','-C',str(dst),'status','--porcelain'))
  if dirty:raise SystemExit('Dirty import: '+str(dst))
  out.append({'source':key,'repository':url,'branch':branch,'commit':sha,'relative_path':str(dst.relative_to(ROOT))})
 if out:
  p=ROOT/'source-provenance.json'; old=json.loads(p.read_text()) if p.exists() else []
  old=[x for x in old if x['source'] not in [y['source'] for y in out]] + out
  p.write_text(json.dumps(old,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
