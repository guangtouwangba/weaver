# 产品需求文档 (PRD): 全链路知识转化平台 v1.1

## 1. 项目背景与目标

*   [cite_start]**产品愿景**：构建一个“认知操作系统”，解决当前知识工作流碎片化的问题，打通从 **获取 (Acquisition) $\rightarrow$ 内化 (Internalization) $\rightarrow$ 链接 (Linking) $\rightarrow$ 创作 (Creation)** 的完整闭环 [cite: 4]。
*   [cite_start]**本次迭代目标 (v1.1)**：在 v1.0 基础之上，优化 Dashboard 的**长期留存体验**与**用户掌控感**。不仅关注“新项目创建”，更强化“每日学习习惯”的养成与“知识复习”闭环 [cite: 130, 131]。
*   **核心价值主张**：将用户的“信息垃圾场”自动清洗为“结构化知识库”，并提供可视化的学习进度追踪与智能复习提醒。

---

## 2. 目标用户画像 (Persona)

*   **典型用户**：Alex，高级全栈工程师/深度研究员。
*   **痛点**：
    *   [cite_start]囤积了大量 PDF、YouTube 链接和网页书签，但从未整理 [cite: 3, 10]。
    *   [cite_start]面对混乱的资料库感到焦虑（FOMO），不知道从哪里开始学习 [cite: 12]。
    *   [cite_start]**[新增 v1.1]** 创建了项目由于没有持续的反馈机制，很容易“三天打鱼两天晒网”，缺乏每日进入心流的触发器。

---

## 3. 用户旅程地图 (User Journey Map)

| 阶段 | 用户行为 (User Action) | 接触点 (Touchpoint) | 系统响应/后台逻辑 | 对应需求点 |
| :--- | :--- | :--- | :--- | :--- |
| **1. 意图触发** | Alex 想要学习“AI Agent 架构”，手里有一堆乱七八糟的 PDF 和几个 YouTube 视频链接。 | 桌面文件夹 | N/A | 痛点：混乱无需整理 |
| **2. 极速获取** | Alex 打开 Dashboard。如果是老用户，拖拽区已折叠，他点击 "+" 展开或直接拖入侧边栏 Inbox。 | **Dashboard (Smart Drop Zone)** | [cite_start]系统识别文件类型（PDF, URL, MP4）；区分“单文件(Inbox)”与“文件夹(Project)” [cite: 134]。 | **[优化] 智能分流** |
| **3. 预览与微调** | Alex 点击 **“Generate Curriculum”**。系统弹出预览窗，展示 AI 规划的路径。Alex 调整了两个步骤的顺序。 | **Curriculum Preview Modal** | LLM 聚类分析 -> 生成草稿 -> 用户确认 -> 正式建库。 | **[新增] 掌控感** |
| **4. 每日回顾** | (次日) Alex 再次打开应用。顶部显示“Daily Review: 12 Cards”。 | **Daily Review Widget** | 基于间隔重复算法 (SRS) 推送需复习的卡片。 | **[新增] 习惯养成** |
| **5. 上下文恢复** | Alex 看到“AI Agent”卡片上显示：“Continue reading: Page 12 of *Attention is All You Need*”。 | **Active Topics Card** | 记录上次视口位置；点击直接跳转至该位置。 | **[优化] 极速心流** |
| **6. 语义检索** | 学习过程中，Alex 在顶部搜索栏问：“Agent 的记忆机制是什么？” | **Global Search Bar** | [cite_start]向量数据库检索 (RAG)，跨文档引用回答 [cite: 30, 90]。 | [cite_start]知识链接/检索 [cite: 19] |

---

## 4. 详细功能需求与 User Stories

### 模块一：智能获取区 (Smart Ingestion & Setup)

