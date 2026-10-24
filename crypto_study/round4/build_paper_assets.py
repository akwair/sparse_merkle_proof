from pathlib import Path
import json,statistics,shutil
ROOT=Path(__file__).resolve().parent
PAPER=ROOT.parent/'round2/manuscript'
E=json.loads((ROOT/'runs/conditions_001/eval.json').read_text())
D=json.loads((ROOT/'runs/conditions_001/measurements/diagnostics.json').read_text())
labels={'ordinary':'Ordinary','compact':'Compact','dictionary':'Dictionary','zlib-ordinary':'zlib ordinary','zlib-compact':'zlib compact','zlib-dictionary':'zlib dictionary','reset-zlib-ordinary':'Reset zlib ordinary','reset-zlib-compact':'Reset zlib compact','reset-zlib-dictionary':'Reset zlib dictionary'}
lines=[r'\begin{table}[tbp]',r'\centering\small',r'\caption{Ranges across all 64 domain-specific cells. Byte ratios are worst-of-three complete-frame ratios; time ratios are medians of 63 paired ratios. The range endpoints can come from different cells. Reset modes share their fresh counterparts\textquotesingle{} frames. All alternative modes exceed the 1.05 time threshold in every cell.}',r'\label{tab:ranges}',r'\begin{tabular}{lrr}',r'\toprule Configuration & Byte ratio range & Local-time ratio range \\',r'\midrule']
for m,label in labels.items():
 if m=='ordinary':continue
 bs=[c['modes'][m]['worst_byte_ratio'] for c in E['cells']];ts=[c['modes'][m]['paired_total_ratio'] for c in E['cells']]
 lines.append(f'{label} & {min(bs):.3f}--{max(bs):.3f} & {min(ts):.3f}--{max(ts):.3f} '+r'\\')
lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
(PAPER/'tables/round4_ranges.tex').write_text('\n'.join(lines)+'\n')
lines=[r'\begin{table}[tbp]',r'\centering\small',r'\caption{Registered writer-lifecycle comparisons meeting their respective criteria. Development requires reset/fresh $\leq0.90$; confirmation requires $<1.00$. Each entry counts eight cells: two populations, two query kinds and two locality patterns. These are condition counts, not independent statistical replicates.}',r'\label{tab:lifecycle}',r'\begin{tabular}{lrrrr}',r'\toprule & \multicolumn{2}{c}{Development} & \multicolumn{2}{c}{Confirmation} \\',r'\cmidrule(lr){2-3}\cmidrule(lr){4-5}',r'Representation & $q=1$ & $q=8$ & $q=1$ & $q=8$ \\',r'\midrule']
for base in ('ordinary','compact','dictionary'):
 vals=[]
 for dom in ('dev','confirm'):
  for q in (1,8):
   xs=[x for x in E['lifecycle'] if x['domain']==dom and x['mode']=='reset-zlib-'+base and f'_q{q}_' in x['cell']];vals.append(f'{sum(x["passed"] for x in xs)}/{len(xs)}')
 lines.append(base.capitalize()+' & '+' & '.join(vals)+r' \\')
lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
(PAPER/'tables/round4_lifecycle.tex').write_text('\n'.join(lines)+'\n')
lines=[r'\begin{table}[tbp]',r'\centering\small',r'\caption{Illustrative same-condition comparison: confirmation domain, $N=16{,}384$, $q=128$, clustered membership queries. Byte and time columns are separate medians over the same cell; the paired-ratio column is not their quotient. Every cell is available in the full report.}',r'\label{tab:example}',r'\begin{tabular}{lrrr}',r'\toprule Configuration & Median bytes & Median time ($\mu$s) & Paired ratio \\',r'\midrule']
c=next(c for c in E['cells'] if c['domain']=='confirm' and c['cell']=='n16384_q128_member_clustered')
for m in labels:
 s=c['modes'][m];lines.append(f"{labels[m]} & {s['median_bytes']:,.0f} & {s['median_total_ns']/1000:,.1f} & {s['paired_total_ratio']:.3f} "+r'\\')
lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
(PAPER/'tables/round4_example.tex').write_text('\n'.join(lines)+'\n')
for p in (ROOT/'manuscript/figures').glob('*.pdf'):shutil.copyfile(p,PAPER/'figures'/('round4_'+p.name))
summary={
 'locality_pp':{dom:[100*min(x['improvement'] for x in E['locality'] if x['domain']==dom),100*max(x['improvement'] for x in E['locality'] if x['domain']==dom)] for dom in ('dev','confirm')},
 'q1_reset_range':[min(c['modes'][m]['reset_fresh_ratio'] for c in E['cells'] if c['q']==1 for m in labels if m.startswith('reset-')),max(c['modes'][m]['reset_fresh_ratio'] for c in E['cells'] if c['q']==1 for m in labels if m.startswith('reset-'))],
 'depth_range':[min(v for d in D for v in d['depths']),max(v for d in D for v in d['depths'])],
 'proof_occurrences':sum(d['q'] for d in D),'side_nodes':sum(d['occurrences'] for d in D),'zero_nodes':sum(d['zero_occurrences'] for d in D),
 'effective_cells':sum(x['effective'] for x in E['effective'])}
(ROOT/'paper_numbers.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
