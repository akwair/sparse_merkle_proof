# Round 7 application and repetition report

Application inputs are YCSB-inspired synthetic reads from an authenticated immutable snapshot, with uniform or exact finite-Zipf selection. They are not a production trace or an exact YCSB implementation. No network service was measured.

本实验为单种子（seed=3407），存在随机噪声风险。Five fresh processes per workload were run in one shared-host session; no independent-workload or day-to-day inference is made.

All ten processes completed: 362,880 timing rows over 557.7 seconds. Both corpora and observation orders matched across their five processes. Independent audits reconstructed and verified every stored frame.

| Block | Application hotness | Application service effective /256 | Application codec effective /256 | Frozen locality | Frozen lifecycle |
|---:|---|---:|---:|---|---|
| 1 | False | 0 | 0 | True | True |
| 2 | False | 0 | 0 | True | True |
| 3 | False | 0 | 0 | True | True |
| 4 | False | 0 | 0 | True | True |
| 5 | False | 0 | 0 | True | True |

Absolute cell-mode median spread exceeded 1.20 in 192/576 application summaries and 413/576 frozen summaries. These are descriptive flags, not statistical tests or exclusion rules.

Agreement with the previously observed Linux/Gold conclusions in all five new processes: {"locality": true, "lifecycle": true, "all_alternative_classifications": true}. A false entry denotes mixed or changed findings and is not described as stable.

A service-path pass and codec-only pass have different denominators. Proof generation is measured in the application arm and can dilute adapter overhead; it does not change the original codec-only verdict. No workload distribution, mode or threshold was selected using confirmation outcomes.

Transfer boundaries in REPETITIONS.json assume serial local processing plus response transmission with common overhead. They are not measured link rates or RPC throughput. A finite range spans the five process estimates; changed boundary classes are retained explicitly.

## Application classifications across processes

| Cell | Mode | Service passes /5 | Codec passes /5 |
|---|---|---:|---:|
| n16384_q128_v1000_member_uniform | compact | 0 | 0 |
| n16384_q128_v1000_member_uniform | dictionary | 0 | 0 |
| n16384_q128_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q128_v1000_member_uniform | zlib-compact | 0 | 0 |
| n16384_q128_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q128_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q128_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q128_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q128_v1000_member_zipf | compact | 0 | 0 |
| n16384_q128_v1000_member_zipf | dictionary | 0 | 0 |
| n16384_q128_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q128_v1000_member_zipf | zlib-compact | 0 | 0 |
| n16384_q128_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q128_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q128_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q128_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n16384_q128_v32_member_uniform | compact | 0 | 0 |
| n16384_q128_v32_member_uniform | dictionary | 0 | 0 |
| n16384_q128_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q128_v32_member_uniform | zlib-compact | 0 | 0 |
| n16384_q128_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q128_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q128_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q128_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q128_v32_member_zipf | compact | 0 | 0 |
| n16384_q128_v32_member_zipf | dictionary | 0 | 0 |
| n16384_q128_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q128_v32_member_zipf | zlib-compact | 0 | 0 |
| n16384_q128_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q128_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q128_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q128_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n16384_q1_v1000_member_uniform | compact | 0 | 0 |
| n16384_q1_v1000_member_uniform | dictionary | 0 | 0 |
| n16384_q1_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q1_v1000_member_uniform | zlib-compact | 0 | 0 |
| n16384_q1_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q1_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q1_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q1_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q1_v1000_member_zipf | compact | 0 | 0 |
| n16384_q1_v1000_member_zipf | dictionary | 0 | 0 |
| n16384_q1_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q1_v1000_member_zipf | zlib-compact | 0 | 0 |
| n16384_q1_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q1_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q1_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q1_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n16384_q1_v32_member_uniform | compact | 0 | 0 |
| n16384_q1_v32_member_uniform | dictionary | 0 | 0 |
| n16384_q1_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q1_v32_member_uniform | zlib-compact | 0 | 0 |
| n16384_q1_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q1_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q1_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q1_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q1_v32_member_zipf | compact | 0 | 0 |
| n16384_q1_v32_member_zipf | dictionary | 0 | 0 |
| n16384_q1_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q1_v32_member_zipf | zlib-compact | 0 | 0 |
| n16384_q1_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q1_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q1_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q1_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n16384_q32_v1000_member_uniform | compact | 0 | 0 |
| n16384_q32_v1000_member_uniform | dictionary | 0 | 0 |
| n16384_q32_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q32_v1000_member_uniform | zlib-compact | 0 | 0 |
| n16384_q32_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q32_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q32_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q32_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q32_v1000_member_zipf | compact | 0 | 0 |
| n16384_q32_v1000_member_zipf | dictionary | 0 | 0 |
| n16384_q32_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q32_v1000_member_zipf | zlib-compact | 0 | 0 |
| n16384_q32_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q32_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q32_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q32_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n16384_q32_v32_member_uniform | compact | 0 | 0 |
| n16384_q32_v32_member_uniform | dictionary | 0 | 0 |
| n16384_q32_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q32_v32_member_uniform | zlib-compact | 0 | 0 |
| n16384_q32_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q32_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q32_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q32_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q32_v32_member_zipf | compact | 0 | 0 |
| n16384_q32_v32_member_zipf | dictionary | 0 | 0 |
| n16384_q32_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q32_v32_member_zipf | zlib-compact | 0 | 0 |
| n16384_q32_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q32_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q32_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q32_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n16384_q8_v1000_member_uniform | compact | 0 | 0 |
| n16384_q8_v1000_member_uniform | dictionary | 0 | 0 |
| n16384_q8_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q8_v1000_member_uniform | zlib-compact | 0 | 0 |
| n16384_q8_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q8_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q8_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q8_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q8_v1000_member_zipf | compact | 0 | 0 |
| n16384_q8_v1000_member_zipf | dictionary | 0 | 0 |
| n16384_q8_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q8_v1000_member_zipf | zlib-compact | 0 | 0 |
| n16384_q8_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q8_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q8_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q8_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n16384_q8_v32_member_uniform | compact | 0 | 0 |
| n16384_q8_v32_member_uniform | dictionary | 0 | 0 |
| n16384_q8_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n16384_q8_v32_member_uniform | zlib-compact | 0 | 0 |
| n16384_q8_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n16384_q8_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n16384_q8_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n16384_q8_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n16384_q8_v32_member_zipf | compact | 0 | 0 |
| n16384_q8_v32_member_zipf | dictionary | 0 | 0 |
| n16384_q8_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n16384_q8_v32_member_zipf | zlib-compact | 0 | 0 |
| n16384_q8_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n16384_q8_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n16384_q8_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n16384_q8_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q128_v1000_member_uniform | compact | 0 | 0 |
| n4096_q128_v1000_member_uniform | dictionary | 0 | 0 |
| n4096_q128_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q128_v1000_member_uniform | zlib-compact | 0 | 0 |
| n4096_q128_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q128_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q128_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q128_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q128_v1000_member_zipf | compact | 0 | 0 |
| n4096_q128_v1000_member_zipf | dictionary | 0 | 0 |
| n4096_q128_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q128_v1000_member_zipf | zlib-compact | 0 | 0 |
| n4096_q128_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q128_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q128_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q128_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q128_v32_member_uniform | compact | 0 | 0 |
| n4096_q128_v32_member_uniform | dictionary | 0 | 0 |
| n4096_q128_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q128_v32_member_uniform | zlib-compact | 0 | 0 |
| n4096_q128_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q128_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q128_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q128_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q128_v32_member_zipf | compact | 0 | 0 |
| n4096_q128_v32_member_zipf | dictionary | 0 | 0 |
| n4096_q128_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q128_v32_member_zipf | zlib-compact | 0 | 0 |
| n4096_q128_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q128_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q128_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q128_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q1_v1000_member_uniform | compact | 0 | 0 |
| n4096_q1_v1000_member_uniform | dictionary | 0 | 0 |
| n4096_q1_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q1_v1000_member_uniform | zlib-compact | 0 | 0 |
| n4096_q1_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q1_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q1_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q1_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q1_v1000_member_zipf | compact | 0 | 0 |
| n4096_q1_v1000_member_zipf | dictionary | 0 | 0 |
| n4096_q1_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q1_v1000_member_zipf | zlib-compact | 0 | 0 |
| n4096_q1_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q1_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q1_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q1_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q1_v32_member_uniform | compact | 0 | 0 |
| n4096_q1_v32_member_uniform | dictionary | 0 | 0 |
| n4096_q1_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q1_v32_member_uniform | zlib-compact | 0 | 0 |
| n4096_q1_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q1_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q1_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q1_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q1_v32_member_zipf | compact | 0 | 0 |
| n4096_q1_v32_member_zipf | dictionary | 0 | 0 |
| n4096_q1_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q1_v32_member_zipf | zlib-compact | 0 | 0 |
| n4096_q1_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q1_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q1_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q1_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q32_v1000_member_uniform | compact | 0 | 0 |
| n4096_q32_v1000_member_uniform | dictionary | 0 | 0 |
| n4096_q32_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q32_v1000_member_uniform | zlib-compact | 0 | 0 |
| n4096_q32_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q32_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q32_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q32_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q32_v1000_member_zipf | compact | 0 | 0 |
| n4096_q32_v1000_member_zipf | dictionary | 0 | 0 |
| n4096_q32_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q32_v1000_member_zipf | zlib-compact | 0 | 0 |
| n4096_q32_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q32_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q32_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q32_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q32_v32_member_uniform | compact | 0 | 0 |
| n4096_q32_v32_member_uniform | dictionary | 0 | 0 |
| n4096_q32_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q32_v32_member_uniform | zlib-compact | 0 | 0 |
| n4096_q32_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q32_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q32_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q32_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q32_v32_member_zipf | compact | 0 | 0 |
| n4096_q32_v32_member_zipf | dictionary | 0 | 0 |
| n4096_q32_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q32_v32_member_zipf | zlib-compact | 0 | 0 |
| n4096_q32_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q32_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q32_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q32_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q8_v1000_member_uniform | compact | 0 | 0 |
| n4096_q8_v1000_member_uniform | dictionary | 0 | 0 |
| n4096_q8_v1000_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q8_v1000_member_uniform | zlib-compact | 0 | 0 |
| n4096_q8_v1000_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q8_v1000_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q8_v1000_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q8_v1000_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q8_v1000_member_zipf | compact | 0 | 0 |
| n4096_q8_v1000_member_zipf | dictionary | 0 | 0 |
| n4096_q8_v1000_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q8_v1000_member_zipf | zlib-compact | 0 | 0 |
| n4096_q8_v1000_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q8_v1000_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q8_v1000_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q8_v1000_member_zipf | reset-zlib-dictionary | 0 | 0 |
| n4096_q8_v32_member_uniform | compact | 0 | 0 |
| n4096_q8_v32_member_uniform | dictionary | 0 | 0 |
| n4096_q8_v32_member_uniform | zlib-ordinary | 0 | 0 |
| n4096_q8_v32_member_uniform | zlib-compact | 0 | 0 |
| n4096_q8_v32_member_uniform | zlib-dictionary | 0 | 0 |
| n4096_q8_v32_member_uniform | reset-zlib-ordinary | 0 | 0 |
| n4096_q8_v32_member_uniform | reset-zlib-compact | 0 | 0 |
| n4096_q8_v32_member_uniform | reset-zlib-dictionary | 0 | 0 |
| n4096_q8_v32_member_zipf | compact | 0 | 0 |
| n4096_q8_v32_member_zipf | dictionary | 0 | 0 |
| n4096_q8_v32_member_zipf | zlib-ordinary | 0 | 0 |
| n4096_q8_v32_member_zipf | zlib-compact | 0 | 0 |
| n4096_q8_v32_member_zipf | zlib-dictionary | 0 | 0 |
| n4096_q8_v32_member_zipf | reset-zlib-ordinary | 0 | 0 |
| n4096_q8_v32_member_zipf | reset-zlib-compact | 0 | 0 |
| n4096_q8_v32_member_zipf | reset-zlib-dictionary | 0 | 0 |

## Application: every process-level cell summary

