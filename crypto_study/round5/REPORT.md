# Linux 跨平台重复实验：结果与改进边界

日期：2026-10-23。本报告是正式运行后的解释文件，不属于运行前冻结协议；原预注册、源代码、Windows 数据与论文均未因本报告改动。

**本轮改变了一个总体判断：H-lifecycle 在 Windows 失败，在 Linux 通过。其他核心负结果保留：两平台均没有替代表示通过联合字节/时间门槛。** 因而原有“q=8 生命周期门槛失败”应明确限定为 Windows 环境观察，不能当作该实现跨平台都成立的规律。Linux 的新通过也不能替换或抹去 Windows 的失败。

## 重复了什么，新增了什么证据

两个平台使用相同 Go 1.27.3 和 Celestia SMT 版本、相同合法查询、相同九模式、两次预热和21次技术重复，固定 seed=3407。每平台仍为64个域内条件、192个 bundle、36,288条计时记录。两轮分开分析，不合并原始时间。跨平台核对发现1,542份相关产物逐字节相同，其中包括4棵树检查点、192个 bundle、1,152个唯一格式帧；全部36,288条观察身份和执行顺序一致。Reset重复帧未另存，逐字节一致性由冻结 Go 检查执行。

Linux 正式程序退出0；远程和本地独立审计均通过。审计重建4棵树，验证48,672个证明实例及同数的错误根拒绝，重算完整评价字段。详细证据见 [CROSS_PLATFORM.json](WORKSPACE/study/crypto_study/round5/CROSS_PLATFORM.json)、[远程审计](WORKSPACE/study/crypto_study/round5/AUDIT.json)、[下载后本地审计](WORKSPACE/study/crypto_study/round5/AUDIT_LOCAL.json)。这里新增的是第二个执行环境下的性能与决策证据，没有新增密码构造或压缩机制。

## 生命周期门槛：总门槛翻转发生在 q=8

下表每个比值是一个条件内63个 Reset/fresh 总时间比的中位数；范围跨越相应24个条件。开发要求每项<=0.90，确认要求每项<1.00。确认门槛不是再要求10%改善。

|域|q|Windows通过|Windows比值范围|Linux通过|Linux比值范围|
|---|---:|---:|---:|---:|---:|
|开发|1|24/24|0.368043–0.654206|24/24|0.186944–0.430629|
|开发|8|6/24|0.701000–1.059027|24/24|0.581536–0.821796|
|确认|1|24/24|0.342205–0.660978|24/24|0.176670–0.428851|
|确认|8|20/24|0.850709–1.022622|24/24|0.628796–0.871377|

Windows开发30/48、确认44/48，故总体失败；Linux开发48/48、确认48/48，故总体通过。96项预注册生命周期判断中有22项由失败转为通过，均为q=8：开发18项、确认4项；没有通过转失败的项目。16项局部性判断保持一致。有效表示判定也没有翻转。

Linux合并两域的q=1配对比值为0.176670–0.430629，相对同表示fresh路径减少56.94%–82.33%；q=8为0.581536–0.871377，减少12.86%–41.85%。这些百分比始终以对应fresh压缩路径为分母，不能写成相对ordinary的整条处理链加速。Linux的q=1 Reset模式相对ordinary仍为2.683814–9.228277倍。

q=8按表示展开如下；所有失败的Windows子条件继续保留于 [CROSS_PLATFORM.json](WORKSPACE/study/crypto_study/round5/CROSS_PLATFORM.json) 的 `decision_comparisons.lifecycle.items`，22项翻转在 CLAIMS_REVIEW.md 逐项列明。

|域|zlib所作用表示|Windows通过|Windows比值范围|Linux通过|Linux比值范围|
|---|---|---:|---:|---:|---:|
|开发|ordinary|1/8|0.876404–1.025947|8/8|0.735841–0.786897|
|开发|compact|0/8|0.956727–1.059027|8/8|0.729437–0.821796|
|开发|dictionary|5/8|0.701000–0.923782|8/8|0.581536–0.708964|
|确认|ordinary|5/8|0.925386–1.017058|8/8|0.739996–0.871377|
|确认|compact|7/8|0.924929–1.022622|8/8|0.724409–0.825878|
|确认|dictionary|8/8|0.850709–0.925959|8/8|0.628796–0.743542|

q=32、128不在H-lifecycle门槛内。Linux的这些预设描述性扩展仍有反向条件：q=32有13/48项 Reset/fresh>=1，范围0.768619–1.038972；q=128有11/48项>=1，范围0.845662–1.044081。Windows对应为17/48和14/48。不得把q=1/8门槛通过写成所有bundle大小都受益，也不将这些小幅反向直接解释为稳定的机制退化。

以上统计来自 [Windows eval.json](WORKSPACE/study/crypto_study/round4/runs/conditions_001/eval.json)、[Linux eval.json](WORKSPACE/study/crypto_study/round5/runs/linux_001/eval.json) 的 `lifecycle` 与 `cells[].modes`，并已从 [Windows 原始日志](WORKSPACE/study/crypto_study/round4/runs/conditions_001/measurements/log.jsonl)、[Linux 原始日志](WORKSPACE/study/crypto_study/round5/runs/linux_001/measurements/log.jsonl) 重新计算所有域内配对比值，逐值吻合。没有独立GC、分配器或缓存实验，因此门槛变化只表明该实现的生命周期收益受执行环境影响，不能定位内部原因。

## 保持不变的负结果与字节结论

