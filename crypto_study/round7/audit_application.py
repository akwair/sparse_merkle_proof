"""Independent artifact/proof/statistic audit; never imports app_analysis."""
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import statistics as st
import sys

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_proof_auditor',ROOT.parent/'round5/audit_results.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
req=old.require
read=old.read_json
MODES=['ordinary','compact','dictionary','zlib-ordinary','zlib-compact','zlib-dictionary',
       'reset-zlib-ordinary','reset-zlib-compact','reset-zlib-dictionary']


def inventory(work):
    c=read(work/'completion.json');req(c['complete'],'not complete')
    actual={p.relative_to(work).as_posix() for p in work.rglob('*') if p.is_file()}
    req(actual==set(c['files'])|{'completion.json'},'completion file set')
    for name,digest in c['files'].items(): req(old.file_sha(work/name)==digest,'changed run '+name)
    return c


def audit(work):
    c=inventory(work);req(read(work/'runner_exit.json')['returncode']==0,'runner exit')
    req(not (work/'failure.json').exists(),'failed application work')
    registration=read(ROOT/'registration.json')
    req(read(work/'registration.json')==registration,'archived registration')
    for name,digest in registration['files'].items():
        req(old.file_sha(old.checked_path(ROOT,name))==digest,'registered source '+name)
        req(old.file_sha(old.checked_path(work/'source',name))==digest,'source snapshot '+name)
    config=read(ROOT/'config.json');req(read(work/'config.json')==config,'archived config')
    req(config['seed']==3407 and config['gomaxprocs']==8 and config['process_blocks']==5,'runtime config')
    metadata=read(work/'metadata.json')
    req(metadata['registration_sha256']==old.file_sha(ROOT/'registration.json'),'metadata registration binding')
    env=read(work/'measurements/environment.json')
    for key,expected in dict(experiment='round7_application',clock='Go monotonic time.Since',frequency=1000000000,
        seed=3407,go='go1.27.3',os='linux',arch='amd64',gomaxprocs=8,gomaxprocs_env='8',gogc_env='',gomemlimit_env='',
        commit='dba215ccb88452c31d823bf156d8f35406c1dc04',warmups=2,repetitions=21,expected_rows=36288,expected_bundles=192,modes=MODES).items():
        req(env[key]==expected,'application environment '+key)
    before,after=read(work/'resources_before.json'),read(work/'resources_after.json')
    req(before['phase']=='before_application' and after['phase']=='after_application','resource phases')
    for resource in (before,after):
        req(resource['system']=='Linux' and resource['machine'].lower() in ('x86_64','amd64'),'resource platform')
        req(resource['environment']['GOMAXPROCS']=='8' and all(resource['environment'][key] is None for key in ('GOGC','GOMEMLIMIT','GODEBUG')),'resource runtime')
    process=read(work/'process.json');req(type(process['pid'])==int and process['pid']>0,'runner PID')
    mc=read(work/'measurements/completion.json')
    req(mc['complete'] and mc['rows']==36288 and mc['bundles']==192,'measurement completion')
    times=[registration['utc'],metadata['utc'],before['utc'],process['utc'],mc['utc'],
           read(work/'runner_exit.json')['utc'],after['utc'],c['utc']]
    parsed=[datetime.fromisoformat(x.replace('Z','+00:00')) for x in times]
    req(parsed==sorted(parsed),'registration/run chronology')
    m=work/'measurements'; trees={}; generated=0
    for d,n,v in itertools.product(('dev','confirm'),(4096,16384),(32,1000)):
        cp=read(m/f'tree_{d}_n{n}_v{v}.json')
        keys=[old.binary_json(x) for x in cp['keys']];values=[old.binary_json(x) for x in cp['values']]
        req(len(keys)==len(values)==n,'tree population')
        for i,(k,val) in enumerate(zip(keys,values)):
            req(k==old.sha(f'r7/{d}/3407/key/{i}'.encode()),'key generation')
            expected=b''.join(old.sha(f'r7/{d}/3407/value/{i}/block/{j}'.encode()) for j in range((v+31)//32))[:v]
            req(val==expected,'value generation');generated+=1
        root=old.binary_json(cp['root'])
        req(old.rebuild_tree_root(keys,values)==root,'independent root reconstruction')
        trees[(d,n,v)]=(root,keys,values)
    request_sets=read(m/'request_sets.json'); requests={}
    for s in request_sets:
        key=(s['domain'],s['n'],s['distribution'],s['batch'])
        req(key not in requests,'duplicate request set')
        indexes=s['request_indexes']
        req(len(indexes)==128 and all(type(i)==int and 0<=i<s['n'] for i in indexes),'request bounds')
        requests[key]=indexes
    req(set(requests)==set(itertools.product(('dev','confirm'),(4096,16384),('uniform','zipf'),range(3))), 'request set matrix')
    diagnostics=read(m/'diagnostics.json'); req(len(diagnostics)==192,'diagnostic count')
    ds={}; sizes={};frames=proofs=0
    expected=set(itertools.product(('dev','confirm'),(4096,16384),(32,1000),('uniform','zipf'),(1,8,32,128),range(3)))
    seen=set()
    for diag in diagnostics:
        key=tuple(diag[k] for k in ('domain','n','value_bytes','distribution','q','batch'))
        req(key in expected and key not in seen,'diagnostic identity');seen.add(key)
        d,n,v,dist,q,b=key;ident=diag['id'];folder=m/ident
        req(ident not in ds,'duplicate bundle id');ds[ident]=diag
        root,keys,values=trees[(d,n,v)]
        indexes=requests[(d,n,dist,b)][:q]
        r=read(folder/'requests.json');req(r['request_indexes']==indexes,'request prefix/order')
        bundle=old.normalize_bundle(read(folder/'bundle.json'))
        req(bundle[0]==root and len(bundle[1])==q,'trusted root/count')
        for index,item in zip(indexes,bundle[1]): req(item[0]==keys[index] and item[1]==values[index],'requested key/value')
        req(diag['unique_query_count']==len(set(indexes)),'unique requests')
        counts=Counter(old.sha(keys[i])[0]>>4 for i in indexes)
        unique_counts=Counter(old.sha(keys[i])[0]>>4 for i in set(indexes))
        req(diag['request_prefix_counts']==[counts[i] for i in range(16)],'prefix counts')
        req(diag['unique_request_prefix_counts']==[unique_counts[i] for i in range(16)],'unique prefix counts')
        sz={}
        for mode in MODES[:6]:
            wire=(folder/(mode+'.wire')).read_bytes();decoded,payload=old.parse_frame(wire,mode)
            req(decoded==bundle,'frame restoration')
            req(payload==old.canonical_payload(bundle,mode.removeprefix('zlib-')),'canonical frame')
            wrong=bytes([root[0]^1])+root[1:]
            for item in decoded[1]:
                req(old.verify_proof(root,item),'valid proof');req(not old.verify_proof(wrong,item),'wrong root rejected');proofs+=1
            sz[mode]=len(wire);frames+=1
        for mode in MODES[6:]: sz[mode]=sz[mode.removeprefix('reset-')]
        req(sz==diag['sizes'],'frame sizes');sizes[ident]=sz
        calculated=old.expected_diagnostic({},bundle,sz)
        for k,value in calculated.items(): req(diag[k]==value,'structural accounting '+k)
        req(read(folder/'diagnostics.json')==diag,'global/per-bundle diagnostic equality')
    req(seen==expected and frames==1152 and proofs==48672,'complete corpus')
    req({p.name for p in m.iterdir() if p.is_dir()}==set(ds),'bundle directories')
    order=read(m/'execution_order.json');req(len(order)==192 and set(order)==set(ds),'execution order')
    rows=[json.loads(x) for x in (m/'log.jsonl').read_text().splitlines()]
    req(len(rows)==36288,'row count');pairs=defaultdict(dict);identity=hashlib.sha256()
    schedule=read(m/'mode_execution_order.json'); req(len(schedule)==4032,'mode schedule')
    rowpos=0
    for bi,ident in enumerate(order):
        for rep in range(21):
            sched=schedule[bi*21+rep]
            req(sched['id']==ident and sched['repeat']==rep and sorted(sched['modes'])==sorted(MODES),'mode schedule identity')
            for pos,mode in enumerate(sched['modes']):
                row=rows[rowpos];rowpos+=1
                req((row['id'],row['repeat'],row['order'],row['mode'])==(ident,rep,pos,mode),'row/order equality')
                diag=ds[ident]
                for k in ('domain','n','value_bytes','distribution','q','batch','cell'): req(row[k]==diag[k],'row metadata '+k)
                req(row['bytes']==sizes[ident][mode],'row bytes')
                times=[row[k] for k in ('proof_ns','encode_ns','decode_ns','verify_ns')]
                req(all(type(t)==int and t>=0 for t in times) and sum(times)==row['total_ns']>0,'total arithmetic')
                req(sum(times[1:])==row['codec_total_ns']>0,'codec arithmetic')
                pairs[(row['domain'],row['cell'],row['batch'],rep)][mode]=row
                identity.update(f"{ident}\t{rep}\t{pos}\t{mode}\t{row['bytes']}\n".encode())
    req(len(pairs)==4032 and all(set(p)==set(MODES) for p in pairs.values()),'pair matrix')
    groups=defaultdict(list)
    for (d,cell,b,rep),p in pairs.items():groups[(d,cell)].append(p)
    stored=read(work/'eval.json'); storedcells={(x['domain'],x['cell']):x for x in stored['cells']}
    req(set(storedcells)==set(groups) and len(groups)==64,'analysis matrix')
    evaluated={}
    for key,ps in groups.items():
        req(len(ps)==63,'cell pairs');evaluated[key]={}
        for mode in MODES:
            s=storedcells[key]['modes'][mode]
            actual={'paired_total_ratio':st.median(p[mode]['total_ns']/p['ordinary']['total_ns'] for p in ps),
                    'paired_codec_ratio':st.median(p[mode]['codec_total_ns']/p['ordinary']['codec_total_ns'] for p in ps),
                    'worst_byte_ratio':max(p[mode]['bytes']/p['ordinary']['bytes'] for p in ps),
                    'median_bytes':st.median(p[mode]['bytes'] for p in ps),
                    'slower_pairs':sum(p[mode]['total_ns']>p['ordinary']['total_ns'] for p in ps),
                    'median_saved_bytes':st.median(p['ordinary']['bytes']-p[mode]['bytes'] for p in ps),
                    'median_extra_total_ns':st.median(p[mode]['total_ns']-p['ordinary']['total_ns'] for p in ps)}
            for field in ('proof_ns','encode_ns','decode_ns','verify_ns','total_ns','codec_total_ns'):
                times=sorted(p[mode][field] for p in ps)
                position=(len(times)-1)*.95;i=int(position)
                actual['median_'+field]=st.median(times)
                actual['p95_'+field]=times[i]+(times[min(i+1,len(times)-1)]-times[i])*(position-i)
                actual['max_'+field]=max(times)
            actual['service_gate']=actual['worst_byte_ratio']<=.8 and actual['paired_total_ratio']<=1.05
            actual['codec_gate']=actual['worst_byte_ratio']<=.8 and actual['paired_codec_ratio']<=1.05
            if mode.startswith('reset-'):
                fresh=mode.removeprefix('reset-')
                actual['reset_fresh_total_ratio']=st.median(p[mode]['total_ns']/p[fresh]['total_ns'] for p in ps)
                actual['reset_fresh_codec_ratio']=st.median(p[mode]['codec_total_ns']/p[fresh]['codec_total_ns'] for p in ps)
            for k,v in actual.items(): req(s[k]==v,'statistic '+k)
            saved,extra=actual['median_saved_bytes'],actual['median_extra_total_ns']
            bound={'class':'no_byte_saving','bits_per_second':None} if saved<=0 else (
                {'class':'model_dominates','bits_per_second':None} if extra<=0 else
                {'class':'finite_threshold','bits_per_second':8*saved*1e9/extra})
            req(s['transfer_boundary']==bound,'transfer model')
            req(set(s)==set(actual)|{'transfer_boundary'},'unaudited cell fields')
            evaluated[key][mode]=actual
    effective=[]
    for (d,cell),modes in sorted(evaluated.items()):
        if d!='dev':continue
        for mode in MODES[1:]:
            a=modes[mode];b=evaluated[('confirm',cell)][mode]
            size=a['worst_byte_ratio']<=.8 and b['worst_byte_ratio']<1
            effective.append(dict(cell=cell,mode=mode,service=size and a['paired_total_ratio']<=1.05 and b['paired_total_ratio']<=1.05,
                codec=size and a['paired_codec_ratio']<=1.05 and b['paired_codec_ratio']<=1.05))
    req(stored['effective']==effective,'engineering decisions')
    hot=[]
    for d,n,v,q in itertools.product(('dev','confirm'),(4096,16384),(32,1000),(32,128)):
        ratios={dist:st.median(x['sizes']['dictionary']/x['sizes']['ordinary'] for x in diagnostics if
            (x['domain'],x['n'],x['value_bytes'],x['q'],x['distribution'])==(d,n,v,q,dist)) for dist in ('uniform','zipf')}
        delta=ratios['uniform']-ratios['zipf']
        hot.append(dict(domain=d,n=n,value_bytes=v,q=q,improvement=delta,passed=delta>=.05 if d=='dev' else delta>0))
    req(stored['hot']==hot,'hot decisions')
    gates=dict(hot=all(x['passed'] for x in hot),service_effective=sum(x['service'] for x in effective),codec_effective=sum(x['codec'] for x in effective))
    req(stored['gates']==gates==c['gates'],'gates')
    corpus={p.relative_to(m).as_posix():old.file_sha(p) for p in m.rglob('*') if p.is_file() and p.name not in ('log.jsonl','environment.json','completion.json')}
    return {'complete':True,'work':str(work),'registration_sha256':old.file_sha(ROOT/'registration.json'),
            'source_config_runtime_bound':True,'chronology_verified':True,
            'tree_records':generated,'frames':frames,'verified_proofs':proofs,
            'wrong_root_rejections':proofs,'rows':len(rows),'pairs':len(pairs),'identity_sha256':identity.hexdigest(),
            'gates':gates,'corpus_files':corpus}


if __name__=='__main__':
    work=Path(sys.argv[1]);out=Path(sys.argv[2])
    result=audit(work)
    with out.open('x',encoding='utf8') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='corpus_files'}))
