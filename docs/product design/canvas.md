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
    * *设计*：强制性的 Source Anchor（源锚点）。

3.  **涌现性 (Emergence)**：
    * *原理*：孤立的信息通过连接产生新的意义。
    * *推导*：连接（Link）的操作必须像呼吸一样自然，且 AI 应该能“看见”这些空间关系并推导出结论。

---

## 2. 核心布局与交互框架 (Layout & Interaction Architecture)

### 2.1 视口与坐标系 (Viewport & Coordinate System)
* **无限平移 (Infinite Pan)**：支持鼠标右键/触控板双指自由拖拽画布。
* **智能缩放 (Semantic Zoom)**：
    * **L1 (微观)**：显示卡片全文、编辑器工具栏。
    * **L2 (中观)**：隐藏正文，仅显示标题、标签、核心摘要图表。
    * **L3 (宏观)**：仅显示 Group 标题和连接线，隐藏单个卡片。*解决画布变大后的混乱感。*

### 2.2 悬浮控制层 (Floating HUD)
参考 UI [image_b3c4d7.png] 的顶部药丸状菜单，该菜单应常驻顶部中央，不随画布移动。

* **Visualize (视觉化)**：默认模式，自由拖拽。
* **Internalize (内化)**：切换视图（如将画布卡片转为 Anki 复习模式）。
* **Create (创作)**：线性化模式（Linearization），将画布选中的卡片序列化为大纲。

---

## 3. 原子组件设计 (Atomic Component Design)

画布上的元素不应仅仅是“文本框”，它们是具备功能性的对象。

### 3.1 核心组件：The Knowledge Card (知识卡片)
这是画布的基本单位，对应 UI 中的白色方块 [image_b3c4f5.png]。

| 属性 | 设计细节 | 第一性原理推导 (Why) |
| :--- | :--- | :--- |
| **来源锚点 (Source Anchor)** | 卡片顶部显示小图标（PDF/Video）+ 来源标题。点击时，**中栏 (Viewer)** 自动滚动到高亮位置。 | **溯源性**：用户必须能在 0.1 秒内验证知识的准确性。 |
| **原子化内容 (Atomic Content)** | 每张卡片只承载一个核心概念 (Concept)。如果内容过长，AI 自动建议拆分。 | **解耦**：只有原子化的知识才能被灵活重组。 |
| **可编辑性 (Block Editor)** | 卡片内部是一个微型 Notion 编辑器，支持 Markdown、嵌入代码块。 | **渐进式形式化**：从简单的摘录逐渐演变为自己的语言。 |
| **磁性边缘 (Magnetic Edge)** | 卡片边缘靠近其他卡片时，出现吸附对齐线。 | **秩序感**：减少整理布局的无谓操作。 |

### 3.2 结构组件：Sections & Connectors (分区与连接)

* **Section (分区容器)**：
    * 用户可以框选一组卡片创建一个 Section。
    * **AI 自动命名**：Section 创建后，后台 AI 分析内部所有卡片，自动生成标题（如“ReAct 核心原理”）。
    * **折叠 (Fold)**：双击 Section 标题，折叠为一个紧凑块，释放屏幕空间。
* **Connector (连接线)**：
    * 不仅仅是线，是**关系 (Relationship)**。
    * 线上支持添加 Label（如 "导致"、"反驳"、"支持"）。
    * **AI 推理**：如果卡片 A 和 B 内容高度相关，当用户拖拽靠近时，虚线连接隐约出现，提示用户建立链接（Auto-suggestion）。

---

## 4. 用户交互流程 (Interaction Flow)

### 4.1 从阅读到画布的“摘录流” (The Extraction Flow)
[cite_start]这是最核心的交互，必须做到极致流畅（类似于 LiquidText [cite: 71]）。

1.  **触发**：用户在 **中栏 (Viewer)** 选中一段 PDF 文本或截取一张图。
2.  **拖拽**：长按文本，文本“浮起”变成半透明卡片。
3.  **放置**：拖入 **右栏 (Canvas)**。
4.  **生成**：
    * 系统在画布坐标生成一张新 Card。
    * **自动摘要**：如果选中文本过长，Card 默认显示 AI 生成的一句话摘要，展开才看原文。
    * **建立回链**：后台写入 `block_id` $\leftrightarrow$ `source_anchor` 的映射。

### 4.2 AI 辅助的“思考流” (The Co-thinking Flow)
参考 UI [image_b3c4fb.png]，AI 不仅仅是聊天机器人，它是画布的“园丁”。

* **场景 A：我卡住了 (Writer's Block)**
    * 用户行为：在画布空白处双击，呼出 `Cmd+K` (Ask AI)。
    * 指令：输入 "根据左侧 PDF，列出 ReAct 框架的优缺点"。
    * 响应：AI 不在对话框回答，而是**直接在画布上生成**两个 Section（优点、缺点）和对应的 5-6 张卡片。

* **场景 B：帮我整理 (Organize for me)**
    * 用户行为：画布上散落了 20 张摘录卡片，乱七八糟。
    * 指令：框选所有卡片 -> 点击 AI 悬浮菜单 -> "Auto Cluster" (自动聚类)。
    * 响应：卡片自动移动动画，归类成 3 个 Section，并自动连线。

### 4.3 从画布到输出的“线性化流” (The Linearization Flow)
解决“记了很多笔记但写不出文章”的痛点。

1.  **路径规划**：用户按住 `Shift` 依次点击卡片 A -> B -> C -> D。
2.  **生成大纲**：点击顶部菜单 "Create" -> "Essay"。
3.  **转换**：
    * 系统弹出一个侧边抽屉（Drawer）。
    * 将选中的卡片按顺序转换为 Markdown 文档的段落。
    * 卡片标题 $\rightarrow$ 二级标题；卡片内容 $\rightarrow$ 正文。

---

## 5. 异常处理与边缘情况 (Edge Cases)

1.  **大量数据性能问题**：
    * *问题*：如果画布上有 1000 张卡片，浏览器会卡顿。
    * *解法*：使用 **Canvas 渲染** (如 HTML5 Canvas 或 WebGL) 而非 DOM 节点渲染（类似于 Figma 的技术栈）。仅渲染视口内的元素 (Virtual Scrolling)。

2.  **多源冲突**：
    * *问题*：一张卡片引用了 PDF A 和 视频 B。
    * *解法*：卡片底部显示多个 Source Badge。点击不同 Badge，中栏切换不同的源文件。

3.  **孤儿卡片**：
    * *问题*：源文件（PDF）被删除了，画布上的卡片还在吗？
    * *解法*：卡片内容**本地化存储**。即使源文件丢失，卡片内的文本/截图依然保留，但 Source Anchor 变灰显示 "Source Missing"。

