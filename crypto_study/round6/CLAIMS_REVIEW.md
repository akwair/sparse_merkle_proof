# Round6 独立科学结论核查

日期：2026-10-23。性质：测量完成后的只读复核与结论审查。本文件不属于补充预注册，不改变冻结的协议、代码、测试、原始观测、门槛或既有结果。

## 核查结论

现有数据支持以下表述：第三台机器重复了前一台 Linux 服务器的 locality、lifecycle 和联合工程门槛判定；三台机器的字节和执行顺序保持一致；第三台机器绝对时间中位数相对两台旧机器的变化并不统一，尤其相对前一台 Linux，574/576 个条件更高。证据支持“在三个已观察环境下的条件性结果”，不支持 CPU 单独因果效应、独立 seed 稳健性或特定运行时机制诊断。

本次复核未发现报告的数值结论与原始数据冲突。须保留的关键口径是：512 指两个 domain 的非基线 cell/mode 时间汇总，256 指开发／确认配对后的替代方案条件，576 指含 ordinary 的 domain-specific cell/mode 汇总；冻结 `effective` 数组的 288 项包括 32 个 ordinary 项。

## 独立复算方法与范围

复算直接读取三台机器的 `measurements/log.jsonl`，未调用冻结 `analyze.py`、`compare_platforms.py` 或 `compare_three.py` 的计算函数。按 `(bundle id, repeat)` 恢复 4,032 个九模式组，再按 `(domain, cell, mode)` 恢复 576 个各含 63 条观测的汇总。

- 每个 cell/mode 的 within-host 时间值为 63 个 `mode total_ns / ordinary total_ns` 的中位数；字节值为三个 bundle 相应字节比的最大值；绝对时间为 63 个 `total_ns` 的中位数。
- Reset/fresh 使用同一 bundle、同一 repeat 的相应 fresh 模式为分母，先求 63 个比值再取中位数。
- locality 从日志中的固定 bundle 字节数独立重算每个 pattern 的三个 dictionary/ordinary 比值中位数，再作 dispersed-minus-clustered。
- 开发门槛按字节 ≤0.80、时间 ≤1.05 重算；确认按字节 <1、时间 ≤1.05 重算；最终 effective 要求开发和对应确认同时满足。ordinary 被排除在 256 个替代方案之外。
- dictionary Pareto 判定从每个 cell 的全部九个模式坐标重算，沿用双坐标均不大、至少一项严格更小的支配定义。
- 跨机器比值由各自 63 条观测的总时间中位数相除，未构造跨机器逐次时间配对。两组共 1,152 个比值逐项等于 `THREE_PLATFORM.json`；576 个 host3 的 paired ratio、worst byte ratio 与 median time 也全部匹配保存评价。
- 三台机器的 1,542 个 corpus 文件分别计算 SHA256，第三台与每个旧环境均完全一致；两组全部 36,288 条身份序列一致，身份字段包括 domain、N、q、kind、pattern、batch、cell、id、repeat、order、mode、bytes。

服务器 `AUDIT.json` 与接收后的 `AUDIT_LOCAL.json` 均记录成功：84 个注册文件、1,637 个运行归档文件、4 棵重建树、192 个 bundle、1,152 个 frame、36,288 条观测、48,672 次证明实例验证、48,672 次错误根拒绝及全部评价字段复现。这是更完整的既有独立解析／验证审计；本核查另行重算上述科学汇总，不把两次对同一数据的审计当成两次实验。

## 可采用的主要结论

