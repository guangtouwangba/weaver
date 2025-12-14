# MVP Scope: Research Agent Studio

| Document Info | Details |
| --- | --- |
| **Version** | v1.0 |
| **Date** | 2025-11-26 |
| **Status** | Draft |
| **Focus** | "From Reading to Knowledge Cards" |

---

## 1. 核心价值主张 (Value Proposition)
MVP 的核心目标是验证**“AI 辅助阅读与知识结构化”**的闭环体验。
用户能够上传一篇 PDF 论文，通过 AI 辅助阅读理解，并将关键信息以**“拖拽”**的方式沉淀到无限画布上，形成可视化的知识笔记。

**核心用户故事：**
> "作为一个研究员，我上传一篇论文 PDF，阅读时选中一段关键定义，将其拖拽到右侧画布生成卡片；随后我针对该概念向 AI 提问，并将 AI 的总结也拖拽成卡片，最后将两张卡片连接起来，形成结构化的知识点。"

---

## 2. 功能列表 (Feature List)

### 2.1 Dashboard (项目管理)
*目标：最简化的项目入口，不包含复杂的全局图谱。*

*   **[P0] 项目列表**：展示已创建的项目卡片（包含标题、最后编辑时间）。
*   **[P0] 创建项目**：点击 "New Project"，输入项目名称，进入 Studio 页面。
*   **[P0] 删除项目**：能够删除废弃的项目。

### 2.2 Studio - Left Column: The Source (资料源)
*目标：提供流畅的 PDF 阅读体验，作为知识的输入端。*

*   **[P0] PDF 文件上传**：支持本地上传 PDF 文件。
*   **[P0] 文件列表**：展示当前项目内的 PDF 文件列表，点击切换阅读。
*   **[P0] PDF 阅读器**：
    *   集成成熟的 PDF 渲染组件 (如 `react-pdf`)。
    *   支持缩放、翻页。
*   **[P0] 文本高亮与拖拽 (The "Magic" Interaction)**：
    *   用户选中 PDF 中的文本后，支持高亮显示。
    *   **关键交互**：支持直接将选中的文本**拖拽 (Drag)** 到右侧画布区域，松手即生成一张引用卡片 (Reference Card)。

### 2.3 Studio - Center Column: The Assistant (AI 助理)
*目标：基于当前文档的 RAG 对话，辅助理解。*

*   **[P0] RAG Chat Interface**：
    *   标准的聊天界面（用户消息右侧，AI 消息左侧）。
    *   支持流式输出 (Streaming) 提升响应体感。
*   **[P0] 基于文档问答**：
    *   后端接入 RAG 能力，限制回答范围在当前项目/当前文档内。
    *   支持指令： "总结这篇文章"、"解释选中的这段话"。
*   **[P1] 引用拖拽**：
    *   支持将 AI 的回答文本拖拽到画布上生成卡片。

### 2.4 Studio - Right Column: The Output (无限画布)
*目标：结构化知识的沉淀场所，MVP 的核心差异化功能。*

*   **[P0] 无限画布 (Infinite Canvas)**：
    *   支持无限平移 (Pan) 和缩放 (Zoom)。
    *   背景网格 (Grid) 随缩放适配。
*   **[P0] 节点系统 (Nodes)**：
    *   **文本卡片**：双击画布创建空白卡片，支持 Markdown 编辑。
    *   **引用卡片**：通过 PDF 拖拽生成的卡片，保留来源元数据（Source ID, Page Number）。
    *   **操作**：卡片拖拽移动、选中删除。
*   **[P0] 连接系统 (Edges)**：
    *   从卡片边缘拖拽出连线，连接到另一张卡片。
    *   简单的箭头连线，表示关联关系。
*   **[P0] 数据持久化**：
    *   画布内容（节点位置、内容、连线关系）必须保存到后端数据库，刷新页面不丢失。

---

## 3. 不在 MVP 范围内 (Out of Scope)

为了确保快速交付验证，以下功能**暂不包含**在 MVP 中：

### 页面级别
*   **全局 Brain** (`/brain`)：跨项目知识图谱。原因：数据量不足时无意义，等用户积累 5+ 项目后再开发。
*   **Inbox** (`/inbox`)：预处理收件箱。原因：增加认知负担，直接上传到项目更简单。
*   **独立 Projects 页** (`/projects`)：Dashboard 已包含项目列表，无需独立页面。

### 功能级别
*   **多媒体支持**：暂不支持视频 (Youtube/MP4) 和音频 (MP3/Podcast) 的播放与转录。
*   **Web Link Reader**：暂不支持直接抓取网页内容。
*   **多视图切换**：暂不开发 Podcast 生成、Writer 写作模式、Slides 幻灯片模式，仅保留 **Canvas**。
*   **Canvas Copilot**：暂不开发画布内的 "一键整理"、"自动连线" 等高级 AI 功能。
*   **协作功能**：暂不支持多人实时协作。

---

## 4. 技术依赖 (Technical Dependencies)

### Backend (API)
*   `POST /api/upload`: 处理 PDF 上传与解析 (Text Extraction)。
*   `POST /api/chat`: RAG 对话接口。
*   `GET/POST /api/projects/{id}/canvas`: 读取和保存画布数据 (JSON blob)。

### Frontend
*   `react-pdf`: PDF 渲染。
*   `reactflow` 或 自研 Canvas (当前原型为自研 SVG 实现，建议 MVP 继续沿用或评估 `reactflow` 的集成成本)。
*   `dnd-kit` 或 原生 DragAPI: 处理跨组件拖拽 (PDF -> Canvas)。

