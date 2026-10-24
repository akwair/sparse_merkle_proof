# 同一 Celestia 宿主中的合法证明结构：静态可行性审计

审计日期：2026-10-23。仅阅读 Round3 源码与报告；本文件不报告新测量，也不改变旧实验、默认算法或 seed=3407。后续 Round4 正式方案以其已登记 PLAN 为准。

## 结论

值得做同一 Celestia 宿主中的实证改进：固定合法树、改变唯一查询的批量与路径局部性，比较原生 ordinary/compact、全 bundle 字典以及 whole-bundle zlib，能回答比两个不同语义宿主排名更清楚的问题。它是已有表示和压缩机制的条件评估，不自动成为新密码协议或新 multiproof。

最重要的限制是：自然生成树上选择共享前缀查询，可以控制查询局部性，却不能保证证明深度和零占位率同时恒定。应完整记录这些量，不把观察到的所有变化归因于局部性；q=1 是没有跨证明重用的阴性对照。

## 代码依据

- [treehasher.go](WORKSPACE/study/crypto_study/round3_qpc/external/smt/treehasher.go:30)：实际路径是 SHA256(key)。[旧 fixture 生成器](WORKSPACE/study/crypto_study/round3_qpc/external_runner/main.go:295) 的 key 已是字符串的 SHA256，因此分类必须再次计算实际路径 SHA256(key)，不能按原字符串或 key 自身前缀分类。
- [updateWithSideNodes](WORKSPACE/study/crypto_study/round3_qpc/external/smt/smt.go:214) 按真实路径的公共前缀建立节点，并在未分叉层插入 32 字节全零占位节点；[sideNodesForRoot](WORKSPACE/study/crypto_study/round3_qpc/external/smt/smt.go:314) 遇叶节点或空节点即停止，故证明不固定包含 256 个兄弟节点。
- [原生证明生成](WORKSPACE/study/crypto_study/round3_qpc/external/smt/smt.go:408) 去掉 nil，保留真实的全零节点；[原生压缩](WORKSPACE/study/crypto_study/round3_qpc/external/smt/proofs.go) 只省略每条证明内的零占位节点，不实现跨证明字典或验证合并。
- [旧 runner](WORKSPACE/study/crypto_study/round3_qpc/external_runner/main.go:273) 在计时外建树/生成证明，计时包含 encode、decode、相同逐证明验证；模式内输出与归档 frame 比较、结构等价检查在计时后进行。zlib 当前每帧创建和关闭 writer，压缩完整 bundle，非逐证明独立压缩。
- [旧报告](WORKSPACE/study/crypto_study/round3_qpc/REPORT.md) 的 11340 是重复计时行；其两个宿主语义不同。新研究应保留负结果，不重新解释为原生算法被错误击败。

## 推荐自然树矩阵与构造

采用母方案：N∈{4096,16384}，q∈{1,8,32,128}，member/absent，scatter/cluster，dev/confirm 两个预先命名域，三个固定 bucket/bundle。全部生成及模式顺序仍只用 seed=3407。共 192 bundle；九模式、21 次配对技术重复对应 36288 行，不能称为 36288 个独立数据集。

1. 用冻结的确定性 key/value 流，通过原生 Update 构造 SHA256 树，不修改哈希函数，不直接构造 proof。
2. 计算每个候选 key 的 SHA256 路径，按最高四位进入 16 个 bucket。cluster 从预先指定的一个 bucket 取 q 个不同 key；scatter 用预先固定的分桶规则取得 q 个不同 key。bucket 和取样规则在结果前固定，禁止按压缩率或时间选 bucket。
3. absent 候选从独立命名的确定性流生成，并对完整实际 key 检查不在已插入集合。按实际路径分桶后通过原生 Prove 取得证明。应记录落空节点型与不匹配叶型，不能默认两类 absence 开销相同。
4. 保留 N、域内相同树和 root；同一 bundle 的所有模式使用完全相同的有序 key/value/proof 序列。跨 q 是否嵌套、跨 bundle 是否重用 query 应预先定义；唯一性要求至少在每个 bundle 内成立。
5. 不足 q 的预定 bucket 应明确失败，不能悄悄换成测得更好的 bucket。N=4096 时每个四位桶期望 256 个成员，但期望值不是容量保证，必须实际断言。

q=1 的两种取样会选到不同 key，但不会产生跨证明重用；其差别只能解释为不同 query 的结构差异或计时波动。q>1 的 prefix 选择仍会伴随 d/k 分布变化，需做结构分解，不宣称独立操纵了深度。

## 必需的机制诊断

