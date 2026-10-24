"""Prospective descriptive analysis of the Round7 application workload."""
import argparse
from collections import defaultdict
import itertools
import json
from pathlib import Path
import statistics as st

MODES=['ordinary','compact','dictionary','zlib-ordinary','zlib-compact','zlib-dictionary',
       'reset-zlib-ordinary','reset-zlib-compact','reset-zlib-dictionary']
META=('domain','n','value_bytes','distribution','q','batch')
STAGES=('proof_ns','encode_ns','decode_ns','verify_ns')


def percentile(xs,p):
    xs=sorted(xs); pos=(len(xs)-1)*p; lo=int(pos)
    return xs[lo]+(xs[min(lo+1,len(xs)-1)]-xs[lo])*(pos-lo)


def boundary(saved_bytes, extra_ns):
    if saved_bytes<=0: return {'class':'no_byte_saving','bits_per_second':None}
    if extra_ns<=0: return {'class':'model_dominates','bits_per_second':None}
    return {'class':'finite_threshold','bits_per_second':8*saved_bytes*1e9/extra_ns}


def classify(dev, confirm):
    size=dev['worst_byte_ratio']<=.8 and confirm['worst_byte_ratio']<1
    return {label:size and dev[field]<=1.05 and confirm[field]<=1.05
            for label,field in [('service','paired_total_ratio'),('codec','paired_codec_ratio')]}


def validate_rows(rows, diagnostics):
    expected=set(itertools.product(('dev','confirm'),(4096,16384),(32,1000),
                                   ('uniform','zipf'),(1,8,32,128),range(3)))
    ds={}
    for d in diagnostics:
        k=tuple(d[x] for x in META)
        if k in ds or k not in expected: raise ValueError('duplicate/unknown diagnostic')
        if set(d['sizes'])!=set(MODES): raise ValueError('diagnostic modes')
        if d['sizes']['ordinary']-d['sizes']['dictionary']!=30*d['occurrences']-32*d['unique_nodes']-2:
            raise ValueError('dictionary accounting')
        if any(len(d[x])!=d['q'] for x in ('depths','retained','masks')): raise ValueError('path counts')
        if d['sizes']['ordinary']-d['sizes']['compact']!=sum(32*(a-b)-2-c for a,b,c in zip(d['depths'],d['retained'],d['masks'])):
            raise ValueError('compact accounting')
        ds[k]=d
    if set(ds)!=expected: raise ValueError('incomplete diagnostic matrix')
    seen=set(); order=defaultdict(set)
    for r in rows:
        k=tuple(r[x] for x in META)
        if k not in ds or r['repeat'] not in range(21) or r['mode'] not in MODES: raise ValueError('unknown row')
        ident=k+(r['repeat'],r['mode'])
        if ident in seen: raise ValueError('duplicate row')
        seen.add(ident)
        if r['id']!=ds[k]['id'] or r['cell']!=ds[k]['cell']: raise ValueError('row labels')
        if r['bytes']!=ds[k]['sizes'][r['mode']]: raise ValueError('row bytes')
        if r['total_ns']<=0 or any(r[s]<0 for s in STAGES) or sum(r[s] for s in STAGES)!=r['total_ns']:
            raise ValueError('stage timing')
        if sum(r[s] for s in STAGES[1:])!=r['codec_total_ns'] or r['codec_total_ns']<=0: raise ValueError('codec timing')
        okey=k+(r['repeat'],)
        if r['order'] in order[okey]: raise ValueError('duplicate order')
        order[okey].add(r['order'])
    if len(rows)!=36288 or any(v!=set(range(9)) for v in order.values()): raise ValueError('incomplete row matrix')


