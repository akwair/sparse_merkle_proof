"""Start/stop only owned Round8 processes, with common append-only console logs."""
from pathlib import Path
import argparse,hashlib,json,os,signal,subprocess,time,urllib.request

ROOT=Path('/RESEARCH_WORKSPACE/round8')

def proc_identity(pid):
    raw=Path(f'/proc/{pid}/stat').read_text();tail=raw[raw.rfind(')')+2:].split()
    return {'pid':pid,'starttime_ticks':int(tail[19]),'cmdline':Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0',b' ').decode()}

def verify_registered(pilot):
    if pilot:return
    r=json.loads((ROOT/'REGISTRATION.json').read_text());assert r['registered_before_formal']
    for n,want in r['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==want,n

def json_get(url,prefix):
    if not prefix:
        with urllib.request.urlopen(url,timeout=2) as r:return json.load(r)
    code='import urllib.request,json; print(urllib.request.urlopen('+repr(url)+',timeout=2).read().decode())'
    p=subprocess.run(prefix+['/opt/conda/bin/python','-c',code],capture_output=True,text=True,timeout=4)
    if p.returncode:raise RuntimeError(p.stderr)
    return json.loads(p.stdout)

def start(role,epoch,pilot):
    verify_registered(pilot);(ROOT/'servers').mkdir(exist_ok=True)
    stem=('pilot_' if pilot else '')+f'{role}_e{epoch:03d}'
    record=ROOT/'servers'/(stem+'_pids.json');assert not record.exists()
    binary=ROOT/'bin/netbench_final';assert binary.is_file()
    jobs=[];children=[]
    cfg=json.loads((ROOT/'config.json').read_text())
    if role=='primary':
        definitions=[('native',cfg['primary_url'],False),('replay',cfg['replay_url'],True)];prefix=[];cpus=cfg['primary_server_cpus'];procs=cfg['primary_gomaxprocs'];workers=cfg['primary_workers']
    else:
        ns=json.loads((ROOT/'preflight/private_link.json').read_text());assert ns['available']
        identities=json.loads((ROOT/'preflight/private_link_identity.json').read_text());pid=ns['server_pid']
        assert os.readlink(f'/proc/{pid}/ns/net')==identities['server_netns']
        prefix=['nsenter','--target',str(pid),'--net','--'];definitions=[('native',cfg['controlled_url'],False)];cpus=cfg['controlled_server_cpus'];procs=cfg['controlled_gomaxprocs'];workers=cfg['controlled_workers']
    try:
        for label,url,replay in definitions:
            work=ROOT/'servers'/(stem+'_'+label);assert not work.exists()
            listen=url.split('://',1)[1]
            cmd=['nohup']+prefix+['taskset','-c',cpus,str(binary),'serve','--data',str(ROOT/'inputs'),'--listen',listen,'--workers',str(workers),'--work-dir',str(work)]
            if replay:cmd+=['--replay']
            env=os.environ.copy();env['GOMAXPROCS']=str(procs);env.pop('GOGC',None);env.pop('GOMEMLIMIT',None)
            with (ROOT/'ALL_RUNS.log').open('ab') as common:
                child=subprocess.Popen(cmd,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=common,stderr=subprocess.STDOUT,start_new_session=True)
            children.append(child)
            deadline=time.monotonic()+100
            while True:
                if child.poll() is not None:raise RuntimeError(f'{label} server exited {child.returncode}')
                try:
                    health=json_get(url+'/health',prefix)
                    if health.get('ready') or health.get('status')=='ready':break
                except Exception:pass
                if time.monotonic()>deadline:raise RuntimeError(f'{label} readiness deadline exceeded')
                time.sleep(.2)
            stats=json_get(url+'/stats',prefix);assert stats['replay']==replay and stats['workers']==workers
            jobs.append({'label':label,'url':url,'replay':replay,'work_dir':str(work),'argv':cmd,'process':proc_identity(child.pid),'ready_stats':stats})
        record.write_text(json.dumps({'role':role,'epoch':epoch,'pilot':pilot,'jobs':jobs,'started_unix':time.time()},indent=2)+'\n')
        print(json.dumps({'ready':True,'record':str(record),'jobs':[{'label':j['label'],'pid':j['process']['pid'],'url':j['url']} for j in jobs]}),flush=True)
    except Exception:
        for child in children:
            if child.poll() is None:child.terminate()
        raise

def stop(role,epoch,pilot):
    stem=('pilot_' if pilot else '')+f'{role}_e{epoch:03d}';record=ROOT/'servers'/(stem+'_pids.json');r=json.loads(record.read_text());result=[]
    for job in r['jobs']:
        identity=job['process'];pid=identity['pid'];alive=Path(f'/proc/{pid}').exists()
        if alive:
            now=proc_identity(pid);assert now['starttime_ticks']==identity['starttime_ticks'] and str(ROOT/'bin/netbench_final') in now['cmdline']
            assert job['work_dir'] in now['cmdline'];os.kill(pid,signal.SIGTERM)
        deadline=time.monotonic()+35;completion=Path(job['work_dir'])/'completion.json'
        while not completion.exists() and time.monotonic()<deadline:time.sleep(.1)
        if not completion.exists():raise RuntimeError('server did not record graceful completion')
        c=json.loads(completion.read_text());assert c['complete'] and c['shutdown']=='graceful'
        result.append({'label':job['label'],'pid':pid,'completion':c})
    out=ROOT/'servers'/(stem+'_stopped.json');assert not out.exists();out.write_text(json.dumps({'stopped':True,'jobs':result,'utc_unix':time.time()},indent=2)+'\n');print(out,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['start','stop']);p.add_argument('--role',choices=['primary','controlled'],required=True);p.add_argument('--epoch',type=int,required=True);p.add_argument('--pilot',action='store_true');a=p.parse_args()
    (start if a.action=='start' else stop)(a.role,a.epoch,a.pilot)
