"""Audit every scheduled process, then report process-level variation."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
from audit_application import audit, old

ROOT=Path(__file__).resolve().parent


def read(p):return json.loads(Path(p).read_text(encoding='utf8'))


def save(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')


def across(evaluations):
    if len(evaluations)!=5:raise ValueError('exactly five processes required')
    maps=[{(c['domain'],c['cell']):c for c in e['cells']} for e in evaluations]
    if any(set(m)!=set(maps[0]) or len(m)!=len(e['cells']) for m,e in zip(maps,evaluations)):
        raise ValueError('process matrix mismatch')
    result=[]
    for key in sorted(maps[0]):
        template=maps[0][key];out={k:v for k,v in template.items() if k not in ('modes','pairs')};out['modes']={}
        for mode in template['modes']:
            ss=[m[key]['modes'][mode] for m in maps]
            fields=[f for f in ss[0] if f.startswith(('median_','paired_','reset_fresh_')) and isinstance(ss[0][f],(int,float))]
            s={f:{'values':[x[f] for x in ss],'min':min(x[f] for x in ss),'max':max(x[f] for x in ss)} for f in fields}
            if len({x['worst_byte_ratio'] for x in ss})!=1:raise ValueError('frame bytes changed across processes')
            s['worst_byte_ratio']=ss[0]['worst_byte_ratio']
            s['absolute_spread']=s['median_total_ns']['max']/s['median_total_ns']['min']
            s['spread_over_120']=s['absolute_spread']>1.20
            if 'transfer_boundary' in ss[0]:
                boundaries=[x['transfer_boundary'] for x in ss]
                finite=[x['bits_per_second'] for x in boundaries if x['class']=='finite_threshold']
                s['transfer_boundaries']=boundaries
                s['finite_boundary_range']=None if not finite else [min(finite),max(finite)]
            out['modes'][mode]=s
        result.append(out)
    return result


def run():
    schedule=read(ROOT/'schedule_completion.json')
    if not schedule['complete'] or len(schedule['blocks'])!=5:raise ValueError('schedule incomplete')
    dispatch=ROOT/schedule['dispatch']
    if (dispatch/'failure.json').exists():raise ValueError('failed schedule')
    blocks=schedule['blocks'];starts=[b['start_monotonic'] for b in blocks]
    if [b['index'] for b in blocks]!=list(range(1,6)) or any(b-a<120 for a,b in zip(starts,starts[1:])):
        raise ValueError('registered schedule/order changed')
    audits=ROOT/'audits';audits.mkdir(exist_ok=False)
    app=[];frozen=[];app_corpus=None;old_corpus=None;identity=None
    expected_frozen_identity=read(ROOT/'prior/round4_fixture_hashes.json')['observation_identity_sha256']
    for block in blocks:
        index=block['index'];w=ROOT/block['application'];f=ROOT.parent/'round5'/block['frozen']
        print('AUDIT APPLICATION',index,flush=True)
        a=audit(w);save(audits/f'app_{index:03d}.json',a)
        if app_corpus is not None and (a['corpus_files']!=app_corpus or a['identity_sha256']!=identity):
            raise ValueError('application corpus/order differs across processes')
        app_corpus=a['corpus_files'];identity=a['identity_sha256'];app.append(read(w/'eval.json'))
        print('AUDIT FROZEN',index,flush=True)
        b=old.audit(f,ROOT.parent/'round5'/block['frozen_launch']);save(audits/f'frozen_{index:03d}.json',b)
        frozen_identity=hashlib.sha256()
        with (f/'measurements/log.jsonl').open() as stream:
            for line in stream:
                r=json.loads(line)
                frozen_identity.update(f"{r['id']}\t{r['repeat']}\t{r['order']}\t{r['mode']}\t{r['bytes']}\n".encode())
        if frozen_identity.hexdigest()!=expected_frozen_identity:raise ValueError('frozen observation order changed')
        corpus={p.relative_to(f/'measurements').as_posix():old.file_sha(p) for p in (f/'measurements').rglob('*')
                if p.is_file() and p.name not in ('log.jsonl','environment.json','completion.json')}
        if old_corpus is not None and corpus!=old_corpus:raise ValueError('frozen corpus differs across processes')
        old_corpus=corpus;frozen.append(read(f/'eval.json'))
    ac=across(app);fc=across(frozen)
    decisions=[]
    for i,e in enumerate(app):
        if i==0:
            decisions=[dict(cell=x['cell'],mode=x['mode'],service_count=0,codec_count=0) for x in e['effective']]
        for agg,x in zip(decisions,e['effective']):
            if (agg['cell'],agg['mode'])!=(x['cell'],x['mode']):raise ValueError('effective order')
            agg['service_count']+=int(x['service']);agg['codec_count']+=int(x['codec'])
    frozen_counts=[]
    prior=read(ROOT/'prior/linux_gold_eval.json')
    for row in frozen[0]['effective']:
        if row['mode']=='ordinary':continue
        matched=[next(x for x in e['effective'] if (x['cell'],x['mode'])==(row['cell'],row['mode'])) for e in frozen]
        previous=next(x['effective'] for x in prior['effective'] if (x['cell'],x['mode'])==(row['cell'],row['mode']))
        agrees=sum(x['effective']==previous for x in matched)
        frozen_counts.append(dict(cell=row['cell'],mode=row['mode'],effective_count=sum(x['effective'] for x in matched),
                                  prior_effective=previous,prior_agreement_count=agrees,stable_this_session=agrees==5))
    stability={key:all(e['gates'][key]==value for e in frozen) for key,value in prior['gates'].items()}
    stability['all_alternative_classifications']=all(x['stable_this_session'] for x in frozen_counts)
    result={'complete':True,'seed':3407,'processes':5,'total_timing_rows':362880,
            'first_start_utc':blocks[0]['start_utc'],'last_finish_utc':blocks[-1]['finish_utc'],
            'session_seconds':(datetime.fromisoformat(blocks[-1]['finish_utc'])-datetime.fromisoformat(blocks[0]['start_utc'])).total_seconds(),
            'application_corpus_equal':True,'frozen_corpus_equal':True,'application_identity_sha256':identity,
            'frozen_identity_sha256':expected_frozen_identity,
            'application_gates':[e['gates'] for e in app],'frozen_gates':[e['gates'] for e in frozen],
            'prior_frozen_gates':prior['gates'],'prior_conclusion_stability':stability,
            'application_effective_counts':decisions,'frozen_effective_counts':frozen_counts,
            'application_cells':ac,'frozen_cells':fc,
            'application_spread_over_120':sum(s['spread_over_120'] for c in ac for s in c['modes'].values()),
            'frozen_spread_over_120':sum(s['spread_over_120'] for c in fc for s in c['modes'].values())}
    save(ROOT/'REPETITIONS.json',result)
    lines=['# Round 7 application and repetition report','',
       'Application inputs are YCSB-inspired synthetic reads from an authenticated immutable snapshot, with uniform or exact finite-Zipf selection. They are not a production trace or an exact YCSB implementation. No network service was measured.','',
       '本实验为单种子（seed=3407），存在随机噪声风险。Five fresh processes per workload were run in one shared-host session; no independent-workload or day-to-day inference is made.','',
       f"All ten processes completed: {result['total_timing_rows']:,} timing rows over {result['session_seconds']:.1f} seconds. Both corpora and observation orders matched across their five processes. Independent audits reconstructed and verified every stored frame.",'',
       '| Block | Application hotness | Application service effective /256 | Application codec effective /256 | Frozen locality | Frozen lifecycle |',
       '|---:|---|---:|---:|---|---|']
    for i,(a,f) in enumerate(zip(result['application_gates'],result['frozen_gates']),1):
        lines.append(f"| {i} | {a['hot']} | {a['service_effective']} | {a['codec_effective']} | {f['locality']} | {f['lifecycle']} |")
    lines+=['',f"Absolute cell-mode median spread exceeded 1.20 in {result['application_spread_over_120']}/576 application summaries and {result['frozen_spread_over_120']}/576 frozen summaries. These are descriptive flags, not statistical tests or exclusion rules.",'',
       f"Agreement with the previously observed Linux/Gold conclusions in all five new processes: {json.dumps(stability)}. A false entry denotes mixed or changed findings and is not described as stable.",'',
       'A service-path pass and codec-only pass have different denominators. Proof generation is measured in the application arm and can dilute adapter overhead; it does not change the original codec-only verdict. No workload distribution, mode or threshold was selected using confirmation outcomes.','',
       'Transfer boundaries in REPETITIONS.json assume serial local processing plus response transmission with common overhead. They are not measured link rates or RPC throughput. A finite range spans the five process estimates; changed boundary classes are retained explicitly.','',
       '## Application classifications across processes','',
       '| Cell | Mode | Service passes /5 | Codec passes /5 |','|---|---|---:|---:|']
    for x in decisions:lines.append(f"| {x['cell']} | {x['mode']} | {x['service_count']} | {x['codec_count']} |")
    for label,cells in [('Application',ac),('Frozen corpus',fc)]:
        lines+=['',f'## {label}: every process-level cell summary','',
           '| Domain/cell | Mode | Paired total ratio range | Absolute median us range | Max/min |',
           '|---|---|---:|---:|---:|']
        for c in cells:
            for mode,s in c['modes'].items():
                r=s['paired_total_ratio'];t=s['median_total_ns']
                lines.append(f"| {c['domain']}/{c['cell']} | {mode} | {r['min']:.6f}–{r['max']:.6f} | {t['min']/1000:.3f}–{t['max']/1000:.3f} | {s['absolute_spread']:.4f} |")
    with (ROOT/'REPORT.md').open('x',encoding='utf8') as f:f.write('\n'.join(lines)+'\n')
    print('ROUND7 AUDIT AND SUMMARY COMPLETE',flush=True)


if __name__=='__main__':run()
