# PRD: 深度内化工作台 (Deep Work Studio) v2.0

| 文档信息 | 内容 |
| :--- | :--- |
| **版本** | v2.0 (整合版) |
| **核心变更** | 融合三栏布局、画布工具箱、AI主动伴读、多模式切换 |
| **涉及设计图** | Studio 02 (Toolbox), 03 (Assistance), 04 (Chat/Modes) |

---

## 1. 核心理念 (Core Philosophy)

**"IDE for Knowledge" (知识集成开发环境)**

本模块不仅仅是一个阅读器，而是一个从 **输入 (Ingest)** 到 **内化 (Internalize)** 再到 **输出 (Create)** 的完整闭环工作流。
*   **左栏 (Navigator)**：结构化引导 (Map)。
*   **中栏 (Viewer)**：液态数据源 (Source)。
*   **右栏 (Canvas)**：无限思考空间 (Sink)。

---

## 2. 全局布局架构 (Layout Architecture)

界面采用 **三栏流式布局 (3-Column Fluid Layout)**，对应认知的三个阶段。

### 2.1 区域定义

| 区域 | 名称 | 宽度策略 | 核心功能 | 对应设计 |
| :--- | :--- | :--- | :--- | :--- |
| **Left** | **The Navigator (导航器)** | 固定/可折叠 (280px) | 资源库 (Library) + 学习路径 (Path) | `studio_sidbar.md` |
| **Middle** | **The Viewer (阅读器)** | 弹性 (Flex 1) | 文档渲染、流式高亮、拖拽源 | `studio.md` |
| **Right** | **The Canvas (画布)** | 弹性 (Flex 1.5) | 笔记、图解、AI 生成、多模式视图 | `studio_02/04` |

### 2.2 交互流 (Interaction Flow)
1.  **Orient (左)**: 在 Path 中确认当前学习进度 "Step 2: Core Concepts"。
2.  **Read (中)**: 点击加载 PDF，进行高亮。
3.  **Flow (中 -> 右)**: 将高亮内容**拖拽**至右侧画布，生成引用卡片。
4.  **Synthesize (右)**: 使用工具箱连接卡片，或呼叫 AI 生成图解。

---

## 3. 详细功能模块

### 3.1 左栏：双视图导航 (The Navigator)

通过顶部的 **Segment Control** 切换两种视图：

#### A. Library View (资源库)
*   **功能**：传统文件树，管理项目内所有素材 (PDF, URL, Video)。
*   **操作**：支持拖拽上传、链接抓取、全文检索。

#### B. Path View (学习路径)
*   **功能**：AI 生成的结构化 Curriculum。
*   **结构**：
    *   *Step 1: Foundation* (关联 PDF A)
    *   *Step 2: Deep Dive* (关联 Video B)
    *   *Step 3: Review* (关联 Quiz C)
*   **状态**：每一步有 Checkbox (Pending/Done)，勾选后自动推荐下一步。

---

### 3.2 中栏：液态阅读器 (Liquid Reader)

#### 功能特性
*   **多格式支持**：PDF (页码定位), Video (时间戳定位), Web (段落定位)。
*   **Drag-to-Link (核心交互)**：
    *   用户选中一段文本/截图。
    *   长按拖拽至右侧 Canvas。
    *   **结果**：在 Canvas 生成一个 "Excerpt Card" (摘录卡)，带有**回溯链接 (Backlink)**。点击卡片锚点，阅读器自动滚动至原文位置。
*   **AI Context Menu (右键菜单)**：
    *   选中即弹出：`Explain`, `Summarize`, `Add to Canvas`.

---

### 3.3 右栏：无限画布与多模式 (The Canvas)

这是核心工作区，支持基于设计图 `studio_04` 的多模式切换。

#### 3.3.1 顶部模式切换 (Mode Switcher)
位于画布顶部居中的胶囊菜单 (参考 `studio_04` 截图)，包含三组能力：