| 结论 | 独立复核的定量证据 | 允许的解释边界 |
|---|---|---|
| H-locality 在 host3 通过 | 开发 8/8、确认 8/8；差值范围分别为 0.226078–0.264796、0.203707–0.271513 | 相同 fixture 的确定性字节复核，不是新的独立随机样本 |
| H-lifecycle 在 host3 通过 | q∈{1,8} 的开发 48/48 满足 ≤0.90，确认 48/48 满足 <1 | 不改写 Windows 的整体失败，也不把大 q 条件纳入注册门槛 |
| 与 Windows 的 lifecycle 细分判定不同 | 96 项中 22 项由失败转通过，全部 q=8；开发 18 项、确认 4 项 | 条件与环境有关，不能归因于某一硬件或运行时机制 |
| 与前一台 Linux 的门槛判定一致 | locality 16 项、lifecycle 96 项与全部 effective 项均无变化 | 两个 Linux 样本不是 Linux 平台总体或机器总体的代表样本 |
| 联合工程门槛仍未通过 | 512/512 非 ordinary 条件的配对时间比中位数 >1.05；0/256 有效替代方案 | 这是汇总门槛失败，不是声称每一次个别观测都更慢 |
| dictionary 保有部分 Pareto 前沿位置 | 48/64 个 cell，为全部 q≥8；q=1 为 0/16 | 汇总非支配不等于时间门槛通过、逐请求支配或通用最佳模式 |
| 第三主机绝对时间没有统一优于旧环境 | 对 Windows 367 个中位数更小、209 个更大；对 w5 为 2 个更小、574 个更大，各 576 项 | 仅描述匹配条件下的中位数，不是总体性能排名或显著性检验 |

非 ordinary 的配对时间比中位数范围为 **1.1225850746–23.5538723141**。最小值为开发域 N=16384、q=128、member、clustered 的 dictionary；最大值为确认域 N=4096、q=1、absent、clustered 的 zlib-compact。Reset 模式相对 ordinary 的最小比值为 **1.9300959030**，对应开发域 N=16384、q=128、absent、dispersed 的 reset-zlib-dictionary。Reset 相对 fresh 的改进没有使其通过 ordinary 对照下的联合门槛。

## 各 q 的 Reset/fresh 结果

以下每个范围均覆盖两个 domain、三个 Reset 模式下的 48 个条件中位数；每个 domain 为 24 个条件。

| q | 最小值 | 最大值 | 开发 ≤0.90 | 开发 <1 | 确认 <1 | 合并 ≥1 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.1634317360 | 0.3950514601 | 24/24 | 24/24 | 24/24 | 0/48 |
| 8 | 0.5672723096 | 0.8292605779 | 24/24 | 24/24 | 24/24 | 0/48 |
| 32 | 0.7239967789 | 1.0603947782 | 10/24 | 17/24 | 24/24 | 7/48 |
| 128 | 0.8394385663 | 1.0438626471 | 5/24 | 16/24 | 21/24 | 11/48 |

q=32、128 的计数仅作描述。q=32 的 7 个 ≥1 条件全部在开发域；q=128 为开发域 8 个、确认域 3 个；没有恰好等于 1 的条件。不能为这些大 q 条件增设事后通过门槛，或以其有利子集替代原门槛。

## 两组跨机器比值和最大观测

| 第三主机／对照主机 | 总项数 | <1 / =1 / >1 | 最小中位数比 | 最大中位数比 |
|---|---:|---:|---:|---:|
| 第三主机／Windows i5 | 576 | 367 / 0 / 209 | 0.5241837809 | 2.7093037975 |
| 第三主机／Linux w5 | 576 | 2 / 0 / 574 | 0.9629281891 | 3.1998534886 |

对 Windows 的最小值为开发域 `n4096_q8_absent_clustered / reset-zlib-compact`。对 w5 的最小值为开发域 `n4096_q1_absent_dispersed / zlib-ordinary`。两个最大值均为确认域 `n4096_q1_member_dispersed / zlib-ordinary`。所有比值为对应 cell/mode 的中位数之比，不是逐重复配对比值的中位数。

最大单条观测为 `confirm_n4096_q128_member_dispersed_b2`、repeat=13、order=8、zlib-compact：12,697,069 ns，包含 encode=10,498,575、decode=904,020、verify=1,294,474 ns，frame=37,405 bytes。阶段和精确等于总时间。应保留这条记录，不可将其删除为异常值，也不能仅据某个阶段较大就诊断其机制。

