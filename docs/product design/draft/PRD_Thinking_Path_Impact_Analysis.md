# PRD: 思考路径（Thinking Path）+ 影响分析（Impact Analysis）+ 快速回到状态（Re-entry）

| Document Info | Details |
| --- | --- |
| **Version** | v0.1 |
| **Status** | Design Phase |
| **Scope** | Studio / Canvas / Assistant (Research workflow) |
| **Feature Type** | New capability set (core differentiation) |

---

## 1. 背景与问题（Context & Pain）

### 1.1 目标用户
- **终身学习者**：跨主题探索、长期积累、频繁回看与复盘。
- **研究者 / 知识工作者**：论文/报告阅读密集，最终需要产出（写作/汇报/方案）。

### 1.2 “今天仍未被解决”的核心痛点
> 不是缺少笔记/收藏/问答，而是缺少一种**可解释、可追溯、可长期复用的「理解记忆」**：

- **回到状态困难（Return after months）**：隔一段时间回来，能找到材料，但找不到当时“为什么相信/不相信”。
- **推理丢失（Lost reasoning）**：信息有了，链路没了——从证据到结论的路径不可见。
- **信念漂移不可控（Belief drift）**：新增资料后，不知道哪些结论被影响、哪里需要改写。
- **规模化合成难（Synthesis with accountability）**：从几十/上百来源写出结构化观点时，缺少“每个段落 → 证据集合 → 推理步骤”的可审计链。

---

## 2. 产品原则（Must align with current product design）

### 2.1 Minimal Canvas（画布是工作台，不是仓库）
- 上传/入库内容**不自动生成节点**。
- Canvas 初始保持纯净；只有用户拖拽/选择/明确动作才生成结构化产物。

### 2.2 Drag to Focus（拖拽即关注）
- 用户从侧边栏/阅读器/Assistant 把“材料/卡片/引用”拖上画布时，才进入思考空间。

### 2.3 Process Visible（过程可视化）
- 系统要帮助用户看到：
  - 观点如何形成（Thinking Path）
  - 观点如何被证据支撑/挑战（Evidence + Counter-evidence）
  - 新信息如何改变既有结构（Impact Analysis）

---

## 3. 核心概念（Key Concepts）

### 3.1 证据驱动的原子单元（Evidence-backed primitives）
在 Canvas 上引入三类一等公民：
- **Claim（主张）**：可被证据支持/反驳的陈述。
- **Question（问题）**：结构化的未知点/研究空洞。
- **Concept（概念）**：定义、同义/歧义、关联语境。

每个单元必须支持：
- **Source Anchors**：引用片段（highlight/excerpt）+ 来源（文档/网页/时间戳/页码）
- **Confidence / Status**：Tentative / Supported / Disputed（或 0–100 置信滑条）
- **Assumptions**：支撑该主张的前提（可被单独挑战）

### 3.2 Thinking Path（理解的历史记录）
- 记录“理解如何演化”：创建/编辑/连接/置信度变化/引用增删/合并拆分。
- 支持**回放**与**关键节点（checkpoint）**。

### 3.3 Impact Analysis（新信息的影响分析）
当用户引入新来源或更新来源时，系统能回答：
- “哪些 Claim 受到影响？”
- “影响原因是什么（哪些 excerpt 冲突/补强）？”
- “需要用户确认的变更有哪些（建议降级置信度/添加反例/改写输出）？”

### 3.4 Re-entry（快速回到状态）
- 让用户在几秒内恢复：
  - 当前主题的结构（Top clusters）
  - 未解决的问题（Open Questions）
  - 最近一次理解变化（Last checkpoints + what changed）

---

## 4. 用户体验与关键流程（UX & Flows）

### 4.1 Flow A：从阅读到“可追溯的主张”
1. 用户在左侧阅读器高亮一段文本（excerpt）。
2. 中栏 Processor/Assistant 提供“转为 Claim / Concept / Question”的轻量动作。
3. 用户**拖拽**该卡片到 Canvas（触发创建节点）。
4. 新节点自动携带 Source Anchor，且默认 confidence=Tentative。

### 4.2 Flow B：从对话到 Thinking Path（不破坏 Minimal Canvas）
- 默认不自动落盘到 Canvas。
- 当用户在 Assistant 中进入“深度探索”，提供显式开关：
  - **[Start Thinking Path]**：开始记录为一条 Path（可视化生成在 Canvas 的一个 group 内）
  - **[Save as Path after chat]**：对话结束后一键生成

### 4.3 Flow C：Impact Analysis（新增来源后自动提醒，但不强推）
1. 用户入库新文档/网页（仍不自动生成节点）。
2. 系统后台完成索引后，在项目层级显示：**“X potential impacts”**。
3. 用户点击进入 Impact Review：
   - 列表：受影响的 Claims（按影响强度排序）
   - 每条展示：冲突/补强 excerpt 对比 + 建议动作
4. 用户选择：接受建议 / 手动调整 / 忽略（并可标注原因）。

### 4.4 Flow D：Resume Mode（回到状态）
- 打开项目时（或从 Dashboard 进入项目）提供一屏 Resume：
  - Top 3 clusters（主题团簇）
  - Open Questions（未解决）
  - Recent changes（最近 7 天的 checkpoints）
  - “Continue from checkpoint”按钮

