"""Freeze, launch and archive the registered study without overwriting previous results."""
from pathlib import Path
import argparse,hashlib,json,os,platform,shutil,subprocess,sys,traceback
from datetime import datetime,timezone
from analyze import evaluate,report
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,obj):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
def validate(reg):
 for n,h in reg['files'].items():
  p=(ROOT/n).resolve()
  if not p.is_relative_to(ROOT) or sha(p)!=h:raise ValueError('registration mismatch '+n)
 old=ROOT.parent/'round3_qpc'
 if sha(old/'registration.json')!=reg['old_registration_sha256']:raise ValueError('prior registration changed')
 oldreg=json.loads((old/'registration.json').read_text())
 for n,h in oldreg['files'].items():
  if sha(old/n)!=h:raise ValueError('prior study changed '+n)
def register():
 names=['PLAN.md','LITERATURE.md','ADAPTATION.md','config.json','dependencies.json','analyze.py','test_analysis.py','run_study.py','launch.sh']
 for folder in ('runner','external/smt'):
  names += [p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.is_file() and (p.suffix in {'.go','.mod','.exe'} or p.name in {'LICENSE','README.md'})]
 reg={'utc':datetime.now(timezone.utc).isoformat(),'files':{n:sha(ROOT/n) for n in sorted(names)},'old_registration_sha256':sha(ROOT.parent/'round3_qpc/registration.json')}
 validate(reg);save(ROOT/'registration.json',reg);print('REGISTERED',len(reg['files']))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--register',action='store_true');ap.add_argument('--work-dir',type=Path);a=ap.parse_args()
 if a.register:return register()
 if a.work_dir is None:raise ValueError('work dir required')
 reg=json.loads((ROOT/'registration.json').read_text());validate(reg)
 work=a.work_dir.resolve();work.parent.mkdir(parents=True,exist_ok=True);work.mkdir(exist_ok=False)
 save(work/'registration.json',reg);save(work/'config.json',json.loads((ROOT/'config.json').read_text()))
 save(work/'metadata.json',{'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'pid':os.getpid(),'registration_sha256':sha(ROOT/'registration.json')})
 for n in reg['files']:
  dest=work/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dest)
 try:
  p=subprocess.run([str(ROOT/'runner/conditional_runner.exe'),str(work/'measurements')],check=False)
  save(work/'runner_exit.json',{'returncode':p.returncode})
  if p.returncode:raise RuntimeError('runner failed')
  validate(reg)
  rows=[json.loads(s) for s in (work/'measurements/log.jsonl').read_text().splitlines()]
  diags=json.loads((work/'measurements/diagnostics.json').read_text())
  result=evaluate(rows,diags);save(work/'eval.json',result);report(result,diags,work/'REPORT.md')
  inventory={p.relative_to(work).as_posix():sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
  save(work/'completion.json',{'complete':True,'rows':len(rows),'gates':result['gates'],'files':inventory,'utc':datetime.now(timezone.utc).isoformat()})
  print('COMPLETED',json.dumps(result['gates']),flush=True)
 except BaseException as e:
  save(work/'failure.json',{'error':repr(e),'traceback':traceback.format_exc()});raise
if __name__=='__main__':main()
