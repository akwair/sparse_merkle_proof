"""Preregistered screening runner. No resume or overwrite."""
from pathlib import Path
import hashlib
import argparse, json, os, platform, random, shutil, statistics, subprocess, sys, traceback
from datetime import datetime,timezone
from time import perf_counter_ns
from collections import defaultdict
import binary_transport as codec
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate(root,reg):
    root=Path(root).resolve()
    for name,digest in reg['files'].items():
        p=(root/name).resolve()
        if not p.is_relative_to(root) or not p.is_file() or sha(p)!=digest:raise ValueError('registered file mismatch: '+name)
def create_workdir(path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.mkdir(exist_ok=False);return p
def save(path,data):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
def writebytes(path,data):
    with Path(path).open('xb') as f:f.write(data)
def readrows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x]
def percentile(xs,p):
    xs=sorted(xs);pos=(len(xs)-1)*p;i=int(pos);return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(pos-i)
def evaluate(rows):
    groups=defaultdict(list)
    for x in rows:
        if x['bytes']<=0 or x['total_ns']<=0:raise ValueError('invalid measurement')
        groups[(x['host'],x['domain'],x['cell'])].append(x)
    cells=[]
    for (host,domain,cell),rr in sorted(groups.items()):
        base,target,threshold=('binary-full','binary-bitmap',.70) if host=='reference' else ('ordinary','compact',.95)
        pairs=defaultdict(dict);permode=defaultdict(list)
        for x in rr:
            key=(x['batch'],x['repeat'])
            if x['mode'] in pairs[key]:raise ValueError('duplicate pair')
            pairs[key][x['mode']]=x;permode[x['mode']].append(x)
        if any(base not in v or target not in v for v in pairs.values()):raise ValueError('missing pair')
        time=[v[target]['total_ns']/v[base]['total_ns'] for v in pairs.values()]
        byte=[v[target]['bytes']/v[base]['bytes'] for v in pairs.values()]
        stats={}
        for mode,obs in permode.items():
            stats[mode]={'median_bytes':statistics.median(x['bytes'] for x in obs),
                         'median_total_ns':statistics.median(x['total_ns'] for x in obs),
                         'p95_total_ns':percentile([x['total_ns'] for x in obs],.95),
                         'max_total_ns':max(x['total_ns'] for x in obs),
                         'median_encode_ns':statistics.median(x['encode_ns'] for x in obs),
                         'median_decode_ns':statistics.median(x['decode_ns'] for x in obs),
                         'median_verify_ns':statistics.median(x['verify_ns'] for x in obs)}
        cells.append({'host':host,'domain':domain,'cell':cell,'pairs':len(pairs),'byte_ratio':max(byte),'time_ratio':statistics.median(time),
                      'slower_pairs':sum(v>1 for v in time),'over_105_pairs':sum(v>1.05 for v in time),
                      'max_time_ratio':max(time),'pass':max(byte)<=threshold and statistics.median(time)<=1.05,'modes':stats})
    return {'cells':cells,'gates':{host:all(c['pass'] for c in cells if c['host']==host) for host in sorted(set(c['host'] for c in cells))},'rows':len(rows)}

