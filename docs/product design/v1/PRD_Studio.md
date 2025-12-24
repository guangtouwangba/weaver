# PRD: Weaver Visual Thinking Studio (Freeform Workbench)

| Document Info | Details |
| :--- | :--- |
| **Version** | v4.0 (Visual Thinking Studio) |
| **Status** | Implementation Phase |
| **Scope** | Studio Page (`/studio`) |

---

## 1. 产品定位与核心理念
**Weaver** 不仅仅是一个 RAG 应用，它是一个 **可视化思维助手 (Visual Thinking Assistant)**。
- **Canvas 是工作台，不是仓库**：初始状态保持绝对纯净。上传文档不自动生成节点，遵循“拖拽即关注 (Drag to Focus)”的原则，避免认知过载。
- **空间化认知**：通过节点的位置、连线和颜色，建立知识之间的逻辑关联，利用人类的空间记忆（Spatial Memory）理清复杂关系。
- **过程可视化**：强调展示思考路径 (Thinking Path) 和知识图谱 (Knowledge Graph)，而非简单的问答结果。

---

## 2. 界面架构设计
界面采用 **“沉浸式画布 + 三段式浮窗”** 的布局，确保工具辅助而不干扰思考。

| 组件 | 功能描述 |
| :--- | :--- |
| **Global Sidebar** | 左侧极简条（72px），提供全局导航。 |
| **Project Header** | 顶部固定（56px），显示项目名称、动态主题色、项目切换器及同步状态。 |
| **Resource Sidebar** | 左侧可折叠（280px），当前项目的多模态资源仓，支持拖拽上屏。 |
| **Infinite Canvas** | 核心区域，无限缩放与平移，承载所有节点与逻辑连线。 |
| **Detail Panel** | 右侧可折叠（320px/600px），节点的深度查看区，支持媒体预览、播客、卡片及对话。 |
| **Chat Input** | 底部居中悬浮，全局思考入口，支持多选节点后的聚合分析。 |

---

## 3. 核心交互特性

### 3.1 空间导航与编辑
- **多模式操作**：
  - `V` (Select Mode): 选择、移动节点。
  - `H` (Hand Mode): 平移画布。
  - `Mouse Wheel`: 以光标为中心的无限缩放（0.1x - 5x）。
- **Connection Mode (连接模式)**：
  - 点击工具栏连线按钮进入。
  - 节点显示 **8 个方向的连接锚点 (Anchors)**。
  - 支持“两点点击”或“拖拽连接”，生成的连线带有平滑的 SVG 曲线与发光效果。

### 3.2 节点生态系统 (Node Types)
| 节点类型 | 视觉呈现 | 核心行为 |
| :--- | :--- | :--- |
| **File Node** | 圆形图标 + 呼吸灯 | 点击展开 Genius 菜单；右侧面板显示文档详情。 |
| **Insight Node** | 黄色便签纸 (Sticky Note) | 承载从 PDF 提取的精华或 AI 发现。 |
| **Action Node** | 圆角功能卡片 | 标记 AI 生成的任务（如 Mindmap, Audio Summary）。 |
| **Chat Node** | 脑图式对话框 | 视觉化对话线程，节点内包含消息流及 AI 思考状态。 |
| **Entity Node** | 小圆形彩色节点 | 用于 AI Mapping 生成的关系图谱中的实体。 |
| **Note Node** | 文档式卡片 | 用于长文创作或笔记，支持自动关联源文档。 |

---

## 4. AI 智能流 (Genius Workflow)

### 4.1 AI Intelligent Mapping (智能关系抽取)
- 用户点击文档节点的 **Sparkles (Genius)** 按钮。
- 输入自然语言指令（如：“分析剧中的人物关系”、“提取 API 调用逻辑”）。
- AI 自动在画布上生成一套 **Entity 节点** 与 **Labeled Edges (带标签的连线)**。

### 4.2 Visual Thinking Thread (可视化思考线程)
- **多选聚合**：用户多选多个不同类型的文档，点击底部 Chat 发起询问。
- **分析节点生成**：在选中的节点簇下方生成一个 **Chat 节点**。
- **自动发散**：AI 回复的同时，自动从分析结果中向外生成多个 **Insight 节点**。

---

## 5. 沉浸式工具集成

### 5.1 PDF Review & Peel Interaction
- **浮动评审**：以 85% 比例的半透明 Dialog 呈现。
- **Peel (剥离) 交互**：选中文字后，出现“Drag Insight”手柄。
- **透明拖拽**：拖拽开始时，PDF 窗口透明度降低，露出下方画布，实现“所见即所得”的放置。

### 5.2 Podcast & Audio Summary
- 将复杂的文档转化为 **Podcast (播客) 剧本**。
- 详情面板提供双人对话式脚本高亮播放。
- 支持在空间中“聆听”研究进展。

### 5.3 空间记忆卡片 (Flashcards)
- AI 基于文档自动生成 Anki 风格的记忆卡片。
- 详情面板提供 3D 翻转交互，支持用户标记掌握程度。

---

## 6. 技术实现要点
- **坐标转换系统**：实现 `Screen Coords` 到 `Infinite Canvas Coords` 的精准映射。
- **SVG 关系渲染**：使用 SVG `path` 和 `Cubic Bezier` 曲线渲染关系，支持 `textPath` 动态边缘标签。
- **项目品牌化 (Project Branding)**：
  - 每个项目拥有独立的 `projectColor`。
  - 画布背景动态生成基于主题色的网格和半透明水印。

---

## 7. 后续 RoadMap
1.  **节点自由组合 (Grouping)**：支持框选节点并组合成组。
2.  **多人协作 (Real-time Sync)**：支持画布上的实时多人操作。
3.  **时间轴回溯 (Time-traveling)**：通过回溯知识图谱的构建过程。