### 4.5 Flow E：Drag-to-Compare（对比工作台）
- 用户拖 2–5 个 Claims/Concepts/Source Anchors 到 Compare Strip。
- 生成结构化对比卡（定义/假设/证据/方法/结论/局限）并可落到 Canvas。

---

## 5. 功能规格（Feature Specs）

### 5.1 Node Types（Canvas 节点类型）
- Claim Node
  - title, statement
  - confidence, status
  - evidence list (anchors)
  - counter-evidence list (anchors)
  - assumptions
  - last_updated, created_from (drag/chat/manual)
- Question Node
  - question text
  - status (open/investigating/answered)
  - related claims / concepts
- Concept Node
  - definition(s)
  - synonyms / disambiguation
  - related concepts

### 5.2 Thinking Path View（路径视图）
- Path timeline（事件流）
- Checkpoints（用户手动或系统建议）
- Replay（按时间回放 Canvas 变化，至少支持“跳转到 checkpoint”）

### 5.3 Impact Review（影响审阅）
- 触发条件（MVP）：
  - 新来源与现有 Claim 的 anchors / embeddings 高相似度
  - 或新来源包含明确反驳措辞（简单规则）
- 展示结构：
  - Affected Claim
  - Why（引用对比）
  - Suggested actions（降级/添加反例/拆分/创建新 Claim）
- 用户决策记录（Audit）：
  - accept / edit / ignore + reason

### 5.4 Resume Mode（重返状态页）
- clusters：基于图结构的社区发现/简化聚类（MVP 可先用“连接密度 + tag”）
- unresolved：open questions
- recent：最近变更（from Thinking Path events）

### 5.5 Writing / Synthesis（可选增强，强约束防幻觉）
- 仅对用户选中的 Canvas 区域与 sources 做输出
- 每段必须带引用或标记“needs evidence”

---

## 6. 数据与可追溯性（Data & Provenance）

### 6.1 Source Anchor（引用锚点）
最小字段：
- source_id（doc/url）
- locator（page, timecode, paragraph id）
- quote（excerpt）
- created_at, created_by

### 6.2 Audit Trail（审计链）
- node_event：create/update/link/unlink/confidence_change/anchor_add/remove
- impact_event：detected/accepted/ignored + reason

---

## 7. Non-Goals（非目标）
- 不追求“自动把整个知识库变成图谱并铺满画布”。
- 不做完全自动化的“真理判定”；Impact Analysis 提供建议与证据对比，最终由用户确认。
- 不把 Assistant 变成通用问答入口；必须被“当前选区/当前画布区域”强约束。

---

## 8. 成功指标（Success Metrics）

### 8.1 Re-entry
- TTR（Time to Re-orient）：用户从打开项目到“继续工作”的时间（目标：< 60s）
- Checkpoint revisit rate：回放/跳转到 checkpoint 的比例

### 8.2 Accountability
- Citation coverage：输出内容中带有效 anchors 的比例
- Unsupported claim rate：被标记为“needs evidence”的段落比例下降

### 8.3 Impact Analysis
- Impact review open rate：用户打开影响审阅的比例
- Accepted suggestions rate：建议被采纳/部分采纳的比例
- “Oops I forgot why” survey：主观反馈下降

---

## 9. 开发优先级与里程碑（Priority Plan）

### P0（MVP：先解决“理解记忆”与“回到状态”）
1. **Evidence-backed Claim（最小闭环）**
   - Claim 节点 + Source Anchors + confidence/status
   - 从阅读器/Assistant 生成卡片，但**仅拖拽到 Canvas 才创建节点**
2. **Thinking Path（事件记录 + checkpoint）**
   - 记录节点事件
   - checkpoint（手动）+ 最近变更列表
3. **Resume Mode（重返状态）**
   - Top clusters（简化）+ Open Questions + Recent changes

> 交付定义：用户能用少量节点建立“可追溯主张”，并在几个月后快速理解当时的推理线索。

### P1（增强：解决“信念漂移不可控”与“对比困难”）
1. **Impact Review v1（规则/相似度驱动）**
   - 检测受影响 Claims
   - 展示冲突/补强 excerpt 对比 + 建议动作
2. **Drag-to-Compare（对比工作台）**
   - 2–5 项对比生成结构化卡
3. **Thinking Path Replay（基础回放）**
   - 从 checkpoint 回放关键变更（可先只回放事件，不做复杂动画）

### P2（差异化护城河：规模化合成与更智能的影响）
1. **Impact Analysis v2（更精细的“影响强度/原因归因”）**
2. **Controversy / School-of-thought Map（争议结构图）**
3. **Synthesis with accountability（写作输出强约束 + 引用覆盖）**
4. **“What would change my mind?”（反事实触发器）**：把“改变信念的条件”结构化并可被新资料触发

---

## 10. 依赖与风险（Dependencies & Risks）
- **依赖**：可靠的 Source Anchor（定位与引用持久性）、基础图数据结构、索引/嵌入。
- **风险 1（违背 Minimal Canvas）**：任何自动创建节点都必须是用户显式触发（Start Path / drag）。
- **风险 2（噪声影响提醒）**：Impact 检测容易过多；MVP 必须做“强阈值 + 可关闭 + 只在项目级提示”。
- **风险 3（信任）**：所有建议必须展示“为什么”（excerpts），不能只给结论。
