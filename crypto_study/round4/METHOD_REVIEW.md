# 最终稿方法与冻结实现复核

日期：2026-10-23。只读检查论文、冻结源码、注册及既有运行元数据；未改测量源码、数据或论文，未重跑性能或分析。静态检查发现上游畸形输入边界后，经主代理明确授权，在独立目录执行了一次非计时功能探针，结果如下。

**结论：未发现使本次合法输入性能结果失效的方法描述矛盾。存在一项应明确披露的上游畸形输入处理缺口，及两处值得补清的计量范围。**

## 1. 已知 compact 畸形掩码可能异常退出

[稿件第83行](WORKSPACE/study/crypto_study/round2/manuscript/main.tex:83) 已谨慎限定为 tested compatibility/rejection behavior，并明确不构成完整 parser security；这没有声称拒绝所有非法输入。但现在已发现具体缺口，建议显式披露，而不只保留泛泛限制。

最小输入是上游 `SparseCompactMerkleProof{NumSideNodes: 1, BitMask: []byte{0x01}, SideNodes: nil}`，其他字段为空。静态处理路径为：

1. [compact sanityCheck](WORKSPACE/study/crypto_study/round4/external/smt/proofs.go:75) 检查掩码长度为 ceil(1/8)=1，满足。
2. [countSetBits](WORKSPACE/study/crypto_study/round4/external/smt/utils.go:19) 计入整个掩码的八个位；0x01 有一位为1。因此 `len(SideNodes)==1-1==0`，检查通过。
3. [DecompactProof](WORKSPACE/study/crypto_study/round4/external/smt/proofs.go:199) 只迭代一个有效位；MSB第0位为0，于第212行读取空数组的 `SideNodes[0]`，发生越界 panic。

隔离探针已经确认：该输入触发并被 `recover` 捕获的实际消息为 `runtime error: index out of range [0] with length 0`。合法掩码结构 `NumSideNodes=1, BitMask=0x80, SideNodes=nil` 无异常地恢复一个全零节点；另一个通过原生 Update/Prove/CompactProof 生成的成员证明，其mask=0x00、保留一个节点，无异常且 `VerifyCompactProof=true`。探针以全部预期差异得到确认结束，实际进程退出码为0。

证据：[探针源码](WORKSPACE/study/crypto_study/round4/diagnostic_compact/main.go)、[隔离模块](WORKSPACE/study/crypto_study/round4/diagnostic_compact/go.mod)、[实际结果](WORKSPACE/study/crypto_study/round4/diagnostic_compact/result.json)、[命令/实际exit/源码哈希](WORKSPACE/study/crypto_study/round4/diagnostic_compact/process_exit.json)。命令为在该目录用固定 Go1.27.3 工具链执行 `go run .`；无计时器、性能循环或外部目标。

根因是未使用的掩码 padding 位计入了节点数量，但没有要求这些位为零。旧 wrapper 在 compact 解码中直接调用该上游函数，因此 compact、zlib-compact 以及 reset-zlib-compact 路径继承此边界。新 dictionary 路径不调用 DecompactProof。这里没有修改上游，也没有把任意畸形材料作为测量工作负载。

建议论文增加一句具体限制，例如：

> The retained upstream compact decoder also has an unchecked mask-padding case that can panic on a malformed frame; the measured fixtures are valid upstream outputs, and the adapter is not a hardened untrusted-input boundary.

此缺口不改变合法帧恢复、字节恒等式或本次性能结果。不要直接修改已冻结 codec 后继续沿用旧测量；如未来用于接收不可信帧，应在另一个版本加入边界检查及回归测试，并另行评估开销。这是本地受控解析诊断，不代表外部漏洞披露或正常实验失效。

## 2. 可信 root 是前置条件，完整等价检查不在计时内

[固定任务描述](WORKSPACE/study/crypto_study/round2/manuscript/main.tex:51) 称 bundle 包含 trusted-root value；这可以成立，但读者应明确它是实验前置条件。[verify](WORKSPACE/study/crypto_study/round4/runner/legacy.go:244) 把解码后的 `Bundle.Root` 传给原生 verifier。[主计时循环](WORKSPACE/study/crypto_study/round4/runner/main.go:125) 在第133行完成最后计时后，才通过第140行 `equalBundle` 检查解码 root 等全部字段等于准备好的输入。

