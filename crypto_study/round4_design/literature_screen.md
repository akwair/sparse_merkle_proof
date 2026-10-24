# Round4：原生 SMT 证明传输的定向文献筛查

核实日期：2026-10-23。范围：少量直接近邻的一手全文、规范和源代码；不是系统综述。本文件只提出研究边界，不登记实验方案、不实现代码、不报告新实验结果。

## 判断

**条件性保留为受控工程实证；“新压缩算法／新密码协议”方向不成立。** 默认节点省略、bitmap、共享路径多证明、紧凑索引／形状表示以及通用压缩均已有明确先例。特别是 Ipsilon 已把多证明、零省略和 Snappy 放在同一真实工作负载中比较，不能再把这些组合或“压缩效果取决于证明大小”当作新发现。

这次读取的资料没有给出与拟定设计完全相同的、原生 Celestia SMT 上“不同查询的结构局部性 × 批量 × 树规模 × 压缩器生命周期”的字节和本地处理成本矩阵。但**有限检索未找到同一矩阵不构成创新证据**。可新增的是特定宿主下有复现价值的选择边界、反例和成本解释，而不是新机制。是否足以形成 CCPE 论文仍取决于结果能否回答实际工程选择，以及工作负载和边界是否有说服力。

## 直接近邻及读取状态

### 1. Ipsilon：Code Merkleization Practical Implementation & Analysis

