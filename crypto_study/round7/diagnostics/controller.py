"""Seal and execute the separate, allocation-only diagnostic."""
import argparse,hashlib,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from analyze import CASES,read,save,run as analyze

ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent
PARENT_SHA='ed90a24551cdff1cbbf9472601f0cbbeb8f991e505870e6182f3f5e84d26d81a'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else hashlib.sha256(f.read()).hexdigest()

def now():return datetime.now(timezone.utc).isoformat()

def parent_valid():
    if sha(PARENT/'registration.json')!=PARENT_SHA:raise ValueError('parent registration changed')
    parent=read(PARENT/'registration.json')
    dependency={n:h for n,h in parent['files'].items() if n.startswith('external/smt/')}
    actual={p.relative_to(PARENT).as_posix():sha(p) for p in (PARENT/'external/smt').rglob('*') if p.is_file()}
    extra=set(actual)-set(dependency)
    if any(actual.get(n)!=h for n,h in dependency.items()) or any(n!='external/smt/README.md' for n in extra):raise ValueError('pinned dependency inventory or content changed')
    expected_mod='module ccpe-round7-allocation-diagnostic\n\ngo 1.23\n\nrequire github.com/celestiaorg/smt v0.0.0\n\nreplace github.com/celestiaorg/smt => ../../external/smt\n'
    if (ROOT/'runner/go.mod').read_text()!=expected_mod:raise ValueError('dependency module path/version')
    if not read(PARENT/'schedule_completion.json')['complete'] or not read(PARENT/'REPETITIONS.json')['complete']:raise ValueError('timing incomplete')
    for n in ('codec.go','legacy.go','clock_linux.go','clock_windows.go'):
        if sha(ROOT/'runner'/n)!=sha(PARENT/'runner'/n) or sha(ROOT/'runner'/n)!=parent['files']['runner/'+n]:raise ValueError('timing source changed: '+n)
    for case in CASES:
        h=sha(ROOT/'inputs'/case/'bundle.json')
        if h!=sha(PARENT/'runs/app_001/measurements'/case/'bundle.json') or h!=read(PARENT/'runs/app_001/completion.json')['files']['measurements/'+case+'/bundle.json']:raise ValueError('input binding: '+case)

def runtime_valid():
    if platform.system()!='Linux' or platform.machine()!='x86_64':raise ValueError('Linux amd64 required')
    if os.environ.get('GOMAXPROCS')!='8' or any(k in os.environ for k in ('GOGC','GOMEMLIMIT','GODEBUG')):raise ValueError('runtime controls')

def freeze():
    parent_valid();runtime_valid()
    for n in ('linux_go','linux_python'):
        if (ROOT/'validation'/f'{n}_001.exit').read_text().strip()!='0':raise ValueError('preflight failed')
    if '\nPASS\n' not in (ROOT/'validation/linux_go_001.log').read_text():raise ValueError('Go test missing PASS')
    if '\nOK\n' not in (ROOT/'validation/linux_python_001.log').read_text():raise ValueError('Python test missing OK')
    names=('PLAN.md','ADAPTATION.md','analyze.py','test_analyze.py','controller.py','launch.sh','config.json')
    paths=[ROOT/n for n in names]
    paths += [p for folder in ('runner','inputs','validation') for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'tmp' not in p.relative_to(ROOT).parts]
    files={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    # Bind already audited parent roots, input bytes, and source without changing it.
    save(ROOT/'registration.json',dict(utc=now(),parent_registration_sha256=PARENT_SHA,files=files,
        source_application='runs/app_001',source_application_audit_sha256=sha(PARENT/'audits/app_001.json'),
        source_completion_sha256=sha(PARENT/'runs/app_001/completion.json')))
    print('DIAGNOSTIC REGISTERED',len(files),sha(ROOT/'registration.json'),flush=True)

def verify():
    parent_valid();reg=read(ROOT/'registration.json')
    if reg['parent_registration_sha256']!=PARENT_SHA:raise ValueError('registration parent')
    for n,h in reg['files'].items():
        if sha(ROOT/n)!=h:raise ValueError('registered file changed '+n)
    if reg['source_application_audit_sha256']!=sha(PARENT/'audits/app_001.json') or reg['source_completion_sha256']!=sha(PARENT/'runs/app_001/completion.json'):raise ValueError('source receipt changed')
    return reg

def execute(dispatch):
    dispatch=Path(dispatch);work=ROOT/'runs/allocation_001'
    try:
        runtime_valid();reg=verify()
        if work.exists():raise ValueError('work dir exists')
        (ROOT/'runs').mkdir(exist_ok=True)
        save(dispatch/'start.json',dict(utc=now(),registration_sha256=sha(ROOT/'registration.json'),
            hostname=platform.node(),machine=platform.machine(),system=platform.platform(),
            env={k:os.environ.get(k) for k in ('GOMAXPROCS','GOGC','GOMEMLIMIT','GODEBUG')},
            loadavg=os.getloadavg(),source_files=reg['files']))
        command=[str(ROOT/'runner/diagnostic_runner'),str(ROOT/'inputs'),str(work)]
        print('DIAGNOSTIC RUN',work,now(),flush=True)
        code=subprocess.run(command,check=False).returncode
        (dispatch/'runner.exit').write_text(str(code)+'\n')
        if code:raise RuntimeError('diagnostic runner failed '+str(code))
        verify()
        env=read(work/'env.json')
        if env['os']!='linux' or env['arch']!='amd64' or env['go']!='go1.27.3' or env['gomaxprocs']!=8:raise ValueError('runner runtime')
        if any(env[k] for k in ('gogc_env_set','gomemlimit_env_set','godebug_env_set')):raise ValueError('runner environment overrides')
        result=analyze(work)
        save(work/'audit.json',dict(complete=True,utc=now(),rows=result['rows'],operations=result['operations'],
            registration_sha256=sha(ROOT/'registration.json'),input_files={n:h for n,h in reg['files'].items() if n.startswith('inputs/')},
            output_files={p.name:sha(p) for p in work.iterdir() if p.is_file()},
            scope='independent Python matrix and counter arithmetic checks; native Go stage correctness checks; copied input hashes bound to independently audited application corpus'))
        save(dispatch/'finish.json',dict(utc=now(),complete=True,loadavg=os.getloadavg(),hypothesis=result['allocation_hypothesis']))
        print('DIAGNOSTIC COMPLETE',result['allocation_hypothesis'],now(),flush=True)
    except Exception as e:
        save(dispatch/'failure.json',dict(utc=now(),error=repr(e)));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--freeze',action='store_true');g.add_argument('--execute');g.add_argument('--verify',action='store_true');a=p.parse_args()
    if a.freeze:freeze()
    elif a.verify:verify();print('REGISTRATION VERIFIED')
    else:execute(a.execute)
