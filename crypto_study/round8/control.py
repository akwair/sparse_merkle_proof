"""Registered finite-window controller. No cloud credentials or package installs."""
from pathlib import Path
import argparse,hashlib,json,os,random,signal,subprocess,sys,time,traceback,urllib.request

ROOT=Path('/RESEARCH_WORKSPACE/round8')

def write_json(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def schedule(config):
    rng=random.Random(config['seed']);entries=[]
    def add(phase,epoch,case,mode,c,link='lan',kind=None,cpu=None):
        suffix='' if kind is None else '_'+kind+('_'+str(cpu) if cpu else '')
        ident=f'{phase}_e{epoch:02d}_{case}_c{c:02d}_{mode}_{link}{suffix}'
        entries.append({'id':ident,'phase':phase,'epoch':epoch,'domain':case.split('_')[0], 'case_id':case,'mode':mode,
            'concurrency':c,'link':link,'diagnostic_kind':kind,'client_gomaxprocs':cpu or (4 if phase=='controlled' else 8),
            'work_dir':'clients/'+ident})
    for epoch in range(1,config['epochs']+1):
        cells=[(f'{d}_n16384_q128_v{v}_member_{dist}',c) for d in config['domains'] for v in config['value_bytes'] for dist in config['distributions'] for c in config['concurrency']]
        rng.shuffle(cells)
        for case,c in cells:
            modes=list(config['modes']);rng.shuffle(modes)
            for mode in modes:add('crosshost',epoch,case,mode,c)
        domains=list(config['domains']);rng.shuffle(domains)
        for d in domains:
            modes=list(config['modes']);rng.shuffle(modes)
            for mode in modes:add('q1_anchor',epoch,f'{d}_n16384_q1_v32_member_uniform',mode,1)
        diag=[(d,v) for d in config['domains'] for v in config['value_bytes']];rng.shuffle(diag)
        for d,v in diag:
            modes=list(config['modes']);rng.shuffle(modes)
            for mode in modes:add('diagnostic',epoch,f'{d}_n16384_q128_v{v}_member_zipf',mode,16,kind='replay')
        for d in config['domains']:
            budgets=[4,8];rng.shuffle(budgets)
            for cpu in budgets:add('diagnostic',epoch,f'{d}_n16384_q128_v32_member_zipf','ordinary',16,kind='client_budget',cpu=cpu)
    for epoch in range(1,config['epochs']+1):
        cells=[(link,d) for link in config['controlled_links'] for d in config['domains']];rng.shuffle(cells)
        for link,d in cells:
            modes=list(config['modes']);rng.shuffle(modes)
            for mode in modes:add('controlled',epoch,f'{d}_n16384_q128_v32_member_zipf',mode,1,link=link)
    assert len(entries)==444 and len({x['id'] for x in entries})==444
    return entries

def initialize():
    config=json.loads((ROOT/'config.json').read_text());out=ROOT/'results/network_001';out.mkdir(parents=True,exist_ok=False)
    (out/'clients').mkdir();(out/'phase_receipts').mkdir()
    write_json(out/'schedule.json',schedule(config));write_json(out/'config.json',config)
    (out/'provenance').mkdir()
    receipt_map={};values={}
    for role,host in [('client','secondary'),('server','primary'),('controlled_server','secondary')]:
        original=ROOT/'preflight'/(host+'_proc_clock_ticks.json')
        observed=json.loads(original.read_text());assert observed['source']=='os.sysconf(SC_CLK_TCK)' and observed['role']==host
        assert isinstance(observed['value'],int) and observed['value']>0
        if host=='secondary':assert observed['value']==os.sysconf('SC_CLK_TCK')
        target=out/'provenance'/original.name
        if not target.exists():target.write_bytes(original.read_bytes())
        receipt_map[role]={'path':'provenance/'+original.name,'sha256':digest(target),'field':'value'}
        values[role+'_proc_clock_ticks_per_second']=observed['value']
    write_json(out/'environment.json',{**values,'proc_clock_tick_receipts':receipt_map,
        'utc_unix':time.time(),'new_timing_runs':0})
    print('INITIALIZED',out,flush=True)

def http_json(url):
    with urllib.request.urlopen(url,timeout=10) as r:return json.load(r)

def event(out,kind,**fields):
    data={'utc_unix':time.time(),'event':kind,**fields}
    with (out/'controller_events.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
    state=out/'CURRENT_STATE.json';tmp=out/'CURRENT_STATE.tmp';tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(state)
    print(json.dumps(data),flush=True)

def verify_registration():
    reg=json.loads((ROOT/'REGISTRATION.json').read_text());assert reg['registered_before_formal']
    for name,sha in reg['files'].items():assert digest(ROOT/name)==sha,name
    return reg

def private_context():
    p=json.loads((ROOT/'preflight/private_link.json').read_text());assert p['available']
    identities=json.loads((ROOT/'preflight/private_link_identity.json').read_text())
    for role in ['server','client']:
        pid=p[role+'_pid'];assert os.readlink(f'/proc/{pid}/ns/net')==identities[role+'_netns']
    return p

def tc_command(pid,args,out):
    tool=ROOT/'offline_tools/iproute2/bin/tc';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(ROOT/'offline_tools/iproute2/lib')
    cmd=['nsenter','--target',str(pid),'--net','--',str(tool)]+args
    r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=15)
    event(out,'private_tc',argv=cmd,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    return r

def set_link(link,out):
    p=private_context()
    for role,iface in [('server','r8sa'),('client','r8cl')]:
        pid=p[role+'_pid']
        if link=='unshaped':
            r=tc_command(pid,['qdisc','del','dev',iface,'root'],out)
            # An absent custom root is the intended unshaped state.
            assert r.returncode==0 or ('Cannot delete qdisc with handle of zero' in r.stderr or 'No such file' in r.stderr),r.stderr
        else:
            rate='10mbit' if link=='10mbit_2ms' else '100mbit'
            r=tc_command(pid,['qdisc','replace','dev',iface,'root','netem','limit','4096','delay','1ms','rate',rate],out);assert r.returncode==0
        assert tc_command(pid,['-j','-s','qdisc','show','dev',iface],out).returncode==0

def namespace_prefix():return ['nsenter','--target',str(private_context()['client_pid']),'--net','--']

def run_cell(entry,config,out,expected_server_pid=None):
    diag=entry['phase']=='diagnostic';controlled=entry['phase']=='controlled';replay=entry['diagnostic_kind']=='replay'
    url=config['controlled_url'] if controlled else (config['replay_url'] if replay else config['primary_url'])
    prefix=namespace_prefix() if controlled else []
    if not controlled:
        stats=http_json(url+'/stats');assert stats['replay']==replay
        pid=int(stats['proc']['stat'].split(' ',1)[0]);assert expected_server_pid is None or pid==expected_server_pid,(pid,expected_server_pid)
    warm=config['diagnostic_warmup_seconds'] if diag else config['warmup_seconds']
    seconds=config['diagnostic_measurement_seconds'] if diag else config['measurement_seconds']
    cpus=config['controlled_client_cpus'] if controlled else ('0-3' if entry['client_gomaxprocs']==4 else config['primary_client_cpus'])
    binary=ROOT/'bin/netbench_final';work=out/entry['work_dir']
    cmd=prefix+['taskset','-c',cpus,str(binary),'client','--data',str(ROOT/'inputs'),'--url',url,
        '--case',entry['case_id'],'--mode',entry['mode'],'--concurrency',str(entry['concurrency']),
        '--warmup',str(warm)+'s','--duration',str(seconds)+'s','--timeout',str(config['http_timeout_seconds'])+'s','--work-dir',str(work)]
    env=os.environ.copy();env['GOMAXPROCS']=str(entry['client_gomaxprocs']);env.pop('GOGC',None);env.pop('GOMEMLIMIT',None)
    start=time.time();event(out,'cell_start',entry=entry,argv=cmd)
    try:
        with (ROOT/'ALL_RUNS.log').open('ab') as common:
            child=subprocess.Popen(cmd,env=env,stdout=common,stderr=subprocess.STDOUT,start_new_session=True)
            try:rc=child.wait(timeout=config['controller_watchdog_seconds'])
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                raise RuntimeError('client process exceeded registered whole-process watchdog')
        summary=json.loads((work/'summary.json').read_text()) if (work/'summary.json').exists() else None
        completion=json.loads((work/'completion.json').read_text()) if (work/'completion.json').exists() else None
        receipt={'entry':entry,'returncode':rc,'start_unix':start,'end_unix':time.time(),'summary_present':summary is not None,'completion':completion}
        with (out/'cell_receipts.jsonl').open('a') as f:f.write(json.dumps(receipt)+'\n')
        assert summary is not None and completion is not None,'missing measurement output'
        assert summary['server_replay']==replay,'wrong server endpoint'
        assert summary['integrity_ok'],'integrity failure; stop and retain'
        assert summary['measurement_complete'],'incomplete measurement; stop and retain'
        assert rc==0,'client command failed; artifacts retained'
        event(out,'cell_done',id=entry['id'],errors=summary['errors'],success=summary['success'],fixed_window_verified_success=summary['fixed_window_verified_success'])
    except Exception as e:
        write_json(out/'phase_receipts'/('FAILED_'+entry['id']+'.json'),{'entry':entry,'error':repr(e),'utc_unix':time.time()})
        event(out,'cell_failed',id=entry['id'],error=repr(e));raise

def run_phase(phase,epoch,server_pid,replay_pid):
    verify_registration();config=json.loads((ROOT/'config.json').read_text());out=ROOT/'results/network_001'
    all_entries=json.loads((out/'schedule.json').read_text())
    selected=[x for x in all_entries if x['epoch']==epoch and (x['phase']=='controlled' if phase=='controlled' else x['phase']!='controlled')]
    assert len(selected)==(24 if phase=='controlled' else 124)
    receipt_file=out/'phase_receipts'/f'{phase}_epoch_{epoch:03d}.json';assert not receipt_file.exists()
    start=time.time();event(out,'phase_start',phase=phase,epoch=epoch,cells=len(selected))
    link=None
    for entry in selected:
        if phase=='controlled' and link!=entry['link']:
            set_link(entry['link'],out);link=entry['link']
        pid=replay_pid if entry['diagnostic_kind']=='replay' else server_pid
        run_cell(entry,config,out,pid)
    if phase=='controlled':set_link('unshaped',out)
    write_json(receipt_file,{'complete':True,'phase':phase,'epoch':epoch,'cells':len(selected),'start_unix':start,'end_unix':time.time()})
    event(out,'phase_complete',phase=phase,epoch=epoch,cells=len(selected))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['init','run']);parser.add_argument('--phase',choices=['crosshost','controlled']);parser.add_argument('--epoch',type=int);parser.add_argument('--server-pid',type=int);parser.add_argument('--replay-pid',type=int);args=parser.parse_args()
    if args.action=='init':initialize()
    else:
        assert args.phase and args.epoch in [1,2,3]
        run_phase(args.phase,args.epoch,args.server_pid,args.replay_pid)