因此计时包含同一根关系的验证，但不包括取得/认证可信 root，也不包括完整 bundle 等价审计。当前第53及96行已有大部分范围说明，建议补一句：

> Roots are treated as externally trusted fixtures; root acquisition/authentication and the full restoration-equality audit are outside the timed path.

不应把仅校验收到的 root 与收到的 proof 自洽，描述成完整根认证协议。本稿没有作该协议贡献，但补明边界会避免误解。

## 3. Reset writer 的存活范围与确认域顺序

[稿件第60行](WORKSPACE/study/crypto_study/round2/manuscript/main.tex:60) 的 fresh/reset 行为与实现吻合：fresh每帧创建，Reset每帧清流状态后写入/关闭，各路径均分配新输出缓冲、创建新 decoder，无外部压缩字典。

更精确地说，[runner Encoder](WORKSPACE/study/crypto_study/round4/runner/main.go:80) 在所有 bundle 循环前创建一次；三个 retained writer 持续跨越全部192个 bundle。构造器不提前创建 writer；首次创建由预热触发。每个 bundle 的每模式仍执行两次预热。开发/确认 bundle 混合随机运行，而非先开发、再重新启动一个确认进程。稿件第96行“shuffled all bundle execution order”正确，若补一句生命周期范围，复现会更明确：

> Each retained writer lives across the complete shuffled run, including both input domains; two warmups precede each bundle, while every frame starts an independent stream.

两域是预先确定的输入复现，不是独立种子、不涉及训练选择，也不是隔离进程下的时间 holdout。稿件现有第87、104、164行对此没有误称。

## 4. 其余核对结果

| 项目 | 核对结果 |
|---|---|
| 旧四模式与默认行为 | `Encoder.Encode` 的旧四模式直接调用 legacy encode；空模式为 ordinary。稿件与保留的288帧回放证据一致。 |
| 字典 | 首次出现顺序、uint16计数/索引、零节点作为普通条目、逐证明恢复/验证均吻合。它是确定性 encoder，不是仅接受 canonical 字典的 parser；稿件未声称后者，无需加新检查改变测量。 |
| 边界 | decoder接受输入和膨胀数据的8MiB上界、最多256 items/256 side nodes及字段/索引/尾部检查吻合。旧 encoder 未普遍加固非法 caller 输入，稿件已有说明。字典上限为65535不同节点，未产生新增隐式超限格式。 |
| whole-bundle压缩 | 三种表示均整帧payload采用level6；fresh/Reset dictionary共用builder，ordinary/compact Reset复制旧路径、仅writer生命周期改变。无额外中间帧复制或复用reader/buffer。 |
| 工作负载 | keys/values域分离字符串SHA256；实际树路径再SHA256；cluster固定高四位0/5/10；dispersed采用hash排序；每bundle无重复；q为嵌套前缀。全部与稿件吻合。 |
| 输入依赖 | 同一域下N=4096的key/value集合还是N=16384集合的前缀。稿件没有声称四树独立；可以在更详细复现说明中写出这层嵌套，不把四棵可重建树当四个独立总体样本。 |
| 时钟与范围 | QPC频率10MHz，计时三段、总时间正值且和相等、KeepAlive、检查/日志在计时后；保留GC默认与GOMAXPROCS=8；稿件正确称wall time。 |
| 样本与阈值 | 192 bundles×21 repeats×9 modes=36288 observations；63配对值/cell；development幅度门槛与confirmation方向门槛区分正确；重复不当作独立数据集。 |
| 种子 | 所有生成与顺序约束仍为3407，两域不被称为两个种子；未提出或执行多种子。 |

## 5. 本次只读验证证据

读取 [registration.json](WORKSPACE/study/crypto_study/round4/registration.json)，用标准库SHA256检查其中37个文件在当前目录及 [运行source快照](WORKSPACE/study/crypto_study/round4/runs/conditions_001/source) 的字节：**74项哈希比对全部一致，0项不匹配**。读取既有 runner_exit 为0；既有 environment 记录 Go1.27.3、windows/amd64、QPC10,000,000Hz、8逻辑处理器、GOMAXPROCS=8，GOGC/GOMEMLIMIT/GOMAXPROCS环境覆盖值均为空，seed=3407。

本次没有运行正式计时、执行分析或改变任何登记文件；新增文件仅为本复核文档和独立 `diagnostic_compact` 目录内的非计时探针源码/结果。探针编译调用现有固定Go工具链与本地上游副本。