- 作者：Hugo De la cruz / Ipsilon Team；页面未核实到明确出版日期，不补造期刊或 DOI。
- [原始全文](https://notes.ethereum.org/@ipsilon/code-merkleization-implementation-analysis)。已读正文、Proof Format、Results 和附录；属于团队技术分析，不称同行评审论文。
- 覆盖 1,016,695 个非空 Ethereum 主网块。Baseline 已是 SSZ Merkle multiproof；Slim 省略可重建的零子树哈希；另测 Snappy。作者明确说明 Slim 加 Snappy 只在小证明上优于压缩 Baseline，故未纳入该项主比较。本文公开的是证明字节分析，未报告编码、解码和验证耗时矩阵。
- [公开数据入口](https://github.com/hugo-dc/cm-analysis/tree/master/data)；本次核实到文章链接，未重新下载或复现数据。
- **对本题的限制：**“结构省略 vs 通用压缩”的宽泛题目已有直接先例。其代码分块、RLP 和交易证明语义与原生 SMT 查询不同；可测这种差异，不能把差异直接称为方法创新。

### 2. Celestia SMT：既有 compact proof

- [官方包文档](https://pkg.go.dev/github.com/celestiaorg/smt)：本次页面显示 v0.3.0、2022-04-14、MIT；读取了相关类型和函数文档。另读取 Round3 保存的 `external/smt/proofs.go` 完整实现；固定实验版本应继续以项目 manifest 的 commit 为准，不能拿文档版本替换它。
- `SparseCompactMerkleProof` 已含 `BitMask` 和 `NumSideNodes`。置位表示该位置为 placeholder；`CompactProof` 删除这些节点，`DecompactProof` 恢复，`VerifyCompactProof` 随后调用普通验证器。非成员证明和可更新证明还有附加字段。
- **对本题的限制：**bitmap 零省略及“恢复后使用原验证器”均非新贡献。必须以实际原生 `SideNodes` 为基线，不能先补齐 256 层再展示压缩优势。完整字节应计入掩码、长度、附加叶数据和帧元数据。

### 3. Ramabaja 与 Avdullahu：Compact Merkle Multiproofs

- Lum Ramabaja, Arber Avdullahu，arXiv:2002.07648v2，2020-02-24。[元数据](https://arxiv.org/abs/2002.07648v2)，[5 页全文](https://arxiv.org/pdf/2002.07648v2)。已读全文；仅按预印本引用，未核实同行评审出版版本。
- PDF 第 1 页 Related Work 已承认近似先例；第 1–2 页区分 sparse multiproof 与 sparse Merkle tree。第 2–4 页描述共享路径、多余辅助节点去除和仅传目标叶索引的紧凑表示；第 4 页给出结论。全文未提供本题所需的通用压缩与本地阶段计时矩阵。
- **对本题的限制：**共享路径和批量证明去冗余早已有之；不能把普通节点字典称为新 multiproof。文中的 Fig. 6 取自其参考文献 [3]，不能当作本文独立的新性能实验。

### 4. Ethereum consensus-specs：Merkle proof formats

- [固定提交的官方规范](https://github.com/ethereum/consensus-specs/blob/b5c3b619887c7850a8c1d3540b471092be73ad84/ssz/merkle-proofs.md)。已读 generalized indices 与 Merkle multiproofs 节及相关函数；属于规范，不是实证论文。
- `get_helper_indices` 合并分支节点并排除可从目标路径推导的节点；`calculate_multi_merkle_root` 共同重建根。它说明同根多查询的共享验证结构，不能简化成仅对单证明字节做独立压缩。
- **对本题的限制：**Round4 是同根查询 bundle，因此真正 multiproof 是直接替代方案。旧稿针对顺序更新、不同根的排除理由不再适用。若不实现 multiproof，结论必须限定为兼容现有逐项验证 API 的传输表示，不能声称最佳通信或最佳批量验证。

### 5. EIP-8364：SSZ Compact Multiproofs

- Zsolt Felföldi、Cayman、Lodekeeper，创建于 2026-08-04。[官方全文](https://eips.ethereum.org/EIPS/eip-8364)。已读 Specification、Rationale、Test Cases、Security Considerations；核实时状态为 **Draft**，不是已采纳标准或实测性能论文。
- 用形状描述符编码多证明；包含 N 个请求／辅助节点时描述符为 2N−1 bits。规范要求描述符与预期查询位置一致，并讨论长度限制和递归资源风险。
- **对本题的限制：**紧凑结构表示仍是活跃工程领域，不能假定已有索引格式就是最佳替代。其性能措辞属于提案论证，本次没有独立验证；不应用它替代我们的实测，也不必为凑近期引用而扩充不相干文献。

补充访问失败：Ramabaja 引用的 [Weald Technology 原文](https://www.wealdtech.com/articles/understanding-sparse-merkle-multiproofs/) 本次返回 502，未作为已读全文使用。没有据其标题推断额外实验覆盖。

## 剩余可问的具体问题

以下是基于上述来源的研究判断，不是文献已经证明的结论，也不是预先承诺会取得的正结果。

**建议核心问题：在同一原生 SMT 和同根、互不重复的查询中，已有兼容编码的字节—本地成本选择边界，如何随批量和实际共享结构变化；压缩器的 fresh／reset 生命周期是否改变选择？**

这比“重复越多越好压缩”更值得测量。将完全相同的请求重复多次，往往只证明可以去重请求或缓存结果；若服务允许这些操作，应用层去重就是直接竞争方案。主实验使用 distinct 查询可以避开这一人为优势；查询重复只能作为明确语义下的补充问题，不能承担主要贡献。

父任务当前拟定的 B=1/8/32/128、N=4096/16384、digest 共享 4-bit 前缀 vs 散布，可以作为结构受控的筛查。不过需满足以下解释边界：

1. **前缀是受控结构局部性。** 对先哈希再寻址的树，原始应用键相近并不意味着 digest 前缀相近。不得把筛选出的共享前缀直接写成真实业务 locality；应披露生成规则和筛选工作是否计入端到端范围。
2. **N 不是纯深度开关。** 树规模同时影响深度分布、空位、共享路径等。需记录实际节点计数、原生深度、placeholder 数和跨证明重复 digest 数；仅改变 N 不能独立证明“深度导致”某个时间变化。
3. **字典与 multiproof 不同。** 字典可以恢复所有原始证明和顺序后照旧逐项验证；多证明还会删除可推导节点并共享根重建工作。前者有 API 兼容价值，不能据此宣布后者没有优势。
4. **整 bundle 压缩是必要强基线。** 仅逐条 zlib 无法公平反映通用压缩对跨证明重复的利用。fresh/reset 应在相同输入和帧语义下比较，计入真实初始化、重用和重置成本；不能把状态复用优势误归为编码机制优势。
5. **指标应匹配所能声称的结论。** 全部线上字节、编码／解码／验证及合计本地时间是本地评价；没有网络实验就不称网络延迟改善。生成成本若在范围外，应明确标注。结果应容许压缩失败、空间膨胀或 Pareto 权衡。
6. **正确性不等于新安全证明。** 编码必须保留 root、key、value、非成员附加字段、查询顺序和多重性；解码边界检查与原验证器测试属于实现正确性证据。不能以 round-trip 测试推出新密码学安全协议。

## 保留／换题条件与 CCPE 定位

**保留条件：**能产生可复现、可解释的工程选择边界；使用原生证明和强二进制／整 bundle 压缩基线；对不同结构的结论由实际节点统计支持；明确固定实现、机器、种子和工作负载限制。当前 Round3 已有强二进制基线和 Celestia 外部实现，Round4 的增量应是同宿主受控结构和生命周期分析，不能再声称“首次引入外部实现”。

**停下或换题条件：**结果只是已知零省略在人工补齐证明上获胜、相同请求重复造成显然收益，或仅多跑参数而没有实际选择问题。若整 bundle zlib 已支配其它表示，仍可如实报告该负结果，但不能追加挑选工作负载来强求“新算法”故事。若希望提出所有同根批量证明中的最好方案，则目前范围不足，必须面对真正 multiproof；这会成为另一项工作。

**期刊判断：**这类公开认证数据结构的实现、性能与复现问题，原则上可按 CCPE 的 practice/experience 研究组织。但目前是一个库上的受控合成工作负载筛查，系统场景、真实访问分布、跨实现／跨机器稳定性仍较弱；本报告不把主题相关等同于达到发表门槛，也不承诺录用。最诚实的定位是已有机制的条件性经验评估。该判断是研究范围评估，不是期刊编辑意见。

本次未修改既有稿件、注册源、代码或实验数据，未运行正式实验。