| Domain/cell | Mode | Paired total ratio range | Absolute median us range | Max/min |
|---|---|---:|---:|---:|
| confirm/n16384_q128_v1000_member_uniform | ordinary | 1.000000–1.000000 | 1499.460–1596.566 | 1.0648 |
| confirm/n16384_q128_v1000_member_uniform | compact | 1.101589–1.121113 | 1640.674–1787.828 | 1.0897 |
| confirm/n16384_q128_v1000_member_uniform | dictionary | 1.111331–1.132143 | 1658.460–1812.834 | 1.0931 |
| confirm/n16384_q128_v1000_member_uniform | zlib-ordinary | 2.888293–3.039953 | 4486.214–4695.674 | 1.0467 |
| confirm/n16384_q128_v1000_member_uniform | zlib-compact | 2.803574–2.915552 | 4275.535–4504.399 | 1.0535 |
| confirm/n16384_q128_v1000_member_uniform | zlib-dictionary | 1.813153–1.858794 | 2772.420–2950.446 | 1.0642 |
| confirm/n16384_q128_v1000_member_uniform | reset-zlib-ordinary | 2.898847–3.032926 | 4445.611–4710.133 | 1.0595 |
| confirm/n16384_q128_v1000_member_uniform | reset-zlib-compact | 2.790491–2.922892 | 4320.994–4586.046 | 1.0613 |
| confirm/n16384_q128_v1000_member_uniform | reset-zlib-dictionary | 1.784563–1.886343 | 2713.477–2993.459 | 1.1032 |
| confirm/n16384_q128_v1000_member_zipf | ordinary | 1.000000–1.000000 | 1361.220–1519.172 | 1.1160 |
| confirm/n16384_q128_v1000_member_zipf | compact | 1.096428–1.123631 | 1521.871–1697.911 | 1.1157 |
| confirm/n16384_q128_v1000_member_zipf | dictionary | 1.082376–1.117701 | 1539.838–1638.556 | 1.0641 |
| confirm/n16384_q128_v1000_member_zipf | zlib-ordinary | 2.665736–2.912670 | 3868.119–4447.180 | 1.1497 |
| confirm/n16384_q128_v1000_member_zipf | zlib-compact | 2.687020–2.843145 | 3934.470–4371.582 | 1.1111 |
| confirm/n16384_q128_v1000_member_zipf | zlib-dictionary | 2.083990–2.205526 | 3013.448–3145.020 | 1.0437 |
| confirm/n16384_q128_v1000_member_zipf | reset-zlib-ordinary | 2.704934–2.920873 | 3886.765–4255.172 | 1.0948 |
| confirm/n16384_q128_v1000_member_zipf | reset-zlib-compact | 2.685983–2.852556 | 3947.097–4218.191 | 1.0687 |
| confirm/n16384_q128_v1000_member_zipf | reset-zlib-dictionary | 2.103232–2.188747 | 2998.669–3303.568 | 1.1017 |
| confirm/n16384_q128_v32_member_uniform | ordinary | 1.000000–1.000000 | 1263.658–1381.650 | 1.0934 |
| confirm/n16384_q128_v32_member_uniform | compact | 1.096660–1.127979 | 1430.873–1586.917 | 1.1091 |
| confirm/n16384_q128_v32_member_uniform | dictionary | 1.120193–1.182958 | 1445.550–1586.735 | 1.0977 |
| confirm/n16384_q128_v32_member_uniform | zlib-ordinary | 1.923326–2.053857 | 2556.168–2746.345 | 1.0744 |
| confirm/n16384_q128_v32_member_uniform | zlib-compact | 2.062137–2.182513 | 2668.047–2901.462 | 1.0875 |
| confirm/n16384_q128_v32_member_uniform | zlib-dictionary | 1.626199–1.743590 | 2169.742–2404.909 | 1.1084 |
| confirm/n16384_q128_v32_member_uniform | reset-zlib-ordinary | 1.955192–2.017638 | 2423.854–2791.253 | 1.1516 |
| confirm/n16384_q128_v32_member_uniform | reset-zlib-compact | 2.053199–2.160580 | 2765.801–2916.566 | 1.0545 |
| confirm/n16384_q128_v32_member_uniform | reset-zlib-dictionary | 1.633495–1.711927 | 2066.577–2372.807 | 1.1482 |
| confirm/n16384_q128_v32_member_zipf | ordinary | 1.000000–1.000000 | 1184.578–1509.453 | 1.2743 |
| confirm/n16384_q128_v32_member_zipf | compact | 1.111283–1.155150 | 1306.468–1685.076 | 1.2898 |
| confirm/n16384_q128_v32_member_zipf | dictionary | 1.108404–1.132672 | 1330.654–1557.614 | 1.1706 |
| confirm/n16384_q128_v32_member_zipf | zlib-ordinary | 1.815079–1.921134 | 2226.528–2642.403 | 1.1868 |
| confirm/n16384_q128_v32_member_zipf | zlib-compact | 1.944990–2.018178 | 2373.338–2827.517 | 1.1914 |
| confirm/n16384_q128_v32_member_zipf | zlib-dictionary | 1.600337–1.681601 | 1947.029–2339.339 | 1.2015 |
| confirm/n16384_q128_v32_member_zipf | reset-zlib-ordinary | 1.803785–1.875387 | 2205.714–2769.300 | 1.2555 |
| confirm/n16384_q128_v32_member_zipf | reset-zlib-compact | 1.959394–2.038451 | 2312.836–3152.979 | 1.3633 |
| confirm/n16384_q128_v32_member_zipf | reset-zlib-dictionary | 1.566150–1.616941 | 1867.205–2334.628 | 1.2503 |
| confirm/n16384_q1_v1000_member_uniform | ordinary | 1.000000–1.000000 | 13.181–15.240 | 1.1562 |
| confirm/n16384_q1_v1000_member_uniform | compact | 1.065518–1.154749 | 14.554–18.219 | 1.2518 |
| confirm/n16384_q1_v1000_member_uniform | dictionary | 1.180217–1.256777 | 16.115–18.236 | 1.1316 |
| confirm/n16384_q1_v1000_member_uniform | zlib-ordinary | 11.908510–14.663481 | 160.393–233.833 | 1.4579 |
| confirm/n16384_q1_v1000_member_uniform | zlib-compact | 9.925378–14.767100 | 155.603–270.857 | 1.7407 |
| confirm/n16384_q1_v1000_member_uniform | zlib-dictionary | 13.358989–16.646081 | 195.080–271.509 | 1.3918 |
| confirm/n16384_q1_v1000_member_uniform | reset-zlib-ordinary | 2.785873–3.403109 | 41.853–47.664 | 1.1388 |
| confirm/n16384_q1_v1000_member_uniform | reset-zlib-compact | 2.301358–2.470875 | 30.587–38.164 | 1.2477 |
| confirm/n16384_q1_v1000_member_uniform | reset-zlib-dictionary | 3.930618–4.565802 | 61.717–79.319 | 1.2852 |
| confirm/n16384_q1_v1000_member_zipf | ordinary | 1.000000–1.000000 | 12.856–17.713 | 1.3778 |
| confirm/n16384_q1_v1000_member_zipf | compact | 1.128218–1.183693 | 14.640–20.990 | 1.4337 |
| confirm/n16384_q1_v1000_member_zipf | dictionary | 1.211121–1.278124 | 15.862–19.977 | 1.2594 |
| confirm/n16384_q1_v1000_member_zipf | zlib-ordinary | 10.946600–19.484339 | 132.351–258.146 | 1.9505 |
| confirm/n16384_q1_v1000_member_zipf | zlib-compact | 10.464863–18.715963 | 132.685–242.828 | 1.8301 |
| confirm/n16384_q1_v1000_member_zipf | zlib-dictionary | 14.045220–19.487124 | 213.009–286.633 | 1.3456 |
| confirm/n16384_q1_v1000_member_zipf | reset-zlib-ordinary | 2.415306–2.720927 | 32.354–40.032 | 1.2373 |
| confirm/n16384_q1_v1000_member_zipf | reset-zlib-compact | 2.388946–2.614367 | 31.991–38.182 | 1.1935 |
| confirm/n16384_q1_v1000_member_zipf | reset-zlib-dictionary | 2.731619–3.035582 | 37.051–47.870 | 1.2920 |
| confirm/n16384_q1_v32_member_uniform | ordinary | 1.000000–1.000000 | 11.444–14.009 | 1.2241 |
| confirm/n16384_q1_v32_member_uniform | compact | 1.130625–1.197755 | 13.190–16.642 | 1.2617 |
| confirm/n16384_q1_v32_member_uniform | dictionary | 1.266969–1.300374 | 14.531–18.014 | 1.2397 |
| confirm/n16384_q1_v32_member_uniform | zlib-ordinary | 13.094351–14.835135 | 165.947–213.006 | 1.2836 |
| confirm/n16384_q1_v32_member_uniform | zlib-compact | 11.546842–13.634665 | 130.605–185.778 | 1.4224 |
| confirm/n16384_q1_v32_member_uniform | zlib-dictionary | 13.107562–14.276843 | 148.698–208.241 | 1.4004 |
| confirm/n16384_q1_v32_member_uniform | reset-zlib-ordinary | 4.239469–4.647250 | 52.305–63.758 | 1.2190 |
| confirm/n16384_q1_v32_member_uniform | reset-zlib-compact | 2.186289–2.449933 | 25.634–34.081 | 1.3295 |
| confirm/n16384_q1_v32_member_uniform | reset-zlib-dictionary | 3.994243–4.415582 | 52.185–62.302 | 1.1939 |
| confirm/n16384_q1_v32_member_zipf | ordinary | 1.000000–1.000000 | 10.410–13.094 | 1.2578 |
| confirm/n16384_q1_v32_member_zipf | compact | 1.163419–1.209744 | 12.393–15.750 | 1.2709 |
| confirm/n16384_q1_v32_member_zipf | dictionary | 1.205208–1.281691 | 13.848–15.956 | 1.1522 |
| confirm/n16384_q1_v32_member_zipf | zlib-ordinary | 11.612992–17.983777 | 127.717–258.182 | 2.0215 |
| confirm/n16384_q1_v32_member_zipf | zlib-compact | 11.355985–20.560603 | 115.889–235.487 | 2.0320 |
| confirm/n16384_q1_v32_member_zipf | zlib-dictionary | 12.466466–15.693244 | 133.000–224.152 | 1.6854 |
| confirm/n16384_q1_v32_member_zipf | reset-zlib-ordinary | 2.429639–2.789835 | 24.557–34.953 | 1.4233 |
| confirm/n16384_q1_v32_member_zipf | reset-zlib-compact | 2.365329–2.698379 | 25.839–33.935 | 1.3133 |
| confirm/n16384_q1_v32_member_zipf | reset-zlib-dictionary | 2.593173–3.097743 | 28.784–39.249 | 1.3636 |
| confirm/n16384_q32_v1000_member_uniform | ordinary | 1.000000–1.000000 | 356.026–412.648 | 1.1590 |
| confirm/n16384_q32_v1000_member_uniform | compact | 1.120892–1.142612 | 397.430–464.709 | 1.1693 |
| confirm/n16384_q32_v1000_member_uniform | dictionary | 1.118180–1.155979 | 405.421–476.637 | 1.1757 |
| confirm/n16384_q32_v1000_member_uniform | zlib-ordinary | 3.197757–3.292856 | 1182.649–1322.610 | 1.1183 |
| confirm/n16384_q32_v1000_member_uniform | zlib-compact | 2.324080–2.456902 | 828.532–1109.168 | 1.3387 |
| confirm/n16384_q32_v1000_member_uniform | zlib-dictionary | 2.012468–2.078981 | 736.312–824.652 | 1.1200 |
| confirm/n16384_q32_v1000_member_uniform | reset-zlib-ordinary | 3.043494–3.243807 | 1091.355–1300.405 | 1.1916 |
| confirm/n16384_q32_v1000_member_uniform | reset-zlib-compact | 2.135799–2.459783 | 757.223–1070.791 | 1.4141 |
| confirm/n16384_q32_v1000_member_uniform | reset-zlib-dictionary | 1.839584–1.888049 | 658.369–775.756 | 1.1783 |
| confirm/n16384_q32_v1000_member_zipf | ordinary | 1.000000–1.000000 | 346.819–391.816 | 1.1297 |
| confirm/n16384_q32_v1000_member_zipf | compact | 1.090224–1.160826 | 377.589–434.674 | 1.1512 |
| confirm/n16384_q32_v1000_member_zipf | dictionary | 1.105430–1.177330 | 399.020–447.039 | 1.1203 |
| confirm/n16384_q32_v1000_member_zipf | zlib-ordinary | 2.946904–3.242815 | 1090.080–1226.074 | 1.1248 |
| confirm/n16384_q32_v1000_member_zipf | zlib-compact | 2.950764–3.268523 | 1083.118–1218.972 | 1.1254 |
| confirm/n16384_q32_v1000_member_zipf | zlib-dictionary | 2.773399–2.905962 | 977.334–1109.498 | 1.1352 |
| confirm/n16384_q32_v1000_member_zipf | reset-zlib-ordinary | 2.810395–3.104271 | 1053.163–1179.804 | 1.1202 |
| confirm/n16384_q32_v1000_member_zipf | reset-zlib-compact | 2.796597–3.164199 | 1036.790–1187.528 | 1.1454 |
| confirm/n16384_q32_v1000_member_zipf | reset-zlib-dictionary | 2.582608–2.875271 | 949.412–1049.141 | 1.1050 |
| confirm/n16384_q32_v32_member_uniform | ordinary | 1.000000–1.000000 | 318.634–346.401 | 1.0871 |
| confirm/n16384_q32_v32_member_uniform | compact | 1.125066–1.172442 | 360.098–392.927 | 1.0912 |
| confirm/n16384_q32_v32_member_uniform | dictionary | 1.146385–1.191667 | 361.618–414.505 | 1.1463 |
| confirm/n16384_q32_v32_member_uniform | zlib-ordinary | 2.218262–2.357318 | 730.936–815.445 | 1.1156 |
| confirm/n16384_q32_v32_member_uniform | zlib-compact | 2.384299–2.440818 | 784.824–832.492 | 1.0607 |
| confirm/n16384_q32_v32_member_uniform | zlib-dictionary | 2.156845–2.256653 | 705.542–781.676 | 1.1079 |
| confirm/n16384_q32_v32_member_uniform | reset-zlib-ordinary | 2.063785–2.241288 | 685.711–774.188 | 1.1290 |
| confirm/n16384_q32_v32_member_uniform | reset-zlib-compact | 2.199452–2.386993 | 720.437–807.581 | 1.1210 |
| confirm/n16384_q32_v32_member_uniform | reset-zlib-dictionary | 1.894133–2.020498 | 608.593–695.352 | 1.1426 |
| confirm/n16384_q32_v32_member_zipf | ordinary | 1.000000–1.000000 | 292.850–324.007 | 1.1064 |
| confirm/n16384_q32_v32_member_zipf | compact | 1.121071–1.196225 | 330.139–386.059 | 1.1694 |
| confirm/n16384_q32_v32_member_zipf | dictionary | 1.141466–1.171318 | 342.501–374.496 | 1.0934 |
| confirm/n16384_q32_v32_member_zipf | zlib-ordinary | 2.278060–2.351949 | 680.027–798.206 | 1.1738 |
| confirm/n16384_q32_v32_member_zipf | zlib-compact | 2.370439–2.472540 | 711.732–822.949 | 1.1563 |
| confirm/n16384_q32_v32_member_zipf | zlib-dictionary | 2.232996–2.306338 | 668.966–787.599 | 1.1773 |
| confirm/n16384_q32_v32_member_zipf | reset-zlib-ordinary | 2.032220–2.185934 | 596.400–711.885 | 1.1936 |
| confirm/n16384_q32_v32_member_zipf | reset-zlib-compact | 2.133831–2.299555 | 634.030–739.756 | 1.1668 |
| confirm/n16384_q32_v32_member_zipf | reset-zlib-dictionary | 1.996639–2.096078 | 599.535–670.819 | 1.1189 |
| confirm/n16384_q8_v1000_member_uniform | ordinary | 1.000000–1.000000 | 92.155–97.519 | 1.0582 |
| confirm/n16384_q8_v1000_member_uniform | compact | 1.101493–1.147642 | 103.294–110.600 | 1.0707 |
| confirm/n16384_q8_v1000_member_uniform | dictionary | 1.175318–1.227461 | 110.520–114.250 | 1.0337 |
| confirm/n16384_q8_v1000_member_uniform | zlib-ordinary | 3.257987–3.605803 | 314.085–367.157 | 1.1690 |
| confirm/n16384_q8_v1000_member_uniform | zlib-compact | 2.863256–3.217789 | 276.493–310.405 | 1.1227 |
| confirm/n16384_q8_v1000_member_uniform | zlib-dictionary | 3.202461–3.465214 | 308.634–348.448 | 1.1290 |
| confirm/n16384_q8_v1000_member_uniform | reset-zlib-ordinary | 2.369631–2.580177 | 235.089–258.546 | 1.0998 |
| confirm/n16384_q8_v1000_member_uniform | reset-zlib-compact | 1.797473–1.973897 | 185.070–206.635 | 1.1165 |
| confirm/n16384_q8_v1000_member_uniform | reset-zlib-dictionary | 2.113501–2.241797 | 206.653–221.074 | 1.0698 |
| confirm/n16384_q8_v1000_member_zipf | ordinary | 1.000000–1.000000 | 83.584–93.314 | 1.1164 |
| confirm/n16384_q8_v1000_member_zipf | compact | 1.081717–1.134008 | 93.405–102.731 | 1.0998 |
| confirm/n16384_q8_v1000_member_zipf | dictionary | 1.178582–1.204071 | 100.422–113.445 | 1.1297 |
| confirm/n16384_q8_v1000_member_zipf | zlib-ordinary | 4.716345–4.779522 | 404.733–454.001 | 1.1217 |
| confirm/n16384_q8_v1000_member_zipf | zlib-compact | 4.405712–4.715046 | 373.407–429.700 | 1.1508 |
| confirm/n16384_q8_v1000_member_zipf | zlib-dictionary | 4.259121–4.540125 | 373.177–410.084 | 1.0989 |
| confirm/n16384_q8_v1000_member_zipf | reset-zlib-ordinary | 3.200570–3.920194 | 279.657–363.836 | 1.3010 |
| confirm/n16384_q8_v1000_member_zipf | reset-zlib-compact | 3.102359–3.430535 | 269.965–316.139 | 1.1710 |
| confirm/n16384_q8_v1000_member_zipf | reset-zlib-dictionary | 2.619549–2.682168 | 224.562–266.763 | 1.1879 |
| confirm/n16384_q8_v32_member_uniform | ordinary | 1.000000–1.000000 | 76.291–86.144 | 1.1292 |
| confirm/n16384_q8_v32_member_uniform | compact | 1.098525–1.148382 | 85.635–96.788 | 1.1302 |
| confirm/n16384_q8_v32_member_uniform | dictionary | 1.184821–1.224334 | 92.031–99.754 | 1.0839 |
| confirm/n16384_q8_v32_member_uniform | zlib-ordinary | 3.850016–4.113141 | 290.927–368.743 | 1.2675 |
| confirm/n16384_q8_v32_member_uniform | zlib-compact | 3.878115–4.125761 | 304.443–372.775 | 1.2244 |
| confirm/n16384_q8_v32_member_uniform | zlib-dictionary | 3.160946–3.370193 | 248.111–310.941 | 1.2532 |
| confirm/n16384_q8_v32_member_uniform | reset-zlib-ordinary | 2.664896–3.041493 | 217.526–252.191 | 1.1594 |
| confirm/n16384_q8_v32_member_uniform | reset-zlib-compact | 2.804353–3.054726 | 227.841–249.403 | 1.0946 |
| confirm/n16384_q8_v32_member_uniform | reset-zlib-dictionary | 1.887589–2.155157 | 164.744–186.872 | 1.1343 |
| confirm/n16384_q8_v32_member_zipf | ordinary | 1.000000–1.000000 | 76.373–85.758 | 1.1229 |
| confirm/n16384_q8_v32_member_zipf | compact | 1.113021–1.178756 | 90.180–97.637 | 1.0827 |
| confirm/n16384_q8_v32_member_zipf | dictionary | 1.216479–1.255279 | 93.535–106.852 | 1.1424 |
| confirm/n16384_q8_v32_member_zipf | zlib-ordinary | 4.098544–4.266396 | 322.803–435.241 | 1.3483 |
| confirm/n16384_q8_v32_member_zipf | zlib-compact | 4.128586–4.314475 | 335.076–435.720 | 1.3004 |
| confirm/n16384_q8_v32_member_zipf | zlib-dictionary | 3.560700–3.773575 | 307.345–371.453 | 1.2086 |
| confirm/n16384_q8_v32_member_zipf | reset-zlib-ordinary | 2.768837–3.051578 | 229.920–253.398 | 1.1021 |
| confirm/n16384_q8_v32_member_zipf | reset-zlib-compact | 2.793000–3.039781 | 228.910–246.007 | 1.0747 |
| confirm/n16384_q8_v32_member_zipf | reset-zlib-dictionary | 2.259397–2.360316 | 180.899–201.369 | 1.1132 |
| confirm/n4096_q128_v1000_member_uniform | ordinary | 1.000000–1.000000 | 1351.834–1432.582 | 1.0597 |
| confirm/n4096_q128_v1000_member_uniform | compact | 1.100608–1.120311 | 1509.218–1612.785 | 1.0686 |
| confirm/n4096_q128_v1000_member_uniform | dictionary | 1.099897–1.111960 | 1503.354–1609.240 | 1.0704 |
| confirm/n4096_q128_v1000_member_uniform | zlib-ordinary | 3.084281–3.195930 | 4389.335–4569.929 | 1.0411 |
| confirm/n4096_q128_v1000_member_uniform | zlib-compact | 2.881089–2.989719 | 3834.622–4308.005 | 1.1234 |
| confirm/n4096_q128_v1000_member_uniform | zlib-dictionary | 1.679358–1.775353 | 2309.846–2476.288 | 1.0721 |
| confirm/n4096_q128_v1000_member_uniform | reset-zlib-ordinary | 3.050584–3.167833 | 4323.645–4640.365 | 1.0733 |
| confirm/n4096_q128_v1000_member_uniform | reset-zlib-compact | 2.813136–2.983873 | 3899.244–4233.494 | 1.0857 |
| confirm/n4096_q128_v1000_member_uniform | reset-zlib-dictionary | 1.678119–1.785734 | 2307.780–2540.071 | 1.1007 |
| confirm/n4096_q128_v1000_member_zipf | ordinary | 1.000000–1.000000 | 1291.185–1430.482 | 1.1079 |
| confirm/n4096_q128_v1000_member_zipf | compact | 1.097539–1.133492 | 1459.946–1536.432 | 1.0524 |
| confirm/n4096_q128_v1000_member_zipf | dictionary | 1.080763–1.110418 | 1388.561–1521.818 | 1.0960 |
| confirm/n4096_q128_v1000_member_zipf | zlib-ordinary | 2.766814–3.020367 | 3829.704–4095.541 | 1.0694 |
| confirm/n4096_q128_v1000_member_zipf | zlib-compact | 2.763122–3.033811 | 3793.409–4015.207 | 1.0585 |
| confirm/n4096_q128_v1000_member_zipf | zlib-dictionary | 2.273093–2.397162 | 2982.763–3280.791 | 1.0999 |
| confirm/n4096_q128_v1000_member_zipf | reset-zlib-ordinary | 2.837670–3.016674 | 3722.750–4082.432 | 1.0966 |
| confirm/n4096_q128_v1000_member_zipf | reset-zlib-compact | 2.820890–2.998218 | 3717.431–4074.727 | 1.0961 |
| confirm/n4096_q128_v1000_member_zipf | reset-zlib-dictionary | 2.257788–2.443124 | 2938.784–3283.848 | 1.1174 |
| confirm/n4096_q128_v32_member_uniform | ordinary | 1.000000–1.000000 | 1124.315–1198.459 | 1.0659 |
| confirm/n4096_q128_v32_member_uniform | compact | 1.116475–1.147799 | 1255.551–1335.859 | 1.0640 |
| confirm/n4096_q128_v32_member_uniform | dictionary | 1.117999–1.161873 | 1263.003–1367.526 | 1.0828 |
| confirm/n4096_q128_v32_member_uniform | zlib-ordinary | 1.920412–1.978702 | 2220.456–2357.127 | 1.0616 |
| confirm/n4096_q128_v32_member_uniform | zlib-compact | 2.007718–2.094830 | 2323.650–2519.405 | 1.0842 |
| confirm/n4096_q128_v32_member_uniform | zlib-dictionary | 1.688376–1.720821 | 1931.636–2050.317 | 1.0614 |
| confirm/n4096_q128_v32_member_uniform | reset-zlib-ordinary | 1.884490–1.968583 | 2116.334–2332.623 | 1.1022 |
| confirm/n4096_q128_v32_member_uniform | reset-zlib-compact | 2.013446–2.079634 | 2327.210–2494.208 | 1.0718 |
| confirm/n4096_q128_v32_member_uniform | reset-zlib-dictionary | 1.652910–1.719299 | 1889.192–2052.674 | 1.0865 |
| confirm/n4096_q128_v32_member_zipf | ordinary | 1.000000–1.000000 | 1075.801–1160.014 | 1.0783 |
| confirm/n4096_q128_v32_member_zipf | compact | 1.124075–1.144832 | 1218.232–1312.660 | 1.0775 |
| confirm/n4096_q128_v32_member_zipf | dictionary | 1.119024–1.134637 | 1171.596–1320.995 | 1.1275 |
| confirm/n4096_q128_v32_member_zipf | zlib-ordinary | 1.793412–1.849936 | 1998.943–2105.666 | 1.0534 |
| confirm/n4096_q128_v32_member_zipf | zlib-compact | 1.881751–1.961754 | 2053.120–2196.178 | 1.0697 |
| confirm/n4096_q128_v32_member_zipf | zlib-dictionary | 1.634713–1.696372 | 1808.842–1892.524 | 1.0463 |
| confirm/n4096_q128_v32_member_zipf | reset-zlib-ordinary | 1.770372–1.829530 | 1871.257–2104.741 | 1.1248 |
| confirm/n4096_q128_v32_member_zipf | reset-zlib-compact | 1.890462–1.936322 | 2016.389–2224.619 | 1.1033 |
| confirm/n4096_q128_v32_member_zipf | reset-zlib-dictionary | 1.607020–1.648706 | 1733.683–1906.631 | 1.0998 |
| confirm/n4096_q1_v1000_member_uniform | ordinary | 1.000000–1.000000 | 13.354–15.073 | 1.1287 |
| confirm/n4096_q1_v1000_member_uniform | compact | 1.101077–1.165591 | 13.874–16.809 | 1.2115 |
| confirm/n4096_q1_v1000_member_uniform | dictionary | 1.152270–1.222158 | 14.982–17.513 | 1.1689 |
| confirm/n4096_q1_v1000_member_uniform | zlib-ordinary | 11.450697–13.355774 | 163.907–178.353 | 1.0881 |
| confirm/n4096_q1_v1000_member_uniform | zlib-compact | 10.317561–12.669023 | 151.508–184.665 | 1.2188 |
| confirm/n4096_q1_v1000_member_uniform | zlib-dictionary | 11.234064–13.570932 | 146.889–175.730 | 1.1963 |
| confirm/n4096_q1_v1000_member_uniform | reset-zlib-ordinary | 2.444333–2.939777 | 35.370–49.548 | 1.4008 |
| confirm/n4096_q1_v1000_member_uniform | reset-zlib-compact | 2.405159–2.779657 | 33.717–38.791 | 1.1505 |
| confirm/n4096_q1_v1000_member_uniform | reset-zlib-dictionary | 2.742799–3.288191 | 38.526–53.943 | 1.4002 |
| confirm/n4096_q1_v1000_member_zipf | ordinary | 1.000000–1.000000 | 11.411–13.835 | 1.2124 |
| confirm/n4096_q1_v1000_member_zipf | compact | 1.106992–1.199909 | 12.611–16.115 | 1.2779 |
| confirm/n4096_q1_v1000_member_zipf | dictionary | 1.130621–1.229150 | 13.733–16.291 | 1.1863 |
| confirm/n4096_q1_v1000_member_zipf | zlib-ordinary | 12.921628–20.307352 | 179.916–267.422 | 1.4864 |
| confirm/n4096_q1_v1000_member_zipf | zlib-compact | 15.443166–22.114865 | 211.279–271.123 | 1.2832 |
| confirm/n4096_q1_v1000_member_zipf | zlib-dictionary | 14.124045–21.393821 | 186.232–258.735 | 1.3893 |
| confirm/n4096_q1_v1000_member_zipf | reset-zlib-ordinary | 2.244548–2.421930 | 26.704–33.885 | 1.2689 |
| confirm/n4096_q1_v1000_member_zipf | reset-zlib-compact | 2.491211–2.652702 | 29.347–37.257 | 1.2695 |
| confirm/n4096_q1_v1000_member_zipf | reset-zlib-dictionary | 2.477991–2.857228 | 31.329–39.498 | 1.2607 |
| confirm/n4096_q1_v32_member_uniform | ordinary | 1.000000–1.000000 | 11.551–12.656 | 1.0957 |
| confirm/n4096_q1_v32_member_uniform | compact | 1.133543–1.243328 | 13.451–15.433 | 1.1473 |
| confirm/n4096_q1_v32_member_uniform | dictionary | 1.187312–1.228121 | 13.934–15.139 | 1.0865 |
| confirm/n4096_q1_v32_member_uniform | zlib-ordinary | 12.517608–18.392154 | 133.767–230.513 | 1.7232 |
| confirm/n4096_q1_v32_member_uniform | zlib-compact | 11.286237–18.702829 | 121.732–231.056 | 1.8981 |
| confirm/n4096_q1_v32_member_uniform | zlib-dictionary | 12.028859–18.528007 | 142.060–234.225 | 1.6488 |
| confirm/n4096_q1_v32_member_uniform | reset-zlib-ordinary | 2.234153–2.687125 | 28.049–41.957 | 1.4958 |
| confirm/n4096_q1_v32_member_uniform | reset-zlib-compact | 2.258506–2.588046 | 26.114–33.764 | 1.2929 |
| confirm/n4096_q1_v32_member_uniform | reset-zlib-dictionary | 2.636178–3.076042 | 31.594–44.884 | 1.4206 |
| confirm/n4096_q1_v32_member_zipf | ordinary | 1.000000–1.000000 | 10.228–12.046 | 1.1777 |
| confirm/n4096_q1_v32_member_zipf | compact | 1.130614–1.149939 | 11.187–14.085 | 1.2591 |
| confirm/n4096_q1_v32_member_zipf | dictionary | 1.148951–1.237141 | 12.286–14.274 | 1.1618 |
| confirm/n4096_q1_v32_member_zipf | zlib-ordinary | 12.540135–16.425339 | 113.087–219.115 | 1.9376 |
| confirm/n4096_q1_v32_member_zipf | zlib-compact | 12.918624–18.909629 | 112.292–242.925 | 2.1633 |
| confirm/n4096_q1_v32_member_zipf | zlib-dictionary | 13.111382–18.307343 | 113.886–235.457 | 2.0675 |
| confirm/n4096_q1_v32_member_zipf | reset-zlib-ordinary | 2.117471–2.536593 | 21.364–29.809 | 1.3953 |
| confirm/n4096_q1_v32_member_zipf | reset-zlib-compact | 2.279566–2.650600 | 22.626–32.254 | 1.4255 |
| confirm/n4096_q1_v32_member_zipf | reset-zlib-dictionary | 2.295356–2.601786 | 23.622–31.019 | 1.3131 |
| confirm/n4096_q32_v1000_member_uniform | ordinary | 1.000000–1.000000 | 341.860–382.938 | 1.1202 |
| confirm/n4096_q32_v1000_member_uniform | compact | 1.105288–1.140971 | 381.163–436.633 | 1.1455 |
| confirm/n4096_q32_v1000_member_uniform | dictionary | 1.108070–1.156724 | 389.471–439.327 | 1.1280 |
| confirm/n4096_q32_v1000_member_uniform | zlib-ordinary | 3.264165–3.447737 | 1173.778–1260.194 | 1.0736 |
| confirm/n4096_q32_v1000_member_uniform | zlib-compact | 3.052278–3.257003 | 1039.573–1153.518 | 1.1096 |
| confirm/n4096_q32_v1000_member_uniform | zlib-dictionary | 2.117315–2.242424 | 743.315–828.218 | 1.1142 |
| confirm/n4096_q32_v1000_member_uniform | reset-zlib-ordinary | 3.115323–3.291630 | 1105.264–1193.918 | 1.0802 |
| confirm/n4096_q32_v1000_member_uniform | reset-zlib-compact | 2.810377–3.069011 | 957.223–1078.189 | 1.1264 |
| confirm/n4096_q32_v1000_member_uniform | reset-zlib-dictionary | 1.821975–1.957093 | 666.741–728.391 | 1.0925 |
| confirm/n4096_q32_v1000_member_zipf | ordinary | 1.000000–1.000000 | 316.762–394.278 | 1.2447 |
| confirm/n4096_q32_v1000_member_zipf | compact | 1.104400–1.126958 | 355.341–434.090 | 1.2216 |
| confirm/n4096_q32_v1000_member_zipf | dictionary | 1.123793–1.168829 | 359.467–437.053 | 1.2158 |
| confirm/n4096_q32_v1000_member_zipf | zlib-ordinary | 3.133178–3.266987 | 1013.933–1210.918 | 1.1943 |
| confirm/n4096_q32_v1000_member_zipf | zlib-compact | 3.165558–3.309359 | 1044.957–1263.007 | 1.2087 |
| confirm/n4096_q32_v1000_member_zipf | zlib-dictionary | 3.039069–3.219412 | 1013.542–1135.527 | 1.1204 |
| confirm/n4096_q32_v1000_member_zipf | reset-zlib-ordinary | 2.910832–3.085917 | 942.490–1132.481 | 1.2016 |
| confirm/n4096_q32_v1000_member_zipf | reset-zlib-compact | 2.971203–3.089630 | 948.902–1195.425 | 1.2598 |
| confirm/n4096_q32_v1000_member_zipf | reset-zlib-dictionary | 2.846005–2.952791 | 950.954–1092.180 | 1.1485 |
| confirm/n4096_q32_v32_member_uniform | ordinary | 1.000000–1.000000 | 278.094–301.288 | 1.0834 |
| confirm/n4096_q32_v32_member_uniform | compact | 1.110276–1.191542 | 303.243–352.183 | 1.1614 |
| confirm/n4096_q32_v32_member_uniform | dictionary | 1.165985–1.216251 | 320.636–356.929 | 1.1132 |
| confirm/n4096_q32_v32_member_uniform | zlib-ordinary | 2.365940–2.507867 | 667.721–755.230 | 1.1311 |
| confirm/n4096_q32_v32_member_uniform | zlib-compact | 2.493088–2.626650 | 708.496–789.383 | 1.1142 |
| confirm/n4096_q32_v32_member_uniform | zlib-dictionary | 2.276044–2.399216 | 644.388–729.791 | 1.1325 |
| confirm/n4096_q32_v32_member_uniform | reset-zlib-ordinary | 2.056427–2.361534 | 595.759–728.302 | 1.2225 |
| confirm/n4096_q32_v32_member_uniform | reset-zlib-compact | 2.228621–2.488592 | 609.791–758.864 | 1.2445 |
| confirm/n4096_q32_v32_member_uniform | reset-zlib-dictionary | 1.944743–2.071621 | 538.434–627.900 | 1.1662 |
| confirm/n4096_q32_v32_member_zipf | ordinary | 1.000000–1.000000 | 274.904–325.714 | 1.1848 |
| confirm/n4096_q32_v32_member_zipf | compact | 1.119349–1.149658 | 306.292–379.061 | 1.2376 |
| confirm/n4096_q32_v32_member_zipf | dictionary | 1.141587–1.182671 | 315.378–373.265 | 1.1835 |
| confirm/n4096_q32_v32_member_zipf | zlib-ordinary | 2.317578–2.388293 | 636.528–761.571 | 1.1964 |
| confirm/n4096_q32_v32_member_zipf | zlib-compact | 2.378033–2.471190 | 666.056–759.153 | 1.1398 |
| confirm/n4096_q32_v32_member_zipf | zlib-dictionary | 2.250540–2.302191 | 635.442–712.570 | 1.1214 |
| confirm/n4096_q32_v32_member_zipf | reset-zlib-ordinary | 2.032022–2.124637 | 574.538–665.557 | 1.1584 |
| confirm/n4096_q32_v32_member_zipf | reset-zlib-compact | 2.141723–2.288415 | 602.035–697.719 | 1.1589 |
| confirm/n4096_q32_v32_member_zipf | reset-zlib-dictionary | 2.009242–2.105645 | 554.031–641.076 | 1.1571 |
| confirm/n4096_q8_v1000_member_uniform | ordinary | 1.000000–1.000000 | 82.600–94.646 | 1.1458 |
| confirm/n4096_q8_v1000_member_uniform | compact | 1.091397–1.136281 | 89.973–102.842 | 1.1430 |
| confirm/n4096_q8_v1000_member_uniform | dictionary | 1.163559–1.224010 | 98.573–111.224 | 1.1283 |
| confirm/n4096_q8_v1000_member_uniform | zlib-ordinary | 4.530338–4.893663 | 386.167–435.155 | 1.1269 |
| confirm/n4096_q8_v1000_member_uniform | zlib-compact | 3.030772–3.260079 | 254.014–291.720 | 1.1484 |
| confirm/n4096_q8_v1000_member_uniform | zlib-dictionary | 3.573729–3.895488 | 301.243–347.952 | 1.1551 |
| confirm/n4096_q8_v1000_member_uniform | reset-zlib-ordinary | 3.377257–3.906849 | 305.565–346.553 | 1.1341 |
| confirm/n4096_q8_v1000_member_uniform | reset-zlib-compact | 1.832507–2.099461 | 173.050–199.571 | 1.1533 |
| confirm/n4096_q8_v1000_member_uniform | reset-zlib-dictionary | 2.375135–2.527922 | 202.160–228.604 | 1.1308 |
| confirm/n4096_q8_v1000_member_zipf | ordinary | 1.000000–1.000000 | 80.373–90.040 | 1.1203 |
| confirm/n4096_q8_v1000_member_zipf | compact | 1.112228–1.140274 | 88.620–98.798 | 1.1148 |
| confirm/n4096_q8_v1000_member_zipf | dictionary | 1.174540–1.193870 | 96.716–104.098 | 1.0763 |
| confirm/n4096_q8_v1000_member_zipf | zlib-ordinary | 4.005827–4.726757 | 358.017–426.467 | 1.1912 |
| confirm/n4096_q8_v1000_member_zipf | zlib-compact | 4.022032–4.746757 | 352.195–391.991 | 1.1130 |
| confirm/n4096_q8_v1000_member_zipf | zlib-dictionary | 4.179633–4.829787 | 357.717–447.432 | 1.2508 |
| confirm/n4096_q8_v1000_member_zipf | reset-zlib-ordinary | 2.360851–2.769970 | 194.658–274.457 | 1.4099 |
| confirm/n4096_q8_v1000_member_zipf | reset-zlib-compact | 1.992285–2.349353 | 184.685–248.153 | 1.3437 |
| confirm/n4096_q8_v1000_member_zipf | reset-zlib-dictionary | 2.575384–2.775723 | 225.203–272.069 | 1.2081 |
| confirm/n4096_q8_v32_member_uniform | ordinary | 1.000000–1.000000 | 67.368–81.569 | 1.2108 |
| confirm/n4096_q8_v32_member_uniform | compact | 1.130691–1.168669 | 78.189–96.400 | 1.2329 |
| confirm/n4096_q8_v32_member_uniform | dictionary | 1.216432–1.272356 | 85.523–99.270 | 1.1607 |
| confirm/n4096_q8_v32_member_uniform | zlib-ordinary | 4.196786–4.731752 | 278.243–425.982 | 1.5310 |
| confirm/n4096_q8_v32_member_uniform | zlib-compact | 4.271253–5.094964 | 282.962–427.576 | 1.5111 |
| confirm/n4096_q8_v32_member_uniform | zlib-dictionary | 3.629930–4.444060 | 244.819–370.688 | 1.5141 |
| confirm/n4096_q8_v32_member_uniform | reset-zlib-ordinary | 2.831098–3.394720 | 202.168–264.691 | 1.3093 |
| confirm/n4096_q8_v32_member_uniform | reset-zlib-compact | 2.713255–3.201904 | 192.005–249.625 | 1.3001 |
| confirm/n4096_q8_v32_member_uniform | reset-zlib-dictionary | 2.245649–2.456799 | 157.631–192.015 | 1.2181 |
| confirm/n4096_q8_v32_member_zipf | ordinary | 1.000000–1.000000 | 66.450–73.767 | 1.1101 |
| confirm/n4096_q8_v32_member_zipf | compact | 1.130837–1.211023 | 76.567–85.839 | 1.1211 |
| confirm/n4096_q8_v32_member_zipf | dictionary | 1.215745–1.275859 | 83.729–90.380 | 1.0794 |
| confirm/n4096_q8_v32_member_zipf | zlib-ordinary | 4.253809–4.353307 | 285.363–308.357 | 1.0806 |
| confirm/n4096_q8_v32_member_zipf | zlib-compact | 4.290364–4.495885 | 288.714–315.623 | 1.0932 |
| confirm/n4096_q8_v32_member_zipf | zlib-dictionary | 3.797175–4.058935 | 258.590–284.359 | 1.0997 |
| confirm/n4096_q8_v32_member_zipf | reset-zlib-ordinary | 2.808437–3.240003 | 192.501–219.578 | 1.1407 |
| confirm/n4096_q8_v32_member_zipf | reset-zlib-compact | 2.950260–3.322967 | 203.385–232.248 | 1.1419 |
| confirm/n4096_q8_v32_member_zipf | reset-zlib-dictionary | 2.477846–2.836319 | 169.740–195.571 | 1.1522 |
| dev/n16384_q128_v1000_member_uniform | ordinary | 1.000000–1.000000 | 1417.768–1584.254 | 1.1174 |
| dev/n16384_q128_v1000_member_uniform | compact | 1.100859–1.142968 | 1584.696–1788.341 | 1.1285 |
| dev/n16384_q128_v1000_member_uniform | dictionary | 1.111683–1.150792 | 1608.239–1762.599 | 1.0960 |
| dev/n16384_q128_v1000_member_uniform | zlib-ordinary | 2.917221–3.131694 | 4243.750–4774.318 | 1.1250 |
| dev/n16384_q128_v1000_member_uniform | zlib-compact | 2.478295–2.671432 | 3597.750–3975.217 | 1.1049 |
| dev/n16384_q128_v1000_member_uniform | zlib-dictionary | 1.618378–1.759425 | 2546.517–2723.980 | 1.0697 |
| dev/n16384_q128_v1000_member_uniform | reset-zlib-ordinary | 2.964232–3.141188 | 4255.185–4767.512 | 1.1204 |
| dev/n16384_q128_v1000_member_uniform | reset-zlib-compact | 2.526800–2.712396 | 3644.028–3975.637 | 1.0910 |
| dev/n16384_q128_v1000_member_uniform | reset-zlib-dictionary | 1.700517–1.722333 | 2506.782–2740.715 | 1.0933 |
| dev/n16384_q128_v1000_member_zipf | ordinary | 1.000000–1.000000 | 1408.000–1550.938 | 1.1015 |
| dev/n16384_q128_v1000_member_zipf | compact | 1.100034–1.132452 | 1528.648–1733.070 | 1.1337 |
| dev/n16384_q128_v1000_member_zipf | dictionary | 1.076587–1.110962 | 1516.384–1709.121 | 1.1271 |
| dev/n16384_q128_v1000_member_zipf | zlib-ordinary | 2.804075–2.900434 | 3929.685–4436.437 | 1.1290 |
| dev/n16384_q128_v1000_member_zipf | zlib-compact | 2.773339–2.901309 | 3964.571–4484.214 | 1.1311 |
| dev/n16384_q128_v1000_member_zipf | zlib-dictionary | 2.247353–2.375918 | 3325.097–3608.564 | 1.0853 |
| dev/n16384_q128_v1000_member_zipf | reset-zlib-ordinary | 2.806595–2.871858 | 3920.505–4548.629 | 1.1602 |
| dev/n16384_q128_v1000_member_zipf | reset-zlib-compact | 2.772626–2.857550 | 3843.826–4497.673 | 1.1701 |
| dev/n16384_q128_v1000_member_zipf | reset-zlib-dictionary | 2.303713–2.401512 | 3362.078–3692.430 | 1.0983 |
| dev/n16384_q128_v32_member_uniform | ordinary | 1.000000–1.000000 | 1255.332–1405.007 | 1.1192 |
| dev/n16384_q128_v32_member_uniform | compact | 1.108133–1.142744 | 1357.316–1592.786 | 1.1735 |
| dev/n16384_q128_v32_member_uniform | dictionary | 1.136225–1.165379 | 1439.895–1626.403 | 1.1295 |
| dev/n16384_q128_v32_member_uniform | zlib-ordinary | 1.985913–2.054072 | 2518.614–2804.772 | 1.1136 |
| dev/n16384_q128_v32_member_uniform | zlib-compact | 2.056920–2.166988 | 2670.273–2956.462 | 1.1072 |
| dev/n16384_q128_v32_member_uniform | zlib-dictionary | 1.688372–1.761733 | 2159.950–2426.306 | 1.1233 |
| dev/n16384_q128_v32_member_uniform | reset-zlib-ordinary | 1.931895–2.092027 | 2442.070–3002.440 | 1.2295 |
| dev/n16384_q128_v32_member_uniform | reset-zlib-compact | 2.030461–2.200156 | 2632.732–3121.545 | 1.1857 |
| dev/n16384_q128_v32_member_uniform | reset-zlib-dictionary | 1.657675–1.732489 | 2152.360–2399.456 | 1.1148 |
| dev/n16384_q128_v32_member_zipf | ordinary | 1.000000–1.000000 | 1246.664–1374.776 | 1.1028 |
| dev/n16384_q128_v32_member_zipf | compact | 1.105322–1.135196 | 1364.032–1514.418 | 1.1103 |
| dev/n16384_q128_v32_member_zipf | dictionary | 1.089283–1.138499 | 1384.981–1532.819 | 1.1067 |
| dev/n16384_q128_v32_member_zipf | zlib-ordinary | 1.777606–1.850316 | 2334.735–2476.081 | 1.0605 |
| dev/n16384_q128_v32_member_zipf | zlib-compact | 1.908104–2.005536 | 2478.401–2693.274 | 1.0867 |
| dev/n16384_q128_v32_member_zipf | zlib-dictionary | 1.601365–1.683814 | 2067.121–2235.700 | 1.0816 |
| dev/n16384_q128_v32_member_zipf | reset-zlib-ordinary | 1.773509–1.872029 | 2298.308–2462.178 | 1.0713 |
| dev/n16384_q128_v32_member_zipf | reset-zlib-compact | 1.861616–1.986624 | 2480.161–2685.328 | 1.0827 |
| dev/n16384_q128_v32_member_zipf | reset-zlib-dictionary | 1.599667–1.642773 | 1982.121–2247.255 | 1.1338 |
| dev/n16384_q1_v1000_member_uniform | ordinary | 1.000000–1.000000 | 12.944–16.419 | 1.2685 |
| dev/n16384_q1_v1000_member_uniform | compact | 1.043760–1.114539 | 14.396–17.549 | 1.2190 |
| dev/n16384_q1_v1000_member_uniform | dictionary | 1.205378–1.249315 | 15.487–20.139 | 1.3004 |
| dev/n16384_q1_v1000_member_uniform | zlib-ordinary | 12.978304–18.368098 | 201.592–274.295 | 1.3606 |
| dev/n16384_q1_v1000_member_uniform | zlib-compact | 11.960277–18.323418 | 159.306–252.329 | 1.5839 |
| dev/n16384_q1_v1000_member_uniform | zlib-dictionary | 12.194873–18.138388 | 189.218–259.887 | 1.3735 |
| dev/n16384_q1_v1000_member_uniform | reset-zlib-ordinary | 2.381752–2.991401 | 31.550–40.399 | 1.2805 |
| dev/n16384_q1_v1000_member_uniform | reset-zlib-compact | 2.175032–2.551849 | 28.879–42.170 | 1.4602 |
| dev/n16384_q1_v1000_member_uniform | reset-zlib-dictionary | 2.718384–3.108353 | 35.444–52.219 | 1.4733 |
| dev/n16384_q1_v1000_member_zipf | ordinary | 1.000000–1.000000 | 13.235–15.464 | 1.1684 |
| dev/n16384_q1_v1000_member_zipf | compact | 1.089504–1.168051 | 15.231–17.976 | 1.1802 |
| dev/n16384_q1_v1000_member_zipf | dictionary | 1.213133–1.297444 | 16.496–19.831 | 1.2022 |
| dev/n16384_q1_v1000_member_zipf | zlib-ordinary | 15.143815–20.156416 | 205.547–277.065 | 1.3479 |
| dev/n16384_q1_v1000_member_zipf | zlib-compact | 12.276996–19.712332 | 178.567–268.453 | 1.5034 |
| dev/n16384_q1_v1000_member_zipf | zlib-dictionary | 15.148058–20.693238 | 225.753–270.189 | 1.1968 |
| dev/n16384_q1_v1000_member_zipf | reset-zlib-ordinary | 2.340559–2.868697 | 29.351–41.124 | 1.4011 |
| dev/n16384_q1_v1000_member_zipf | reset-zlib-compact | 2.294260–2.627989 | 30.664–40.711 | 1.3276 |
| dev/n16384_q1_v1000_member_zipf | reset-zlib-dictionary | 2.921684–3.128337 | 37.866–46.162 | 1.2191 |
| dev/n16384_q1_v32_member_uniform | ordinary | 1.000000–1.000000 | 11.985–14.983 | 1.2501 |
| dev/n16384_q1_v32_member_uniform | compact | 1.066461–1.233733 | 13.539–17.976 | 1.3277 |
| dev/n16384_q1_v32_member_uniform | dictionary | 1.163877–1.292440 | 14.604–18.268 | 1.2509 |
| dev/n16384_q1_v32_member_uniform | zlib-ordinary | 12.645090–18.107412 | 158.075–244.547 | 1.5470 |
| dev/n16384_q1_v32_member_uniform | zlib-compact | 11.672976–16.173745 | 136.324–232.148 | 1.7029 |
| dev/n16384_q1_v32_member_uniform | zlib-dictionary | 12.021269–15.871114 | 152.562–216.627 | 1.4199 |
| dev/n16384_q1_v32_member_uniform | reset-zlib-ordinary | 2.306133–2.772528 | 23.569–45.664 | 1.9375 |
| dev/n16384_q1_v32_member_uniform | reset-zlib-compact | 2.137405–2.412908 | 25.265–33.165 | 1.3127 |
| dev/n16384_q1_v32_member_uniform | reset-zlib-dictionary | 2.722247–3.083894 | 29.006–48.423 | 1.6694 |
| dev/n16384_q1_v32_member_zipf | ordinary | 1.000000–1.000000 | 12.360–14.090 | 1.1400 |
| dev/n16384_q1_v32_member_zipf | compact | 1.111073–1.153672 | 14.340–15.991 | 1.1151 |
| dev/n16384_q1_v32_member_zipf | dictionary | 1.249795–1.322209 | 15.675–17.070 | 1.0890 |
| dev/n16384_q1_v32_member_zipf | zlib-ordinary | 12.065859–17.647828 | 171.071–234.545 | 1.3710 |
| dev/n16384_q1_v32_member_zipf | zlib-compact | 10.892472–19.010715 | 139.674–242.982 | 1.7396 |
| dev/n16384_q1_v32_member_zipf | zlib-dictionary | 11.803023–18.473227 | 165.382–255.381 | 1.5442 |
| dev/n16384_q1_v32_member_zipf | reset-zlib-ordinary | 2.463828–2.694594 | 28.061–35.787 | 1.2753 |
| dev/n16384_q1_v32_member_zipf | reset-zlib-compact | 2.233671–2.562768 | 28.829–34.742 | 1.2051 |
| dev/n16384_q1_v32_member_zipf | reset-zlib-dictionary | 2.797289–3.066032 | 32.079–44.437 | 1.3852 |
| dev/n16384_q32_v1000_member_uniform | ordinary | 1.000000–1.000000 | 366.084–406.028 | 1.1091 |
| dev/n16384_q32_v1000_member_uniform | compact | 1.103894–1.136816 | 413.505–454.804 | 1.0999 |
| dev/n16384_q32_v1000_member_uniform | dictionary | 1.099167–1.191297 | 411.102–473.294 | 1.1513 |
| dev/n16384_q32_v1000_member_uniform | zlib-ordinary | 3.137316–3.329563 | 1219.006–1311.229 | 1.0757 |
| dev/n16384_q32_v1000_member_uniform | zlib-compact | 1.974890–2.132815 | 758.803–855.409 | 1.1273 |
| dev/n16384_q32_v1000_member_uniform | zlib-dictionary | 2.070143–2.142825 | 756.384–885.497 | 1.1707 |
| dev/n16384_q32_v1000_member_uniform | reset-zlib-ordinary | 3.004744–3.166972 | 1106.098–1306.156 | 1.1809 |
| dev/n16384_q32_v1000_member_uniform | reset-zlib-compact | 1.888185–2.001546 | 678.346–832.179 | 1.2268 |
| dev/n16384_q32_v1000_member_uniform | reset-zlib-dictionary | 1.876623–1.973696 | 716.135–798.557 | 1.1151 |
| dev/n16384_q32_v1000_member_zipf | ordinary | 1.000000–1.000000 | 356.127–408.490 | 1.1470 |
| dev/n16384_q32_v1000_member_zipf | compact | 1.091637–1.127579 | 398.349–453.921 | 1.1395 |
| dev/n16384_q32_v1000_member_zipf | dictionary | 1.105783–1.150958 | 410.798–442.454 | 1.0771 |
| dev/n16384_q32_v1000_member_zipf | zlib-ordinary | 2.950378–3.149195 | 1146.503–1180.369 | 1.0295 |
| dev/n16384_q32_v1000_member_zipf | zlib-compact | 2.821437–3.021626 | 1035.963–1101.047 | 1.0628 |
| dev/n16384_q32_v1000_member_zipf | zlib-dictionary | 2.063833–2.132573 | 756.111–829.090 | 1.0965 |
| dev/n16384_q32_v1000_member_zipf | reset-zlib-ordinary | 2.817295–3.014221 | 1055.079–1124.839 | 1.0661 |
| dev/n16384_q32_v1000_member_zipf | reset-zlib-compact | 2.625319–2.861540 | 990.885–1056.177 | 1.0659 |
| dev/n16384_q32_v1000_member_zipf | reset-zlib-dictionary | 1.805953–1.906637 | 676.899–739.661 | 1.0927 |
| dev/n16384_q32_v32_member_uniform | ordinary | 1.000000–1.000000 | 317.201–345.009 | 1.0877 |
| dev/n16384_q32_v32_member_uniform | compact | 1.120516–1.145412 | 348.121–386.501 | 1.1102 |
| dev/n16384_q32_v32_member_uniform | dictionary | 1.143738–1.170411 | 362.876–389.138 | 1.0724 |
| dev/n16384_q32_v32_member_uniform | zlib-ordinary | 2.246396–2.311179 | 729.566–783.586 | 1.0740 |
| dev/n16384_q32_v32_member_uniform | zlib-compact | 2.354028–2.439317 | 769.702–841.095 | 1.0928 |
| dev/n16384_q32_v32_member_uniform | zlib-dictionary | 2.160752–2.315458 | 716.798–735.719 | 1.0264 |
| dev/n16384_q32_v32_member_uniform | reset-zlib-ordinary | 2.033190–2.240466 | 652.349–740.556 | 1.1352 |
| dev/n16384_q32_v32_member_uniform | reset-zlib-compact | 2.149879–2.284097 | 684.898–785.219 | 1.1465 |
| dev/n16384_q32_v32_member_uniform | reset-zlib-dictionary | 1.877451–1.982678 | 619.984–668.826 | 1.0788 |
| dev/n16384_q32_v32_member_zipf | ordinary | 1.000000–1.000000 | 313.012–373.209 | 1.1923 |
| dev/n16384_q32_v32_member_zipf | compact | 1.119840–1.157693 | 352.530–416.625 | 1.1818 |
| dev/n16384_q32_v32_member_zipf | dictionary | 1.118871–1.191651 | 354.462–415.286 | 1.1716 |
| dev/n16384_q32_v32_member_zipf | zlib-ordinary | 2.177887–2.295088 | 694.035–803.056 | 1.1571 |
| dev/n16384_q32_v32_member_zipf | zlib-compact | 2.317279–2.406456 | 723.264–851.301 | 1.1770 |
| dev/n16384_q32_v32_member_zipf | zlib-dictionary | 2.097290–2.218514 | 686.548–782.266 | 1.1394 |
| dev/n16384_q32_v32_member_zipf | reset-zlib-ordinary | 1.989263–2.141343 | 626.154–752.155 | 1.2012 |
| dev/n16384_q32_v32_member_zipf | reset-zlib-compact | 2.071211–2.313914 | 656.433–823.903 | 1.2551 |
| dev/n16384_q32_v32_member_zipf | reset-zlib-dictionary | 1.888065–1.919962 | 586.668–717.325 | 1.2227 |
| dev/n16384_q8_v1000_member_uniform | ordinary | 1.000000–1.000000 | 87.322–107.199 | 1.2276 |
| dev/n16384_q8_v1000_member_uniform | compact | 1.086002–1.165464 | 103.942–126.937 | 1.2212 |
| dev/n16384_q8_v1000_member_uniform | dictionary | 1.174173–1.230968 | 107.386–125.074 | 1.1647 |
| dev/n16384_q8_v1000_member_uniform | zlib-ordinary | 3.531260–4.690850 | 345.428–424.405 | 1.2286 |
| dev/n16384_q8_v1000_member_uniform | zlib-compact | 2.626346–2.984171 | 267.557–353.189 | 1.3201 |
| dev/n16384_q8_v1000_member_uniform | zlib-dictionary | 3.563288–4.090644 | 364.594–423.800 | 1.1624 |
| dev/n16384_q8_v1000_member_uniform | reset-zlib-ordinary | 2.411287–2.752136 | 247.928–265.786 | 1.0720 |
| dev/n16384_q8_v1000_member_uniform | reset-zlib-compact | 1.473699–1.527692 | 135.836–154.383 | 1.1365 |
| dev/n16384_q8_v1000_member_uniform | reset-zlib-dictionary | 2.337831–2.495485 | 218.298–258.073 | 1.1822 |
| dev/n16384_q8_v1000_member_zipf | ordinary | 1.000000–1.000000 | 82.942–101.239 | 1.2206 |
| dev/n16384_q8_v1000_member_zipf | compact | 1.101032–1.197028 | 95.275–117.507 | 1.2333 |
| dev/n16384_q8_v1000_member_zipf | dictionary | 1.192063–1.275054 | 102.289–123.266 | 1.2051 |
| dev/n16384_q8_v1000_member_zipf | zlib-ordinary | 3.133952–4.031828 | 308.140–415.640 | 1.3489 |
| dev/n16384_q8_v1000_member_zipf | zlib-compact | 2.882680–3.078008 | 282.224–305.738 | 1.0833 |
| dev/n16384_q8_v1000_member_zipf | zlib-dictionary | 3.450686–3.666226 | 331.985–369.765 | 1.1138 |
| dev/n16384_q8_v1000_member_zipf | reset-zlib-ordinary | 1.933166–2.124798 | 170.338–262.387 | 1.5404 |
| dev/n16384_q8_v1000_member_zipf | reset-zlib-compact | 1.718096–1.954976 | 163.168–184.429 | 1.1303 |
| dev/n16384_q8_v1000_member_zipf | reset-zlib-dictionary | 2.357714–2.457340 | 209.484–235.953 | 1.1264 |
| dev/n16384_q8_v32_member_uniform | ordinary | 1.000000–1.000000 | 78.195–95.236 | 1.2179 |
| dev/n16384_q8_v32_member_uniform | compact | 1.149799–1.196962 | 91.293–111.291 | 1.2191 |
| dev/n16384_q8_v32_member_uniform | dictionary | 1.208485–1.280955 | 94.688–111.436 | 1.1769 |
| dev/n16384_q8_v32_member_uniform | zlib-ordinary | 3.943701–4.161262 | 311.012–432.344 | 1.3901 |
| dev/n16384_q8_v32_member_uniform | zlib-compact | 4.000107–4.375944 | 317.072–384.124 | 1.2115 |
| dev/n16384_q8_v32_member_uniform | zlib-dictionary | 3.548984–3.736387 | 275.272–394.574 | 1.4334 |
| dev/n16384_q8_v32_member_uniform | reset-zlib-ordinary | 2.776090–3.009763 | 222.271–284.347 | 1.2793 |
| dev/n16384_q8_v32_member_uniform | reset-zlib-compact | 2.776683–3.149699 | 235.849–281.443 | 1.1933 |
| dev/n16384_q8_v32_member_uniform | reset-zlib-dictionary | 2.183464–2.339809 | 179.996–207.943 | 1.1553 |
| dev/n16384_q8_v32_member_zipf | ordinary | 1.000000–1.000000 | 76.445–85.151 | 1.1139 |
| dev/n16384_q8_v32_member_zipf | compact | 1.129565–1.163580 | 85.511–94.882 | 1.1096 |
| dev/n16384_q8_v32_member_zipf | dictionary | 1.194649–1.268821 | 93.840–105.034 | 1.1193 |
| dev/n16384_q8_v32_member_zipf | zlib-ordinary | 4.196616–5.032787 | 332.781–405.911 | 1.2198 |
| dev/n16384_q8_v32_member_zipf | zlib-compact | 4.412678–5.253118 | 362.824–445.086 | 1.2267 |
| dev/n16384_q8_v32_member_zipf | zlib-dictionary | 3.819626–4.504891 | 313.846–374.678 | 1.1938 |
| dev/n16384_q8_v32_member_zipf | reset-zlib-ordinary | 2.754587–2.976319 | 213.655–252.868 | 1.1835 |
| dev/n16384_q8_v32_member_zipf | reset-zlib-compact | 2.867851–3.093224 | 224.144–266.181 | 1.1875 |
| dev/n16384_q8_v32_member_zipf | reset-zlib-dictionary | 2.274980–2.424103 | 180.680–203.365 | 1.1256 |
| dev/n4096_q128_v1000_member_uniform | ordinary | 1.000000–1.000000 | 1231.351–1418.110 | 1.1517 |
| dev/n4096_q128_v1000_member_uniform | compact | 1.109460–1.125410 | 1351.424–1558.093 | 1.1529 |
| dev/n4096_q128_v1000_member_uniform | dictionary | 1.101115–1.123548 | 1381.308–1588.127 | 1.1497 |
| dev/n4096_q128_v1000_member_uniform | zlib-ordinary | 3.056008–3.208497 | 3955.384–4518.532 | 1.1424 |
| dev/n4096_q128_v1000_member_uniform | zlib-compact | 2.962473–3.210396 | 3997.892–4401.313 | 1.1009 |
| dev/n4096_q128_v1000_member_uniform | zlib-dictionary | 1.782269–1.860413 | 2310.344–2570.366 | 1.1125 |
| dev/n4096_q128_v1000_member_uniform | reset-zlib-ordinary | 3.014623–3.268179 | 3956.331–4568.585 | 1.1548 |
| dev/n4096_q128_v1000_member_uniform | reset-zlib-compact | 2.994925–3.168736 | 3888.051–4416.217 | 1.1358 |
| dev/n4096_q128_v1000_member_uniform | reset-zlib-dictionary | 1.789138–1.854630 | 2295.358–2594.365 | 1.1303 |
| dev/n4096_q128_v1000_member_zipf | ordinary | 1.000000–1.000000 | 1270.220–1413.847 | 1.1131 |
| dev/n4096_q128_v1000_member_zipf | compact | 1.105214–1.125500 | 1387.139–1595.793 | 1.1504 |
| dev/n4096_q128_v1000_member_zipf | dictionary | 1.060911–1.120312 | 1426.422–1517.433 | 1.0638 |
| dev/n4096_q128_v1000_member_zipf | zlib-ordinary | 2.745785–2.921696 | 3691.712–3907.498 | 1.0585 |
| dev/n4096_q128_v1000_member_zipf | zlib-compact | 2.787224–2.895372 | 3603.694–3975.694 | 1.1032 |
| dev/n4096_q128_v1000_member_zipf | zlib-dictionary | 2.135488–2.278484 | 2806.022–3073.627 | 1.0954 |
| dev/n4096_q128_v1000_member_zipf | reset-zlib-ordinary | 2.796775–2.887266 | 3636.956–4039.918 | 1.1108 |
| dev/n4096_q128_v1000_member_zipf | reset-zlib-compact | 2.796784–2.920442 | 3561.010–3950.084 | 1.1093 |
| dev/n4096_q128_v1000_member_zipf | reset-zlib-dictionary | 2.132469–2.261815 | 2789.973–3209.239 | 1.1503 |
| dev/n4096_q128_v32_member_uniform | ordinary | 1.000000–1.000000 | 1059.945–1178.258 | 1.1116 |
| dev/n4096_q128_v32_member_uniform | compact | 1.113178–1.143872 | 1172.263–1327.817 | 1.1327 |
| dev/n4096_q128_v32_member_uniform | dictionary | 1.126460–1.176119 | 1206.651–1364.846 | 1.1311 |
| dev/n4096_q128_v32_member_uniform | zlib-ordinary | 1.921573–2.022759 | 2073.875–2313.371 | 1.1155 |
| dev/n4096_q128_v32_member_uniform | zlib-compact | 1.990488–2.151841 | 2245.225–2419.064 | 1.0774 |
| dev/n4096_q128_v32_member_uniform | zlib-dictionary | 1.735664–1.793184 | 1864.891–2091.898 | 1.1217 |
| dev/n4096_q128_v32_member_uniform | reset-zlib-ordinary | 1.915074–1.971130 | 2023.523–2304.475 | 1.1388 |
| dev/n4096_q128_v32_member_uniform | reset-zlib-compact | 2.027850–2.069266 | 2160.756–2447.806 | 1.1328 |
| dev/n4096_q128_v32_member_uniform | reset-zlib-dictionary | 1.664352–1.715806 | 1795.480–2052.390 | 1.1431 |
| dev/n4096_q128_v32_member_zipf | ordinary | 1.000000–1.000000 | 1093.007–1212.234 | 1.1091 |
| dev/n4096_q128_v32_member_zipf | compact | 1.115847–1.144190 | 1207.696–1364.297 | 1.1297 |
| dev/n4096_q128_v32_member_zipf | dictionary | 1.123617–1.146052 | 1245.843–1349.835 | 1.0835 |
| dev/n4096_q128_v32_member_zipf | zlib-ordinary | 1.760754–1.844843 | 1999.015–2168.958 | 1.0850 |
| dev/n4096_q128_v32_member_zipf | zlib-compact | 1.847583–1.961263 | 2150.095–2303.269 | 1.0712 |
| dev/n4096_q128_v32_member_zipf | zlib-dictionary | 1.619011–1.693607 | 1834.018–1947.723 | 1.0620 |
| dev/n4096_q128_v32_member_zipf | reset-zlib-ordinary | 1.742866–1.799873 | 1967.722–2138.004 | 1.0865 |
| dev/n4096_q128_v32_member_zipf | reset-zlib-compact | 1.858137–1.913288 | 2070.188–2258.479 | 1.0910 |
| dev/n4096_q128_v32_member_zipf | reset-zlib-dictionary | 1.617700–1.672961 | 1759.375–1965.546 | 1.1172 |
| dev/n4096_q1_v1000_member_uniform | ordinary | 1.000000–1.000000 | 10.897–14.124 | 1.2961 |
| dev/n4096_q1_v1000_member_uniform | compact | 1.115762–1.176879 | 12.543–15.498 | 1.2356 |
| dev/n4096_q1_v1000_member_uniform | dictionary | 1.097880–1.178092 | 12.490–15.895 | 1.2726 |
| dev/n4096_q1_v1000_member_uniform | zlib-ordinary | 12.428872–21.533734 | 193.225–251.683 | 1.3025 |
| dev/n4096_q1_v1000_member_uniform | zlib-compact | 11.508230–21.823998 | 166.452–237.881 | 1.4291 |
| dev/n4096_q1_v1000_member_uniform | zlib-dictionary | 12.857778–21.304207 | 203.066–255.015 | 1.2558 |
| dev/n4096_q1_v1000_member_uniform | reset-zlib-ordinary | 2.394756–3.293796 | 28.589–39.987 | 1.3987 |
| dev/n4096_q1_v1000_member_uniform | reset-zlib-compact | 2.310342–2.636224 | 27.934–34.929 | 1.2504 |
| dev/n4096_q1_v1000_member_uniform | reset-zlib-dictionary | 2.957812–3.438423 | 33.788–42.953 | 1.2713 |
| dev/n4096_q1_v1000_member_zipf | ordinary | 1.000000–1.000000 | 11.535–13.399 | 1.1616 |
| dev/n4096_q1_v1000_member_zipf | compact | 1.121614–1.197146 | 13.042–15.514 | 1.1895 |
| dev/n4096_q1_v1000_member_zipf | dictionary | 1.158889–1.184284 | 13.540–16.079 | 1.1875 |
| dev/n4096_q1_v1000_member_zipf | zlib-ordinary | 11.464383–19.536034 | 125.969–262.271 | 2.0820 |
| dev/n4096_q1_v1000_member_zipf | zlib-compact | 12.400662–21.020841 | 142.792–273.550 | 1.9157 |
| dev/n4096_q1_v1000_member_zipf | zlib-dictionary | 12.457834–19.546469 | 129.494–260.466 | 2.0114 |
| dev/n4096_q1_v1000_member_zipf | reset-zlib-ordinary | 2.309353–2.632830 | 28.862–34.758 | 1.2043 |
| dev/n4096_q1_v1000_member_zipf | reset-zlib-compact | 2.556691–2.795912 | 31.026–37.134 | 1.1969 |
| dev/n4096_q1_v1000_member_zipf | reset-zlib-dictionary | 2.605361–2.750908 | 31.668–36.364 | 1.1483 |
| dev/n4096_q1_v32_member_uniform | ordinary | 1.000000–1.000000 | 11.080–13.640 | 1.2310 |
| dev/n4096_q1_v32_member_uniform | compact | 1.117476–1.190914 | 12.376–16.355 | 1.3215 |
| dev/n4096_q1_v32_member_uniform | dictionary | 1.195821–1.278482 | 13.323–17.209 | 1.2917 |
| dev/n4096_q1_v32_member_uniform | zlib-ordinary | 12.761086–14.558113 | 145.459–175.459 | 1.2062 |
| dev/n4096_q1_v32_member_uniform | zlib-compact | 11.407054–12.369883 | 116.066–166.066 | 1.4308 |
| dev/n4096_q1_v32_member_uniform | zlib-dictionary | 12.555906–13.392206 | 140.316–169.551 | 1.2084 |
| dev/n4096_q1_v32_member_uniform | reset-zlib-ordinary | 2.185739–2.888825 | 22.847–45.778 | 2.0037 |
| dev/n4096_q1_v32_member_uniform | reset-zlib-compact | 2.150997–2.554615 | 24.377–33.289 | 1.3656 |
| dev/n4096_q1_v32_member_uniform | reset-zlib-dictionary | 2.558128–3.180020 | 27.906–45.786 | 1.6407 |
| dev/n4096_q1_v32_member_zipf | ordinary | 1.000000–1.000000 | 9.616–11.437 | 1.1894 |
| dev/n4096_q1_v32_member_zipf | compact | 1.119605–1.209474 | 11.017–13.410 | 1.2172 |
| dev/n4096_q1_v32_member_zipf | dictionary | 1.202512–1.273493 | 11.385–14.117 | 1.2400 |
| dev/n4096_q1_v32_member_zipf | zlib-ordinary | 15.868660–20.881004 | 148.610–247.408 | 1.6648 |
| dev/n4096_q1_v32_member_zipf | zlib-compact | 16.466543–20.879634 | 154.996–249.909 | 1.6124 |
| dev/n4096_q1_v32_member_zipf | zlib-dictionary | 14.189110–21.690907 | 134.854–244.328 | 1.8118 |
| dev/n4096_q1_v32_member_zipf | reset-zlib-ordinary | 2.153712–2.537662 | 21.798–25.709 | 1.1794 |
| dev/n4096_q1_v32_member_zipf | reset-zlib-compact | 2.282983–2.711424 | 22.156–27.705 | 1.2505 |
| dev/n4096_q1_v32_member_zipf | reset-zlib-dictionary | 2.417697–2.643208 | 24.539–28.363 | 1.1558 |
| dev/n4096_q32_v1000_member_uniform | ordinary | 1.000000–1.000000 | 323.414–374.301 | 1.1573 |
| dev/n4096_q32_v1000_member_uniform | compact | 1.129150–1.186421 | 369.273–432.920 | 1.1724 |
| dev/n4096_q32_v1000_member_uniform | dictionary | 1.122800–1.174586 | 368.002–426.649 | 1.1594 |
| dev/n4096_q32_v1000_member_uniform | zlib-ordinary | 3.275598–3.557084 | 1185.319–1224.163 | 1.0328 |
| dev/n4096_q32_v1000_member_uniform | zlib-compact | 2.923260–3.366098 | 1063.283–1161.368 | 1.0922 |
| dev/n4096_q32_v1000_member_uniform | zlib-dictionary | 2.095318–2.223655 | 735.068–793.463 | 1.0794 |
| dev/n4096_q32_v1000_member_uniform | reset-zlib-ordinary | 3.134926–3.382437 | 1097.430–1177.926 | 1.0733 |
| dev/n4096_q32_v1000_member_uniform | reset-zlib-compact | 2.779411–3.137422 | 953.692–1116.121 | 1.1703 |
| dev/n4096_q32_v1000_member_uniform | reset-zlib-dictionary | 1.887596–1.978915 | 648.774–716.577 | 1.1045 |
| dev/n4096_q32_v1000_member_zipf | ordinary | 1.000000–1.000000 | 348.504–369.189 | 1.0594 |
| dev/n4096_q32_v1000_member_zipf | compact | 1.085187–1.154845 | 382.293–410.454 | 1.0737 |
| dev/n4096_q32_v1000_member_zipf | dictionary | 1.091489–1.137108 | 383.287–411.761 | 1.0743 |
| dev/n4096_q32_v1000_member_zipf | zlib-ordinary | 2.975332–3.267137 | 1052.944–1140.620 | 1.0833 |
| dev/n4096_q32_v1000_member_zipf | zlib-compact | 3.011514–3.253646 | 1073.093–1156.316 | 1.0776 |
| dev/n4096_q32_v1000_member_zipf | zlib-dictionary | 2.036780–2.212110 | 716.949–943.746 | 1.3163 |
| dev/n4096_q32_v1000_member_zipf | reset-zlib-ordinary | 2.809811–3.093720 | 1023.328–1090.212 | 1.0654 |
| dev/n4096_q32_v1000_member_zipf | reset-zlib-compact | 2.934110–3.107648 | 1019.232–1100.107 | 1.0793 |
| dev/n4096_q32_v1000_member_zipf | reset-zlib-dictionary | 1.868912–1.968413 | 651.487–895.884 | 1.3751 |
| dev/n4096_q32_v32_member_uniform | ordinary | 1.000000–1.000000 | 268.188–302.049 | 1.1263 |
| dev/n4096_q32_v32_member_uniform | compact | 1.089344–1.147888 | 308.401–336.319 | 1.0905 |
| dev/n4096_q32_v32_member_uniform | dictionary | 1.146004–1.198793 | 322.796–358.879 | 1.1118 |
| dev/n4096_q32_v32_member_uniform | zlib-ordinary | 2.313310–2.422413 | 649.761–722.467 | 1.1119 |
| dev/n4096_q32_v32_member_uniform | zlib-compact | 2.425984–2.501794 | 686.265–755.001 | 1.1002 |
| dev/n4096_q32_v32_member_uniform | zlib-dictionary | 2.243705–2.297255 | 622.001–709.924 | 1.1414 |
| dev/n4096_q32_v32_member_uniform | reset-zlib-ordinary | 2.051778–2.122473 | 568.873–638.122 | 1.1217 |
| dev/n4096_q32_v32_member_uniform | reset-zlib-compact | 2.128599–2.292646 | 603.110–668.756 | 1.1088 |
| dev/n4096_q32_v32_member_uniform | reset-zlib-dictionary | 1.931933–1.967698 | 524.395–595.167 | 1.1350 |
| dev/n4096_q32_v32_member_zipf | ordinary | 1.000000–1.000000 | 273.180–302.337 | 1.1067 |
| dev/n4096_q32_v32_member_zipf | compact | 1.093827–1.131326 | 310.115–340.142 | 1.0968 |
| dev/n4096_q32_v32_member_zipf | dictionary | 1.108550–1.179509 | 315.772–338.366 | 1.0716 |
| dev/n4096_q32_v32_member_zipf | zlib-ordinary | 2.277691–2.401094 | 643.580–693.216 | 1.0771 |
| dev/n4096_q32_v32_member_zipf | zlib-compact | 2.354193–2.506497 | 678.706–738.279 | 1.0878 |
| dev/n4096_q32_v32_member_zipf | zlib-dictionary | 2.251248–2.357675 | 623.942–681.263 | 1.0919 |
| dev/n4096_q32_v32_member_zipf | reset-zlib-ordinary | 1.961710–2.116146 | 568.231–637.068 | 1.1211 |
| dev/n4096_q32_v32_member_zipf | reset-zlib-compact | 2.047281–2.243309 | 591.223–672.330 | 1.1372 |
| dev/n4096_q32_v32_member_zipf | reset-zlib-dictionary | 1.814647–1.981434 | 533.961–571.197 | 1.0697 |
| dev/n4096_q8_v1000_member_uniform | ordinary | 1.000000–1.000000 | 82.126–93.330 | 1.1364 |
| dev/n4096_q8_v1000_member_uniform | compact | 1.083043–1.140701 | 90.020–102.625 | 1.1400 |
| dev/n4096_q8_v1000_member_uniform | dictionary | 1.154438–1.236992 | 97.164–111.554 | 1.1481 |
| dev/n4096_q8_v1000_member_uniform | zlib-ordinary | 3.729229–4.336155 | 294.538–417.953 | 1.4190 |
| dev/n4096_q8_v1000_member_uniform | zlib-compact | 2.982362–3.462263 | 258.109–308.507 | 1.1953 |
| dev/n4096_q8_v1000_member_uniform | zlib-dictionary | 3.550801–4.125644 | 305.037–365.910 | 1.1996 |
| dev/n4096_q8_v1000_member_uniform | reset-zlib-ordinary | 2.725157–3.145514 | 234.587–303.254 | 1.2927 |
| dev/n4096_q8_v1000_member_uniform | reset-zlib-compact | 1.879096–2.074994 | 162.203–186.633 | 1.1506 |
| dev/n4096_q8_v1000_member_uniform | reset-zlib-dictionary | 2.516262–2.734607 | 214.783–242.430 | 1.1287 |
| dev/n4096_q8_v1000_member_zipf | ordinary | 1.000000–1.000000 | 75.063–88.392 | 1.1776 |
| dev/n4096_q8_v1000_member_zipf | compact | 1.134143–1.185515 | 86.864–100.977 | 1.1625 |
| dev/n4096_q8_v1000_member_zipf | dictionary | 1.167418–1.248081 | 90.854–110.368 | 1.2148 |
| dev/n4096_q8_v1000_member_zipf | zlib-ordinary | 4.216232–4.998221 | 339.438–412.624 | 1.2156 |
| dev/n4096_q8_v1000_member_zipf | zlib-compact | 3.021555–3.686397 | 230.320–322.739 | 1.4013 |
| dev/n4096_q8_v1000_member_zipf | zlib-dictionary | 3.826740–4.276289 | 296.107–348.429 | 1.1767 |
| dev/n4096_q8_v1000_member_zipf | reset-zlib-ordinary | 2.242356–2.640744 | 171.832–226.329 | 1.3172 |
| dev/n4096_q8_v1000_member_zipf | reset-zlib-compact | 1.688664–1.854521 | 125.263–163.951 | 1.3089 |
| dev/n4096_q8_v1000_member_zipf | reset-zlib-dictionary | 2.280143–2.520160 | 179.987–218.409 | 1.2135 |
| dev/n4096_q8_v32_member_uniform | ordinary | 1.000000–1.000000 | 64.679–76.916 | 1.1892 |
| dev/n4096_q8_v32_member_uniform | compact | 1.146308–1.168355 | 74.375–90.448 | 1.2161 |
| dev/n4096_q8_v32_member_uniform | dictionary | 1.202602–1.301490 | 81.511–95.327 | 1.1695 |
| dev/n4096_q8_v32_member_uniform | zlib-ordinary | 4.600928–5.617675 | 284.638–390.488 | 1.3719 |
| dev/n4096_q8_v32_member_uniform | zlib-compact | 4.708925–5.803179 | 319.805–394.258 | 1.2328 |
| dev/n4096_q8_v32_member_uniform | zlib-dictionary | 4.098858–5.025796 | 267.676–354.047 | 1.3227 |
| dev/n4096_q8_v32_member_uniform | reset-zlib-ordinary | 2.851095–3.066041 | 183.572–227.027 | 1.2367 |
| dev/n4096_q8_v32_member_uniform | reset-zlib-compact | 2.818445–2.937808 | 182.214–228.386 | 1.2534 |
| dev/n4096_q8_v32_member_uniform | reset-zlib-dictionary | 2.392761–2.447963 | 154.844–180.145 | 1.1634 |
| dev/n4096_q8_v32_member_zipf | ordinary | 1.000000–1.000000 | 67.551–75.115 | 1.1120 |
| dev/n4096_q8_v32_member_zipf | compact | 1.116137–1.216096 | 76.972–86.363 | 1.1220 |
| dev/n4096_q8_v32_member_zipf | dictionary | 1.225690–1.264452 | 85.048–94.049 | 1.1058 |
| dev/n4096_q8_v32_member_zipf | zlib-ordinary | 4.206975–4.594294 | 281.540–361.773 | 1.2850 |
| dev/n4096_q8_v32_member_zipf | zlib-compact | 4.405642–4.723267 | 290.698–350.219 | 1.2048 |
| dev/n4096_q8_v32_member_zipf | zlib-dictionary | 3.796815–4.077657 | 255.400–327.984 | 1.2842 |
| dev/n4096_q8_v32_member_zipf | reset-zlib-ordinary | 2.795424–3.154253 | 195.049–239.007 | 1.2254 |
| dev/n4096_q8_v32_member_zipf | reset-zlib-compact | 2.857592–3.299506 | 199.488–244.666 | 1.2265 |
| dev/n4096_q8_v32_member_zipf | reset-zlib-dictionary | 2.265972–2.447939 | 165.373–188.105 | 1.1375 |

