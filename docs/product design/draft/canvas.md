# 产品需求文档 (PRD): 深度内化画布 (The Deep Internalization Canvas)

## 1. 设计哲学 (Based on First Principles)

在设计功能之前，我们必须明确画布要解决的根本问题：

1.  **认知负荷最小化 (Cognitive Offloading)**：
    * *原理*：大脑的工作记忆（Working Memory）只能同时处理 4-7 个单位的信息。
    * *推导*：画布必须充当“外挂显存”。用户不需要记住所有信息，只需将它们摆在视觉空间中。
    * *设计*：卡片必须极简，支持“语义缩放”（离远了看标题，凑近了看细节）。

2.  **双向溯源 (Traceability)**：
    * *原理*：脱离上下文的知识是脆弱的（Hallucination & Misinterpretation）。
    * *推导*：画布上的每一个原子（Atom）都必须保留其“脐带”，连接回原始的 PDF/视频。
    * *设计*：强制性的 Source Anchor（源锚点）和快照机制。

3.  **涌现性 (Emergence)**：
    * *原理*：孤立的信息通过连接产生新的意义。
    * *推导*：连接（Link）的操作必须像呼吸一样自然，且 AI 应该能“看见”这些空间关系并推导出结论。

---

## 2. 核心布局与交互框架 (Layout & Interaction Architecture)

**注意：** 本文档描述的是 Studio 右栏 (Output OS) 中的核心应用 —— **Infinite Canvas**。它只是 Output OS 支持的众多视图之一（其他包括 Audio, Report, Flashcards 等）。

### 2.1 视口与坐标系 (Viewport & Coordinate System)
* **无限平移 (Infinite Pan)**：支持鼠标右键/触控板双指自由拖拽画布。
* **智能缩放 (Semantic Zoom)**：
    * **L1 (微观)**：显示卡片全文、编辑器工具栏。
    * **L2 (中观)**：隐藏正文，仅显示标题、标签、核心摘要图表。
    * **L3 (宏观)**：仅显示 Group 标题和连接线，隐藏单个卡片。*解决画布变大后的混乱感。*
    * **L3+ (热力/过滤)**：在宏观视图下，支持热力图（显示信息密度）或关键词过滤（高亮特定路径，其余变暗）。
* **导航器 (Mini-map)**：右下角常驻小地图，显示全局视口位置，并用色块标识不同 Section，防止迷失。

### 2.2 悬浮控制层 (Floating HUD)
* **Canvas Tools**: 位于画布内部的悬浮工具条（Select, Note, Shape, Connector）。
* **View Switcher (视图切换)**: 位于右栏顶部 Tab Bar（属于 Studio 框架层），用于切换出 Canvas 模式，进入 Audio 或 Report 模式。

---

## 3. 原子组件设计 (Atomic Component Design)

画布上的元素不应仅仅是“文本框”，它们是具备功能性的对象。

### 3.1 核心组件：The Knowledge Card (知识卡片)
这是画布的基本单位，对应 UI 中的白色方块 [image_b3c4f5.png]。

| 属性 | 设计细节 | 第一性原理推导 (Why) |
| :--- | :--- | :--- |
| **来源锚点 (Source Anchor)** | 卡片顶部显示小图标（PDF/Video）+ 来源标题。点击时，**左栏 (Source)** 自动滚动到高亮位置。 | **溯源性**：用户必须能在 0.1 秒内验证知识的准确性。 |
| **原子化内容 (Atomic Content)** | 每张卡片只承载一个核心概念 (Concept)。如果内容过长，AI 自动建议拆分。 | **解耦**：只有原子化的知识才能被灵活重组。 |
| **可编辑性 (Block Editor)** | 卡片内部是一个微型 Notion 编辑器，支持 Markdown、嵌入代码块。 | **渐进式形式化**：从简单的摘录逐渐演变为自己的语言。 |
| **磁性边缘 (Magnetic Edge)** | 卡片边缘靠近其他卡片时，出现吸附对齐线。 | **秩序感**：减少整理布局的无谓操作。 |
| **标签系统 (Orthogonal Tagging)** | 支持 `#Todo`, `#KeyConcept` 等标签。提供 **Matrix View** 辅助检查（Section x Tags）。 | **多维组织**：空间分组不足以表达所有维度。 |

