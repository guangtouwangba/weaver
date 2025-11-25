# 产品需求文档 (PRD): 全链路知识转化平台 v1.0

## 1\. 项目背景与目标

  * [cite\_start]**产品愿景**：构建一个“认知操作系统”，解决当前知识工作流碎片化的问题，打通从 **获取 (Acquisition) $\rightarrow$ 内化 (Internalization) $\rightarrow$ 链接 (Linking) $\rightarrow$ 创作 (Creation)** 的完整闭环 [cite: 4]。
  * [cite\_start]**本次迭代目标**：实现“智能获取引擎”与“深度内化工作台”的入口对接。通过 Dashboard 实现“一键从混乱文件夹生成结构化学习路径（Curriculum）”的核心价值 [cite: 130, 131]。
  * **核心价值主张**：将用户的“信息垃圾场”自动清洗为“结构化知识库”，并提供可视化的学习进度追踪。

-----

## 2\. 目标用户画像 (Persona)

  * **典型用户**：Alex，高级全栈工程师/深度研究员。
  * **痛点**：
      * [cite\_start]囤积了大量 PDF、YouTube 链接和网页书签，但从未整理 [cite: 3, 10]。
      * [cite\_start]面对混乱的资料库感到焦虑（FOMO），不知道从哪里开始学习 [cite: 12]。
      * [cite\_start]现有的 Notion/Obsidian 需要手动整理，认知负担太重 [cite: 89, 92]。

-----

## 3\. 用户旅程地图 (User Journey Map)

| 阶段 | 用户行为 (User Action) | 接触点 (Touchpoint) | 系统响应/后台逻辑 | 对应需求点 |
| :--- | :--- | :--- | :--- | :--- |
| **1. 意图触发** | Alex 想要学习“AI Agent 架构”，手里有一堆乱七八糟的 PDF 和几个 YouTube 视频链接。 | 桌面文件夹 | N/A | 痛点：混乱无需整理 |
| **2. 极速获取** | Alex 打开 Dashboard，将整个文件夹直接拖入“Create a New Knowledge Project”区域。 | **Dashboard (Drag & Drop Zone)** | [cite\_start]系统识别文件类型（PDF, URL, MP4）；自动提取元数据（作者、主题）[cite: 134]。 | [cite\_start]全模态捕获 [cite: 11] |
| **3. 智能转化** | Alex 点击 **“Generate Curriculum”** 按钮。 | **Dashboard (CTA Button)** | [cite\_start]LLM 分析所有素材内容的语义关联；生成大纲；提取 YouTube 字幕 [cite: 133][cite\_start]；生成 Flashcards [cite: 141]。 | [cite\_start]自动去噪与结构化 [cite: 10] |
| **4. 概览与规划** | 页面刷新，出现“AI Agent Architecture”卡片，显示进度 0%。 | **Dashboard (Active Topics)** | 创建项目实体；计算预计学习时长；建立知识图谱索引。 | 进度可视化 |
| **5. 深度内化** | Alex 点击卡片，进入沉浸式学习模式（阅读/观看/测验）。 | **Active Topics Card** | [cite\_start]打开“液态阅读视图”或“视频笔记视图” [cite: 137]。 | [cite\_start]主动阅读/内化 [cite: 15] |
| **6. 语义检索** | 学习过程中，Alex 在顶部搜索栏问：“Agent 的记忆机制是什么？” | **Global Search Bar** | [cite\_start]向量数据库检索 (RAG)，跨文档引用回答 [cite: 30, 90]。 | [cite\_start]知识链接/检索 [cite: 19] |

-----

## 4\. 详细功能需求与 User Stories

### 模块一：智能获取区 (Smart Ingestion & Setup)

**对应 UI 区域**：页面上方虚线框 "Create a New Knowledge Project"

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-01** | 作为用户，我希望能够直接**拖拽文件夹或多个文件**到上传区，而不需要手动分类。 | 1. 支持拖拽操作。<br>2. 支持格式：PDF, Markdown, Web Links (HTML/URL), YouTube 链接。<br>3. 无需用户手动打标签。 | **P0** | [cite\_start]"做最无感的收集器...支持一键保存" [cite: 131, 132] |
| **US-02** | 作为用户，我希望点击 **"Generate Curriculum" (生成课程)** 后，系统能把碎片资料变成有顺序的学习路径。 | 1. 点击后显示加载状态。<br>2. 后台 LLM 进行聚类分析，识别核心主题。<br>3. 输出结果必须包含逻辑顺序（如：先看这个视频，再读这篇 PDF）。 | **P0** | [cite\_start]"从信息获取到知识创造...自动进行预处理" [cite: 4, 10] |
| **US-03** | 作为用户，当我上传 **YouTube 链接**时，系统应自动处理视频内容。 | 1. 自动下载/提取字幕 (Transcript)。<br>2. 自动生成带时间戳的摘要。<br>3. 视频内容可被搜索检索到。 | **P1** | [cite\_start]"自动下载字幕、生成时间戳摘要" [cite: 133] |

