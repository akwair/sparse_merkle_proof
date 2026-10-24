# Round5结果论断核验

日期：2026-10-23。本文件为结果后复核，不改变注册协议。复核读取两个平台eval、两份原始log.jsonl、CROSS_PLATFORM、远程/下载后本地审计和资源快照；重新从全部原始行计算每条件的mode/ordinary及Reset/fresh配对中位比值，与eval逐值一致。登记的84份文件哈希也全部吻合。未改原数据、冻结文件或论文。

## 主要论断与证据口径

|可支持的论断|数值与机器定位|边界或易错写法|
|---|---|---|
|Linux复制了相同工作与顺序|CROSS_PLATFORM的same_corpus_files=1542、same_bundles=192、same_unique_frames=1152、same_tree_checkpoints=4、same_observation_order=true；每平台36288行|仅六种唯一格式落盘；Reset字节断言来自Go，独立Python不能重建未存的瞬时输出|
|总体生命周期判断由失败变通过|Windows gates.lifecycle=false；Linux=true；两者gates.locality=true|旧Windows失败保持有效，不能写成旧实验被证明错误|
|生命周期变化集中于q=8|96项中22项false->true：dev18、confirm4；其余74项仍通过|没有修改门槛；开发<=0.90，确认<1；不是96项均改变|
|Linux q=1/8门槛全通过|两个域各q各24/24，见REPORT的完整比值范围|不覆盖q=32/128，也不等于每次技术重复都加速|
|联合工程负结果跨平台保持|每平台512/512替代模式/域内条件time ratio>1.05；每平台0/256有效替代模式/条件|effective数组288条包含32个ordinary自比；512、256、288不可混用|
|字典的汇总Pareto位置保持|每平台q>=8 dictionary48/48；ordinary64/64|不是字节最好、联合门槛通过、逐请求支配或新multiproof|
|字节结论保持|locality16项不变；q>=8 zlib-ordinary小于dictionary144/144；zlib-dictionary大于zlib-ordinary128/144|相同确定性帧是结构不变性检查，不是第二份独立随机字节样本|
|Linux并非所有条件绝对时间更低|19/576组中位时间更高，全部fresh-zlib的q=1；见下表|跨平台指标是ratio of cell medians，不能称跨平台paired median ratio|
|反向生命周期条件仍存在|Linux q32有13/48项>=1，q128有11/48项>=1|描述性扩展不改H-lifecycle通过，也阻止“所有batch都更快”的论断|
|全部慢样本保留|Windows最大154.0603ms，Linux最大5.274394ms；576组p95/max完整可查|各自极值来自不同请求；不能用其比值声称稳定尾延迟改善|
|环境并非被证明隔离|before load=5.78/5.93/6.11；after=6.27/6.03/6.14；GOMAXPROCS=8|load不是百分比；快照不识别别的服务，也不定位调度/GC/缓存机制|

数据定位：[Windows eval.json](WORKSPACE/study/crypto_study/round4/runs/conditions_001/eval.json)、[Linux eval.json](WORKSPACE/study/crypto_study/round5/runs/linux_001/eval.json)；`cells[].modes[mode].paired_total_ratio`为域内配对比中位数，`reset_fresh_ratio`为对应fresh分母；`lifecycle[]`保存96项判定；`effective[]`保存288项含自比的开发/确认组合。[CROSS_PLATFORM.json](WORKSPACE/study/crypto_study/round5/CROSS_PLATFORM.json) 的 `matched_cell_summaries` 保存全部576组跨平台中位数之比及双方p95/max，`decision_comparisons` 保存每项门槛一致性。

## 全部22项生命周期门槛翻转

以下每项均为Windows失败、Linux通过；没有反向翻转。cell名称保留原始标签，便于直接筛选日志。比值展示六位小数，判定使用未舍入值。

|域|cell|模式|Windows Reset/fresh|Linux Reset/fresh|
|---|---|---|---:|---:|
|confirm|n16384_q8_member_dispersed|reset-zlib-compact|1.022622|0.812837|
|confirm|n16384_q8_member_dispersed|reset-zlib-ordinary|1.017058|0.871377|
|confirm|n4096_q8_absent_clustered|reset-zlib-ordinary|1.001125|0.793834|
|confirm|n4096_q8_member_dispersed|reset-zlib-ordinary|1.014740|0.739996|
|dev|n16384_q8_absent_clustered|reset-zlib-compact|0.979688|0.759200|
|dev|n16384_q8_absent_clustered|reset-zlib-ordinary|1.025947|0.786897|
|dev|n16384_q8_absent_dispersed|reset-zlib-compact|1.059027|0.821796|
|dev|n16384_q8_absent_dispersed|reset-zlib-ordinary|0.951862|0.735841|
|dev|n16384_q8_member_clustered|reset-zlib-compact|0.976365|0.774283|
|dev|n16384_q8_member_clustered|reset-zlib-dictionary|0.915124|0.708964|
|dev|n16384_q8_member_clustered|reset-zlib-ordinary|1.012584|0.779530|
|dev|n16384_q8_member_dispersed|reset-zlib-compact|1.009709|0.760863|
|dev|n16384_q8_member_dispersed|reset-zlib-ordinary|0.979744|0.759861|
|dev|n4096_q8_absent_clustered|reset-zlib-compact|0.956727|0.794611|
|dev|n4096_q8_absent_clustered|reset-zlib-ordinary|1.020460|0.740151|
|dev|n4096_q8_absent_dispersed|reset-zlib-compact|0.991202|0.729437|
|dev|n4096_q8_absent_dispersed|reset-zlib-ordinary|0.934368|0.762677|
|dev|n4096_q8_member_clustered|reset-zlib-compact|0.970013|0.769647|
|dev|n4096_q8_member_clustered|reset-zlib-dictionary|0.923782|0.672042|
|dev|n4096_q8_member_clustered|reset-zlib-ordinary|0.968095|0.744229|
|dev|n4096_q8_member_dispersed|reset-zlib-compact|0.971772|0.743756|
|dev|n4096_q8_member_dispersed|reset-zlib-dictionary|0.918499|0.614315|

