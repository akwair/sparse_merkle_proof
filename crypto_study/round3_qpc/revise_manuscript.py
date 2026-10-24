"""Evidence-led substantive revision; old manuscript saved before this script."""
from pathlib import Path
import json,shutil,re,difflib
ROOT=Path(__file__).resolve().parent
M=ROOT.parent/'round2/manuscript'
summary=json.loads((ROOT/'analysis/summary.json').read_text())
audit=json.loads((ROOT/'AUDIT.json').read_text())
old=(ROOT/'manuscript_before/main.tex').read_text()
s=old
title=r'Baseline Sensitivity of Sparse Merkle Proof Transport\\Binary Encodings and an External Implementation'
s=re.sub(r'\\title\{.*?\}\n',lambda _:r'\title{'+title+'}\n',s,count=1)
s=s.replace('pdftitle={Representation Costs of Sparse Merkle Proof Transport in a Fixed Public-State Reference}', 'pdftitle={Baseline Sensitivity of Sparse Merkle Proof Transport}')
ref=summary['reference'];ext=summary['external']
old_json=[x['comparisons']['bitmap']['time_ratio'] for x in audit['comparisons'] if x['host']=='reference']
numbers={'RThreeRefMinSaving':100*(1-ref['paired_time_ratio_range'][1]),'RThreeRefMaxSaving':100*(1-ref['paired_time_ratio_range'][0]),
         'RThreeExtMinSlow':100*(ext['paired_time_ratio_range'][0]-1),'RThreeExtMaxSlow':100*(ext['paired_time_ratio_range'][1]-1),
         'RThreeJSONMinSlow':100*(min(old_json)-1),'RThreeJSONMaxSlow':100*(max(old_json)-1)}
