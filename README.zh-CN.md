<p align="center">
  <img src="app/frontend/public/weaver-logo.svg" alt="Weaver Logo" width="120" height="120">
</p>

<h1 align="center">🕸️ Weaver</h1>

<p align="center">
  <strong>开源 NotebookLM 替代品 · 无限画布 · 自托管</strong><br>
  一个可以自托管的 Google NotebookLM 开源替代方案<br>
  与文档对话、生成思维导图、可视化组织你的研究
</p>

<p align="center">
  <a href="https://github.com/guangtouwangba/weaver/stargazers"><img src="https://img.shields.io/github/stars/guangtouwangba/weaver?style=for-the-badge&logo=github&color=gold" alt="GitHub stars"></a>
  <a href="https://github.com/guangtouwangba/weaver/network/members"><img src="https://img.shields.io/github/forks/guangtouwangba/weaver?style=for-the-badge&logo=github" alt="GitHub forks"></a>
  <a href="https://github.com/guangtouwangba/weaver/issues"><img src="https://img.shields.io/github/issues/guangtouwangba/weaver?style=for-the-badge" alt="GitHub issues"></a>
</p>

<p align="center">
  <a href="https://weaver.zeabur.app"><strong>🌐 在线体验</strong></a> · 
  <a href="#-快速开始"><strong>🚀 快速开始</strong></a> · 
  <a href="#-功能特性"><strong>✨ 功能特性</strong></a> · 
  <a href="./README.md"><strong>🇬🇧 English</strong></a>
</p>

---

## 🤔 为什么选择 Weaver？

**受够了 Google NotebookLM 的限制？** Weaver 是一个**免费、开源的 NotebookLM 替代品**，你可以自托管并完全定制。

| 功能 | Google NotebookLM | **Weaver** |
|------|-------------------|------------|
| **开源** | ❌ 闭源 | ✅ **AGPL-3.0 开源** |
| **自托管** | ❌ 仅限 Google Cloud | ✅ **随处部署** |
| **可视化画布** | ❌ 列表式 UI | ✅ **无限画布工作区** |
| **LLM 选择** | ❌ 仅 Gemini | ✅ **任意 LLM**（Claude、GPT-4、通义、本地 Ollama） |
| **视频来源** | 仅 YouTube | ✅ **YouTube + B站 + 抖音** |
| **数据隐私** | ⚠️ Google 服务器 | ✅ **你的数据，你的服务器** |
| **API 访问** | ❌ 无 | ✅ **完整 REST API** |
| **成本** | 💰 使用限制 | ✅ **仅付 LLM API 费用** |

> **Weaver = NotebookLM + Miro + Obsidian** — 全部开源在一个项目中。

---

## ✨ 功能特性

### 📚 多源导入（比 NotebookLM 更强）
从多种来源导入，让 AI 帮你理解：
- **📄 PDF 文档** — 支持 OCR 扫描件
- **🌐 网页** — 从任意 URL 提取内容
- **🎬 YouTube 视频** — 自动转录带时间戳
- **📺 B站 & 抖音** — 支持国内视频平台（NotebookLM 做不到！）

### 🎨 无限画布工作区（Weaver 独有）
不同于 NotebookLM 死板的列表视图，Weaver 给你一个**可视化思考空间**：
- **拖拽式** 节点布局
- **连线关联** 想法之间的关系
- **丰富节点类型** — 笔记、来源、AI 生成内容
- **实时协作** 基于 WebSocket

### 🤖 AI 驱动的研究工具
- **💬 RAG 对话** — 基于文档问答，带引用
- **🧠 思维导图** — 自动生成结构化思维导图
- **📝 摘要** — AI 摘要带来源引用
- **📇 闪卡** — 自动生成学习卡片
- **📰 文章** — 综合多源生成长文

### 🔌 为开发者而生
- **完整 API** — 集成到你的工作流
- **自带 LLM** — OpenRouter、OpenAI、Anthropic 或本地 Ollama
- **可扩展** — 添加自定义来源和生成器

---

## 🚀 快速开始

30 秒启动 Weaver：

```bash
# 克隆仓库
git clone https://github.com/guangtouwangba/weaver.git
cd weaver

# 安装依赖
make setup

# 配置 API 密钥
cp env.example .env
# 编辑 .env，添加 OPENROUTER_API_KEY

# 运行
make run-backend   # 终端 1: API 在 :8000
make run-frontend  # 终端 2: UI 在 :3000
```

> 💡 **提示**：快速本地测试可设置 `AUTH_BYPASS_ENABLED=true`

**打开 http://localhost:3000 开始你的研究！** 🎉

---

## 📖 使用场景

### 🎓 学生 & 研究者
- 上传课件 PDF 和论文
- 跨多个来源提问
- 自动生成学习闪卡
- 创建考试复习思维导图

### ✍️ 内容创作者
- 多来源研究主题
- 生成文章大纲
- 在画布上组织想法
- 导出结构化内容

### 💼 职场人士
- 分析报告和文档
- 建立个人知识库
- 自托管保护数据隐私
- 集成到现有工作流

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js 15, React 19, TypeScript, Konva.js |
| **后端** | Python 3.11+, FastAPI, SQLAlchemy, LangGraph |
| **数据库** | PostgreSQL, pgvector (向量搜索) |
| **AI/LLM** | OpenRouter, OpenAI, Anthropic, Ollama |

---

## 📋 环境要求

- Python 3.11+ / Node.js 18+
- PostgreSQL + pgvector 扩展
- macOS: `brew install poppler ffmpeg`
- Linux: `apt install poppler-utils ffmpeg`

---

## 🗺️ 路线图

- [x] PDF/网页/YouTube 导入
- [x] 无限画布工作区
- [x] RAG 对话带引用
- [x] 思维导图生成
- [ ] 🎙️ 播客生成（类似 NotebookLM 音频概览）
- [ ] 📱 移动端 App
- [ ] 🔗 Obsidian 插件
- [ ] 🌍 多语言界面

---

## 🤝 贡献

欢迎贡献！无论是：
- 🐛 Bug 报告
- 💡 功能建议
- 📖 文档完善
- 🔧 代码 PR

查看 [CONTRIBUTING.md](CONTRIBUTING.md) 开始贡献。

---

## 💬 社区

- ⭐ **觉得有用就 Star 一下！**
- 🐛 [报告 Bug](https://github.com/guangtouwangba/weaver/issues)
- 💡 [功能建议](https://github.com/guangtouwangba/weaver/issues)

---

## 📄 许可证

**双重许可：**
- **开源版**: [AGPL-3.0](LICENSE-AGPL) — 免费使用，修改需开源
- **商业版**: 联系 819110812@qq.com 获取闭源授权

---

<p align="center">
  <strong>🕸️ Weaver — 开源 NotebookLM 替代品</strong><br>
  <sub>由 Weaver 社区用 ❤️ 构建</sub><br>
  <sub>灵感来自 <a href="https://notebooklm.google.com/">Google NotebookLM</a></sub>
</p>

<p align="center">
  <strong>如果你在寻找开源的 NotebookLM 替代品，给 Weaver 一个 ⭐ 吧！</strong>
</p>
