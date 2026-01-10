# 🕸️ Weaver

> **Weave knowledge into insights.**
> An AI-powered research workspace with an infinite canvas.
> *Inspired by [NotebookLM](https://notebooklm.google.com/)*

![Weaver](https://img.shields.io/badge/Status-Alpha-orange)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)

Weaver is a powerful, open-source research workspace inspired by Google's NotebookLM. It helps you organize, analyze, and synthesize information using an infinite canvas interface and advanced RAG (Retrieval-Augmented Generation) capabilities.

## ✨ Features

### 📚 Multi-Source Content Import
- **PDF Documents** - Upload and parse PDFs with OCR support
- **Web Pages** - Extract and process any URL content
- **YouTube Videos** - Auto-transcribe with timestamp markers (via YouTube API or Gemini Audio)
- **Bilibili Videos** - Chinese video platform support
- **Douyin Videos** - TikTok China content extraction

### 🎨 Infinite Canvas Workspace
- **Visual Organization** - Drag-and-drop nodes on an infinite canvas
- **Rich Node Types** - Notes, documents, web pages, videos, and generated content
- **Connection Lines** - Link related content with relationship labels
- **Real-time Sync** - WebSocket-based live collaboration

### 🤖 AI-Powered Generation
- **Mindmaps** - Generate structured mindmaps from your content with source references
- **Summaries** - AI-generated summaries with citation links
- **Flashcards** - Auto-generate study cards from documents
- **Articles** - Synthesize long-form content from multiple sources
- **Action Lists** - Extract actionable items from content

### 💬 RAG Chat Assistant
- **Long Context RAG** - Chat with your documents using context-aware retrieval
- **Citation Grounding** - Every answer includes source references
- **Multi-Document Q&A** - Ask questions across all your imported content
- **Streaming Responses** - Real-time AI response streaming

### 📄 Document Features
- **PDF Viewer** - Built-in PDF reader with annotations
- **Highlighting** - Select and highlight text in documents
- **Page-Level References** - Jump to exact source locations `[PAGE:X]`
- **Video Timestamps** - Click to jump to video positions `[TIME:MM:SS]`

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 15, React 19, TypeScript, Konva.js (Canvas) |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, LangGraph |
| **Database** | PostgreSQL, pgvector (Vector Search) |
| **AI/LLM** | OpenRouter API (Claude, GPT-4, Gemini, etc.) |
| **Infrastructure** | Docker, WebSocket, Background Workers |

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** & **npm**
- **PostgreSQL** with pgvector extension
- **Poppler** (for PDF processing)
  - macOS: `brew install poppler`
  - Ubuntu: `sudo apt-get install poppler-utils`
- **FFmpeg** (for audio transcription)
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt-get install ffmpeg`

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/guangtouwangba/research-agent-rag.git
cd research-agent-rag

# 2. Setup environment (creates venv, installs deps)
make setup

# 3. Configure API keys
cp env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 4. Run database migrations
make migrate

# 5. Start the application
make run-backend   # Terminal 1: Backend on :8000
make run-frontend  # Terminal 2: Frontend on :3000
```

Access the app at `http://localhost:3000` and API docs at `http://localhost:8000/docs`.

## 📖 Usage

1. **Create a Project** - Start by creating a new research project
2. **Import Sources** - Upload PDFs, paste URLs, or add YouTube videos
3. **Organize on Canvas** - Arrange your sources on the infinite canvas
4. **Generate Insights** - Create mindmaps, summaries, or flashcards
5. **Chat with Content** - Ask questions and get cited answers

## 🧪 Development

```bash
make test          # Run tests
make lint          # Run linters
make migrate       # Database migrations
make clean         # Clean build artifacts
```

## 🤝 Contributing

Contributions are welcome! Please read:
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community guidelines
- [AGENTS.md](AGENTS.md) - Instructions for AI assistants

## 📄 License

This project is dual-licensed:

- **Open Source**: [AGPL-3.0](LICENSE-AGPL) - Use freely, but you must open-source your application
- **Commercial**: Contact for closed-source use - Email: 819110812@qq.com

See [LICENSE](LICENSE) for details.

---

Built with ❤️ by [Weaver Contributors](https://github.com/guangtouwangba/research-agent-rag)