两个平台各有 **512/512个替代模式/域内条件** 的配对中位总时间比>1.05。分母是8种替代模式乘64个域内条件；Windows范围1.160920–15.386364，Linux范围1.145424–29.574863。联合工程规则在两个平台都得到 **0/256个有效替代模式/条件**：8种替代模式乘32个开发/确认对应条件。机器文件 `effective` 有288条，因为还保留32条ordinary自比记录，不能把288写成替代方案总数。

字典在两平台q>=8的48/48个域内条件中均位于注册的汇总Pareto前沿；ordinary在64/64个条件中都在前沿。q=1的16个域内条件中，八种替代模式均被ordinary汇总支配。这里的前沿坐标是最坏字节比与配对中位时间比，表示两个汇总指标间的取舍，不代表逐请求支配、所有部署最优或联合工程门槛通过。

字节数据完全一致，H-locality在两个平台均通过：开发8/8项达到10个百分点，实际22.61–26.48个百分点；确认8/8项同向，实际20.37–27.15个百分点。这是固定结构和固定格式的跨平台不变性证据，不是新增独立样本对同一字节效应的统计确认。

强基线的反例仍成立：全部144个q>=8 bundle中，zlib-ordinary帧均小于未压缩dictionary；其中128/144个zlib-dictionary帧反而大于zlib-ordinary。因此不能声称字典取得更优压缩率，或先去重再zlib总会改善体积。完整格式、条件及失败项见两个正式运行的REPORT.md与eval.json。

## 绝对时间跨平台比较及尾部

下表的Linux/Windows比值是**同一域内条件和模式的总时间中位数之比**；不是跨平台逐重复比值的中位数，也不是同时运行的硬件配对实验。每行覆盖64个条件，完整576组的双方中位时间、p95和最大值均在 [CROSS_PLATFORM.json](WORKSPACE/study/crypto_study/round5/CROSS_PLATFORM.json) 的 `matched_cell_summaries`。最后两列是在该模式全部条件中的最大已观察时间，单位ms；不是平均值。

|模式|Linux/Windows中位数之比范围|Linux中位时间更高条件|Windows最大观察ms|Linux最大观察ms|
|---|---:|---:|---:|---:|
|ordinary|0.482918–0.681259|0/64|49.432600|2.385225|
|compact|0.472488–0.657049|0/64|38.089200|2.908342|
|dictionary|0.447954–0.705927|0/64|10.992500|2.460670|
|zlib-ordinary|0.508311–1.347138|6/64|123.266900|4.275270|
|zlib-compact|0.520181–1.398098|7/64|78.466800|5.274394|
|zlib-dictionary|0.471379–1.238715|6/64|25.388000|3.731443|
|reset-zlib-ordinary|0.440385–0.723034|0/64|15.946500|4.116100|
|reset-zlib-compact|0.416687–0.713345|0/64|154.060300|4.274437|
|reset-zlib-dictionary|0.395403–0.691585|0/64|22.641600|3.316007|

19/576组条件的Linux中位时间更高，全部属于q=1的fresh zlib：ordinary表示6项、compact7项、dictionary6项。其余557组低于Windows；没有相等项。不能以“新服务器所有情况都更快”概括这些结果。

全部慢样本均保留。Windows最大值154.0603ms位于 `confirm_n4096_q32_member_dispersed_b1 / repeat=6 / reset-zlib-compact`；Linux最大值5.274394ms位于 `confirm_n16384_q128_member_clustered_b1 / repeat=18 / zlib-compact`。这些是不同请求的各自最大值，不能当作同一请求尾延迟的因果降幅。p95采用原注册线性插值，各条件分别计算，未合并平台或删除离群值。

## 环境背景和解释上限

Windows平台为Core i5-11300H、Windows 11、8逻辑CPU，原时钟QPC；Linux平台为Xeon w5-3425、Ubuntu 22.04.4、24逻辑CPU，时钟为Go monotonic time.Since。两平台GOMAXPROCS实际均为8，Linux显式设置；GOGC/GOMEMLIMIT未设置，未修改亲和性或电源设置。Go版本相同，但CPU、OS、计时实现及环境一起变化，因此无法把收益因果归于Xeon或Linux某一个因素。

[运行前资源快照](WORKSPACE/study/crypto_study/round5/runs/linux_001/resources_before.json)记录1/5/15分钟load average为5.78/5.93/6.11，[运行后快照](WORKSPACE/study/crypto_study/round5/runs/linux_001/resources_after.json)为6.27/6.03/6.14。允许CPU集合为0–23，cgroup CPU和内存未设上限。Load average不是CPU使用百分比；两个端点不能说明其他服务全程无干扰、没有竞争或某项GC原因。本轮没有监测并发服务行为，也没有以负载删样或选择结果。

实验只测本地encode、decode和逐证明verify的总路径；证明生成、根获取/认证和完整恢复等价检查在计时外。没有真实网络、并发服务或吞吐量实验。payload带宽模型仍只是无排队、无重叠的算术示例。

原上游compact解码器的非法padding-bit可触发panic问题保持原样，合法输入的性能审计通过不能转换成不可信输入安全保证。所有正式样本是合法原生证明。仍只有一个seed=3407、两组确定性输入域、每平台一次完整正式过程；技术重复不是独立机器或独立数据集。

**本实验为单种子，存在随机噪声风险。** 本轮实质改进是把Windows局部结论放到第二个环境检验，并发现生命周期判断的环境依赖性；它加强了工程证据的边界，不提高方法本身的创新程度，也不构成发表质量或普遍可移植性的保证。