**对应 UI 区域**：页面上方虚线框 "Create a New Knowledge Project" (v1.1 支持动态折叠)

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-01** | [v1.1 优化] 作为老用户，我希望上传区不要一直占据屏幕一半空间，以便我关注当下的学习。 | 1. **动态折叠**：当 Active Topics > 0 时，上传区收缩为 "Quick Drop Bar" 或移至右上角。<br>2. **拖拽展开**：当用户拖拽文件进入窗口时，上传区自动高亮展开。 | **P1** | **布局优化** |
| **US-02** | [v1.1 优化] 作为用户，我希望清楚地知道拖进去的文件去了哪里（是新项目还是收件箱）。 | 1. **智能分流**：拖入文件夹 -> 提示 "Create Project"; 拖入单文件 -> 提示 "Add to Inbox"。<br>2. 文案更新：`Drag folder to create Project, or drop files to Inbox.` | **P1** | **模糊性消除** |
| **US-03** | [v1.1 新增] 作为用户，我希望在 AI 生成课程前能先**预览并微调**，以免生成不合理的路径。 | 1. 点击 Generate 后弹出 **Preview Modal**。<br>2. 展示 AI 规划的 Step 1, Step 2...<br>3. 支持简单的拖拽排序或删除条目。<br>4. 点击 "Confirm" 才正式生成 Project。 | **P0** | **用户掌控感** |

### 模块二：活跃项目看板 (Active Topics Dashboard)

**对应 UI 区域**：页面核心内容区 "Active Topics" 卡片流

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-04** | 作为用户，我希望看到**每个学习项目的元数据统计**。 | 1. 卡片显示：文档图标+数量、视频图标+数量、链接图标+数量。<br>2. 显示自动生成的标签 (e.g., Deep Learning)。 | **P1** | [cite_start]"元数据自动提取" [cite: 11] |
| **US-05** | [v1.1 优化] 作为用户，我希望卡片能告诉我**具体的下一步行动**，而不是通用的“开始学习”。 | 1. **Context Recovery**：显示 "Continue: [Document Name] (Page X)"。<br>2. 点击直接跳转到该文档的该页码/时间戳。<br>3. 若项目未开始，显示 "Start: [First Step Name]"。 | **P0** | **极速心流** |
| **US-06** | 作为用户，我希望能够对卡片进行**管理操作**。 | 1. 卡片右上角 `...` 菜单提供编辑选项。<br>2. 支持修改自动生成的项目名称。 | **P2** | 基本交互需求 |

### 模块三：每日回顾 (Daily Review Widget) - [v1.1 新增]

**对应 UI 区域**：Dashboard 侧边或顶部显眼位置

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-11** | [v1.1 新增] 作为用户，我希望每天看到**需要复习的知识点数量**，以保持记忆。 | 1. 显示简单的统计："12 Cards due for review"。<br>2. 点击进入全屏 Flashcard 复习模式。<br>3. 复习算法基于简单的间隔重复 (如 SM-2)。 | **P1** | **留存与习惯** |

### 模块四：全局语义检索引擎 (Global Semantic Search)

**对应 UI 区域**：顶部搜索栏

| ID | User Story (用户故事) | 验收标准 (Acceptance Criteria) | 优先级 | 来源支撑 |
| :--- | :--- | :--- | :--- | :--- |
| **US-07** | 作为用户，我希望通过**自然语言提问**来搜索知识库。 | 1. 支持自然语言输入。<br>2. 基于 RAG 技术返回综合答案。<br>3. 答案必须标注来源（Source Citation）。 | **P0** | [cite_start]Grounded Generation [cite: 40] |
| **US-08** | 作为用户，我希望在搜索时能触发**跨项目的知识关联**。 | 1. 搜索结果应包含不同 Project 中的相关 Block。<br>2. 提示“你正在搜索的概念与 Project B 中的某条笔记有关”。 | **P2** | [cite_start]Serendipity [cite: 19] |

---

## 5. 关键交互细节 (UX Micro-interactions)

1.  **拖拽反馈 (Smart Drop)**：当用户拖入文件时，整个 Dashboard 变暗，仅高亮两个区域：中心显示 "Create Project"，左侧 Sidebar Inbox 显示 "Add to Inbox"，用户拖到哪里哪里高亮。
2.  **Curriculum 生成动效**：点击 Confirm 后，显示具体的 AI 处理步骤文案，例如：“Reading PDFs...”, “Extracting Audio Transcripts...”, “Structuring Knowledge Graph...”。
3.  **心流恢复 (Resume State)**：点击 Active Topic 卡片时，不要仅仅打开项目主页。如果上次是在阅读 PDF，直接打开 PDF 阅读器并滚动到上次位置；如果上次是在看视频，直接播放视频并在上次暂停处继续。