### 3.2 结构组件：Sections & Connectors (分区与连接)

* **Section (分区容器)**：
    * 用户可以框选一组卡片创建一个 Section。
    * **AI 自动命名**：Section 创建后，后台 AI 分析内部所有卡片，自动生成标题（如“ReAct 核心原理”）。
    * **折叠 (Fold)**：双击 Section 标题，折叠为一个紧凑块，释放屏幕空间。
* **Connector (连接线)**：
    * 不仅仅是线，是**关系 (Relationship)**。
    * **AI Labeling**: 连线时 AI 自动建议关系类型（如 "Caused by", "Refutes"），用户仅需确认。
    * **AI 推理**：如果卡片 A 和 B 内容高度相关，当用户拖拽靠近时，虚线连接隐约出现，提示用户建立链接（Auto-suggestion）。

---

## 4. 用户交互流程 (Interaction Flow)

### 4.1 从 Processor 到 Canvas 的“沉淀流” (The Distillation Flow)
*这是 v3.0 架构下的新交互*

1.  **触发**：用户在 **中栏 (Processor)** 确认了 AI 提取的 Insight 或 Concept。
2.  **拖拽/点击**：用户将中栏的卡片拖入 **右栏 (Canvas)**，或点击 "Add to Canvas"。
3.  **放置**：
    *   系统在画布坐标生成一张新 Card。
    *   **建立回链**：Card 记录了它来自哪个 Source (左栏) 和哪次 AI 对话 (中栏)。

### 4.2 AI 辅助的“思考流” (The Co-thinking Flow)
参考 UI [image_b3c4fb.png]，AI 不仅仅是聊天机器人，它是画布的“园丁”和“副驾驶”。

* **场景 A：我卡住了 (Writer's Block)**
    * 用户行为：在画布空白处双击，呼出 `Cmd+K` (Ask AI)。
    * 指令：输入 "根据左侧 PDF，列出 ReAct 框架的优缺点"。
    * 响应：AI 不在对话框回答，而是**直接在画布上生成**两个 Section（优点、缺点）和对应的 5-6 张卡片。

* **场景 B：帮我整理 (Organize for me)**
    * 用户行为：画布上散落了 20 张摘录卡片，乱七八糟。
    * 指令：框选所有卡片 -> 点击 AI 悬浮菜单 -> "Auto Cluster" (自动聚类)。
    * 响应：卡片自动移动动画，归类成 3 个 Section，并自动连线。

* **场景 C: 对抗性思考 (Challenge Me)**
    * 用户行为：用户构建了 A -> B -> C 的观点链。
    * 响应：AI 生成红色边框卡片：“但这与 Source D 的实验结果矛盾”，迫使深度思考。

### 4.3 多态输出同步 (Polymorphic Sync)
Canvas 是“单一数据源”的可视化。
*   **修改同步**：在 Canvas 上修改卡片文字，切换到 **Report App** 时，对应的段落也会更新。
*   **结构同步**：在 Canvas 上调整连接顺序，切换到 **Audio App** 时，对话脚本的逻辑流也会随之改变。

---

## 5. 异常处理与边缘情况 (Edge Cases)

1.  **大量数据性能问题**：
    * *问题*：如果画布上有 1000 张卡片，浏览器会卡顿。
    * *解法*：使用 **Canvas 渲染** (如 HTML5 Canvas 或 WebGL) 而非 DOM 节点渲染（类似于 Figma 的技术栈）。仅渲染视口内的元素 (Virtual Scrolling)。

2.  **多源冲突**：
    * *问题*：一张卡片引用了 PDF A 和 视频 B。
    * *解法*：卡片底部显示多个 Source Badge。点击不同 Badge，左栏切换不同的源文件。

3.  **孤儿卡片**：
    * *问题*：源文件（PDF）被删除了，画布上的卡片还在吗？
    * *解法*：**快照机制 (Snapshotting)**。创建卡片时保存上下文 HTML/截图。即使源文件丢失，卡片内的文本/截图依然保留，Source Anchor 变灰但允许查看快照。