1.  **VISUALIZE (可视化)**
    *   **Canvas** (默认): 无限白板，自由拖拽。
2.  **INTERNALIZE (内化)**
    *   **Flashcards**: 将画布笔记转换为 Anki 风格的间隔重复卡片。
    *   **Audio Review**: 生成 AI Podcast 脚本并朗读。
    *   **Quiz**: 基于笔记生成测试题。
3.  **CREATE (创作)**
    *   **Essay**: 线性文档编辑模式（分屏双向同步）。
    *   **Sandbox**: 可执行代码环境。

#### 3.3.2 画布工具箱 (Canvas Toolbox)
位于画布右下角或侧边的悬浮工具栏 (参考 `studio_02` 截图)：
*   **Select/Hand**: 选择与漫游。
*   **Note**: 创建便签。
*   **Shape**: 矩形、圆形、菱形。
*   **Connector**: 智能连线。
*   **Text**: 纯文本。
*   **AI Magic**: 触发 AI 生成（见下文）。

---

### 3.4 底部/全局：AI 伴侣 (AI Companion)

基于 `studio_03` 和 `studio_04`，AI 不再是单纯的聊天框，而是**上下文感知的行动者**。

#### 3.4.1 交互形态
*   **形态**：底部悬浮胶囊 (Input Bar) + 动态浮窗 (Toast/Popover)。
*   **触发方式**：
    1.  **主动提问**：在底部输入框输入 "@PDF 总结这一章"。
    2.  **被动触发 (Proactive)**：当用户高亮一段“复杂逻辑”文本时，AI 自动弹出建议。

#### 3.4.2 核心场景：文本转图示 (Text-to-Diagram)
(参考 `studio_04` 截图逻辑)

1.  **User Action**: 在中栏高亮一段关于 "Interleaved Reasoning" 的复杂文本。
2.  **System Response**: AI 识别到这是一个过程描述，在底部弹出浮窗：
    > "I noticed you highlighted the section on 'interleaved reasoning'. Would you like me to create a diagram on the canvas comparing this to standard Chain-of-Thought?"
    > [ Buttons: **Yes, create diagram** | **Explain concept first** ]
3.  **Execution**:
    *   用户点击 "Yes"。
    *   AI 直接在右侧 Canvas 生成一个可编辑的流程图 (Nodes + Edges)。
    *   **关键点**：生成的不是图片，是**原生画布节点**，用户可继续修改。

---

## 4. 数据结构 (Data Schema)

需要统一 Navigation (Path) 和 Canvas 的数据模型。

```json
// Project Data
{
  "project_id": "proj_001",
  "layout": "3-column",
  
  // 1. Left Column: Curriculum
  "curriculum": {
    "steps": [
      { "id": "step_1", "resource_ref": "doc_A", "status": "done" },
      { "id": "step_2", "resource_ref": "video_B", "status": "active" }
    ]
  },

  // 2. Right Column: Canvas
  "canvas": {
    "nodes": [
      {
        "id": "node_1",
        "type": "excerpt_card", // 摘录卡
        "content": "Raw text from PDF...",
        "source_link": { "doc_id": "doc_A", "anchor": "page_3_para_2" },
        "position": { "x": 100, "y": 200 }
      },
      {
        "id": "node_2",
        "type": "diagram_group", // AI生成的图组
        "label": "Interleaved Reasoning Flow",
        "children": ["node_3", "node_4", "edge_1"]
      }
    ]
  }
}
```

## 5. 开发优先级 (Roadmap Priority)

1.  **P0**: 实现三栏布局框架 + 左侧 Library/Path 切换。
2.  **P0**: 实现 Middle -> Right 的拖拽交互 (Drag-to-Link)。
3.  **P1**: 实现 Canvas 基础工具箱 (Note, Connector)。
4.  **P1**: 实现 AI Chat UI (`studio_04` 样式) 及 Text-to-Diagram 的 Prompt 逻辑。
5.  **P2**: 实现 Visualize/Flashcards 模式切换视图。

