# PRD: 深度内化工作台 (Deep Work Studio) v3.0

| 文档信息 | 内容 |
| :--- | :--- |
| **版本** | v3.0 (Input-Process-Output 重构版) |
| **核心变更** | 确立 "Input -> Processor -> Output" 核心流；右栏升级为 "Output OS" |
| **涉及设计图** | Studio 02, 03, 04, New Output Grid |

---

## 1. 核心理念 (Core Philosophy)

**"The Knowledge Distillation Flow" (知识蒸馏流)**

我们将工作台重新定义为一条从“原材料”到“智慧结晶”的流水线。
*   **Left (Input)**: The Source. (原材料：只读、外部)
*   **Center (Processor)**: The Bridge. (加工厂：AI Agent、语义桥接、去重)
*   **Right (Output)**: The Stage. (成品库：多态展示、无限扩展)

---

## 2. 全局布局架构 (Layout Architecture)

界面采用 **三栏流式布局 (3-Column Fluid Layout)**，严格遵循数据流向。

### 2.1 区域定义

| 区域 | 名称 | 角色 | 核心交互 |
| :--- | :--- | :--- | :--- |
| **Left** | **The Source (输入源)** | **Raw Data** | 文件导航、PDF/视频阅读器。**只读**。 |
| **Center** | **The Processor (处理器)** | **Intelligence** | AI 聊天、语义萃取、关联推荐。**暂存与处理**。 |
| **Right** | **The Stage (输出台)** | **Synthesis** | 多视图容器 (Canvas, Audio, Doc)。**创作与沉淀**。 |

---

## 3. 详细功能模块

### 3.1 Left Column: The Source (输入源)
*   **集成阅读器**：不再将阅读器放在中栏。用户点击左侧文件树，直接在左栏下方或覆盖文件树打开阅读器 (PDF/Video Viewer)。
*   **保持原始**：这里的内容是客观的、不可变的引用源。

### 3.2 Center Column: The AI Processor (智能处理器)
*这是 v3.0 的核心差异点。它是连接左右的桥梁。*

#### 功能特性
*   **Live Extraction (实时萃取)**：
    *   当用户在左侧高亮文本时，中栏自动提取核心概念卡片 (Atomic Cards)。
    *   **Anti-Hallucination**: AI 自动在卡片上标注 Source Anchor。
*   **Contextual Bridge (语义桥接)**：
    *   **查重与关联**：AI 实时扫描右侧 Output 和后台数据库。
    *   *Example*: "你正在阅读的概念 'Attention'，在你去年的笔记中出现过（点击查看）。建议直接引用，而不是新建。"
*   **Command Center**: 用户在这里向 AI 发指令（"把这些卡片转成一篇周报"），AI 在这里反馈处理进度。

### 3.3 Right Column: The Output OS (输出操作系统)
*这是 v3.0 的扩展性引擎。*

#### 3.3.1 架构：Tabs + Launcher
右栏不是一个单一的画布，而是一个支持多任务的操作系统。
*   **Top Bar (Tab System)**: 类似浏览器标签页，显示当前打开的输出视图 (e.g., `[ Canvas ]` `[ Audio ]`).
*   **The Launcher (能力矩阵)**: 当点击 "+" 或空闲时，显示 **Output Matrix**（网格菜单）。

#### 3.3.2 Output Matrix (能力矩阵)
一个可扩展的插件选择器，包含：
1.  **Visualize (可视化)**
    *   **Infinite Canvas**: 默认白板，节点网络。
    *   **Mind Map**: 自动布局的树状图。
2.  **Listen & Watch (视听)**
    *   **Audio Overview**: 生成 Podcast 风格的双人对话脚本并朗读。
    *   **Video Explainer**: 生成动态幻灯片视频。
3.  **Internalize (内化)**
    *   **Flashcards**: Anki 风格复习卡。
    *   **Quiz**: AI 生成的测试题。
4.  **Create (创作)**
    *   **Report / Essay**: 线性文档编辑器。
    *   **Presentation**: 幻灯片生成器。

#### 3.3.3 视图同步 (View Synchronization)
所有视图都是**同一组数据 (Knowledge Graph)** 的不同投影。
*   在 **Canvas** 里建立的连接，切换到 **Audio** 模式就是一段对话逻辑。
*   在 **Flashcard** 里修改的笔记，切换回 **Report** 模式就是一段正文。

---

## 4. 交互流示例 (User Flow)

**场景：从阅读到生成播客**

1.  **Input (Left)**: 用户打开 "AI Trends 2024.pdf"。
2.  **Process (Center)**:
    *   用户阅读并高亮关键段落。
    *   AI 在中栏弹出："提取到 5 个关键趋势，已去重。"
    *   用户点击："Generate Audio Overview"。
3.  **Output (Right)**:
    *   AI 自动在右栏创建一个新 Tab `[ Audio 2024 ]`。
    *   调用 **Audio Renderer**，显示播放器界面和滚动脚本。
    *   用户点击播放，开始听，同时脚本中提到的概念在左侧 PDF 自动高亮对应位置 (双向溯源)。

---

## 5. 开发优先级

1.  **P0**: 重构三栏布局 (Left-Reader, Center-Chat, Right-Container)。
2.  **P0**: 实现 Right Column 的 **Tab Manager** 和 **Launcher UI**。
3.  **P1**: 迁移 Canvas 到 Right Column 作为默认 App。
4.  **P1**: 实现 Center Column 的 "Live Extraction" (从左侧拖拽到中栏)。
5.  **P2**: 开发第二个 Renderer (如 Flashcards 或 Audio)，验证多态架构的可行性。
