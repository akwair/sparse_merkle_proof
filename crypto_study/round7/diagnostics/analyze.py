"""Preregistered stage-allocation summaries; never latency estimates."""
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

MODES=['ordinary','compact','dictionary','zlib-ordinary','zlib-compact','zlib-dictionary','reset-zlib-ordinary','reset-zlib-compact','reset-zlib-dictionary']
CASES=[f'dev_n16384_q{q}_v32_member_{d}_b0' for d in ('uniform','zipf') for q in (1,128)]
STAGES=('encode','decode','verify')
IDENTITY=('id','q','distribution','stage','mode','repeat','order','sequence')

def read(p):return json.loads(Path(p).read_text(encoding='utf8'))

def save(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def evaluate(rows,env):
    if len(rows)!=540 or len(env['execution_order'])!=540:raise ValueError('540 rows required')
    seen=set();order=defaultdict(set);groups=defaultdict(list)
    for i,(r,step) in enumerate(zip(rows,env['execution_order'])):
        if any(r[k]!=step[k] for k in IDENTITY) or r['sequence']!=i:raise ValueError('execution order')
        if r['id'] not in CASES or r['stage'] not in STAGES or r['mode'] not in MODES or r['repeat'] not in range(5):raise ValueError('unknown row')
        ci=CASES.index(r['id']);q=(1,128)[ci%2];d=('uniform','zipf')[ci//2]
        if (r['q'],r['distribution'])!=(q,d):raise ValueError('case metadata')
        if (ci,r['repeat'],r['stage'],r['order'])!=(i//135,(i%135)//27,STAGES[(i%27)//9],i%9):raise ValueError('registered case/repeat/stage order')
        ident=(r['id'],r['repeat'],r['stage'],r['mode'])
        if ident in seen:raise ValueError('duplicate row')
        seen.add(ident);order[ident[:3]].add(r['order'])
        if r['batch_operations']!=32:raise ValueError('batch count')
        for k in ('allocated_bytes','mallocs','frees','num_gc','pause_ns'):
            if type(r[k]) is not int or r[k]<0:raise ValueError('invalid counter')
        if r['bytes_per_operation']!=r['allocated_bytes']/32 or r['mallocs_per_operation']!=r['mallocs']/32:raise ValueError('per-operation arithmetic')
        if any(k in r for k in ('total_ns','elapsed_ns','latency_ns')):raise ValueError('unregistered timing')
        groups[(r['id'],r['stage'],r['mode'])].append(r)
    if len(seen)!=540 or len(order)!=60 or any(x!=set(range(9)) for x in order.values()):raise ValueError('matrix')
    cells=[];by={}
    for key,rr in sorted(groups.items()):
        if len(rr)!=5:raise ValueError('five batches')
        s={'id':key[0],'stage':key[1],'mode':key[2]}
        for k in ('bytes_per_operation','mallocs_per_operation','frees','num_gc','pause_ns'):
            xs=[r[k] for r in rr];s[k]={'median':st.median(xs),'min':min(xs),'max':max(xs),'values':xs}
        cells.append(s);by[key]=s
    conditions=[]
    for case in CASES:
        for mode in MODES[3:6]:
            fresh=by[(case,'encode',mode)]['bytes_per_operation']['median']
            reset=by[(case,'encode','reset-'+mode)]['bytes_per_operation']['median']
            if fresh<=0:raise ValueError('invalid fresh denominator')
            conditions.append(dict(id=case,mode=mode,ratio=reset/fresh,passed=reset/fresh<=.5,fresh_bytes=fresh,reset_bytes=reset))
    return {'rows':540,'operations':17280,'single_seed':3407,'diagnostic_processes':1,'technical_batches_per_cell':5,
            'allocation_hypothesis':all(x['passed'] for x in conditions),'conditions':conditions,'cells':cells}

def run(work):
    work=Path(work);env=read(work/'env.json');completion=read(work/'completion.json')
    if not completion['complete'] or completion['rows']!=540 or completion['operations']!=17280:raise ValueError('incomplete')
    result=evaluate([json.loads(x) for x in (work/'log.jsonl').read_text().splitlines()],env)
    save(work/'eval.json',result)
    lines=['# Stage-allocation diagnostic','',
      'Single process, seed=3407, five technical batches per condition; not independent workload replication. No latency or peak-memory estimates. 本实验为单种子，存在随机噪声风险。','',
      f"H_allocation: {result['allocation_hypothesis']}. Rows: 540; stage operations: 17,280.",'',
      '| Fixture | Representation | Fresh bytes/op | Primed-reset bytes/op | Reset/fresh | Pass |',
      '|---|---|---:|---:|---:|---|']
    for c in result['conditions']:lines.append(f"| {c['id']} | {c['mode']} | {c['fresh_bytes']:.1f} | {c['reset_bytes']:.1f} | {c['ratio']:.6f} | {c['passed']} |")
    lines+=['','The reset writer is primed before counters; retained workspace is excluded from allocation flow. This does not imply zero retained memory or establish a causal fraction of latency due to allocation/GC. Decode and native verification are separately measured with prepared inputs.','',
      '| Fixture | Stage | Mode | Median bytes/op | Range bytes/op | Median allocations/op | GC events range/batch |',
      '|---|---|---|---:|---:|---:|---:|']
    for c in result['cells']:
        b=c['bytes_per_operation'];g=c['num_gc']
        lines.append(f"| {c['id']} | {c['stage']} | {c['mode']} | {b['median']:.1f} | {b['min']:.1f}–{b['max']:.1f} | {c['mallocs_per_operation']['median']:.3f} | {g['min']}–{g['max']} |")
    with (work/'REPORT.md').open('x',encoding='utf8') as f:f.write('\n'.join(lines)+'\n')
    return result

if __name__=='__main__':
    import sys
    run(sys.argv[1])
