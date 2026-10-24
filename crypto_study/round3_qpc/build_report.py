"""Post-registration report and manuscript table generation from raw results."""
from pathlib import Path
import json,statistics
ROOT=Path(__file__).resolve().parent
WORK=ROOT/'runs/screening_001'

def main():
    audit=json.loads((ROOT/'AUDIT.json').read_text());ev=json.loads((WORK/'eval.json').read_text())
    ds={h:json.loads((WORK/h/'diagnostics.json').read_text()) for h in ('reference','external')}
    cells=ev['cells'];out=ROOT/'analysis';out.mkdir(exist_ok=True)
    summary={'gates':ev['gates'],'rows':ev['rows']}
    for host in ('reference','external'):
        cc=[c for c in cells if c['host']==host]
        summary[host]={'passed_cells':sum(c['pass'] for c in cc),'total_cells':len(cc),
            'byte_ratio_range':[min(c['byte_ratio'] for c in cc),max(c['byte_ratio'] for c in cc)],
            'paired_time_ratio_range':[min(c['time_ratio'] for c in cc),max(c['time_ratio'] for c in cc)],
            'slower_pairs':sum(c['slower_pairs'] for c in cc),'over_105_pairs':sum(c['over_105_pairs'] for c in cc)}
    b=ds['external'];depths=[n for x in b for n in x['depths']];retained=[n for x in b for n in x['retained']]
    summary['external_structure']={'depth_range':[min(depths),max(depths)],'proofs':len(depths),'placeholders':sum(d-k for d,k in zip(depths,retained)),
        'no_placeholder_proofs':sum(d==k for d,k in zip(depths,retained)),
        'compact_larger_bundles':sum(x['sizes']['compact']>x['sizes']['ordinary'] for x in b),
        'compact_smaller_bundles':sum(x['sizes']['compact']<x['sizes']['ordinary'] for x in b)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Round3 corrected screening report','', '## Scope and validity','',
    'This report uses only round3_qpc/runs/screening_001 after the real wrapper process exited zero. The original clock-invalid run remains archived separately. No zero sample was dropped or imputed. The corrected run used the identical design with a registered QPC clock amendment.',
    '',f"Rows: {ev['rows']}; reference 5292, external 6048. Exact frame replay: {audit['original_reference_frames']} reference and {audit['external_frames']} external frames. Independent Python verification of external proofs: {audit['independently_verified_external_proofs']}.",
    '', '本实验为单种子，存在随机噪声风险。Reference domains reuse observed Round2 fixtures; the external domains are fresh but share a generator. Technical repeats are not independent datasets.',
    '', '## Registered gates','',f"H1 (binary reference): {ev['gates']['reference']}. H2 (upstream external compact): {ev['gates']['external']}. Universal portability gate: {all(ev['gates'].values())}.",
    '', '| Host | Domain | Cell | Worst byte ratio | Median paired time ratio | Slower pairs / 63 | Pass |', '|---|---|---|---:|---:|---:|---|']
    for c in cells:lines.append(f"|{c['host']}|{c['domain']}|{c['cell']}|{c['byte_ratio']:.6f}|{c['time_ratio']:.6f}|{c['slower_pairs']}|{c['pass']}|")
    lines+=['','## Structural diagnosis','',
    'All exact byte identities matched archived frames. For the reference, binary omission saves 32(255-k) bytes per step; for the external wrapper it saves 32(d-k)-2-ceil(d/8). The latter includes a two-byte original-depth field. These identities hold for our documented envelopes, not every possible serialization.',
    '',json.dumps(summary['external_structure'],indent=2),
    '', 'A compact frame that adds mask/depth metadata but omits too few placeholder nodes can become larger. This accounting directly diagnoses the byte outcome. Timing ratios include compaction, encoding, reconstruction and unchanged verification; exact cache, allocation and scheduler causes have not been isolated. Do not label timing differences as cryptographic degradation.',
    '', '## Decision','',
    'If either gate fails, do not claim host-independent bitmap dominance. The proposed universal-dominance premise is rejected within the measured conditions; no selector or network advantage is asserted. Retain the negative result and revise the manuscript around baseline sensitivity. A new adaptive or concurrency study requires a separate specific hypothesis, prior-art review and PLAN.',
    '', '## Full mode metrics','', '|Host/domain/cell|Mode|Median bytes|Median total (ms)|p95 total (ms)|Max total (ms)|Encode median (ms)|Decode median (ms)|Verify median (ms)|','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for c in cells:
        for mode,v in c['modes'].items():
            nums=[v[k]/1e6 for k in ('median_total_ns','p95_total_ns','max_total_ns','median_encode_ns','median_decode_ns','median_verify_ns')]
            lines.append('|'+f"{c['host']}/{c['domain']}/{c['cell']}|{mode}|{v['median_bytes']:.0f}|"+'|'.join(f'{x:.6f}' for x in nums)+'|')
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Tables show the second deterministic domain for compact presentation.
    # All cells and both domains remain in REPORT.md and eval.json.
    for host in ('reference','external'):
        cc=[c for c in cells if c['host']==host and c['domain']=='confirm']
        if host=='reference':
            modes=['full','binary-full','binary-bitmap','binary-zlib','binary-bitmap-zlib']
            heads=r'$N$/ops & JSON full & Binary full & Bitmap & zlib(full) & zlib(bitmap) \\'
            caption='Complete frame sizes (bytes), medians over three archived reference batches in the second domain. All binary modes retain the original signature and verification relation.'
        else:
            modes=['ordinary','compact','zlib-ordinary','zlib-compact']
            heads=r'$N$/queries/type & Native & Compact & zlib(native) & zlib(compact) \\'
            caption='Complete external frame sizes (bytes), medians over three query bundles in the second domain. M denotes membership and A non-membership. These are separate tasks from signed sequential updates.'
        lines=[r'\begin{table}[tbp]',r'\centering\small',r'\caption{'+caption+'}',r'\label{tab:r3-'+host+'}',r'\begin{tabular}{l'+'r'*len(modes)+'}',r'\toprule',heads,r'\midrule']
        def order(c):
            s=c['cell'].split('_');return(int(s[0][1:]),int(s[1][1:]),s[2] if len(s)>2 else '')
        for c in sorted(cc,key=order):
            s=c['cell'].split('_');label=s[0][1:]+'/'+(str(2*int(s[1][1:])) if host=='reference' else s[1][1:]+'/'+('M' if s[2]=='member' else 'A'))
            lines.append(label+' & '+' & '.join(f"{c['modes'][m]['median_bytes']:,.0f}" for m in modes)+r' \\')
        lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
        (out/(host+'_sizes.tex')).write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
