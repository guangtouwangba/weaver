# 产品需求文档 (PRD): 用户中心与设置 (User Center & Settings)

## 1. 背景与定位 (Background & Positioning)

*   **组件名称**：User Center (用户中心)
*   **核心定位**：
    1.  **Control (掌控感)**：为高级用户（如工程师/研究员）提供对 AI 模型、数据所有权和隐私的完全控制。
    2.  **Achievement (成就感)**：通过可视化的“知识复利”统计，对抗学习过程中的枯燥感，强化长期留存。
*   **入口**：点击 Global Sidebar 底部的用户头像 -> 弹出菜单 -> 选择 "Settings & Stats"。

---

## 2. 页面布局 (Page Layout)

采用经典的 **双栏设置布局 (Two-column Settings Layout)**，确保在桌面端的高效浏览。

*   **左侧导航 (Settings Navigation)**：宽度固定 (200-240px)。
    *   分组：Account, Workspace, Preferences.
*   **右侧内容 (Content Panel)**：根据左侧选择动态切换。顶部包含面包屑或当前模块标题。

---

## 3. 详细功能模块 (Functional Modules)

### 3.1 概览与洞察 (Profile & Insights) - *Default View*
这是用户进入后的默认视图，不仅仅是个人资料，更是“知识仪表盘”。

*   **User Profile**: 头像、昵称、注册时长。
*   **Knowledge Heatmap (知识热力图)**：
    *   仿 GitHub Contribution Graph 风格。
    *   维度：过去一年中，每天产生的 "Meaningful Actions" (创建卡片、建立连接、完成复习)。
    *   *价值*：可视化用户的勤奋程度，建立习惯回路。
*   **Asset Stats (资产统计)**：
    *   **Total Cards**: 已创建的知识卡片总数。
    *   **Internalized**: 已标记为“掌握”或完成 Anki 复习的卡片数。
    *   **Graph Connections**: 知识图谱中的连接线数量。
    *   **Read Count**: 已阅读/处理的 PDF/视频 数量。

### 3.2 AI 模型配置 (AI Configuration) - *Core for Geeks*
鉴于目标用户是技术人员/深度学习者，他们需要对 LLM 有精细的控制。

*   **Model Selection (模型选择)**：
    *   **Reasoning Model**: 用于复杂推理/生成图谱 (e.g., GPT-4o, Claude 3.5 Sonnet)。
    *   **Chat Model**: 用于日常对话 (e.g., GPT-4o-mini, DeepSeek)。
*   **BYOK (Bring Your Own Key)**：
    *   允许用户输入自己的 OpenAI/Anthropic API Key。
    *   开启 BYOK 后，平台不收取 Token 费用（或仅收基础服务费）。
*   **System Prompt / Persona**:
    *   允许用户自定义全局的 AI 角色设定。
    *   *Example*: "你是一个严肃的学术助理，请只用第一性原理进行解释，拒绝废话。"

### 3.3 数据管理 (Data & Privacy) - *Trust Builder*
强调“数据主权”。

*   **Export (导出)**：
    *   **Markdown Export**: 将所有 Project 导出为标准 Markdown 文件夹结构 (Obsidian/Notion compatible)。
    *   **JSON Dump**: 导出完整数据库结构，用于备份。
*   **Sync Settings**:
    *   查看最后同步时间。
    *   强制手动同步 (Force Sync)。
*   **Clear Data**: 危险操作区，删除账户或清空特定项目数据。

### 3.4 个性化偏好 (Preferences)
*   **Appearance**:
    *   Theme: Light / Dark / System / **Focus (High Contrast)**.
    *   Font Size: 调整全局阅读器和编辑器字号。
*   **Learning Habits**:
    *   **Daily Review Limit**: 设置每天由 SRS (间隔重复) 算法推送的最大复习卡片数 (如：20张/天)。
    *   **Auto-summary**: 是否在拖入 PDF 时自动进行全文摘要 (On/Off)。

### 3.5 订阅与额度 (Billing & Usage)
*   **Current Plan**: Free / Pro / Researcher。
*   **Usage Meter**:
    *   本月 AI Token 使用量进度条。
    *   存储空间使用量 (针对 PDF/视频上传)。
*   **Invoice History**: 历史账单下载。

---

## 4. 关键交互流 (Key Interaction Flows)

### 4.1 BYOK 开启流程
1.  用户进入 "AI Configuration"。
2.  打开 "Use Custom API Key" 开关。
3.  系统弹出输入框（加密存储）。
4.  用户输入 `sk-...` 并点击 "Validate"。
5.  系统发送一个轻量级 Ping 请求验证 Key 有效性。
6.  验证通过 -> 显示 "Active" 绿点 -> 隐藏平台自身的 Token 计费模块。

### 4.2 数据导出流程
1.  用户点击 "Export All Data"。
2.  系统提示 "正在打包，可能需要几分钟..." (Toasting)。
3.  后台生成 zip 包。
4.  浏览器自动开始下载 `knowledge-backup-YYYYMMDD.zip`。

---

## 5. 数据指标定义 (Data Metrics for Heatmap)

为了让热力图真实反映“学习”而非“灌水”，定义以下权重：

| 行为 | 权重 | 说明 |
| :--- | :--- | :--- |
| **Create Card** | Low | 简单的摘录 |
| **Link Cards** | Medium | 建立连接代表思考 |
| **Edit Note** | Medium | 用自己的话重写 |
| **Complete Review** | High | 完成一次间隔重复复习 |
| **Generate Essay** | High | 完成一次输出 |

---

## 6. 优先级 (Roadmap Priority)

*   **P0**: Basic Profile, Billing, **AI Model Selection** (技术产品核心), Dark Mode.
*   **P1**: **Knowledge Heatmap** (留存关键), Data Export (信任关键).
*   **P2**: BYOK 高级配置, Daily Review Limit.