(M/'round3_numbers.tex').write_text('\n'.join('\\newcommand{\\'+name+'}{'+f'{value:.2f}'+'}' for name,value in numbers.items())+'\n')
s=s.replace(r'\input{numbers}',r'\input{numbers}'+'\n'+r'\input{round3_numbers}')
abstract=r'''A sparse Merkle proof format that transmits reconstructible hashes can make compression gains appear large. Evaluating those gains requires separating proof structure from serialization cost. We examine this dependence through a frozen Python signed-state reference and an independent, pinned Go sparse Merkle implementation. An initial registered JSON comparison is followed by a separately registered screening with full binary, bitmap and generic-compression variants. All comparisons preserve each host's verification relation. The corrected screening contains 11,340 timing observations across 12 reference cells and 24 external cells, using seed 3407. In the reference, binary bitmap encoding reduced median paired local processing time by \RThreeRefMinSaving--\RThreeRefMaxSaving\% relative to full binary. The original JSON bitmap was smaller but \RThreeJSONMinSlow--\RThreeJSONMaxSlow\% slower than that binary baseline. In the external implementation, compact proofs increased median paired processing time by \RThreeExtMinSlow--\RThreeExtMaxSlow\%; 28 of 72 query bundles also became larger. Structural accounting found no removable placeholder in 778 of 1,188 external proofs, directly explaining why compaction metadata can exceed the saved node bytes. Exact replay covered 540 screening frames, including independent verification of the external proofs. These results delimit the benefit of established omission mechanisms in two implementations. They do not establish a new cryptographic primitive, a universal format preference or network-level acceleration.'''
s=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _:r'\begin{abstract}'+'\n'+abstract+'\n'+r'\end{abstract}',s,count=1,flags=re.S)
intro=r'''\section{Introduction}
Authenticated state services send proofs that allow a receiver to check data or a state transition against a trusted root. The communication cost depends on what the underlying tree already omits and how the remaining proof is serialized. A fixed-depth sparse path can contain many reconstructible default hashes; a native path-compacted implementation may expose a much shorter proof before any transport transform is applied.

Default-node omission is established practice. Its benefit should therefore be assessed against the representation an implementation would otherwise use. A large reduction relative to hexadecimal JSON does not by itself establish an advantage over full binary transport, and fewer transmitted bytes need not reduce encoding and decoding work. Generic compression introduces a further tradeoff: it may exploit repeated proof material while adding processing cost.

We investigate these issues in two stages. The initial experiment evaluates a reversible bitmap layer over a frozen Python signed-state reference. A subsequent screening introduces binary baselines for the same signed objects and tests the upstream compact-proof operations of a pinned Go sparse Merkle library. The external library verifies key-value membership and non-membership, while the reference verifies signed sequential updates. Each comparison is therefore made within its host; we do not rank their absolute execution times.

The study contributes a reproducible baseline-sensitivity analysis, exact accounting of the bytes saved or added by omission, and an independently checked external comparison that exposes a limit of the initial result. It evaluates existing mechanisms rather than proposing a new proof system. The central question is whether the observed benefit survives a stronger representation baseline and a host whose native paths are already compacted.

'''
s=re.sub(r'\\section\{Introduction\}.*?(?=\\section\{Prior mechanisms)',lambda _:intro,s,flags=re.S)
s=s.replace('The optional module is therefore placed after the frozen serializer', 'In the initial experiment, the optional module is placed after the frozen serializer')
s=s.replace('These are direct precedents, although their complete implementations were neither reproduced nor benchmarked here.',r'These are direct precedents. The initial JSON study did not benchmark them; the later screening uses a pinned Celestia SMT revision and its upstream compaction and verification functions \citep{celestiaPinned}. JMT and Nervos remain literature comparators.')
needle=r'\section{Reference and transport formats}'
s=s.replace(needle,r'''The Ipsilon code-merkleization analysis compared baseline and slim proofs with Snappy-compressed baseline proofs on Ethereum block data \citep{ipsilonAnalysis}. This directly precedes comparisons between structural omission and general-purpose compression. Our contribution is not the introduction of that comparison; it is the controlled diagnosis of how the baseline and native path structure affect the results in the two studied hosts.

'''+needle)
s=s.replace('Every mode first computes \\(S(B)\\).','Every mode in the initial JSON experiment first computes \\(S(B)\\).')
s=s.replace('The experiment therefore compares JSON representations without a binary transport protocol as a comparator.','The initial experiment therefore compares JSON representations. The subsequent screening adds binary comparators under a separate registration.')
s=s.replace(r'\section{Preregistered evaluation}',r'\section{Initial registered JSON evaluation}')
s=s.replace(r'\section{Results}',r'\section{Initial JSON results}')
s=s.replace('Initial launch attempts did not enter the experiment because the child search path lacked MSYS utilities. In the recorded retry, the existing MSYS binary directory was prepended to the child process\'s path.', 'Initial launch attempts did not enter the experiment, and their records were retained. A recorded retry prepended the existing MSYS binary directory to the child process\'s path; the records do not isolate the cause of every initial failure.')
newsection=r'''\section{Strong-baseline and external screening}
\subsection{Representations and verification boundaries}
The screening retained the reference's tree, signature payload and verifier. Four binary modes were added: full, bitmap, zlib-compressed full and zlib-compressed bitmap. Each frame carries both checkpoints, ordered operations and the original signature. Integers and lengths use unsigned big-endian fields; hashes use their original 32 bytes. All four binary modes start from the same prepared batch. They do not first serialize and parse JSON, although the unchanged verifier still reconstructs its signed JSON payload. The three original transport modes were remeasured alongside them. This design measures complete representation paths and does not attribute their differences solely to node omission.

The external host was Celestia SMT commit \texttt{dba215cc}, with the full revision and unmodified sources archived. It used SHA-256 and upstream update, proof, compaction, decompaction and verification functions. Its native proofs have variable-depth sibling lists and may carry unrelated-leaf data for non-membership. We wrapped ordinary and compact proofs in a common binary bundle format, preserving roots, keys, values and all proof fields, and also compressed each format with level-6 zlib. Compact proofs were restored by upstream decompaction before the same ordinary verifier was called. No proof was padded to 256 siblings. These wrappers are research transport formats, not an upstream wire standard.

The reference adapter enforces limits on input bytes, restored JSON bytes, steps and key lengths, along with exact frame termination. The external wrapper bounds frames and inflated data at 8 MiB, bundles at 256 proofs and paths at 256 siblings. Functional checks covered reconstruction, changed values or signatures, truncated frames and trailing data. They do not establish comprehensive parser security. The default reference mode remains byte-identical to the frozen serializer.

\subsection{Registered design and timer repair}
Reference inputs were the two previously observed Round2 domains, with three batches per set-size and operation-count cell. They are remeasurements, not a new held-out confirmation. External inputs used two new deterministic domains, with set sizes 128, 512 and 2048, query bundles of 1 or 32, and membership and non-membership separately. Each external cell contained three bundles of individual proofs against one root. Both hosts used seed 3407, two warmups per mode and 21 paired repetitions, with randomized mode order. The two hosts ran sequentially on the same CPU as the initial study. The external executable used Go 1.27.3; no absolute Python--Go speed comparison was made.

The screening preregistered two separate gates. The reference gate required at least 30\% fewer bytes for binary bitmap than binary full, and a median paired total-time ratio at most 1.05 in every cell of both domains. The external gate required at least 5\% fewer bytes for compact than ordinary proofs and the same time limit. Byte criteria used the worst of three bundles; time criteria used 63 paired observations. These thresholds were not substituted for the initial study's criteria. A portable-dominance claim required both screening gates to pass.

The first screening run failed measurement validation. Of 6048 external observations, 3573 had zero total duration; all 5292 reference totals were positive. A separate clock probe and short-work regression test diagnosed inadequate resolution of \texttt{time.Now} for the external pipeline on this runtime and host. We retained the complete invalid run and registered an instrument-only amendment before rerunning both hosts. The corrected external runner used Windows QueryPerformanceCounter at 10 MHz \citep{microsoftQpc}. Timestamp overhead was included, with no calibration subtraction. A probe observed a mean adjacent-call difference of approximately 132.5 ns; this is an instrument diagnostic, not a per-request correction.

The amended run kept inputs, modes, repetitions, seeds and thresholds unchanged. Its 11,340 observations contained positive total durations and passed integrity checks. Source hashes, full frames, query objects, checkpoints, launch failures and actual process exits were retained. Independent analysis reproduced all paired metrics and byte identities. Replay checked 252 reference and 288 external frames; a separate Python implementation also verified all 4752 proof instances in the archived external frames against their roots. These repeated instances derive from 1188 external query proofs, not 4752 independent queries.

\subsection{A stronger reference baseline changes the speed comparison}
All 12 reference cells passed the screening gate. The worst-within-cell binary-bitmap/full byte ratios ranged from 0.03599 to 0.06533. Thus substantial omission savings remained after replacing hexadecimal JSON with full binary. Median paired local-time reductions were \RThreeRefMinSaving--\RThreeRefMaxSaving\%, smaller than those in the initial JSON-baseline comparison. More directly, the original JSON bitmap was \RThreeJSONMinSlow--\RThreeJSONMaxSlow\% slower than binary full in the same screening cells, despite its smaller frames (Figure~\ref{fig:baseline-sensitivity}). The choice of baseline therefore changed the speed claim.

At 2048 keys and 32 operations in the second domain, median full-binary and binary-bitmap sizes were 262,971 and 13,403 bytes. Compressing the full binary frame produced 21,427 bytes; compressing the bitmap frame produced 10,117 bytes (Table~\ref{tab:r3-reference}). Generic compression and structural omission are therefore not mutually exclusive alternatives. Across reference cells, the bitmap-plus-zlib/full-binary median paired time ratio ranged from 0.94717 to 1.02148, so its smaller frames did not yield a consistent processing advantage over full binary.

\input{tables/round3_reference_sizes}
\begin{figure}[tbp]
\centering
\includegraphics[width=\linewidth]{figures/baseline_sensitivity.pdf}
\caption{Baseline sensitivity in the corrected screening. Each point is one cell: panel A uses its worst byte ratio across three inputs; panel B uses its median of 63 paired total-time ratios. The denominator is binary full in the reference and ordinary binary proofs in the external host. Domains use different markers; vertical offsets only separate points. Reference domains reuse archived inputs, whereas external domains use newly generated queries. The byte axis is logarithmic. Points are descriptive summaries, not independent-seed estimates or confidence intervals. AI-assisted Python plotting used audited observations without imputation.}
\label{fig:baseline-sensitivity}
\end{figure}

\subsection{The external implementation does not reproduce dominance}
None of the 24 external cells passed the joint byte/time gate. Upstream compact proofs increased median paired local total time by \RThreeExtMinSlow--\RThreeExtMaxSlow\%. Compact frames were larger than ordinary frames in 28 of 72 bundles and smaller in the remaining 44. Their worst-within-cell byte ratios ranged from 0.90332 to 1.01250. This does not contradict the reference result: the underlying proof representation and verified task differ.

Table~\ref{tab:r3-external} shows why generic compression also needs a workload-qualified interpretation. For 2048 keys and 32 membership queries in the second domain, median ordinary and compact frames contained 15,302 and 14,280 bytes; zlib reduced them to 10,113 and 10,092 bytes. For single-query membership bundles at the same set size, both zlib variants enlarged the frames. Across external cells, zlib-ordinary had median paired local-time ratios of 3.90--34.80 relative to ordinary transport. These measurements include a fresh compressor per bundle and no network transfer, so they do not decide whether the byte savings would repay their cost on a particular link.

\input{tables/round3_external_sizes}

\subsection{Exact structural diagnosis and observed variation}
Let \(k\) be the retained sibling count of one reference step. Full binary transmits 256 hashes, whereas binary bitmap transmits a 32-byte mask and \(k\) hashes. The exact reduction in our frames is
\[
\Delta W_{\mathrm{reference}}=32(255-k).
\]
For an external path of native depth \(d\) with \(k\) retained siblings, the compact envelope additionally carries a two-byte original-depth field and \(\lceil d/8\rceil\) mask bytes. Its exact reduction is
\[
\Delta W_{\mathrm{external}}=32(d-k)-2-\lceil d/8\rceil.
\]
Other fields cancel within each host. These are format-accounting identities, not a new cryptographic theorem or a latency predictor. They matched every archived screening bundle.

External native depths ranged from 5 to 21. Among 1188 proofs, 778 contained no removable placeholder; the remaining proofs contributed 780 removable nodes in total. When \(d=k\), the compact frame necessarily grows by its depth and mask overhead. This directly explains the byte cost of compaction for those proofs. It does not isolate the microarchitectural cause of the timing increase. Stage measurements identify where work is charged, but cache, allocator and scheduling effects were not experimentally separated.

Median criteria also conceal individual slow observations. Binary bitmap was slower than binary full in 270 of 756 reference pairs, with 188 exceeding a ratio of 1.05. External compact was slower in 1143 of 1512 pairs, with 1099 exceeding 1.05. All observations remain in the report. The passing reference gate therefore establishes neither per-request dominance nor a tail-latency bound.

'''
discussion=r'''\section{Discussion and limitations}
The main result is the sensitivity of a transport claim to its baseline and native proof structure. In the fixed-depth reference, omission still saves many bytes against binary full, so the initial byte reduction cannot be explained solely by hexadecimal JSON overhead. The local processing advantage is smaller under that stronger baseline. The original JSON bitmap even becomes slower than binary full, showing that a compact message and an efficient processing path are separate properties.

The external comparison places a further boundary on the result. Its native paths contain far fewer siblings, and most measured proofs have no removable placeholder. Adding compaction metadata can consequently increase size, while the compaction/reconstruction path adds work. This finding concerns the measured upstream operations and our common envelopes. It is not a ranking of tree libraries or a claim that compact proofs are generally undesirable. A different envelope could reduce metadata overhead, and persistent compression contexts or multiproofs could change the tradeoff; neither was evaluated.

The prior Ipsilon comparison already showed that generic compression can outperform structural omission in a different proof workload. Our results add an explicit binary baseline, a separate native-proof comparison and exact byte accounting within a reproducible paired design. The study does not establish a new compression algorithm or a transferable latency-selection rule. The failed external gate gives no basis for proceeding directly from the initial result to a universal adaptive transport claim.

External validity remains limited by one machine, seed 3407, synthetic inputs, warm repeated processing and one additional library revision. The reference inputs were already observed before screening. The two hosts differ in runtime, proof semantics and acceptance work, so their normalized within-host comparisons do not isolate the causal effect of tree depth alone. A controlled intervention that changes only depth or redundancy would be needed for that causal claim. Repeated observations quantify variation within these setups and do not establish robustness across independent seeds or deployments.

The measurements contain no sockets, network transfer, concurrent service throughput, crash recovery or production workload trace. Original Python allocation measurements apply only to the initial JSON modes; they cannot rank the new binary and external modes. QPC improved the external timer's resolution, but timestamp overhead and uncontrolled operating-system activity remain in the observations. No tail bound or process-wide memory improvement is claimed.

Security claims are similarly bounded. Each representation restores its host's original proof or signed object before verification. This preserves the checked relation for supported inputs, while leaving the host's trust assumptions intact. The work adds no confidentiality, private set intersection, global fork prevention, durable execution or new signature security. Parsing tests and independent replay strengthen implementation evidence but do not substitute for an adversarial security proof.

\section{Conclusion}
The initial bitmap result survived a stronger binary byte baseline but supported a smaller local-time benefit. An external path-compacted implementation did not reproduce joint size/time dominance, and exact structural accounting explained when compaction metadata outweighed omitted node bytes. These findings support evaluating proof transport against native binary formats and preserving negative comparisons alongside favorable ones. They establish a bounded empirical result across two hosts, with reproducible artifacts and no universal format or deployment-speed claim.

'''
s=re.sub(r'\\section\{Discussion and limitations\}.*?(?=\\section\*\{Data, code and drafting status\})',lambda _:newsection+discussion,s,flags=re.S)
s=s.replace('The local archive contains the frozen plan and sources, configurations, synthetic workloads, test-only keys, frames, checkpoints, raw logs, evaluations, replay diagnostics, figures and manuscript sources.', 'The local archives contain the original study, both screening registrations, the retained invalid timing run and clock diagnostics, pinned upstream source, configurations, synthetic workloads, test-only keys, frames, checkpoints, raw logs, evaluations, independent replay, figures and manuscript sources.')
(M/'main.tex').write_text(s,encoding='utf-8')
for host in ('reference','external'):
    shutil.copyfile(ROOT/'analysis'/(host+'_sizes.tex'),M/'tables'/('round3_'+host+'_sizes.tex'))