def summarize_cell(rows, modes=MODES, expected_pairs=63):
    pairs=defaultdict(dict)
    for r in rows:
        p=pairs[(r['batch'],r['repeat'])]
        if r['mode'] in p: raise ValueError('duplicate pair')
        p[r['mode']]=r
    if len(pairs)!=expected_pairs or any(set(p)!=set(modes) for p in pairs.values()): raise ValueError('pair matrix')
    out={}
    for mode in modes:
        obs=[p[mode] for p in pairs.values()]
        ratios=[p[mode]['total_ns']/p['ordinary']['total_ns'] for p in pairs.values()]
        cr=[p[mode]['codec_total_ns']/p['ordinary']['codec_total_ns'] for p in pairs.values()]
        byte_ratios=[p[mode]['bytes']/p['ordinary']['bytes'] for p in pairs.values()]
        saved=st.median(p['ordinary']['bytes']-p[mode]['bytes'] for p in pairs.values())
        extra=st.median(p[mode]['total_ns']-p['ordinary']['total_ns'] for p in pairs.values())
        s={'paired_total_ratio':st.median(ratios),'paired_codec_ratio':st.median(cr),
           'worst_byte_ratio':max(byte_ratios),'median_bytes':st.median(r['bytes'] for r in obs),
           'slower_pairs':sum(x>1 for x in ratios),'p95_total_ns':percentile([r['total_ns'] for r in obs],.95),
           'max_total_ns':max(r['total_ns'] for r in obs),'median_saved_bytes':saved,
           'median_extra_total_ns':extra,'transfer_boundary':boundary(saved,extra)}
        for field in STAGES+('total_ns','codec_total_ns'):
            values=[r[field] for r in obs]
            s['median_'+field]=st.median(values)
            s['p95_'+field]=percentile(values,.95)
            s['max_'+field]=max(values)
        s['service_gate']=s['worst_byte_ratio']<=.8 and s['paired_total_ratio']<=1.05
        s['codec_gate']=s['worst_byte_ratio']<=.8 and s['paired_codec_ratio']<=1.05
        if mode.startswith('reset-'):
            fresh=mode.removeprefix('reset-')
            if any(p[mode]['bytes']!=p[fresh]['bytes'] for p in pairs.values()): raise ValueError('reset bytes')
            for label,field in [('total','total_ns'),('codec','codec_total_ns')]:
                s['reset_fresh_'+label+'_ratio']=st.median(p[mode][field]/p[fresh][field] for p in pairs.values())
        out[mode]=s
    return out


def hot_decisions(diagnostics):
    grouped=defaultdict(list)
    for d in diagnostics:
        if d['q'] in (32,128):
            grouped[(d['domain'],d['n'],d['value_bytes'],d['q'],d['distribution'])].append(d['sizes']['dictionary']/d['sizes']['ordinary'])
    out=[]
    for d,n,v,q in itertools.product(('dev','confirm'),(4096,16384),(32,1000),(32,128)):
        a,b=grouped[(d,n,v,q,'uniform')],grouped[(d,n,v,q,'zipf')]
        if len(a)!=3 or len(b)!=3: raise ValueError('hotness matrix')
        delta=st.median(a)-st.median(b)
        out.append(dict(domain=d,n=n,value_bytes=v,q=q,improvement=delta,passed=delta>=.05 if d=='dev' else delta>0))
    return out


def evaluate(rows, diagnostics):
    validate_rows(rows,diagnostics)
    groups=defaultdict(list)
    for r in rows: groups[(r['domain'],r['cell'])].append(r)
    cells=[]
    for (domain,cell),rr in sorted(groups.items()):
        cells.append(dict(domain=domain,cell=cell,**{x:rr[0][x] for x in ('n','q','value_bytes','distribution')},modes=summarize_cell(rr)))
    by={(c['domain'],c['cell']):c for c in cells}; effective=[]
    for c in cells:
        if c['domain']!='dev': continue
        for mode in MODES[1:]:
            effective.append(dict(cell=c['cell'],mode=mode,**classify(c['modes'][mode],by[('confirm',c['cell'])]['modes'][mode])))
    hot=hot_decisions(diagnostics)
    return {'rows':len(rows),'cells':cells,'hot':hot,'effective':effective,
            'gates':{'hot':all(x['passed'] for x in hot),'service_effective':sum(x['service'] for x in effective),
                     'codec_effective':sum(x['codec'] for x in effective)}}


def report(result, path):
    lines=['# Application run report','', 'Single seed 3407; technical repetitions are not independent experiments.',
           '',f"Rows: {result['rows']}. Gates: {json.dumps(result['gates'])}",'',
           '| Domain | Cell | Mode | Bytes/ordinary (worst) | Service ratio | Codec ratio |',
           '|---|---|---|---:|---:|---:|']
    for c in result['cells']:
        for mode,s in c['modes'].items():
            lines.append(f"| {c['domain']} | {c['cell']} | {mode} | {s['worst_byte_ratio']:.6f} | {s['paired_total_ratio']:.6f} | {s['paired_codec_ratio']:.6f} |")
    with Path(path).open('x',encoding='utf8') as f: f.write('\n'.join(lines)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('work',type=Path);a=p.parse_args()
    rows=[json.loads(x) for x in (a.work/'measurements/log.jsonl').read_text().splitlines()]
    result=evaluate(rows,json.loads((a.work/'measurements/diagnostics.json').read_text()))
    with (a.work/'eval.json').open('x') as f: json.dump(result,f,indent=2,allow_nan=False)
    report(result,a.work/'REPORT.md')