def run_reference(work,config):
    work.mkdir();rows=0;diags=[];rng=random.Random(config['seed'])
    with (work/'log.jsonl').open('x',encoding='utf-8') as log:
        for domain in config['domains']:
            inputs=ROOT/'inputs'/domain;index=json.loads((inputs/'fixtures.json').read_text())
            pub=Ed25519PublicKey.from_public_bytes((inputs/'TEST_ONLY_ed25519_public.key').read_bytes())
            for entry in index['batches']:
                cell=entry['cell_id'];bi=entry['batch_index'];name=f'{domain}_{cell}_b{bi}'
                directory=work/name;directory.mkdir()
                item=entry['wires']['full'];path=inputs/item['path']
                if sha(path)!=item['sha256']:raise ValueError('archived frame mismatch')
                b=codec.old.decode_batch(path.read_bytes())
                wires={m:codec.encode_batch(b,m) for m in codec.MODES}
                for m,w in wires.items():
                    decoded=codec.decode_batch(w,m)
                    if decoded!=b or codec.host.payload(decoded)!=codec.host.payload(b):raise ValueError('reconstruction')
                    v=codec.host.Verifier(pub,b.previous);v.accept(decoded)
                    if v.checkpoint!=b.next:raise ValueError('checkpoint')
                    writebytes(directory/(m+'.wire'),w)
                retained=[sum(v!=codec.host.DEFAULTS[i] for i,v in enumerate(s.siblings)) for s in b.steps]
                savings=32*(256*len(b.steps)-sum(retained)-len(b.steps))
                if len(wires['binary-full'])-len(wires['binary-bitmap'])!=savings:raise ValueError('byte identity')
                diags.append({'domain':domain,'cell':cell,'batch':bi,'retained':retained,'sizes':{m:len(w) for m,w in wires.items()},'identity_saving':savings})
                for m in codec.MODES:
                    for _ in range(config['warmups']):
                        v=codec.host.Verifier(pub,b.previous);v.accept(codec.decode_batch(codec.encode_batch(b,m),m))
                for rep in range(config['repeats']):
                    modes=list(codec.MODES);rng.shuffle(modes)
                    for order,m in enumerate(modes):
                        v=codec.host.Verifier(pub,b.previous)
                        t0=perf_counter_ns();wire=codec.encode_batch(b,m);t1=perf_counter_ns()
                        decoded=codec.decode_batch(wire,m);t2=perf_counter_ns();v.accept(decoded);t3=perf_counter_ns()
                        if decoded!=b or wire!=wires[m] or v.checkpoint!=b.next:raise ValueError('timed correctness')
                        row={'host':'reference','domain':domain,'cell':cell,'batch':bi,'repeat':rep,'order':order,'mode':m,'bytes':len(wire),
                             'encode_ns':t1-t0,'decode_ns':t2-t1,'verify_ns':t3-t2,'total_ns':t3-t0}
                        log.write(json.dumps(row)+'\n');log.flush();rows+=1
                print('reference finished',name,flush=True)
    if rows!=5292:raise ValueError('row count')
    save(work/'diagnostics.json',diags);save(work/'completion.json',{'rows':rows,'complete':True})

def register():
    if (ROOT/'registration.json').exists():raise FileExistsError('registration exists')
    names=['PLAN.md','config.json','LITERATURE.md','ADAPTATION.md','dependencies.json','binary_transport.py','run_screening.py',
           'test_binary_transport.py','test_run_screening.py','launch.sh','external_runner/main.go','external_runner/codec_test.go',
           'external_runner/go.mod','external_runner/external_runner.exe','external_runner/clock_windows.go','external_runner/clock_test.go']
    for folder in ('frozen','external/smt','inputs'):
        names.extend(p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files={n:sha(ROOT/n) for n in sorted(names)}
    save(ROOT/'registration.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':files})
    print('Registered',len(files),'files.',flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--register',action='store_true');ap.add_argument('--work-dir',type=Path);a=ap.parse_args()
    if a.register:return register()
    if a.work_dir is None:raise ValueError('work directory required')
    reg=json.loads((ROOT/'registration.json').read_text());validate(ROOT,reg)
    config=json.loads((ROOT/'config.json').read_text());work=create_workdir(a.work_dir)
    save(work/'registration.json',reg);save(work/'config.json',config)
    save(work/'metadata.json',{'utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'pid':os.getpid(),'registration_sha256':sha(ROOT/'registration.json')})
    snapshot=work/'source';snapshot.mkdir()
    for name in reg['files']:
        target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    try:
        run_reference(work/'reference',config);validate(ROOT,reg)
        p=subprocess.run([str(ROOT/'external_runner/external_runner.exe'),str(work/'external')],check=False)
        save(work/'external_exit.json',{'returncode':p.returncode})
        if p.returncode:raise RuntimeError('external process failed')
        validate(ROOT,reg)
        rows=readrows(work/'reference/log.jsonl')+readrows(work/'external/log.jsonl')
        if len(rows)!=11340:raise ValueError('total rows')
        result=evaluate(rows);save(work/'eval.json',result)
        inventory={p.relative_to(work).as_posix():sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
        save(work/'completion.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'rows':len(rows),'gates':result['gates'],'files':inventory})
        print('COMPLETED',json.dumps(result['gates']),flush=True)
    except BaseException as e:
        save(work/'failure.json',{'error':repr(e),'traceback':traceback.format_exc()});raise

if __name__=='__main__':main()