对每个 proof 记录 d=兄弟节点数、z=全零节点数、k=d-z、非成员叶材料字节数；对每个 bundle 记录 S=全部兄弟节点出现次数、U=全部节点 hash 的去重数。若字典包含零 hash，U 必须把它算作一个条目。

另外单独计算非零跨证明重复：令 A_i 为第 i 条 proof 的非零 side-node hash 集合，则 R=sum|A_i|-|union A_i|。这能将跨证明重复与一条 proof 内重复出现的零节点分开。还应保存每个 query 的四位前缀及顺序、每种 frame 的精确字节数；不把哈希值数量直接当成 zlib 必然可压缩的字节数。

旧 compact 的精确节省是 sum[32z-2-ceil(d/8)]。按 U 个 32 字节字典条目、每个出现位置用 uint16 索引、额外 uint16 字典长度且其他字段相同的格式，ordinary 相对 dictionary 的精确节省为 30S-32U-2。这两式是格式核对工具，不是延迟模型或独立算法贡献。

## 如需真正独立控制 d/z，可用合法输入的探针

以下是静态代码推导，尚未执行；不建议并入当前自然树主矩阵。它们可在将来单独注册为构造性机制测试，不能伪装成实际业务分布。

- 两叶树：寻找实际 SHA256 路径恰好共享 h 位前缀的两个不同 key，正常 Update 后，每条成员证明预计 d=h+1、z=h、k=1。该探针会同时改变深度和零节点，不能声称二者被分离。
- 单目标梳状树：固定目标 key x；对选定分叉位置集合 J，插入与 x 共享 j 位、在第 j 位相反的一个 companion key。要求最深位置 d-1∈J，则目标证明预计 d 固定、k=|J|、z=d-|J|。再固定 0∈J，将所有补充叶放在与 x 首位相反的已有支路中，可补足相同 N，而不增加目标路径的分叉数。这样可做 d∈{8,16}、z∈{0,4} 的四个合法性单元探针。
- 上述筛键只涉及短前缀匹配，不改变 SHA256、不解密、不伪造 proof；筛选候选数量、上限和失败策略须记录，生成开销不能隐藏成实际服务免费操作。得到 key 后仍只通过 Update/Prove/VerifyProof 产生与核验材料。
- 多查询规则树也可用合法短前缀筛键构造：八个顶层组、每组 32 个叶，组内插入 h 个无分叉层，则 N=256、d=8+h、k=8、z=h；同组查询与跨组查询可保持 d/k 相同而改变共享节点。然而它是人为条件分布，当前自然树方案更适合作为主研究。

## 冻结前功能探针与计量边界

1. 原生 Update 后，每个插入 key 的 Get/value 正确；每条查询经原生 Prove/VerifyProof 通过。拒绝重复 query；assert bucket 和 absent 条件；保存树输入、root、query 顺序及 proof。
2. 九模式解码后与同一原生 bundle 完全等价，保持顺序、重数、非成员材料、全部节点与同次数验证。改 root/key/value/节点/索引、截断、尾部垃圾、非法计数必须拒绝。
3. 字典以确定的首次出现顺序编号，不以 Go map 遍历决定 wire 顺序；验证上述精确字节恒等式。它不合并哈希验证，不得称为密码 multiproof。
4. fresh 与 Reset zlib 都压缩整个同样的 payload；每帧 Close，下一帧 Reset，无跨消息压缩历史。Reset、输出缓冲清理、写入、Close、解码与验证包含在相应计时中。writer 首次建立、后续复用的范围明确披露；预热不应偷偷发生在构造器。
5. 保留原四模式逐位回放作为默认行为不变证据。QPC 单调性/频率检查、对象存活、GC 默认、日志计时外写、配对模式顺序及重复行完整性继续保留。内存/分配诊断应另跑而不污染正式延迟计时；不把单进程 codec 时间写成网络或并发服务结果。
6. 三个 bundle 不等于三棵独立树，两个命名域不等于两个种子，技术重复不扩增独立工作负载数。先报告固定条件下的配对结果与范围；单 seed=3407 的适用边界保持披露，不要求未经授权的多种子运行。

## 值得继续的判断

当前方案具备可实施的控制、已有强基线和可证伪问题：省零、跨证明去重、通用压缩及 writer 生命周期何时改变字节/本地时间权衡。它能把旧结果提升为同宿主内有机制解释的评估研究。是否足够发表仍取决于实际结果提供的可迁移认识和相关工作定位；192 个 bundle 或新增模式数量本身不能保证贡献，也不预先承诺更优排名。