## Frozen corpus: every process-level cell summary

| Domain/cell | Mode | Paired total ratio range | Absolute median us range | Max/min |
|---|---|---:|---:|---:|
| confirm/n16384_q128_absent_clustered | compact | 1.200387–1.234751 | 678.655–791.611 | 1.1664 |
| confirm/n16384_q128_absent_clustered | dictionary | 1.161421–1.237908 | 646.988–773.004 | 1.1948 |
| confirm/n16384_q128_absent_clustered | ordinary | 1.000000–1.000000 | 551.144–707.500 | 1.2837 |
| confirm/n16384_q128_absent_clustered | reset-zlib-compact | 2.852237–2.973410 | 1632.034–2108.829 | 1.2921 |
| confirm/n16384_q128_absent_clustered | reset-zlib-dictionary | 2.164155–2.291924 | 1242.373–1504.398 | 1.2109 |
| confirm/n16384_q128_absent_clustered | reset-zlib-ordinary | 2.633546–2.732496 | 1493.096–1776.188 | 1.1896 |
| confirm/n16384_q128_absent_clustered | zlib-compact | 2.955049–3.264375 | 1695.055–2053.907 | 1.2117 |
| confirm/n16384_q128_absent_clustered | zlib-dictionary | 2.310311–2.486305 | 1307.255–1794.293 | 1.3726 |
| confirm/n16384_q128_absent_clustered | zlib-ordinary | 2.805442–3.124786 | 1611.233–2082.722 | 1.2926 |
| confirm/n16384_q128_absent_dispersed | compact | 1.212815–1.256556 | 702.854–809.229 | 1.1513 |
| confirm/n16384_q128_absent_dispersed | dictionary | 1.234569–1.303229 | 739.699–866.694 | 1.1717 |
| confirm/n16384_q128_absent_dispersed | ordinary | 1.000000–1.000000 | 575.645–689.314 | 1.1975 |
| confirm/n16384_q128_absent_dispersed | reset-zlib-compact | 3.327823–3.639699 | 2004.365–2339.973 | 1.1674 |
| confirm/n16384_q128_absent_dispersed | reset-zlib-dictionary | 2.269905–2.422699 | 1416.562–1610.911 | 1.1372 |
| confirm/n16384_q128_absent_dispersed | reset-zlib-ordinary | 3.150953–3.293190 | 1854.675–2195.027 | 1.1835 |
| confirm/n16384_q128_absent_dispersed | zlib-compact | 3.470225–3.658479 | 2014.785–2384.147 | 1.1833 |
| confirm/n16384_q128_absent_dispersed | zlib-dictionary | 2.480606–2.736710 | 1476.502–1873.593 | 1.2689 |
| confirm/n16384_q128_absent_dispersed | zlib-ordinary | 3.157550–3.431474 | 1919.042–2360.553 | 1.2301 |
| confirm/n16384_q128_member_clustered | compact | 1.199085–1.249929 | 748.049–910.972 | 1.2178 |
| confirm/n16384_q128_member_clustered | dictionary | 1.144079–1.202773 | 736.626–809.178 | 1.0985 |
| confirm/n16384_q128_member_clustered | ordinary | 1.000000–1.000000 | 607.172–721.232 | 1.1879 |
| confirm/n16384_q128_member_clustered | reset-zlib-compact | 2.776546–2.903287 | 1741.378–2042.801 | 1.1731 |
| confirm/n16384_q128_member_clustered | reset-zlib-dictionary | 2.005895–2.112044 | 1227.919–1512.426 | 1.2317 |
| confirm/n16384_q128_member_clustered | reset-zlib-ordinary | 2.481179–2.565314 | 1616.236–1762.761 | 1.0907 |
| confirm/n16384_q128_member_clustered | zlib-compact | 2.830766–3.026865 | 1801.772–2109.788 | 1.1710 |
| confirm/n16384_q128_member_clustered | zlib-dictionary | 2.205172–2.438636 | 1380.506–1714.810 | 1.2422 |
| confirm/n16384_q128_member_clustered | zlib-ordinary | 2.570030–2.727584 | 1683.027–2151.270 | 1.2782 |
| confirm/n16384_q128_member_dispersed | compact | 1.196500–1.225555 | 772.255–963.566 | 1.2477 |
| confirm/n16384_q128_member_dispersed | dictionary | 1.276228–1.338910 | 836.558–1040.712 | 1.2440 |
| confirm/n16384_q128_member_dispersed | ordinary | 1.000000–1.000000 | 645.985–747.095 | 1.1565 |
| confirm/n16384_q128_member_dispersed | reset-zlib-compact | 3.143510–3.356029 | 2114.338–2466.321 | 1.1665 |
| confirm/n16384_q128_member_dispersed | reset-zlib-dictionary | 2.255899–2.420089 | 1517.322–1818.360 | 1.1984 |
| confirm/n16384_q128_member_dispersed | reset-zlib-ordinary | 2.985207–3.078566 | 1954.523–2306.497 | 1.1801 |
| confirm/n16384_q128_member_dispersed | zlib-compact | 3.347275–3.435168 | 2212.548–2620.570 | 1.1844 |
| confirm/n16384_q128_member_dispersed | zlib-dictionary | 2.471132–2.820421 | 1632.780–2250.225 | 1.3782 |
| confirm/n16384_q128_member_dispersed | zlib-ordinary | 2.992385–3.269771 | 1989.570–2377.308 | 1.1949 |
| confirm/n16384_q1_absent_clustered | compact | 1.193173–1.363561 | 7.536–10.191 | 1.3523 |
| confirm/n16384_q1_absent_clustered | dictionary | 1.395737–1.509217 | 8.660–11.222 | 1.2958 |
| confirm/n16384_q1_absent_clustered | ordinary | 1.000000–1.000000 | 6.036–7.551 | 1.2510 |
| confirm/n16384_q1_absent_clustered | reset-zlib-compact | 7.628995–7.861855 | 46.182–59.484 | 1.2880 |
| confirm/n16384_q1_absent_clustered | reset-zlib-dictionary | 2.990295–3.620945 | 17.682–27.412 | 1.5503 |
| confirm/n16384_q1_absent_clustered | reset-zlib-ordinary | 2.507358–3.035710 | 14.507–24.086 | 1.6603 |
| confirm/n16384_q1_absent_clustered | zlib-compact | 15.890140–20.878471 | 90.629–150.833 | 1.6643 |
| confirm/n16384_q1_absent_clustered | zlib-dictionary | 10.052140–16.958501 | 57.287–130.721 | 2.2819 |
| confirm/n16384_q1_absent_clustered | zlib-ordinary | 9.761210–13.728699 | 56.216–115.165 | 2.0486 |
| confirm/n16384_q1_absent_dispersed | compact | 1.232816–1.308408 | 7.407–11.650 | 1.5728 |
| confirm/n16384_q1_absent_dispersed | dictionary | 1.370948–1.562639 | 8.853–13.750 | 1.5531 |
| confirm/n16384_q1_absent_dispersed | ordinary | 1.000000–1.000000 | 5.952–9.183 | 1.5428 |
| confirm/n16384_q1_absent_dispersed | reset-zlib-compact | 7.625721–8.075045 | 45.872–69.304 | 1.5108 |
| confirm/n16384_q1_absent_dispersed | reset-zlib-dictionary | 2.792587–3.721732 | 16.626–32.297 | 1.9426 |
| confirm/n16384_q1_absent_dispersed | reset-zlib-ordinary | 2.282011–3.128443 | 14.079–28.197 | 2.0028 |
| confirm/n16384_q1_absent_dispersed | zlib-compact | 16.368005–21.629307 | 97.481–187.294 | 1.9213 |
| confirm/n16384_q1_absent_dispersed | zlib-dictionary | 10.872642–18.922895 | 63.066–141.591 | 2.2451 |
| confirm/n16384_q1_absent_dispersed | zlib-ordinary | 10.734432–18.069362 | 58.517–152.869 | 2.6124 |
| confirm/n16384_q1_member_clustered | compact | 1.199325–1.320939 | 8.162–10.339 | 1.2667 |
| confirm/n16384_q1_member_clustered | dictionary | 1.376656–1.512935 | 9.292–12.747 | 1.3718 |
| confirm/n16384_q1_member_clustered | ordinary | 1.000000–1.000000 | 6.574–8.719 | 1.3263 |
| confirm/n16384_q1_member_clustered | reset-zlib-compact | 2.492244–3.513287 | 16.961–28.443 | 1.6770 |
| confirm/n16384_q1_member_clustered | reset-zlib-dictionary | 3.370805–4.324233 | 23.050–33.269 | 1.4433 |
| confirm/n16384_q1_member_clustered | reset-zlib-ordinary | 2.696703–3.636869 | 19.221–29.258 | 1.5222 |
| confirm/n16384_q1_member_clustered | zlib-compact | 10.295173–16.286433 | 63.778–130.968 | 2.0535 |
| confirm/n16384_q1_member_clustered | zlib-dictionary | 12.472853–17.963098 | 83.182–138.600 | 1.6662 |
| confirm/n16384_q1_member_clustered | zlib-ordinary | 11.517078–18.653465 | 98.807–141.501 | 1.4321 |
| confirm/n16384_q1_member_dispersed | compact | 1.122347–1.250104 | 9.163–12.038 | 1.3138 |
| confirm/n16384_q1_member_dispersed | dictionary | 1.316111–1.453530 | 10.871–14.187 | 1.3050 |
| confirm/n16384_q1_member_dispersed | ordinary | 1.000000–1.000000 | 7.469–9.484 | 1.2698 |
| confirm/n16384_q1_member_dispersed | reset-zlib-compact | 2.345673–2.910851 | 17.845–28.866 | 1.6176 |
| confirm/n16384_q1_member_dispersed | reset-zlib-dictionary | 5.017093–6.146965 | 51.479–60.540 | 1.1760 |
| confirm/n16384_q1_member_dispersed | reset-zlib-ordinary | 5.427277–6.853699 | 54.436–63.759 | 1.1713 |
| confirm/n16384_q1_member_dispersed | zlib-compact | 9.372458–13.323718 | 64.520–131.620 | 2.0400 |
| confirm/n16384_q1_member_dispersed | zlib-dictionary | 12.180649–15.244566 | 95.887–150.683 | 1.5715 |
| confirm/n16384_q1_member_dispersed | zlib-ordinary | 12.736733–17.563701 | 110.313–159.027 | 1.4416 |
| confirm/n16384_q32_absent_clustered | compact | 1.218372–1.255826 | 176.432–217.744 | 1.2342 |
| confirm/n16384_q32_absent_clustered | dictionary | 1.214471–1.282583 | 176.707–207.836 | 1.1762 |
| confirm/n16384_q32_absent_clustered | ordinary | 1.000000–1.000000 | 146.083–173.031 | 1.1845 |
| confirm/n16384_q32_absent_clustered | reset-zlib-compact | 3.225775–3.569242 | 443.246–628.080 | 1.4170 |
| confirm/n16384_q32_absent_clustered | reset-zlib-dictionary | 2.578260–2.715414 | 367.584–466.877 | 1.2701 |
| confirm/n16384_q32_absent_clustered | reset-zlib-ordinary | 2.987176–3.307956 | 425.765–599.412 | 1.4078 |
| confirm/n16384_q32_absent_clustered | zlib-compact | 3.507819–3.946113 | 511.077–675.836 | 1.3224 |
| confirm/n16384_q32_absent_clustered | zlib-dictionary | 2.870900–3.876335 | 431.222–576.658 | 1.3373 |
| confirm/n16384_q32_absent_clustered | zlib-ordinary | 3.293923–3.480980 | 485.089–576.765 | 1.1890 |
| confirm/n16384_q32_absent_dispersed | compact | 1.217359–1.277406 | 179.949–204.682 | 1.1374 |
| confirm/n16384_q32_absent_dispersed | dictionary | 1.309130–1.351096 | 197.275–217.947 | 1.1048 |
| confirm/n16384_q32_absent_dispersed | ordinary | 1.000000–1.000000 | 146.980–165.964 | 1.1292 |
| confirm/n16384_q32_absent_dispersed | reset-zlib-compact | 3.626563–4.106583 | 547.076–682.362 | 1.2473 |
| confirm/n16384_q32_absent_dispersed | reset-zlib-dictionary | 3.006442–3.155485 | 456.646–515.143 | 1.1281 |
| confirm/n16384_q32_absent_dispersed | reset-zlib-ordinary | 3.295353–3.601054 | 505.795–617.667 | 1.2212 |
| confirm/n16384_q32_absent_dispersed | zlib-compact | 3.907763–4.128599 | 640.480–788.470 | 1.2311 |
| confirm/n16384_q32_absent_dispersed | zlib-dictionary | 3.320052–3.512609 | 562.736–669.476 | 1.1897 |
| confirm/n16384_q32_absent_dispersed | zlib-ordinary | 3.583354–3.964648 | 612.400–664.354 | 1.0848 |
| confirm/n16384_q32_member_clustered | compact | 1.202060–1.238183 | 190.999–225.252 | 1.1793 |
| confirm/n16384_q32_member_clustered | dictionary | 1.217601–1.295505 | 205.111–225.540 | 1.0996 |
| confirm/n16384_q32_member_clustered | ordinary | 1.000000–1.000000 | 161.108–186.351 | 1.1567 |
| confirm/n16384_q32_member_clustered | reset-zlib-compact | 2.975839–3.288796 | 480.076–628.029 | 1.3082 |
| confirm/n16384_q32_member_clustered | reset-zlib-dictionary | 2.524181–2.684647 | 410.573–486.203 | 1.1842 |
| confirm/n16384_q32_member_clustered | reset-zlib-ordinary | 2.815748–3.111391 | 454.750–573.287 | 1.2607 |
| confirm/n16384_q32_member_clustered | zlib-compact | 3.293527–3.657469 | 526.064–663.668 | 1.2616 |
| confirm/n16384_q32_member_clustered | zlib-dictionary | 2.784473–3.041616 | 454.148–552.182 | 1.2159 |
| confirm/n16384_q32_member_clustered | zlib-ordinary | 2.952334–3.661093 | 479.110–636.921 | 1.3294 |
| confirm/n16384_q32_member_dispersed | compact | 1.211895–1.288024 | 204.999–235.069 | 1.1467 |
| confirm/n16384_q32_member_dispersed | dictionary | 1.277621–1.352188 | 223.219–256.798 | 1.1504 |
| confirm/n16384_q32_member_dispersed | ordinary | 1.000000–1.000000 | 168.315–194.252 | 1.1541 |
| confirm/n16384_q32_member_dispersed | reset-zlib-compact | 3.256594–3.577241 | 549.235–694.957 | 1.2653 |
| confirm/n16384_q32_member_dispersed | reset-zlib-dictionary | 2.826698–3.060015 | 486.204–602.656 | 1.2395 |
| confirm/n16384_q32_member_dispersed | reset-zlib-ordinary | 3.070622–3.453039 | 519.474–693.269 | 1.3346 |
| confirm/n16384_q32_member_dispersed | zlib-compact | 3.462491–3.695379 | 596.892–756.061 | 1.2667 |
| confirm/n16384_q32_member_dispersed | zlib-dictionary | 3.059496–3.451000 | 525.261–655.017 | 1.2470 |
| confirm/n16384_q32_member_dispersed | zlib-ordinary | 3.306754–3.583894 | 565.195–760.726 | 1.3460 |
| confirm/n16384_q8_absent_clustered | compact | 1.204861–1.264630 | 44.955–58.383 | 1.2987 |
| confirm/n16384_q8_absent_clustered | dictionary | 1.281902–1.348222 | 49.655–62.287 | 1.2544 |
| confirm/n16384_q8_absent_clustered | ordinary | 1.000000–1.000000 | 36.932–48.687 | 1.3183 |
| confirm/n16384_q8_absent_clustered | reset-zlib-compact | 4.455333–4.571735 | 168.930–222.284 | 1.3158 |
| confirm/n16384_q8_absent_clustered | reset-zlib-dictionary | 3.896838–4.108175 | 149.859–189.287 | 1.2631 |
| confirm/n16384_q8_absent_clustered | reset-zlib-ordinary | 4.176231–4.477468 | 157.368–208.952 | 1.3278 |
| confirm/n16384_q8_absent_clustered | zlib-compact | 5.584478–6.065428 | 204.745–285.720 | 1.3955 |
| confirm/n16384_q8_absent_clustered | zlib-dictionary | 5.194183–5.733215 | 192.723–277.327 | 1.4390 |
| confirm/n16384_q8_absent_clustered | zlib-ordinary | 5.210191–5.719611 | 196.731–278.631 | 1.4163 |
| confirm/n16384_q8_absent_dispersed | compact | 1.221506–1.312110 | 47.438–67.020 | 1.4128 |
| confirm/n16384_q8_absent_dispersed | dictionary | 1.321882–1.392675 | 54.233–65.917 | 1.2154 |
| confirm/n16384_q8_absent_dispersed | ordinary | 1.000000–1.000000 | 39.237–51.195 | 1.3048 |
| confirm/n16384_q8_absent_dispersed | reset-zlib-compact | 4.653382–5.072737 | 181.462–254.641 | 1.4033 |
| confirm/n16384_q8_absent_dispersed | reset-zlib-dictionary | 3.256788–3.438026 | 126.821–183.264 | 1.4451 |
| confirm/n16384_q8_absent_dispersed | reset-zlib-ordinary | 4.116681–4.626493 | 167.207–220.670 | 1.3197 |
| confirm/n16384_q8_absent_dispersed | zlib-compact | 5.726772–6.538606 | 231.021–353.047 | 1.5282 |
| confirm/n16384_q8_absent_dispersed | zlib-dictionary | 4.430524–5.107030 | 175.897–274.529 | 1.5607 |
| confirm/n16384_q8_absent_dispersed | zlib-ordinary | 5.365227–5.771991 | 215.649–324.204 | 1.5034 |
| confirm/n16384_q8_member_clustered | compact | 1.181335–1.232122 | 53.293–70.473 | 1.3224 |
| confirm/n16384_q8_member_clustered | dictionary | 1.263982–1.318149 | 58.224–73.405 | 1.2607 |
| confirm/n16384_q8_member_clustered | ordinary | 1.000000–1.000000 | 44.016–58.781 | 1.3354 |
| confirm/n16384_q8_member_clustered | reset-zlib-compact | 4.007840–4.267525 | 181.176–236.724 | 1.3066 |
| confirm/n16384_q8_member_clustered | reset-zlib-dictionary | 3.559064–3.743329 | 168.561–203.487 | 1.2072 |
| confirm/n16384_q8_member_clustered | reset-zlib-ordinary | 3.918067–4.208661 | 172.754–234.221 | 1.3558 |
| confirm/n16384_q8_member_clustered | zlib-compact | 4.996077–5.688220 | 219.182–332.226 | 1.5158 |
| confirm/n16384_q8_member_clustered | zlib-dictionary | 4.701802–5.218160 | 212.882–340.781 | 1.6008 |
| confirm/n16384_q8_member_clustered | zlib-ordinary | 4.838971–5.380000 | 218.248–337.078 | 1.5445 |
| confirm/n16384_q8_member_dispersed | compact | 1.170446–1.241199 | 53.005–67.928 | 1.2815 |
| confirm/n16384_q8_member_dispersed | dictionary | 1.283507–1.359947 | 59.744–72.370 | 1.2113 |
| confirm/n16384_q8_member_dispersed | ordinary | 1.000000–1.000000 | 44.221–56.030 | 1.2670 |
| confirm/n16384_q8_member_dispersed | reset-zlib-compact | 3.954598–4.149837 | 185.981–239.433 | 1.2874 |
| confirm/n16384_q8_member_dispersed | reset-zlib-dictionary | 2.906628–3.094777 | 137.662–177.394 | 1.2886 |
| confirm/n16384_q8_member_dispersed | reset-zlib-ordinary | 3.973836–4.212688 | 191.694–244.745 | 1.2767 |
| confirm/n16384_q8_member_dispersed | zlib-compact | 5.169491–5.717651 | 234.432–330.150 | 1.4083 |
| confirm/n16384_q8_member_dispersed | zlib-dictionary | 4.033374–4.981928 | 184.863–261.248 | 1.4132 |
| confirm/n16384_q8_member_dispersed | zlib-ordinary | 5.124959–5.403618 | 232.463–307.489 | 1.3227 |
| confirm/n4096_q128_absent_clustered | compact | 1.201524–1.256105 | 596.676–710.743 | 1.1912 |
| confirm/n4096_q128_absent_clustered | dictionary | 1.161609–1.198842 | 566.488–659.564 | 1.1643 |
| confirm/n4096_q128_absent_clustered | ordinary | 1.000000–1.000000 | 473.234–578.579 | 1.2226 |
| confirm/n4096_q128_absent_clustered | reset-zlib-compact | 2.664755–2.756532 | 1324.232–1543.763 | 1.1658 |
| confirm/n4096_q128_absent_clustered | reset-zlib-dictionary | 2.148843–2.231548 | 1043.365–1205.149 | 1.1551 |
| confirm/n4096_q128_absent_clustered | reset-zlib-ordinary | 2.426432–2.531701 | 1177.675–1430.039 | 1.2143 |
| confirm/n4096_q128_absent_clustered | zlib-compact | 2.793520–3.053411 | 1382.295–1636.399 | 1.1838 |
| confirm/n4096_q128_absent_clustered | zlib-dictionary | 2.216597–2.560359 | 1122.162–1343.373 | 1.1971 |
| confirm/n4096_q128_absent_clustered | zlib-ordinary | 2.514943–2.874751 | 1255.945–1535.697 | 1.2227 |
| confirm/n4096_q128_absent_dispersed | compact | 1.209949–1.294850 | 618.710–723.728 | 1.1697 |
| confirm/n4096_q128_absent_dispersed | dictionary | 1.237530–1.291269 | 637.169–684.246 | 1.0739 |
| confirm/n4096_q128_absent_dispersed | ordinary | 1.000000–1.000000 | 508.763–540.831 | 1.0630 |
| confirm/n4096_q128_absent_dispersed | reset-zlib-compact | 3.373392–3.589748 | 1699.205–1936.504 | 1.1397 |
| confirm/n4096_q128_absent_dispersed | reset-zlib-dictionary | 2.468103–2.692265 | 1213.882–1418.886 | 1.1689 |
| confirm/n4096_q128_absent_dispersed | reset-zlib-ordinary | 3.180685–3.304326 | 1636.375–1817.480 | 1.1107 |
| confirm/n4096_q128_absent_dispersed | zlib-compact | 3.529897–4.136972 | 1769.984–2143.321 | 1.2109 |
| confirm/n4096_q128_absent_dispersed | zlib-dictionary | 2.614230–2.840632 | 1373.861–1604.406 | 1.1678 |
| confirm/n4096_q128_absent_dispersed | zlib-ordinary | 3.333997–3.577724 | 1675.337–1949.619 | 1.1637 |
| confirm/n4096_q128_member_clustered | compact | 1.194543–1.222853 | 651.630–760.277 | 1.1667 |
| confirm/n4096_q128_member_clustered | dictionary | 1.165673–1.207227 | 673.909–744.252 | 1.1044 |
| confirm/n4096_q128_member_clustered | ordinary | 1.000000–1.000000 | 541.870–616.160 | 1.1371 |
| confirm/n4096_q128_member_clustered | reset-zlib-compact | 2.534139–2.657381 | 1369.190–1688.843 | 1.2335 |
| confirm/n4096_q128_member_clustered | reset-zlib-dictionary | 2.023921–2.109704 | 1121.149–1334.415 | 1.1902 |
| confirm/n4096_q128_member_clustered | reset-zlib-ordinary | 2.348714–2.476977 | 1276.297–1547.078 | 1.2122 |
| confirm/n4096_q128_member_clustered | zlib-compact | 2.673560–2.867782 | 1499.939–1829.590 | 1.2198 |
| confirm/n4096_q128_member_clustered | zlib-dictionary | 2.208072–2.325748 | 1188.536–1572.167 | 1.3228 |
| confirm/n4096_q128_member_clustered | zlib-ordinary | 2.466722–2.651547 | 1398.992–1660.453 | 1.1869 |
| confirm/n4096_q128_member_dispersed | compact | 1.194366–1.225815 | 677.252–748.904 | 1.1058 |
| confirm/n4096_q128_member_dispersed | dictionary | 1.264219–1.284508 | 697.587–798.893 | 1.1452 |
| confirm/n4096_q128_member_dispersed | ordinary | 1.000000–1.000000 | 551.846–612.564 | 1.1100 |
| confirm/n4096_q128_member_dispersed | reset-zlib-compact | 3.016940–3.184080 | 1709.933–1930.718 | 1.1291 |
| confirm/n4096_q128_member_dispersed | reset-zlib-dictionary | 2.265219–2.349572 | 1287.733–1429.966 | 1.1105 |
| confirm/n4096_q128_member_dispersed | reset-zlib-ordinary | 2.852679–2.982513 | 1595.736–1810.852 | 1.1348 |
| confirm/n4096_q128_member_dispersed | zlib-compact | 3.263657–3.509099 | 1832.367–2173.390 | 1.1861 |
| confirm/n4096_q128_member_dispersed | zlib-dictionary | 2.373644–2.866325 | 1362.401–1955.495 | 1.4353 |
| confirm/n4096_q128_member_dispersed | zlib-ordinary | 2.896783–3.100100 | 1623.742–1905.136 | 1.1733 |
| confirm/n4096_q1_absent_clustered | compact | 1.202723–1.387844 | 7.228–8.725 | 1.2071 |
| confirm/n4096_q1_absent_clustered | dictionary | 1.367475–1.491997 | 8.100–9.796 | 1.2094 |
| confirm/n4096_q1_absent_clustered | ordinary | 1.000000–1.000000 | 5.670–6.896 | 1.2162 |
| confirm/n4096_q1_absent_clustered | reset-zlib-compact | 7.539578–8.789482 | 44.387–56.127 | 1.2645 |
| confirm/n4096_q1_absent_clustered | reset-zlib-dictionary | 3.547925–4.898258 | 24.767–32.195 | 1.2999 |
| confirm/n4096_q1_absent_clustered | reset-zlib-ordinary | 2.364787–3.131737 | 14.073–23.014 | 1.6353 |
| confirm/n4096_q1_absent_clustered | zlib-compact | 18.132578–25.890050 | 107.656–157.440 | 1.4624 |
| confirm/n4096_q1_absent_clustered | zlib-dictionary | 12.854970–19.389530 | 85.489–139.942 | 1.6370 |
| confirm/n4096_q1_absent_clustered | zlib-ordinary | 10.923164–18.641436 | 63.792–126.900 | 1.9893 |
| confirm/n4096_q1_absent_dispersed | compact | 1.130920–1.324520 | 7.453–9.857 | 1.3226 |
| confirm/n4096_q1_absent_dispersed | dictionary | 1.335415–1.523143 | 8.493–10.983 | 1.2932 |
| confirm/n4096_q1_absent_dispersed | ordinary | 1.000000–1.000000 | 6.121–7.697 | 1.2575 |
| confirm/n4096_q1_absent_dispersed | reset-zlib-compact | 6.386707–7.039877 | 43.031–53.182 | 1.2359 |
| confirm/n4096_q1_absent_dispersed | reset-zlib-dictionary | 3.477261–4.366450 | 23.154–33.993 | 1.4681 |
| confirm/n4096_q1_absent_dispersed | reset-zlib-ordinary | 2.788065–3.801529 | 18.395–28.302 | 1.5386 |
| confirm/n4096_q1_absent_dispersed | zlib-compact | 15.311507–20.056086 | 86.103–147.984 | 1.7187 |
| confirm/n4096_q1_absent_dispersed | zlib-dictionary | 13.194932–18.734006 | 83.851–137.107 | 1.6351 |
| confirm/n4096_q1_absent_dispersed | zlib-ordinary | 11.640016–19.793071 | 75.490–144.418 | 1.9131 |
| confirm/n4096_q1_member_clustered | compact | 1.209033–1.302451 | 8.081–9.922 | 1.2278 |
| confirm/n4096_q1_member_clustered | dictionary | 1.353028–1.471139 | 8.880–11.053 | 1.2447 |
| confirm/n4096_q1_member_clustered | ordinary | 1.000000–1.000000 | 6.528–7.947 | 1.2174 |
| confirm/n4096_q1_member_clustered | reset-zlib-compact | 2.535532–3.391862 | 18.046–26.585 | 1.4732 |
| confirm/n4096_q1_member_clustered | reset-zlib-dictionary | 3.058274–4.596663 | 22.129–34.329 | 1.5513 |
| confirm/n4096_q1_member_clustered | reset-zlib-ordinary | 2.456041–3.677112 | 17.204–28.407 | 1.6512 |
| confirm/n4096_q1_member_clustered | zlib-compact | 9.921078–16.693376 | 59.374–131.967 | 2.2226 |
| confirm/n4096_q1_member_clustered | zlib-dictionary | 12.074276–19.516978 | 85.431–155.950 | 1.8254 |
| confirm/n4096_q1_member_clustered | zlib-ordinary | 11.961034–21.476502 | 95.349–168.216 | 1.7642 |
| confirm/n4096_q1_member_dispersed | compact | 1.203866–1.328508 | 7.758–9.515 | 1.2265 |
| confirm/n4096_q1_member_dispersed | dictionary | 1.231887–1.442148 | 8.659–9.918 | 1.1454 |
| confirm/n4096_q1_member_dispersed | ordinary | 1.000000–1.000000 | 6.342–7.726 | 1.2182 |
| confirm/n4096_q1_member_dispersed | reset-zlib-compact | 2.647362–3.045933 | 15.755–23.311 | 1.4796 |
| confirm/n4096_q1_member_dispersed | reset-zlib-dictionary | 2.680428–3.443810 | 16.185–25.356 | 1.5666 |
| confirm/n4096_q1_member_dispersed | reset-zlib-ordinary | 2.396273–2.879507 | 14.292–22.491 | 1.5737 |
| confirm/n4096_q1_member_dispersed | zlib-compact | 10.350861–16.525725 | 59.980–120.734 | 2.0129 |
| confirm/n4096_q1_member_dispersed | zlib-dictionary | 10.528689–16.909950 | 58.216–119.061 | 2.0452 |
| confirm/n4096_q1_member_dispersed | zlib-ordinary | 9.707645–17.902484 | 56.754–114.874 | 2.0241 |
| confirm/n4096_q32_absent_clustered | compact | 1.221746–1.269017 | 155.743–182.206 | 1.1699 |
| confirm/n4096_q32_absent_clustered | dictionary | 1.223551–1.258893 | 156.754–180.279 | 1.1501 |
| confirm/n4096_q32_absent_clustered | ordinary | 1.000000–1.000000 | 123.878–150.327 | 1.2135 |
| confirm/n4096_q32_absent_clustered | reset-zlib-compact | 3.195308–3.303676 | 406.720–480.693 | 1.1819 |
| confirm/n4096_q32_absent_clustered | reset-zlib-dictionary | 2.556612–2.738462 | 332.015–417.797 | 1.2584 |
| confirm/n4096_q32_absent_clustered | reset-zlib-ordinary | 2.944393–3.203532 | 368.358–459.649 | 1.2478 |
| confirm/n4096_q32_absent_clustered | zlib-compact | 3.485679–3.824304 | 431.103–622.137 | 1.4431 |
| confirm/n4096_q32_absent_clustered | zlib-dictionary | 2.986649–3.430241 | 373.754–532.571 | 1.4249 |
| confirm/n4096_q32_absent_clustered | zlib-ordinary | 3.276768–3.540027 | 426.947–552.938 | 1.2951 |
| confirm/n4096_q32_absent_dispersed | compact | 1.227167–1.252057 | 161.106–187.273 | 1.1624 |
| confirm/n4096_q32_absent_dispersed | dictionary | 1.301525–1.362889 | 176.290–199.237 | 1.1302 |
| confirm/n4096_q32_absent_dispersed | ordinary | 1.000000–1.000000 | 129.938–154.219 | 1.1869 |
| confirm/n4096_q32_absent_dispersed | reset-zlib-compact | 3.611954–4.153410 | 477.532–636.368 | 1.3326 |
| confirm/n4096_q32_absent_dispersed | reset-zlib-dictionary | 2.938772–3.021598 | 383.340–453.740 | 1.1836 |
| confirm/n4096_q32_absent_dispersed | reset-zlib-ordinary | 3.439643–3.731099 | 453.156–598.846 | 1.3215 |
| confirm/n4096_q32_absent_dispersed | zlib-compact | 3.948345–4.319950 | 516.582–641.235 | 1.2413 |
| confirm/n4096_q32_absent_dispersed | zlib-dictionary | 3.351582–3.672264 | 449.515–555.455 | 1.2357 |
| confirm/n4096_q32_absent_dispersed | zlib-ordinary | 3.798407–4.054642 | 496.721–622.291 | 1.2528 |
| confirm/n4096_q32_member_clustered | compact | 1.178316–1.248251 | 174.533–199.994 | 1.1459 |
| confirm/n4096_q32_member_clustered | dictionary | 1.195404–1.256080 | 176.013–206.434 | 1.1728 |
| confirm/n4096_q32_member_clustered | ordinary | 1.000000–1.000000 | 143.206–163.995 | 1.1452 |
| confirm/n4096_q32_member_clustered | reset-zlib-compact | 2.961195–3.231911 | 430.351–560.100 | 1.3015 |
| confirm/n4096_q32_member_clustered | reset-zlib-dictionary | 2.488676–2.709631 | 371.402–435.686 | 1.1731 |
| confirm/n4096_q32_member_clustered | reset-zlib-ordinary | 2.693210–3.020396 | 400.860–531.690 | 1.3264 |
| confirm/n4096_q32_member_clustered | zlib-compact | 3.272019–3.642258 | 473.480–619.594 | 1.3086 |
| confirm/n4096_q32_member_clustered | zlib-dictionary | 2.843347–3.158448 | 415.548–517.950 | 1.2464 |
| confirm/n4096_q32_member_clustered | zlib-ordinary | 3.012984–3.201478 | 444.876–543.585 | 1.2219 |
| confirm/n4096_q32_member_dispersed | compact | 1.227828–1.252708 | 173.809–193.996 | 1.1161 |
| confirm/n4096_q32_member_dispersed | dictionary | 1.326440–1.357183 | 190.621–212.378 | 1.1141 |
| confirm/n4096_q32_member_dispersed | ordinary | 1.000000–1.000000 | 139.637–160.287 | 1.1479 |
| confirm/n4096_q32_member_dispersed | reset-zlib-compact | 3.317479–3.773471 | 480.694–582.655 | 1.2121 |
| confirm/n4096_q32_member_dispersed | reset-zlib-dictionary | 2.836903–2.904093 | 401.210–455.266 | 1.1347 |
| confirm/n4096_q32_member_dispersed | reset-zlib-ordinary | 3.095025–3.624643 | 442.418–555.961 | 1.2566 |
| confirm/n4096_q32_member_dispersed | zlib-compact | 3.561340–3.980284 | 529.150–656.891 | 1.2414 |
| confirm/n4096_q32_member_dispersed | zlib-dictionary | 3.170425–3.552614 | 465.508–549.934 | 1.1814 |
| confirm/n4096_q32_member_dispersed | zlib-ordinary | 3.438259–3.663020 | 488.574–603.601 | 1.2354 |
| confirm/n4096_q8_absent_clustered | compact | 1.214605–1.270681 | 41.950–55.101 | 1.3135 |
| confirm/n4096_q8_absent_clustered | dictionary | 1.282483–1.349224 | 44.049–55.364 | 1.2569 |
| confirm/n4096_q8_absent_clustered | ordinary | 1.000000–1.000000 | 34.379–41.685 | 1.2125 |
| confirm/n4096_q8_absent_clustered | reset-zlib-compact | 4.521805–4.702105 | 156.391–201.798 | 1.2903 |
| confirm/n4096_q8_absent_clustered | reset-zlib-dictionary | 3.397397–4.068684 | 143.126–158.737 | 1.1091 |
| confirm/n4096_q8_absent_clustered | reset-zlib-ordinary | 4.343555–4.484880 | 152.633–185.308 | 1.2141 |
| confirm/n4096_q8_absent_clustered | zlib-compact | 5.682632–6.548986 | 209.835–279.453 | 1.3318 |
| confirm/n4096_q8_absent_clustered | zlib-dictionary | 5.411000–6.087047 | 187.508–288.164 | 1.5368 |
| confirm/n4096_q8_absent_clustered | zlib-ordinary | 5.441719–6.246223 | 195.668–269.128 | 1.3754 |
| confirm/n4096_q8_absent_dispersed | compact | 1.226946–1.316666 | 45.998–60.878 | 1.3235 |
| confirm/n4096_q8_absent_dispersed | dictionary | 1.389018–1.424805 | 51.962–69.175 | 1.3313 |
| confirm/n4096_q8_absent_dispersed | ordinary | 1.000000–1.000000 | 36.311–49.109 | 1.3525 |
| confirm/n4096_q8_absent_dispersed | reset-zlib-compact | 4.643089–5.144591 | 182.177–236.984 | 1.3008 |
| confirm/n4096_q8_absent_dispersed | reset-zlib-dictionary | 3.266106–3.663352 | 129.718–163.056 | 1.2570 |
| confirm/n4096_q8_absent_dispersed | reset-zlib-ordinary | 4.490760–5.055364 | 172.839–236.194 | 1.3666 |
| confirm/n4096_q8_absent_dispersed | zlib-compact | 5.934273–6.802983 | 214.917–305.667 | 1.4223 |
| confirm/n4096_q8_absent_dispersed | zlib-dictionary | 4.781126–5.381808 | 179.567–237.658 | 1.3235 |
| confirm/n4096_q8_absent_dispersed | zlib-ordinary | 5.583713–6.474910 | 216.944–283.307 | 1.3059 |
| confirm/n4096_q8_member_clustered | compact | 1.189727–1.252790 | 45.647–57.731 | 1.2647 |
| confirm/n4096_q8_member_clustered | dictionary | 1.294651–1.359215 | 49.606–61.726 | 1.2443 |
| confirm/n4096_q8_member_clustered | ordinary | 1.000000–1.000000 | 37.210–49.483 | 1.3298 |
| confirm/n4096_q8_member_clustered | reset-zlib-compact | 4.073066–4.183857 | 149.090–204.444 | 1.3713 |
| confirm/n4096_q8_member_clustered | reset-zlib-dictionary | 3.765508–3.915482 | 147.997–186.098 | 1.2574 |
| confirm/n4096_q8_member_clustered | reset-zlib-ordinary | 3.983780–4.166344 | 147.843–209.787 | 1.4190 |
| confirm/n4096_q8_member_clustered | zlib-compact | 5.182290–5.902962 | 198.236–281.707 | 1.4211 |
| confirm/n4096_q8_member_clustered | zlib-dictionary | 5.119367–5.604842 | 192.190–274.452 | 1.4280 |
| confirm/n4096_q8_member_clustered | zlib-ordinary | 4.998957–5.830786 | 183.016–282.887 | 1.5457 |
| confirm/n4096_q8_member_dispersed | compact | 1.173253–1.272682 | 49.734–60.740 | 1.2213 |
| confirm/n4096_q8_member_dispersed | dictionary | 1.332369–1.392136 | 51.563–74.311 | 1.4412 |
| confirm/n4096_q8_member_dispersed | ordinary | 1.000000–1.000000 | 38.349–48.527 | 1.2654 |
| confirm/n4096_q8_member_dispersed | reset-zlib-compact | 4.365948–4.535966 | 169.687–222.799 | 1.3130 |
| confirm/n4096_q8_member_dispersed | reset-zlib-dictionary | 3.156991–3.322202 | 124.313–163.029 | 1.3114 |
| confirm/n4096_q8_member_dispersed | reset-zlib-ordinary | 4.253181–4.481598 | 165.525–227.069 | 1.3718 |
| confirm/n4096_q8_member_dispersed | zlib-compact | 5.652954–5.892640 | 229.236–291.340 | 1.2709 |
| confirm/n4096_q8_member_dispersed | zlib-dictionary | 4.391591–5.056404 | 176.825–304.260 | 1.7207 |
| confirm/n4096_q8_member_dispersed | zlib-ordinary | 5.162006–6.223484 | 202.887–289.323 | 1.4260 |
| dev/n16384_q128_absent_clustered | compact | 1.159759–1.293601 | 676.096–749.643 | 1.1088 |
| dev/n16384_q128_absent_clustered | dictionary | 1.113973–1.227788 | 683.794–728.843 | 1.0659 |
| dev/n16384_q128_absent_clustered | ordinary | 1.000000–1.000000 | 559.268–655.953 | 1.1729 |
| dev/n16384_q128_absent_clustered | reset-zlib-compact | 2.879929–2.992816 | 1659.915–1852.582 | 1.1161 |
| dev/n16384_q128_absent_clustered | reset-zlib-dictionary | 2.034925–2.216352 | 1205.163–1337.608 | 1.1099 |
| dev/n16384_q128_absent_clustered | reset-zlib-ordinary | 2.527909–2.735382 | 1452.891–1651.034 | 1.1364 |
| dev/n16384_q128_absent_clustered | zlib-compact | 2.856519–3.123704 | 1712.500–1919.465 | 1.1209 |
| dev/n16384_q128_absent_clustered | zlib-dictionary | 2.160439–2.363892 | 1324.341–1492.301 | 1.1268 |
| dev/n16384_q128_absent_clustered | zlib-ordinary | 2.883220–3.002446 | 1593.630–1930.239 | 1.2112 |
| dev/n16384_q128_absent_dispersed | compact | 1.183856–1.249814 | 637.614–864.633 | 1.3560 |
| dev/n16384_q128_absent_dispersed | dictionary | 1.223013–1.301656 | 698.212–864.380 | 1.2380 |
| dev/n16384_q128_absent_dispersed | ordinary | 1.000000–1.000000 | 545.943–701.403 | 1.2848 |
| dev/n16384_q128_absent_dispersed | reset-zlib-compact | 3.272429–3.581667 | 1857.923–2391.138 | 1.2870 |
| dev/n16384_q128_absent_dispersed | reset-zlib-dictionary | 1.977364–2.382505 | 1254.093–1766.046 | 1.4082 |
| dev/n16384_q128_absent_dispersed | reset-zlib-ordinary | 3.246436–3.312735 | 1749.882–2211.759 | 1.2639 |
| dev/n16384_q128_absent_dispersed | zlib-compact | 3.449252–3.871283 | 1997.713–2704.337 | 1.3537 |
| dev/n16384_q128_absent_dispersed | zlib-dictionary | 2.157221–2.633908 | 1331.006–1864.173 | 1.4006 |
| dev/n16384_q128_absent_dispersed | zlib-ordinary | 3.305346–3.570455 | 1897.827–2477.889 | 1.3056 |
| dev/n16384_q128_member_clustered | compact | 1.185284–1.232460 | 781.024–909.610 | 1.1646 |
| dev/n16384_q128_member_clustered | dictionary | 1.154431–1.229942 | 786.737–871.745 | 1.1081 |
| dev/n16384_q128_member_clustered | ordinary | 1.000000–1.000000 | 682.009–739.051 | 1.0836 |
| dev/n16384_q128_member_clustered | reset-zlib-compact | 2.667398–2.859559 | 1814.469–2133.701 | 1.1759 |
| dev/n16384_q128_member_clustered | reset-zlib-dictionary | 1.959713–2.079703 | 1318.275–1556.008 | 1.1803 |
| dev/n16384_q128_member_clustered | reset-zlib-ordinary | 2.449262–2.652985 | 1654.083–2016.852 | 1.2193 |
| dev/n16384_q128_member_clustered | zlib-compact | 2.874302–3.015225 | 1989.637–2131.604 | 1.0714 |
| dev/n16384_q128_member_clustered | zlib-dictionary | 2.098844–2.315022 | 1486.923–1728.163 | 1.1622 |
| dev/n16384_q128_member_clustered | zlib-ordinary | 2.642010–2.788425 | 1865.151–2102.664 | 1.1273 |
| dev/n16384_q128_member_dispersed | compact | 1.174156–1.249359 | 728.345–879.451 | 1.2075 |
| dev/n16384_q128_member_dispersed | dictionary | 1.237932–1.320935 | 811.255–942.566 | 1.1619 |
| dev/n16384_q128_member_dispersed | ordinary | 1.000000–1.000000 | 623.386–733.581 | 1.1768 |
| dev/n16384_q128_member_dispersed | reset-zlib-compact | 3.019379–3.284537 | 1822.950–2344.683 | 1.2862 |
| dev/n16384_q128_member_dispersed | reset-zlib-dictionary | 2.244406–2.317646 | 1426.967–1642.566 | 1.1511 |
| dev/n16384_q128_member_dispersed | reset-zlib-ordinary | 2.878435–3.062256 | 1729.701–2170.381 | 1.2548 |
| dev/n16384_q128_member_dispersed | zlib-compact | 3.235655–3.551428 | 2070.164–2648.557 | 1.2794 |
| dev/n16384_q128_member_dispersed | zlib-dictionary | 2.471065–2.678324 | 1539.985–1931.487 | 1.2542 |
| dev/n16384_q128_member_dispersed | zlib-ordinary | 3.049285–3.444175 | 2152.212–2315.427 | 1.0758 |
| dev/n16384_q1_absent_clustered | compact | 1.217065–1.431479 | 7.934–10.065 | 1.2686 |
| dev/n16384_q1_absent_clustered | dictionary | 1.415469–1.552313 | 9.425–11.899 | 1.2625 |
| dev/n16384_q1_absent_clustered | ordinary | 1.000000–1.000000 | 6.366–8.096 | 1.2718 |
| dev/n16384_q1_absent_clustered | reset-zlib-compact | 5.628127–6.999429 | 41.000–52.673 | 1.2847 |
| dev/n16384_q1_absent_clustered | reset-zlib-dictionary | 3.632329–4.043456 | 21.995–32.402 | 1.4732 |
| dev/n16384_q1_absent_clustered | reset-zlib-ordinary | 2.901025–3.797643 | 21.422–30.026 | 1.4016 |
| dev/n16384_q1_absent_clustered | zlib-compact | 14.468860–17.644296 | 86.690–132.679 | 1.5305 |
| dev/n16384_q1_absent_clustered | zlib-dictionary | 11.146796–18.220278 | 73.678–152.110 | 2.0645 |
| dev/n16384_q1_absent_clustered | zlib-ordinary | 12.416509–15.965078 | 79.444–141.349 | 1.7792 |
| dev/n16384_q1_absent_dispersed | compact | 1.213384–1.248987 | 7.283–9.301 | 1.2771 |
| dev/n16384_q1_absent_dispersed | dictionary | 1.400027–1.555607 | 8.260–11.222 | 1.3586 |
| dev/n16384_q1_absent_dispersed | ordinary | 1.000000–1.000000 | 5.990–7.577 | 1.2649 |
| dev/n16384_q1_absent_dispersed | reset-zlib-compact | 7.500051–8.304272 | 47.168–61.772 | 1.3096 |
| dev/n16384_q1_absent_dispersed | reset-zlib-dictionary | 2.956380–3.885214 | 16.731–29.001 | 1.7334 |
| dev/n16384_q1_absent_dispersed | reset-zlib-ordinary | 2.482744–3.293924 | 14.369–25.185 | 1.7527 |
| dev/n16384_q1_absent_dispersed | zlib-compact | 18.509125–22.375890 | 101.573–166.883 | 1.6430 |
| dev/n16384_q1_absent_dispersed | zlib-dictionary | 11.608056–19.179399 | 62.925–139.837 | 2.2223 |
| dev/n16384_q1_absent_dispersed | zlib-ordinary | 11.209097–18.324872 | 59.624–131.382 | 2.2035 |
| dev/n16384_q1_member_clustered | compact | 1.127500–1.282621 | 9.051–12.420 | 1.3722 |
| dev/n16384_q1_member_clustered | dictionary | 1.347247–1.468759 | 10.598–13.653 | 1.2883 |
| dev/n16384_q1_member_clustered | ordinary | 1.000000–1.000000 | 7.184–9.499 | 1.3222 |
| dev/n16384_q1_member_clustered | reset-zlib-compact | 2.391315–3.484651 | 18.486–32.903 | 1.7799 |
| dev/n16384_q1_member_clustered | reset-zlib-dictionary | 3.247448–4.055925 | 22.816–41.779 | 1.8311 |
| dev/n16384_q1_member_clustered | reset-zlib-ordinary | 2.752570–3.692026 | 18.535–36.419 | 1.9649 |
| dev/n16384_q1_member_clustered | zlib-compact | 9.410204–16.923728 | 72.267–146.308 | 2.0245 |
| dev/n16384_q1_member_clustered | zlib-dictionary | 11.307866–18.480783 | 107.231–164.619 | 1.5352 |
| dev/n16384_q1_member_clustered | zlib-ordinary | 11.266382–17.836798 | 113.480–168.776 | 1.4873 |
| dev/n16384_q1_member_dispersed | compact | 1.173383–1.325343 | 7.958–11.395 | 1.4319 |
| dev/n16384_q1_member_dispersed | dictionary | 1.389928–1.488821 | 9.722–13.312 | 1.3693 |
| dev/n16384_q1_member_dispersed | ordinary | 1.000000–1.000000 | 6.327–9.530 | 1.5062 |
| dev/n16384_q1_member_dispersed | reset-zlib-compact | 2.494177–3.299738 | 15.716–32.529 | 2.0698 |
| dev/n16384_q1_member_dispersed | reset-zlib-dictionary | 3.214126–4.189371 | 20.856–38.568 | 1.8493 |
| dev/n16384_q1_member_dispersed | reset-zlib-ordinary | 2.637704–3.722281 | 17.363–34.883 | 2.0090 |
| dev/n16384_q1_member_dispersed | zlib-compact | 10.012630–15.654675 | 60.633–135.854 | 2.2406 |
| dev/n16384_q1_member_dispersed | zlib-dictionary | 11.673878–17.484994 | 84.039–155.233 | 1.8472 |
| dev/n16384_q1_member_dispersed | zlib-ordinary | 12.466797–18.018698 | 86.524–161.620 | 1.8679 |
| dev/n16384_q32_absent_clustered | compact | 1.186953–1.243960 | 174.462–208.031 | 1.1924 |
| dev/n16384_q32_absent_clustered | dictionary | 1.226690–1.269623 | 182.148–214.440 | 1.1773 |
| dev/n16384_q32_absent_clustered | ordinary | 1.000000–1.000000 | 145.207–167.532 | 1.1537 |
| dev/n16384_q32_absent_clustered | reset-zlib-compact | 3.136294–3.635842 | 446.607–613.225 | 1.3731 |
| dev/n16384_q32_absent_clustered | reset-zlib-dictionary | 2.278583–2.542619 | 340.075–436.562 | 1.2837 |
| dev/n16384_q32_absent_clustered | reset-zlib-ordinary | 2.969299–3.650377 | 439.863–619.899 | 1.4093 |
| dev/n16384_q32_absent_clustered | zlib-compact | 3.367914–3.663399 | 489.484–626.095 | 1.2791 |
| dev/n16384_q32_absent_clustered | zlib-dictionary | 2.823391–3.020235 | 399.118–527.588 | 1.3219 |
| dev/n16384_q32_absent_clustered | zlib-ordinary | 3.206125–3.703552 | 455.760–641.893 | 1.4084 |
| dev/n16384_q32_absent_dispersed | compact | 1.220418–1.280384 | 189.490–225.668 | 1.1909 |
| dev/n16384_q32_absent_dispersed | dictionary | 1.306114–1.338629 | 198.550–233.494 | 1.1760 |
| dev/n16384_q32_absent_dispersed | ordinary | 1.000000–1.000000 | 150.476–180.736 | 1.2011 |
| dev/n16384_q32_absent_dispersed | reset-zlib-compact | 3.643463–3.969423 | 543.996–711.508 | 1.3079 |
| dev/n16384_q32_absent_dispersed | reset-zlib-dictionary | 2.707969–2.911226 | 408.543–521.967 | 1.2776 |
| dev/n16384_q32_absent_dispersed | reset-zlib-ordinary | 3.371703–3.869264 | 498.248–662.918 | 1.3305 |
| dev/n16384_q32_absent_dispersed | zlib-compact | 3.907991–4.023703 | 613.608–730.336 | 1.1902 |
| dev/n16384_q32_absent_dispersed | zlib-dictionary | 3.273293–3.594859 | 558.742–645.840 | 1.1559 |
| dev/n16384_q32_absent_dispersed | zlib-ordinary | 3.642117–3.850007 | 625.219–745.994 | 1.1932 |
| dev/n16384_q32_member_clustered | compact | 1.198078–1.232023 | 196.096–273.081 | 1.3926 |
| dev/n16384_q32_member_clustered | dictionary | 1.244158–1.262877 | 207.693–268.240 | 1.2915 |
| dev/n16384_q32_member_clustered | ordinary | 1.000000–1.000000 | 164.710–205.252 | 1.2461 |
| dev/n16384_q32_member_clustered | reset-zlib-compact | 2.986757–3.345980 | 481.694–686.816 | 1.4258 |
| dev/n16384_q32_member_clustered | reset-zlib-dictionary | 2.502634–2.639323 | 416.513–537.181 | 1.2897 |
| dev/n16384_q32_member_clustered | reset-zlib-ordinary | 2.854555–3.150249 | 449.177–646.955 | 1.4403 |
| dev/n16384_q32_member_clustered | zlib-compact | 3.168982–4.021989 | 536.624–737.036 | 1.3735 |
| dev/n16384_q32_member_clustered | zlib-dictionary | 2.776675–3.251606 | 482.533–599.360 | 1.2421 |
| dev/n16384_q32_member_clustered | zlib-ordinary | 3.006362–3.163508 | 488.681–670.900 | 1.3729 |
| dev/n16384_q32_member_dispersed | compact | 1.209856–1.234472 | 197.677–224.313 | 1.1347 |
| dev/n16384_q32_member_dispersed | dictionary | 1.276445–1.326972 | 215.073–238.815 | 1.1104 |
| dev/n16384_q32_member_dispersed | ordinary | 1.000000–1.000000 | 164.917–186.497 | 1.1309 |
| dev/n16384_q32_member_dispersed | reset-zlib-compact | 3.301620–3.637631 | 535.947–674.822 | 1.2591 |
| dev/n16384_q32_member_dispersed | reset-zlib-dictionary | 2.872551–3.102568 | 475.682–545.155 | 1.1460 |
| dev/n16384_q32_member_dispersed | reset-zlib-ordinary | 3.142798–3.445600 | 512.287–625.786 | 1.2216 |
| dev/n16384_q32_member_dispersed | zlib-compact | 3.461803–4.583273 | 573.654–809.002 | 1.4103 |
| dev/n16384_q32_member_dispersed | zlib-dictionary | 3.204168–3.369804 | 530.055–690.322 | 1.3024 |
| dev/n16384_q32_member_dispersed | zlib-ordinary | 3.314846–3.599639 | 552.301–661.063 | 1.1969 |
| dev/n16384_q8_absent_clustered | compact | 1.213399–1.259532 | 48.278–67.954 | 1.4076 |
| dev/n16384_q8_absent_clustered | dictionary | 1.252526–1.363510 | 52.242–68.446 | 1.3102 |
| dev/n16384_q8_absent_clustered | ordinary | 1.000000–1.000000 | 39.143–57.674 | 1.4734 |
| dev/n16384_q8_absent_clustered | reset-zlib-compact | 4.472644–4.750444 | 177.405–251.433 | 1.4173 |
| dev/n16384_q8_absent_clustered | reset-zlib-dictionary | 2.925510–3.169067 | 127.199–176.229 | 1.3855 |
| dev/n16384_q8_absent_clustered | reset-zlib-ordinary | 4.208191–4.460146 | 167.362–242.596 | 1.4495 |
| dev/n16384_q8_absent_clustered | zlib-compact | 5.391768–6.330857 | 213.054–354.997 | 1.6662 |
| dev/n16384_q8_absent_clustered | zlib-dictionary | 4.468580–5.227677 | 182.540–281.157 | 1.5402 |
| dev/n16384_q8_absent_clustered | zlib-ordinary | 5.156822–5.756053 | 204.162–290.534 | 1.4231 |
| dev/n16384_q8_absent_dispersed | compact | 1.187748–1.265237 | 51.568–66.168 | 1.2831 |
| dev/n16384_q8_absent_dispersed | dictionary | 1.345761–1.403381 | 58.143–78.623 | 1.3522 |
| dev/n16384_q8_absent_dispersed | ordinary | 1.000000–1.000000 | 41.697–55.683 | 1.3354 |
| dev/n16384_q8_absent_dispersed | reset-zlib-compact | 4.688304–4.893323 | 200.424–264.895 | 1.3217 |
| dev/n16384_q8_absent_dispersed | reset-zlib-dictionary | 2.963514–3.158719 | 129.947–162.924 | 1.2538 |
| dev/n16384_q8_absent_dispersed | reset-zlib-ordinary | 4.280439–4.636532 | 177.033–252.271 | 1.4250 |
| dev/n16384_q8_absent_dispersed | zlib-compact | 5.725453–6.688766 | 249.639–354.251 | 1.4191 |
| dev/n16384_q8_absent_dispersed | zlib-dictionary | 4.213385–5.225272 | 178.942–254.426 | 1.4218 |
| dev/n16384_q8_absent_dispersed | zlib-ordinary | 5.209682–6.157457 | 225.349–316.125 | 1.4028 |
| dev/n16384_q8_member_clustered | compact | 1.185404–1.248674 | 51.045–65.123 | 1.2758 |
| dev/n16384_q8_member_clustered | dictionary | 1.281075–1.345013 | 55.380–68.035 | 1.2285 |
| dev/n16384_q8_member_clustered | ordinary | 1.000000–1.000000 | 41.409–54.718 | 1.3214 |
| dev/n16384_q8_member_clustered | reset-zlib-compact | 3.917601–4.268627 | 162.970–219.712 | 1.3482 |
| dev/n16384_q8_member_clustered | reset-zlib-dictionary | 3.637713–3.805111 | 152.829–199.964 | 1.3084 |
| dev/n16384_q8_member_clustered | reset-zlib-ordinary | 3.770663–4.040698 | 162.149–217.597 | 1.3420 |
| dev/n16384_q8_member_clustered | zlib-compact | 5.036658–5.663458 | 206.393–318.632 | 1.5438 |
| dev/n16384_q8_member_clustered | zlib-dictionary | 5.000949–5.290785 | 208.316–301.211 | 1.4459 |
| dev/n16384_q8_member_clustered | zlib-ordinary | 4.986846–5.573615 | 206.878–336.061 | 1.6244 |
| dev/n16384_q8_member_dispersed | compact | 1.196459–1.263695 | 53.320–71.210 | 1.3355 |
| dev/n16384_q8_member_dispersed | dictionary | 1.317940–1.366935 | 58.406–76.141 | 1.3037 |
| dev/n16384_q8_member_dispersed | ordinary | 1.000000–1.000000 | 42.874–56.297 | 1.3131 |
| dev/n16384_q8_member_dispersed | reset-zlib-compact | 4.205426–4.415030 | 184.674–251.566 | 1.3622 |
| dev/n16384_q8_member_dispersed | reset-zlib-dictionary | 3.103406–3.252012 | 139.334–182.442 | 1.3094 |
| dev/n16384_q8_member_dispersed | reset-zlib-ordinary | 4.180314–4.356725 | 184.537–246.861 | 1.3377 |
| dev/n16384_q8_member_dispersed | zlib-compact | 5.103984–5.719341 | 224.781–387.257 | 1.7228 |
| dev/n16384_q8_member_dispersed | zlib-dictionary | 4.253227–4.632613 | 192.987–297.798 | 1.5431 |
| dev/n16384_q8_member_dispersed | zlib-ordinary | 5.062115–5.847217 | 227.680–359.987 | 1.5811 |
| dev/n4096_q128_absent_clustered | compact | 1.219121–1.252025 | 608.128–684.220 | 1.1251 |
| dev/n4096_q128_absent_clustered | dictionary | 1.142898–1.238299 | 605.949–642.495 | 1.0603 |
| dev/n4096_q128_absent_clustered | ordinary | 1.000000–1.000000 | 494.344–567.614 | 1.1482 |
| dev/n4096_q128_absent_clustered | reset-zlib-compact | 2.643458–2.772220 | 1314.477–1531.088 | 1.1648 |
| dev/n4096_q128_absent_clustered | reset-zlib-dictionary | 2.120382–2.236427 | 994.696–1260.483 | 1.2672 |
| dev/n4096_q128_absent_clustered | reset-zlib-ordinary | 2.461153–2.652002 | 1236.705–1437.015 | 1.1620 |
| dev/n4096_q128_absent_clustered | zlib-compact | 2.755977–3.174668 | 1402.643–1942.052 | 1.3846 |
| dev/n4096_q128_absent_clustered | zlib-dictionary | 2.213415–2.417361 | 1092.911–1372.318 | 1.2557 |
| dev/n4096_q128_absent_clustered | zlib-ordinary | 2.548116–2.835638 | 1277.565–1582.700 | 1.2388 |
| dev/n4096_q128_absent_dispersed | compact | 1.210998–1.268666 | 617.629–723.395 | 1.1712 |
| dev/n4096_q128_absent_dispersed | dictionary | 1.264528–1.311624 | 650.342–706.824 | 1.0868 |
| dev/n4096_q128_absent_dispersed | ordinary | 1.000000–1.000000 | 499.085–558.006 | 1.1181 |
| dev/n4096_q128_absent_dispersed | reset-zlib-compact | 3.395605–3.545571 | 1718.573–1981.839 | 1.1532 |
| dev/n4096_q128_absent_dispersed | reset-zlib-dictionary | 2.173418–2.319015 | 1144.533–1265.067 | 1.1053 |
| dev/n4096_q128_absent_dispersed | reset-zlib-ordinary | 3.173777–3.271764 | 1603.091–1804.723 | 1.1258 |
| dev/n4096_q128_absent_dispersed | zlib-compact | 3.503422–3.917785 | 1917.862–2125.070 | 1.1080 |
| dev/n4096_q128_absent_dispersed | zlib-dictionary | 2.355984–2.767422 | 1199.186–1527.665 | 1.2739 |
| dev/n4096_q128_absent_dispersed | zlib-ordinary | 3.216313–3.693808 | 1804.770–1886.954 | 1.0455 |
| dev/n4096_q128_member_clustered | compact | 1.208330–1.274915 | 658.807–725.667 | 1.1015 |
| dev/n4096_q128_member_clustered | dictionary | 1.162777–1.206332 | 642.762–719.260 | 1.1190 |
| dev/n4096_q128_member_clustered | ordinary | 1.000000–1.000000 | 552.563–605.253 | 1.0954 |
| dev/n4096_q128_member_clustered | reset-zlib-compact | 2.516252–2.756644 | 1357.935–1635.497 | 1.2044 |
| dev/n4096_q128_member_clustered | reset-zlib-dictionary | 1.998367–2.135655 | 1056.915–1297.482 | 1.2276 |
| dev/n4096_q128_member_clustered | reset-zlib-ordinary | 2.324409–2.496965 | 1216.677–1516.052 | 1.2461 |
| dev/n4096_q128_member_clustered | zlib-compact | 2.708540–3.262434 | 1492.939–2030.055 | 1.3598 |
| dev/n4096_q128_member_clustered | zlib-dictionary | 2.075747–2.377924 | 1159.919–1448.421 | 1.2487 |
| dev/n4096_q128_member_clustered | zlib-ordinary | 2.448020–2.687345 | 1333.355–1726.029 | 1.2945 |
| dev/n4096_q128_member_dispersed | compact | 1.200006–1.220582 | 658.945–790.427 | 1.1995 |
| dev/n4096_q128_member_dispersed | dictionary | 1.259091–1.291786 | 707.084–840.523 | 1.1887 |
| dev/n4096_q128_member_dispersed | ordinary | 1.000000–1.000000 | 538.997–665.957 | 1.2355 |
| dev/n4096_q128_member_dispersed | reset-zlib-compact | 3.080680–3.247923 | 1711.823–2125.016 | 1.2414 |
| dev/n4096_q128_member_dispersed | reset-zlib-dictionary | 2.364446–2.420773 | 1276.522–1688.543 | 1.3228 |
| dev/n4096_q128_member_dispersed | reset-zlib-ordinary | 2.895606–3.005443 | 1577.807–1981.855 | 1.2561 |
| dev/n4096_q128_member_dispersed | zlib-compact | 3.202692–3.447056 | 1749.778–2171.429 | 1.2410 |
| dev/n4096_q128_member_dispersed | zlib-dictionary | 2.495490–2.711192 | 1427.046–1749.744 | 1.2261 |
| dev/n4096_q128_member_dispersed | zlib-ordinary | 3.022986–3.222510 | 1661.318–2100.271 | 1.2642 |
| dev/n4096_q1_absent_clustered | compact | 1.240827–1.293792 | 7.070–9.121 | 1.2901 |
| dev/n4096_q1_absent_clustered | dictionary | 1.354142–1.499425 | 7.987–10.207 | 1.2780 |
| dev/n4096_q1_absent_clustered | ordinary | 1.000000–1.000000 | 6.101–7.697 | 1.2616 |
| dev/n4096_q1_absent_clustered | reset-zlib-compact | 6.291373–7.362943 | 39.762–52.649 | 1.3241 |
| dev/n4096_q1_absent_clustered | reset-zlib-dictionary | 3.442021–4.304532 | 21.334–29.733 | 1.3937 |
| dev/n4096_q1_absent_clustered | reset-zlib-ordinary | 3.158568–4.102564 | 20.294–29.110 | 1.4344 |
| dev/n4096_q1_absent_clustered | zlib-compact | 16.661334–22.217007 | 96.788–149.401 | 1.5436 |
| dev/n4096_q1_absent_clustered | zlib-dictionary | 12.199832–24.235116 | 72.289–145.798 | 2.0169 |
| dev/n4096_q1_absent_clustered | zlib-ordinary | 14.105562–19.465103 | 85.353–132.940 | 1.5575 |
| dev/n4096_q1_absent_dispersed | compact | 1.246501–1.334447 | 6.797–8.758 | 1.2885 |
| dev/n4096_q1_absent_dispersed | dictionary | 1.366255–1.575314 | 7.515–10.021 | 1.3335 |
| dev/n4096_q1_absent_dispersed | ordinary | 1.000000–1.000000 | 5.457–6.778 | 1.2421 |
| dev/n4096_q1_absent_dispersed | reset-zlib-compact | 7.892906–8.745463 | 45.751–59.931 | 1.3099 |
| dev/n4096_q1_absent_dispersed | reset-zlib-dictionary | 2.991441–3.959873 | 15.719–28.312 | 1.8011 |
| dev/n4096_q1_absent_dispersed | reset-zlib-ordinary | 2.491522–3.385645 | 13.261–24.184 | 1.8237 |
| dev/n4096_q1_absent_dispersed | zlib-compact | 18.459246–26.354989 | 91.615–163.649 | 1.7863 |
| dev/n4096_q1_absent_dispersed | zlib-dictionary | 11.927799–18.329106 | 60.985–125.180 | 2.0526 |
| dev/n4096_q1_absent_dispersed | zlib-ordinary | 11.741037–18.559220 | 60.153–122.902 | 2.0432 |
| dev/n4096_q1_member_clustered | compact | 1.151475–1.281780 | 7.544–9.750 | 1.2924 |
| dev/n4096_q1_member_clustered | dictionary | 1.347351–1.459770 | 8.601–12.061 | 1.4023 |
| dev/n4096_q1_member_clustered | ordinary | 1.000000–1.000000 | 6.350–8.895 | 1.4008 |
| dev/n4096_q1_member_clustered | reset-zlib-compact | 2.490169–3.024698 | 14.815–26.185 | 1.7675 |
| dev/n4096_q1_member_clustered | reset-zlib-dictionary | 5.828522–6.695185 | 45.120–53.210 | 1.1793 |
| dev/n4096_q1_member_clustered | reset-zlib-ordinary | 6.398231–8.418299 | 54.213–66.025 | 1.2179 |
| dev/n4096_q1_member_clustered | zlib-compact | 10.829144–15.386709 | 61.959–123.232 | 1.9889 |
| dev/n4096_q1_member_clustered | zlib-dictionary | 16.616150–21.418529 | 95.467–154.506 | 1.6184 |
| dev/n4096_q1_member_clustered | zlib-ordinary | 16.601695–21.691521 | 104.609–163.774 | 1.5656 |
| dev/n4096_q1_member_dispersed | compact | 1.189073–1.353070 | 7.198–9.631 | 1.3380 |
| dev/n4096_q1_member_dispersed | dictionary | 1.306284–1.431903 | 8.382–10.455 | 1.2473 |
| dev/n4096_q1_member_dispersed | ordinary | 1.000000–1.000000 | 5.971–7.716 | 1.2922 |
| dev/n4096_q1_member_dispersed | reset-zlib-compact | 2.691250–3.324194 | 15.760–24.410 | 1.5489 |
| dev/n4096_q1_member_dispersed | reset-zlib-dictionary | 2.897795–3.254201 | 16.596–26.680 | 1.6076 |
| dev/n4096_q1_member_dispersed | reset-zlib-ordinary | 2.579117–2.986725 | 15.240–25.297 | 1.6599 |
| dev/n4096_q1_member_dispersed | zlib-compact | 10.920878–17.931748 | 62.064–123.704 | 1.9932 |
| dev/n4096_q1_member_dispersed | zlib-dictionary | 11.027658–21.422442 | 61.155–132.019 | 2.1588 |
| dev/n4096_q1_member_dispersed | zlib-ordinary | 11.084439–15.769306 | 63.744–125.433 | 1.9678 |
| dev/n4096_q32_absent_clustered | compact | 1.231516–1.265077 | 158.775–182.296 | 1.1481 |
| dev/n4096_q32_absent_clustered | dictionary | 1.188236–1.238104 | 155.800–180.924 | 1.1613 |
| dev/n4096_q32_absent_clustered | ordinary | 1.000000–1.000000 | 127.108–146.212 | 1.1503 |
| dev/n4096_q32_absent_clustered | reset-zlib-compact | 3.117696–3.500944 | 403.340–525.532 | 1.3030 |
| dev/n4096_q32_absent_clustered | reset-zlib-dictionary | 2.665837–2.858967 | 335.173–415.522 | 1.2397 |
| dev/n4096_q32_absent_clustered | reset-zlib-ordinary | 2.966498–3.255514 | 372.072–466.191 | 1.2530 |
| dev/n4096_q32_absent_clustered | zlib-compact | 3.427959–3.929010 | 451.230–545.800 | 1.2096 |
| dev/n4096_q32_absent_clustered | zlib-dictionary | 2.999152–3.330394 | 401.275–499.667 | 1.2452 |
| dev/n4096_q32_absent_clustered | zlib-ordinary | 3.285173–3.773943 | 441.195–575.287 | 1.3039 |
| dev/n4096_q32_absent_dispersed | compact | 1.198451–1.266113 | 151.320–183.028 | 1.2095 |
| dev/n4096_q32_absent_dispersed | dictionary | 1.307093–1.372686 | 160.345–198.001 | 1.2348 |
| dev/n4096_q32_absent_dispersed | ordinary | 1.000000–1.000000 | 127.182–147.530 | 1.1600 |
| dev/n4096_q32_absent_dispersed | reset-zlib-compact | 3.542309–4.144402 | 432.091–594.387 | 1.3756 |
| dev/n4096_q32_absent_dispersed | reset-zlib-dictionary | 2.653530–2.837417 | 332.673–409.867 | 1.2320 |
| dev/n4096_q32_absent_dispersed | reset-zlib-ordinary | 3.319820–3.626887 | 427.275–557.864 | 1.3056 |
| dev/n4096_q32_absent_dispersed | zlib-compact | 3.859081–4.083485 | 501.249–599.956 | 1.1969 |
| dev/n4096_q32_absent_dispersed | zlib-dictionary | 3.247676–3.512025 | 414.115–520.044 | 1.2558 |
| dev/n4096_q32_absent_dispersed | zlib-ordinary | 3.665783–3.935344 | 466.555–656.417 | 1.4069 |
| dev/n4096_q32_member_clustered | compact | 1.210501–1.266206 | 170.631–215.818 | 1.2648 |
| dev/n4096_q32_member_clustered | dictionary | 1.209815–1.273996 | 166.738–204.823 | 1.2284 |
| dev/n4096_q32_member_clustered | ordinary | 1.000000–1.000000 | 137.581–171.118 | 1.2438 |
| dev/n4096_q32_member_clustered | reset-zlib-compact | 2.909042–3.241302 | 405.892–536.589 | 1.3220 |
| dev/n4096_q32_member_clustered | reset-zlib-dictionary | 2.541096–2.793493 | 353.055–458.401 | 1.2984 |
| dev/n4096_q32_member_clustered | reset-zlib-ordinary | 2.750035–3.151354 | 386.948–524.714 | 1.3560 |
| dev/n4096_q32_member_clustered | zlib-compact | 3.229539–3.414149 | 434.068–568.263 | 1.3092 |
| dev/n4096_q32_member_clustered | zlib-dictionary | 2.878985–3.069766 | 411.581–528.319 | 1.2836 |
| dev/n4096_q32_member_clustered | zlib-ordinary | 3.005402–3.268504 | 413.296–623.585 | 1.5088 |
| dev/n4096_q32_member_dispersed | compact | 1.218102–1.274002 | 179.102–203.343 | 1.1353 |
| dev/n4096_q32_member_dispersed | dictionary | 1.266355–1.345549 | 189.498–215.108 | 1.1351 |
| dev/n4096_q32_member_dispersed | ordinary | 1.000000–1.000000 | 141.570–160.522 | 1.1339 |
| dev/n4096_q32_member_dispersed | reset-zlib-compact | 3.326022–3.627262 | 465.561–585.449 | 1.2575 |
| dev/n4096_q32_member_dispersed | reset-zlib-dictionary | 2.832903–2.951980 | 421.693–467.684 | 1.1091 |
| dev/n4096_q32_member_dispersed | reset-zlib-ordinary | 3.157950–3.361654 | 449.019–565.532 | 1.2595 |
| dev/n4096_q32_member_dispersed | zlib-compact | 3.652494–3.920132 | 523.275–645.152 | 1.2329 |
| dev/n4096_q32_member_dispersed | zlib-dictionary | 3.254638–3.558263 | 468.002–581.054 | 1.2416 |
| dev/n4096_q32_member_dispersed | zlib-ordinary | 3.486924–3.662178 | 494.659–666.518 | 1.3474 |
| dev/n4096_q8_absent_clustered | compact | 1.230483–1.308526 | 43.993–53.735 | 1.2214 |
| dev/n4096_q8_absent_clustered | dictionary | 1.270980–1.342325 | 46.825–51.580 | 1.1015 |
| dev/n4096_q8_absent_clustered | ordinary | 1.000000–1.000000 | 35.939–41.019 | 1.1414 |
| dev/n4096_q8_absent_clustered | reset-zlib-compact | 4.556625–4.920181 | 166.329–199.587 | 1.2000 |
| dev/n4096_q8_absent_clustered | reset-zlib-dictionary | 4.181745–4.315415 | 152.909–169.454 | 1.1082 |
| dev/n4096_q8_absent_clustered | reset-zlib-ordinary | 4.201967–4.764870 | 154.390–190.304 | 1.2326 |
| dev/n4096_q8_absent_clustered | zlib-compact | 5.626746–6.462026 | 202.975–308.742 | 1.5211 |
| dev/n4096_q8_absent_clustered | zlib-dictionary | 5.538229–6.237151 | 196.431–266.233 | 1.3554 |
| dev/n4096_q8_absent_clustered | zlib-ordinary | 5.435392–6.287196 | 195.643–283.529 | 1.4492 |
| dev/n4096_q8_absent_dispersed | compact | 1.234009–1.322938 | 44.261–52.969 | 1.1967 |
| dev/n4096_q8_absent_dispersed | dictionary | 1.384587–1.439825 | 48.861–57.388 | 1.1745 |
| dev/n4096_q8_absent_dispersed | ordinary | 1.000000–1.000000 | 36.002–41.798 | 1.1610 |
| dev/n4096_q8_absent_dispersed | reset-zlib-compact | 4.800357–5.269853 | 171.323–206.977 | 1.2081 |
| dev/n4096_q8_absent_dispersed | reset-zlib-dictionary | 3.416491–3.528989 | 119.257–141.129 | 1.1834 |
| dev/n4096_q8_absent_dispersed | reset-zlib-ordinary | 4.588996–5.001326 | 163.215–205.041 | 1.2563 |
| dev/n4096_q8_absent_dispersed | zlib-compact | 5.975994–6.892066 | 204.875–335.175 | 1.6360 |
| dev/n4096_q8_absent_dispersed | zlib-dictionary | 4.658206–5.532056 | 164.504–234.078 | 1.4229 |
| dev/n4096_q8_absent_dispersed | zlib-ordinary | 5.684358–6.909194 | 201.249–282.815 | 1.4053 |
| dev/n4096_q8_member_clustered | compact | 1.207519–1.249763 | 50.022–56.232 | 1.1241 |
| dev/n4096_q8_member_clustered | dictionary | 1.289996–1.349208 | 51.145–59.525 | 1.1638 |
| dev/n4096_q8_member_clustered | ordinary | 1.000000–1.000000 | 39.923–45.570 | 1.1414 |
| dev/n4096_q8_member_clustered | reset-zlib-compact | 4.231384–4.511786 | 170.276–199.307 | 1.1705 |
| dev/n4096_q8_member_clustered | reset-zlib-dictionary | 3.730076–3.994136 | 152.297–177.415 | 1.1649 |
| dev/n4096_q8_member_clustered | reset-zlib-ordinary | 4.029130–4.378148 | 162.445–200.684 | 1.2354 |
| dev/n4096_q8_member_clustered | zlib-compact | 5.217181–6.131971 | 216.016–276.685 | 1.2809 |
| dev/n4096_q8_member_clustered | zlib-dictionary | 5.062334–5.967392 | 198.961–252.854 | 1.2709 |
| dev/n4096_q8_member_clustered | zlib-ordinary | 4.959297–6.090050 | 204.676–275.661 | 1.3468 |
| dev/n4096_q8_member_dispersed | compact | 1.189779–1.278856 | 51.001–60.520 | 1.1866 |
| dev/n4096_q8_member_dispersed | dictionary | 1.358961–1.407835 | 57.118–66.885 | 1.1710 |
| dev/n4096_q8_member_dispersed | ordinary | 1.000000–1.000000 | 41.499–48.341 | 1.1649 |
| dev/n4096_q8_member_dispersed | reset-zlib-compact | 4.374222–4.511237 | 179.534–227.425 | 1.2668 |
| dev/n4096_q8_member_dispersed | reset-zlib-dictionary | 3.181672–3.407703 | 139.164–165.711 | 1.1908 |
| dev/n4096_q8_member_dispersed | reset-zlib-ordinary | 4.185914–4.549675 | 173.395–222.855 | 1.2852 |
| dev/n4096_q8_member_dispersed | zlib-compact | 5.494436–6.048488 | 231.153–301.137 | 1.3028 |
| dev/n4096_q8_member_dispersed | zlib-dictionary | 4.538712–5.350137 | 188.175–261.399 | 1.3891 |
| dev/n4096_q8_member_dispersed | zlib-ordinary | 5.348643–6.057497 | 239.714–284.563 | 1.1871 |