## 环境、完整性及不得越过的推断边界

第三主机为 Ubuntu 22.04.5 LTS、Linux 6.8.0-124-generic x86_64、glibc 2.35、Python 3.10.12，双路 Xeon Gold 5418Y、48 物理核／96 逻辑 CPU，MemTotal=263479380 kB（251.273518 GiB）。CPU 允许列表为 0-95；GOMAXPROCS=8，GOGC/GOMEMLIMIT/GODEBUG 未设置。未进行 affinity、NUMA、governor 或频率调整。

正式测量前／后 UTC 快照分别为 08:58:41.146896 与 08:59:22.592271。1/5/15 分钟 load average 分别为 **63.79/66.81/65.01** 与 **64.70/66.54/64.99**，MemAvailable 为 110823892 与 109489952 kB。该 load 是环境端点信息，不是本实验的 CPU 利用率或单条观测的原因识别。根 cgroup 位置的 `cpu.max` 和 `memory.max` 不可用；另外保存的 `prior/runtime_context.json` 已检查 session/user/父级层次，其中 session/user 的 `memory.max` 为 `max`，父级 `user.slice` 的 `cpu.max` 为 `max 100000`、`memory.max` 为 `max`。不能把根位置缺少文件误写成未检查层次，也不能把这些控制项读数当作机器隔离证据。预检文件系统空闲量为 420,276,285,440 bytes。

两份 Linux 运行 source 快照均有 84/84 个文件匹配原注册，runner SHA256 为 `89738eddc911ddffd16d739276c5488398fbb010c33ba393b29f0e9c4652ae8e`。两台 Linux 共用可执行文件和时钟实现，但 CPU、内核、拓扑、运行时段与共享活动仍不同。本实验没有隔离分配器、GC、内存带宽、调度、NUMA 或处理器架构的独立作用。

以下说法不受当前证据支持：

- “双路 CPU 更慢／更快导致本结果”“负载导致本条慢观测”“GC 或 NUMA 已被确认为原因”。需要相应受控干预或探针；目前仅可提出待验证问题。
- “在 Linux 上普遍通过”“三个环境证明跨机器稳健”“21 次重复等于 21 台独立机器”“两个 domain 相当于独立 seed”。实验均为 seed 3407，各环境一次正式进程，fixture 与 query 存在嵌套复用。
- “字节相同给出三个独立字节收益证据”“两个审计给出两个独立实验”。相同输入重放与同一记录审计只增加完整性核查。
- “所有请求都变慢”“Pareto 前沿意味着实际请求始终占优”“某一最大值证明尾延迟改善”。报告的是预定汇总指标或单个观测，不是这些更强命题。
- “实现安全处理任意恶意网络输入”“已证明真实网络加速”“发现了新密码学构造”。现有 compact padding-mask 异常边界未修复；任务限于有效原生合成证明，没有真实网络实验。

## 证据锚点

补充注册 SHA256：`9cf8be6c0d68bb285966a542aa1d622ffec8eec9ee178d769690f73672eed35f`，注册时间 `2026-10-23T08:58:21.055059+00:00`。第三主机正式 metadata 时间为 `2026-10-23T08:58:41.127983+00:00`。原 Round5 注册 SHA256：`90465a3528fb621a94b0d2e877c90fa4c0049e9e0cb6f96b981c9e51b5bd2155`。第三主机正式完成清单 SHA256：`3ba54cfcdd4599e8cfddbfd2da2c97b3b33f5a15d495baa360904d677eb91584`。

证据文件：[原始观测](../round5/runs/linux_host3_001/measurements/log.jsonl)、[保存评价](../round5/runs/linux_host3_001/eval.json)、[服务器审计](AUDIT.json)、[本地审计](AUDIT_LOCAL.json)、[两组比较](THREE_PLATFORM.json)、[本地重算比较](THREE_PLATFORM_LOCAL.json)、[第三主机环境](prior/cloud_environment.json)、[补充完成记录](completion.json)。
