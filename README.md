# 🕸️ Weaver

> **Weave knowledge into insights.**
> Your open-source alternative to NotebookLM — with an infinite canvas.

[![GitHub stars](https://img.shields.io/github/stars/guangtouwangba/weaver?style=social)](https://github.com/guangtouwangba/weaver/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/guangtouwangba/weaver?style=social)](https://github.com/guangtouwangba/weaver/network/members)
[![GitHub issues](https://img.shields.io/github/issues/guangtouwangba/weaver)](https://github.com/guangtouwangba/weaver/issues)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue)](LICENSE-AGPL)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)

---

## 🆚 Why Weaver over NotebookLM?

| Feature | NotebookLM | Weaver |
|---------|------------|--------|
| **Open Source** | ❌ Closed | ✅ AGPL-3.0 |
| **Self-Hosted** | ❌ Google Cloud only | ✅ Deploy anywhere |
| **Visual Canvas** | ❌ List-based | ✅ Infinite canvas workspace |
| **Model Choice** | ❌ Gemini only | ✅ Any LLM (Claude, GPT-4, Gemini, etc.) |
| **Video Sources** | ✅ YouTube | ✅ YouTube + Bilibili + Douyin |
| **Data Privacy** | ⚠️ Google servers | ✅ Your data, your servers |
| **Customization** | ❌ No API | ✅ Full API access |
| **Cost** | 💰 Usage limits | ✅ Pay only for LLM API |

---

## ✨ Features

### 📚 Multi-Source Content Import
- **PDF Documents** — Upload and parse PDFs with OCR support
- **Web Pages** — Extract and process any URL content
- **YouTube Videos** — Auto-transcribe with timestamp markers
- **Bilibili & Douyin** — Chinese video platform support

### 🎨 Infinite Canvas Workspace
- **Visual Organization** — Drag-and-drop nodes on an infinite canvas
- **Rich Node Types** — Notes, documents, web pages, videos, generated content
- **Connection Lines** — Link related content with relationship labels
- **Real-time Sync** — WebSocket-based live collaboration

### 🤖 AI-Powered Generation
- **Mindmaps** — Generate structured mindmaps with source references
- **Summaries** — AI-generated summaries with citation links
- **Flashcards** — Auto-generate study cards from documents
- **Articles** — Synthesize long-form content from multiple sources

### 💬 RAG Chat Assistant
- **Long Context RAG** — Chat with your documents using context-aware retrieval
- **Citation Grounding** — Every answer includes source references
- **Multi-Document Q&A** — Ask questions across all your imported content

---

## 🚀 Quick Start

```bash
# Clone & setup
git clone https://github.com/guangtouwangba/weaver.git
cd weaver && make setup

# Configure (add your OPENROUTER_API_KEY)
cp env.example .env && nano .env

# Run
make run-backend   # Terminal 1: API on :8000
make run-frontend  # Terminal 2: UI on :3000
```

**30 seconds to your first insight!** 🎉

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 15, React 19, TypeScript, Konva.js |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, LangGraph |
| **Database** | PostgreSQL, pgvector (Vector Search) |
| **AI/LLM** | OpenRouter API (Claude, GPT-4, Gemini, etc.) |

---

## � Prerequisites

- Python 3.11+ / Node.js 18+
- PostgreSQL with pgvector
- `brew install poppler ffmpeg` (macOS)

---

## 📈 Star History

<a href="https://star-history.com/#guangtouwangba/weaver&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=guangtouwangba/weaver&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=guangtouwangba/weaver&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=guangtouwangba/weaver&type=Date" />
 </picture>
</a>

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

**Dual Licensed:**
- **Open Source**: [AGPL-3.0](LICENSE-AGPL) — Use freely, must open-source your app
- **Commercial**: Contact 819110812@qq.com for closed-source licensing

---

<p align="center">
  <b>Built with ❤️ by the Weaver community</b><br>
  <i>Inspired by <a href="https://notebooklm.google.com/">Google NotebookLM</a></i>
</p>