### 模块二：活跃项目看板 (Active Topics Dashboard)

**对应 UI 区域**：页面下方 "Active Topics" 卡片流

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-04** | 作为用户，我希望看到**每个学习项目的元数据统计**，以了解资料规模。 | 1. 卡片显示：文档图标+数量、视频图标+数量、链接图标+数量（如 UI 中的 📄50 📺12 🔗20）。<br>2. 显示自动生成的标签 (e.g., Deep Learning)。 | **P1** | [cite\_start]"元数据自动提取" [cite: 11] |
| **US-05** | 作为用户，我希望看到**学习进度条 (Progress Bar)**，以量化我的内化程度。 | 1. 进度条根据“已读/已看/已测验”的 Block 数量计算。<br>2. 显示百分比 (e.g., 35% Complete)。<br>3. 点击 "Start/Continue Learning" 直接跳转到上次位置。 | **P1** | [cite\_start]对抗“遗忘曲线”，提供成就感 [cite: 16] |
| **US-06** | 作为用户，我希望能够对卡片进行**管理操作**（归档、删除、重命名）。 | 1. 卡片右上角 `...` 菜单提供编辑选项。<br>2. 支持修改自动生成的项目名称。 | **P2** | 基本交互需求 |

### 模块三：全局语义检索引擎 (Global Semantic Search)

**对应 UI 区域**：顶部搜索栏 "Search your knowledge base or ask a question..."

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-07** | 作为用户，我希望通过**自然语言提问**来搜索知识库，而不是仅通过关键词。 | 1. 支持自然语言输入（如：“React 性能优化的主要策略是什么？”）。<br>2. 基于 RAG 技术返回综合答案。<br>3. 答案必须标注来源（Source Citation）。 | **P0** | [cite\_start]"基于引用的生成 (Grounded Generation)... 解决幻觉" [cite: 40] |
| **US-08** | 作为用户，我希望在搜索时能触发**跨项目的知识关联**。 | 1. 搜索结果应包含不同 Project 中的相关 Block。<br>2. 提示“你正在搜索的概念与 Project B 中的某条笔记有关”。 | **P2** | [cite\_start]"语义检索... 意外发现 (Serendipity)" [cite: 19] |

### 模块四：导航与系统架构 (Navigation & System)

**对应 UI 区域**：左侧 Sidebar (Logo, Inbox, Dashboard, Brain Icon)

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-09** | 作为用户，我希望通过 **Brain Icon (大脑图标)** 进入知识图谱视图。 | 1. 点击第三个图标，切换至可视化图谱模式。<br>2. 展示项目之间的节点连接。 | **P2** | [cite\_start]"图谱可视化... 从点到网" [cite: 19, 146] |
| **US-10** | (非功能需求) 数据隐私与本地优先。 | 1. 允许用户选择“本地存储 + 加密云同步”。<br>2. 核心索引文件保存在本地。 | **P0** | [cite\_start]"本地优先 (Local-First) 策略" [cite: 158] |

-----

## 5\. 关键交互细节 (UX Micro-interactions)

1.  **拖拽反馈**：当用户拖拽文件进入虚线框时，虚线框应高亮变为实线，并显示“Release to ingest”提示，背景色微变，营造“吸入”感。
2.  [cite\_start]**Curriculum 生成动效**：点击生成后，不要只显示 Loading 转圈。显示具体的 AI 处理步骤文案，例如：“Reading PDFs...”, “Extracting Audio Transcripts...”, “Structuring Knowledge Graph...”。这能降低用户等待焦虑并体现系统智能感 [cite: 24]。
3.  **卡片状态**：未开始的项目显示“Start Learning” (蓝色 CTA)，进行中的项目显示进度条 + “Continue” (如 UI 右侧卡片)。