## 全部19组Linux中位时间更高的条件

下表比值等于Linux条件中位时间除以Windows对应条件中位时间。结果不支持“服务器所有情况均更快”。同一repeat编号不构成同时运行的跨平台配对。

|域|cell|模式|Linux/Windows中位数之比|
|---|---|---|---:|
|confirm|n16384_q1_absent_dispersed|zlib-dictionary|1.100025|
|confirm|n16384_q1_member_clustered|zlib-compact|1.398098|
|confirm|n16384_q1_member_clustered|zlib-dictionary|1.090835|
|confirm|n16384_q1_member_clustered|zlib-ordinary|1.041562|
|confirm|n16384_q1_member_dispersed|zlib-compact|1.325148|
|confirm|n16384_q1_member_dispersed|zlib-dictionary|1.003296|
|confirm|n4096_q1_absent_clustered|zlib-dictionary|1.238715|
|confirm|n4096_q1_absent_clustered|zlib-ordinary|1.258182|
|confirm|n4096_q1_absent_dispersed|zlib-dictionary|1.215980|
|confirm|n4096_q1_member_clustered|zlib-compact|1.124709|
|dev|n16384_q1_absent_dispersed|zlib-ordinary|1.005928|
|dev|n16384_q1_member_clustered|zlib-ordinary|1.347138|
|dev|n16384_q1_member_dispersed|zlib-compact|1.134827|
|dev|n4096_q1_absent_dispersed|zlib-compact|1.051880|
|dev|n4096_q1_absent_dispersed|zlib-ordinary|1.201314|
|dev|n4096_q1_member_clustered|zlib-compact|1.187137|
|dev|n4096_q1_member_dispersed|zlib-compact|1.185838|
|dev|n4096_q1_member_dispersed|zlib-dictionary|1.186972|
|dev|n4096_q1_member_dispersed|zlib-ordinary|1.104688|

## 应保留的失败与因果限制

Windows原有22项生命周期失败未被改写；Linux所有512项替代模式/域内条件仍未达到<=1.05时间容忍线，256个真正替代有效条件全部失败。q32/q128的反向条件保留于原eval与完整正式报告；旧准备阶段的失败和RED测试日志也保留在validation，不能将它们包装成新的正式性能观察。没有进行结果筛选、离群删除或重跑选优。

CPU、操作系统、计时后端和周围环境同时改变，故“Xeon导致Reset收益增加”“Linux消除了GC开销”“时钟提高带来了真实算法加速”等机制论断均超出证据。Fresh/Reset干预本身保持相同帧和fresh decoder；它能支持当前流程下这一实现选择的成本差异，不能单靠阶段计时识别微架构原因。

无真实网络或并发服务试验，无生产trace，无独立多种子或多机器总体样本。seed=3407是唯一种子，dev/confirm仍为同一生成方法的两个确定性域；每平台21次技术重复不构成21台独立机器。保留的compact padding-bit解析panic限制仍在，审计只支持合法固定输入的恢复与证明核验。

建议论文核心结论表述为：相同帧和执行顺序下，字节结构与联合工程负结果在两种环境中保持，而压缩器生命周期的预注册判断改变；这说明该生命周期结论需要附带执行环境。不得使用“提出新的压缩方法”“证明跨硬件普适”“联合优势已经实现”或“CPU独立效果已确认”。

## 本次复核所用文件指纹

|文件|SHA256|
|---|---|
|Round5 registration.json|`90465a3528fb621a94b0d2e877c90fa4c0049e9e0cb6f96b981c9e51b5bd2155`|
|Windows eval.json|`2617a14402ede638e133e8f508cae7e35bc3ac3fe0ae16679dfc798270f3c61c`|
|Linux eval.json|`ab51511021b1cfbeb1981a1a55daf675e576e982800266949481fe676da79c0a`|
|CROSS_PLATFORM.json|`b52b95fb078c21588b364cc3fa3123ea5a72b0b2c81c7f702f15ffd3d7c67fbc`|
|Linux log.jsonl|`42a44f351ed72483022f4fb86d8372f973f1918c4c1aace477e621b2a599af35`|

注册hash固定协议、源码与依赖，正式completion固定运行产物。报告文件属于事后解释，可以修订，但任何修订都应保持上述数据事实和原门槛。完整独立正确性证据见 [AUDIT.json](WORKSPACE/study/crypto_study/round5/AUDIT.json) 和 [AUDIT_LOCAL.json](WORKSPACE/study/crypto_study/round5/AUDIT_LOCAL.json)。