shutil.copyfile(ROOT/'analysis/baseline_sensitivity.pdf',M/'figures/baseline_sensitivity.pdf')
bib=(ROOT/'manuscript_before/references.bib').read_text()+r'''

@misc{celestiaPinned,
  author = {{Celestia SMT contributors}},
  title = {{smt}: Sparse Merkle Tree Implementation},
  howpublished = {Go source code, fixed revision},
  url = {https://github.com/celestiaorg/smt/tree/dba215ccb88452c31d823bf156d8f35406c1dc04},
  note = {Revision dba215ccb88452c31d823bf156d8f35406c1dc04. Retrieved and archived 23 October 2026; upstream tree, proof, compaction and verification code inspected and executed}
}
@misc{ipsilonAnalysis,
  author = {De la cruz, Hugo and {Ipsilon Team}},
  title = {Code Merkleization Practical Implementation and Analysis},
  howpublished = {Author technical report},
  url = {https://notes.ethereum.org/@ipsilon/code-merkleization-implementation-analysis},
  note = {Full report inspected 23 October 2026. Publication date not independently established; reported mainnet results were not reproduced here}
}
@misc{microsoftQpc,
  author = {{Microsoft}},
  title = {Acquiring High-Resolution Time Stamps},
  howpublished = {Windows developer documentation},
  url = {https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps},
  note = {Accessed 23 October 2026}
}
'''
(M/'references.bib').write_text(bib,encoding='utf-8')
(ROOT/'manuscript_revision.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='before/main.tex',tofile='revised/main.tex')),encoding='utf-8')
print('Revised existing manuscript and generated evidence-linked additions.')
