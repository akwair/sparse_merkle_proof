"""Registered descriptive analysis; no filtering, tuning or independent-repeat inference."""
from pathlib import Path
from collections import defaultdict
import json,statistics,argparse

ROOT=Path(__file__).resolve().parent
MODES=['ordinary','compact','dictionary','zlib-ordinary','zlib-compact','zlib-dictionary','reset-zlib-ordinary','reset-zlib-compact','reset-zlib-dictionary']
def pct(xs,p):
 xs=sorted(xs);pos=(len(xs)-1)*p;i=int(pos)
 return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(pos-i)
def validate_matrix(rows,diagnostics):
 expected={(d,n,q,k,p,b) for d in ('dev','confirm') for n in (4096,16384) for q in (1,8,32,128) for k in ('member','absent') for p in ('dispersed','clustered') for b in range(3)}
 def key(x):return tuple(x[k] for k in ('domain','n','q','kind','pattern','batch'))
 def checkmeta(x):
  cell=f"n{x['n']}_q{x['q']}_{x['kind']}_{x['pattern']}"
  if x['cell']!=cell or x['id']!=f"{x['domain']}_{cell}_b{x['batch']}":raise ValueError('inconsistent labels')
 ds={}
 for d in diagnostics:
  checkmeta(d);k=key(d)
  if k in ds:raise ValueError('duplicate diagnostic')
  if set(d['sizes'])!=set(MODES):raise ValueError('diagnostic modes')
  if any(len(d[x])!=d['q'] for x in ('depths','retained','masks')):raise ValueError('diagnostic array length')
  if any(not 0<=kept<=dep<=256 or mask!=(dep+7)//8 for dep,kept,mask in zip(d['depths'],d['retained'],d['masks'])):raise ValueError('diagnostic shape')
  if d['occurrences']!=sum(d['depths']) or d['zero_occurrences']!=sum(dep-kept for dep,kept in zip(d['depths'],d['retained'])):raise ValueError('diagnostic counts')
  if d['nonzero_occurrences']!=d['occurrences']-d['zero_occurrences'] or not 0<=d['unique_nonzero_nodes']<=d['nonzero_occurrences']:raise ValueError('nonzero counts')
  if d['unique_nodes']!=d['unique_nonzero_nodes']+int(d['zero_occurrences']>0):raise ValueError('unique counts')
  ds[k]=d
 if set(ds)!=expected:raise ValueError('diagnostic matrix mismatch')
 seen=set();orders=defaultdict(set)
 for r in rows:
  checkmeta(r);k=key(r)
  if k not in ds or r['repeat'] not in range(21) or r['mode'] not in MODES:raise ValueError('row labels')
  identity=(k,r['repeat'],r['mode'])
  if identity in seen:raise ValueError('duplicate row')
  seen.add(identity)
  if r['bytes']!=ds[k]['sizes'][r['mode']]:raise ValueError('row/diagnostic bytes')
  orders[(k,r['repeat'])].add(r['order'])
 if len(seen)!=len(expected)*21*len(MODES) or any(v!=set(range(9)) for v in orders.values()):raise ValueError('incomplete row matrix or order')
def summarize_cells(rows,required_modes=None,expected_pairs=63):
 required_modes=set(MODES) if required_modes is None else required_modes
 groups=defaultdict(list)
 for r in rows:
  if r['bytes']<=0 or r['total_ns']<=0 or any(r[k]<0 for k in ('encode_ns','decode_ns','verify_ns')) or sum(r[k] for k in ('encode_ns','decode_ns','verify_ns'))!=r['total_ns']:raise ValueError('invalid time/bytes')
  groups[(r['domain'],r['cell'])].append(r)
 result=[]
 for (domain,cell),rr in sorted(groups.items()):
  pairs=defaultdict(dict)
  for r in rr:
   p=pairs[(r['batch'],r['repeat'])]
   if r['mode'] in p:raise ValueError('duplicate pair')
   p[r['mode']]=r
  if len(pairs)!=expected_pairs or any(set(p)!=required_modes for p in pairs.values()):raise ValueError('missing or excess pair')
  stats={}
  for m in sorted(required_modes):
   obs=[p[m] for p in pairs.values()]
   ratios=[p[m]['total_ns']/p['ordinary']['total_ns'] for p in pairs.values()]
   br=[p[m]['bytes']/p['ordinary']['bytes'] for p in pairs.values()]
   v={'median_bytes':statistics.median(r['bytes'] for r in obs),'worst_byte_ratio':max(br),'paired_total_ratio':statistics.median(ratios),'slower_pairs':sum(x>1 for x in ratios),'over_105_pairs':sum(x>1.05 for x in ratios),'max_paired_total_ratio':max(ratios),'p95_total_ns':pct([r['total_ns'] for r in obs],.95),'max_total_ns':max(r['total_ns'] for r in obs)}
   for k in ('encode_ns','decode_ns','verify_ns','total_ns'):v['median_'+k]=statistics.median(r[k] for r in obs)
   v['gate']=v['worst_byte_ratio']<=.8 and v['paired_total_ratio']<=1.05
   if m.startswith('reset-'):
    fresh=m.removeprefix('reset-')
    v['reset_fresh_ratio']=statistics.median(p[m]['total_ns']/p[fresh]['total_ns'] for p in pairs.values())
    if any(p[m]['bytes']!=p[fresh]['bytes'] for p in pairs.values()):raise ValueError('reset byte mismatch')
   stats[m]=v
  for m,s in stats.items():
   s['dominated_by']=[k for k,v in stats.items() if k!=m and v['worst_byte_ratio']<=s['worst_byte_ratio'] and v['paired_total_ratio']<=s['paired_total_ratio'] and (v['worst_byte_ratio']<s['worst_byte_ratio'] or v['paired_total_ratio']<s['paired_total_ratio'])]
  result.append(dict(domain=domain,cell=cell,pairs=len(pairs),**{k:rr[0][k] for k in ('n','q','kind','pattern')},modes=stats))
 return result

def evaluate(rows,diagnostics):
 validate_matrix(rows,diagnostics)
 cells=summarize_cells(rows)
 if len(cells)!=64 or len(rows)!=36288 or len(diagnostics)!=192:raise ValueError('matrix count')
 dc=defaultdict(list)
 for d in diagnostics:
  if d['sizes']['ordinary']-d['sizes']['dictionary']!=30*d['occurrences']-32*d['unique_nodes']-2:raise ValueError('dictionary identity')
  if d['sizes']['ordinary']-d['sizes']['compact']!=sum(32*(dep-k)-2-mask for dep,k,mask in zip(d['depths'],d['retained'],d['masks'])):raise ValueError('compact identity')
  dc[(d['domain'],d['n'],d['q'],d['kind'],d['pattern'])].append(d)
 locality=[]
 for domain in ('dev','confirm'):
  for n in (4096,16384):
   for q in (32,128):
    for kind in ('member','absent'):
     v={p:statistics.median(d['sizes']['dictionary']/d['sizes']['ordinary'] for d in dc[(domain,n,q,kind,p)]) for p in ('dispersed','clustered')}
     delta=v['dispersed']-v['clustered']
     locality.append(dict(domain=domain,n=n,q=q,kind=kind,ratios=v,improvement=delta,passed=delta>=.10 if domain=='dev' else delta>0))
 lifecycle=[]
 for c in cells:
  if c['q'] not in (1,8):continue
  for m,s in c['modes'].items():
   if not m.startswith('reset-'):continue
   ratio=s['reset_fresh_ratio']
   lifecycle.append(dict(domain=c['domain'],cell=c['cell'],mode=m,ratio=ratio,passed=ratio<=.90 if c['domain']=='dev' else ratio<1))
 by={(c['domain'],c['cell']):c for c in cells};effective=[]
 for c in cells:
  if c['domain']!='dev':continue
  conf=by[('confirm',c['cell'])]
  for m,s in c['modes'].items():
   cc=conf['modes'][m]
   effective.append(dict(cell=c['cell'],mode=m,dev_pass=s['gate'],confirm_direction=cc['worst_byte_ratio']<1 and cc['paired_total_ratio']<=1.05,effective=s['gate'] and cc['worst_byte_ratio']<1 and cc['paired_total_ratio']<=1.05))
 return dict(rows=len(rows),bundles=len(diagnostics),cells=cells,locality=locality,lifecycle=lifecycle,effective=effective,payload_model=payload_model(rows),gates={'locality':all(x['passed'] for x in locality),'lifecycle':all(x['passed'] for x in lifecycle)})

def payload_model(rows):
 groups=defaultdict(lambda:defaultdict(dict))
 for r in rows:groups[(r['domain'],r['cell'],r['batch'])][r['repeat']][r['mode']]=r
 out=[]
 for (domain,cell,batch),pairs in sorted(groups.items()):
  for m in MODES[1:]:
   diffs=[p[m]['total_ns']-p['ordinary']['total_ns'] for p in pairs.values()]
   dt=statistics.median(diffs);p=next(iter(pairs.values()));dw=p['ordinary']['bytes']-p[m]['bytes']
   boundary=None
   if dw>0 and dt>0:region='below';boundary=8*dw/(dt/1e9)
   elif dw<0 and dt<0:region='above';boundary=8*dw/(dt/1e9)
   elif dw>=0 and dt<=0 and (dw>0 or dt<0):region='all'
   elif dw==0 and dt==0:region='tie'
   else:region='none'
   out.append(dict(domain=domain,cell=cell,batch=batch,mode=m,delta_bytes=dw,median_delta_ns=dt,p10_delta_ns=pct(diffs,.10),p90_delta_ns=pct(diffs,.90),favorable_region=region,boundary_payload_bits_s=boundary))
 return out

def report(result,diags,path):
 lines=['# Round4 registered results','',f"Observations: {result['rows']}; bundles: {result['bundles']}; domain-specific cells: {len(result['cells'])}.",'','Single seed=3407. 本实验为单种子，存在随机噪声风险。Repeated observations are technical repeats, not independent workload samples. QPC measures local wall time, not processor cycles or network latency.','',f"H-locality: **{result['gates']['locality']}**; H-lifecycle: **{result['gates']['lifecycle']}**. Failure does not change the registered threshold.",'','## Registered locality comparisons','','|Domain|N|q|Kind|Dispersed ratio|Clustered ratio|Difference|Pass|','|---|---:|---:|---|---:|---:|---:|---|']
 for x in result['locality']:lines.append(f"|{x['domain']}|{x['n']}|{x['q']}|{x['kind']}|{x['ratios']['dispersed']:.6f}|{x['ratios']['clustered']:.6f}|{x['improvement']:.6f}|{x['passed']}|")
 lines+=['','## Registered lifecycle comparisons','','|Domain|Cell|Mode|Reset/fresh paired median|Pass|','|---|---|---|---:|---|']
 for x in result['lifecycle']:lines.append(f"|{x['domain']}|{x['cell']}|{x['mode']}|{x['ratio']:.6f}|{x['passed']}|")
 lines+=['','## All modes and all conditions','','Bytes are median complete-frame sizes. Byte ratio is worst of three bundles; time ratio is median of 63 paired ratios. p95/max include every observation. Summary Pareto membership does not imply per-request dominance.','']
 for c in result['cells']:
  lines += [f"### {c['domain']} / {c['cell']}",'','|Mode|Bytes|Worst byte ratio|Paired time ratio|Median total us|p95 us|max us|Encode us|Decode us|Verify us|Slower / >1.05|Gate|Pareto|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|']
  for m in MODES:
   s=c['modes'][m]
   lines.append(f"|{m}|{s['median_bytes']:g}|{s['worst_byte_ratio']:.5f}|{s['paired_total_ratio']:.5f}|{s['median_total_ns']/1000:.2f}|{s['p95_total_ns']/1000:.2f}|{s['max_total_ns']/1000:.2f}|{s['median_encode_ns']/1000:.2f}|{s['median_decode_ns']/1000:.2f}|{s['median_verify_ns']/1000:.2f}|{s['slower_pairs']} / {s['over_105_pairs']}|{s['gate']}|{not s['dominated_by']}|")
 lines+=['','## Structural diagnostics and interpretation boundary','','All compact and dictionary accounting residuals are zero. Native depth, zero-placeholder counts, nonzero repetition, unique node counts and all frame sizes are retained per bundle in diagnostics.json. Dictionary construction and lookup costs are timed. A favorable dictionary result establishes compatibility/cost under this envelope, not multiproof optimality.','', 'H-locality is a workload intervention: the same tree and verifier are retained but selected proofs may differ in depth and zero counts. The exact accounting identity explains frame bytes; it does not establish a unique microarchitectural cause for time. H-lifecycle changes writer allocation reuse while requiring identical frames and fresh decoding. It identifies the effect of this implementation choice in the measured process, without attributing all time to allocator or GC internals.','', 'No thresholds or formats were selected using confirmation results. Directional confirmation is weaker than meeting the development magnitude threshold. All unfavorable cells and slow observations are preserved.']
 path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('work',type=Path);a=ap.parse_args();p=a.work/'measurements'
 rows=[json.loads(x) for x in (p/'log.jsonl').read_text().splitlines()];diags=json.loads((p/'diagnostics.json').read_text())
 result=evaluate(rows,diags)
 with (a.work/'eval.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 report(result,diags,a.work/'REPORT.md')
 print(json.dumps(result['gates']))
if __name__=='__main__':main()
