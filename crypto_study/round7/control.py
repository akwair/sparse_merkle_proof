"""Freeze and execute a fixed serial application/frozen-corpus schedule."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'round5'


def utc(): return datetime.now(timezone.utc).isoformat()


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def read(path): return json.loads(Path(path).read_text(encoding='utf8'))


def save(path,obj):
    with Path(path).open('x',encoding='utf8') as f:
        json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')


def check_files(root,files):
    for name,digest in files.items():
        p=(root/name).resolve()
        if not isinstance(name,str) or not name or '\\' in name or ':' in name or Path(name).is_absolute() or not p.is_relative_to(root.resolve()):
            raise ValueError('unsafe manifest path')
        if not p.is_file() or sha(p)!=digest: raise ValueError('changed file '+name)


def check_schedule(config):
    for k,v in dict(process_blocks=5,minimum_block_start_seconds=120,seed=3407,gomaxprocs=8).items():
        if config[k]!=v: raise ValueError('schedule changed '+k)


def check_preflight(root,receipt,source_names):
    if receipt.get('passed') is not True: raise ValueError('preflight not passed')
    if set(receipt['source_files'])!=set(source_names): raise ValueError('preflight source inventory')
    check_files(root,receipt['source_files'])
    expected={'linux_go','python','frozen_validate'}
    tests=receipt['tests']
    if len(tests)!=3 or {t['name'] for t in tests}!=expected: raise ValueError('preflight test inventory')
    for t in tests:
        if t['exit_code']!=0: raise ValueError('failed preflight test '+t['name'])
        check_files(root,{t['log']:t['log_sha256']})
    if receipt['corpus']!=dict(artifacts=1542,restorations=1728,observations=36288,legacy_frames=288):
        raise ValueError('preflight corpus counts')


def frozen_module():
    # Its own analyzer is named analyze.py; Round7 uses app_analysis.py.
    sys.path.insert(0,str(OLD))
    spec=importlib.util.spec_from_file_location('frozen_round5_runner',OLD/'run_study.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def verify_old():
    cfg=read(ROOT/'config.json');check_schedule(cfg)
    if sha(OLD/'registration.json')!=cfg['frozen_registration_sha256'] or sha(OLD/'runner/conditional_runner')!=cfg['frozen_runner_sha256']:
        raise ValueError('frozen registration/executable changed')
    frozen=frozen_module();frozen.validate(read(OLD/'registration.json'))
    return frozen


def validate():
    reg=read(ROOT/'registration.json')
    if reg['seed']!=3407: raise ValueError('seed')
    check_files(ROOT,reg['files']);verify_old()
    check_preflight(ROOT,read(ROOT/'validation/preflight_receipt.json'),
                    {name for name in reg['files'] if not name.startswith('validation/')})
    return reg


def register():
    verify_old()
    required=['PLAN.md','LITERATURE.md','ADAPTATION.md','config.json','control.py','launch.sh',
              'app_analysis.py','audit_application.py','summarize_repetitions.py','test_repetitions.py',
              'test_app_analysis.py','test_audit_application.py','test_control.py','runner/app_runner',
              'runner/app_tests_linux','prior/round4_fixture_hashes.json','prior/linux_gold_eval.json',
              'validation/preflight_receipt.json']
    paths=set(required)
    for folder in ('runner','external/smt'):
        paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*')
                     if p.is_file() and (p.suffix=='.go' or p.name in ('go.mod','go.sum','LICENSE')))
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'validation').glob('*') if p.is_file())
    files={name:sha(ROOT/name) for name in sorted(paths)}
    check_preflight(ROOT,read(ROOT/'validation/preflight_receipt.json'),
                    {name for name in files if not name.startswith('validation/')})
    save(ROOT/'registration.json',{'utc':utc(),'seed':3407,'files':files,
         'frozen_registration_sha256':sha(OLD/'registration.json'),
         'frozen_runner_sha256':sha(OLD/'runner/conditional_runner')})
    validate();print('REGISTERED',len(files),sha(ROOT/'registration.json'),flush=True)


def start_application(index,reg,frozen):
    work=ROOT/'runs'/f'app_{index:03d}'
    work.parent.mkdir(exist_ok=True);work.mkdir(exist_ok=False)
    save(work/'registration.json',reg);save(work/'config.json',read(ROOT/'config.json'))
    save(work/'metadata.json',{'utc':utc(),'controller_pid':os.getpid(),
          'registration_sha256':sha(ROOT/'registration.json'),'block':index})
    for name in reg['files']:
        dest=work/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,dest)
    save(work/'resources_before.json',frozen.resource_snapshot('before_application'))
    try:
        process=subprocess.Popen([str(ROOT/'runner/app_runner'),'--application',str(work/'measurements')])
        save(work/'process.json',{'pid':process.pid,'utc':utc()})
        rc=process.wait();save(work/'runner_exit.json',{'returncode':rc,'utc':utc()})
    finally:
        save(work/'resources_after.json',frozen.resource_snapshot('after_application'))
    if rc: raise RuntimeError('application runner failed '+str(work))
    if not read(work/'measurements/completion.json')['complete']: raise RuntimeError('incomplete application')
    from app_analysis import validate_rows
    rows=[json.loads(x) for x in (work/'measurements/log.jsonl').read_text().splitlines()]
    validate_rows(rows,read(work/'measurements/diagnostics.json'))
    return work


def frozen_repeat(index):
    env=os.environ.copy();env['PYTHON']='/usr/bin/python3'
    name=f'r7_rep_{index:03d}'
    p=subprocess.run(['/usr/bin/bash','--noprofile','--norc',str(OLD/'launch.sh'),name],env=env,
                     capture_output=True,text=True,check=False)
    if p.returncode: raise RuntimeError('frozen launch failed: '+p.stdout+p.stderr)
    lines=p.stdout.strip().splitlines()
    if len(lines)!=1 or not lines[0].startswith('Dispatched '): raise RuntimeError('unknown frozen dispatch')
    launch=Path(lines[0].removeprefix('Dispatched ')).resolve()
    if not launch.is_relative_to((OLD/'launches').resolve()): raise ValueError('foreign launch')
    print(p.stdout.strip(),flush=True)
    # No study work runs concurrently; this only waits for the child launcher.
    deadline=time.monotonic()+3600
    while not (launch/'python.exit').is_file():
        if time.monotonic()>deadline: raise TimeoutError('frozen launcher has not completed; do not rerun')
        time.sleep(1)
    if int((launch/'python.exit').read_text())!=0: raise RuntimeError('frozen run failed '+str(launch))
    work=OLD/'runs'/name
    if not read(work/'completion.json')['complete']: raise RuntimeError('frozen incomplete')
    return work,launch


def execute(dispatch):
    if not dispatch.resolve().is_relative_to((ROOT/'launches').resolve()): raise ValueError('dispatch outside round7')
    blocks=[];previous_start=None
    try:
        reg=validate();cfg=read(ROOT/'config.json');frozen=verify_old()
        frozen.check_runtime(cfg)
        if 'GODEBUG' in os.environ: raise ValueError('GODEBUG must be unset')
        save(dispatch/'start.json',{'utc':utc(),'pid':os.getpid(),'platform':platform.platform(),
             'registration_sha256':sha(ROOT/'registration.json')})
        for index in range(1,6):
            if previous_start is not None:
                time.sleep(max(0,120-(time.monotonic()-previous_start)))
            start=time.monotonic();previous_start=start
            b={'index':index,'start_utc':utc(),'start_monotonic':start}
            print('ROUND7 BLOCK',index,b['start_utc'],flush=True)
            validate()
            app=start_application(index,reg,frozen)
            old,launch=frozen_repeat(index)
            b.update(application=app.relative_to(ROOT).as_posix(),
                     frozen=old.relative_to(OLD).as_posix(),frozen_launch=launch.relative_to(OLD).as_posix(),
                     finish_utc=utc(),elapsed_seconds=time.monotonic()-start)
            save(dispatch/f'block_{index:03d}.json',b);blocks.append(b)
        # All measurements have ended before analysis starts.
        from app_analysis import evaluate, report
        for b in blocks:
            work=ROOT/b['application']
            rows=[json.loads(x) for x in (work/'measurements/log.jsonl').read_text().splitlines()]
            result=evaluate(rows,read(work/'measurements/diagnostics.json'))
            save(work/'eval.json',result);report(result,work/'REPORT.md')
            inventory={p.relative_to(work).as_posix():sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
            save(work/'completion.json',{'complete':True,'utc':utc(),'rows':len(rows),'gates':result['gates'],'files':inventory})
        validate()
        save(ROOT/'schedule_completion.json',{'complete':True,'utc':utc(),'blocks':blocks,
             'dispatch':dispatch.relative_to(ROOT).as_posix(),'registration_sha256':sha(ROOT/'registration.json')})
        print('ROUND7 TIMING SCHEDULE COMPLETE',flush=True)
        from summarize_repetitions import run as summarize
        summarize()
    except BaseException as exc:
        save(dispatch/'failure.json',{'utc':utc(),'error':repr(exc),'traceback':traceback.format_exc(),'completed_blocks':blocks})
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--register',action='store_true');g.add_argument('--validate',action='store_true')
    g.add_argument('--execute',type=Path);a=p.parse_args()
    if a.register: register()
    elif a.validate: validate();print('ROUND7 REGISTRATION VALID')
    else: execute(a.execute)
