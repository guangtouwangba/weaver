# 🕸️ Weaver

> **Weave knowledge into insights.**
> An AI-powered research workspace with an infinite canvas.

![Weaver](https://img.shields.io/badge/Status-Alpha-orange)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Next.js](https://img.shields.io/badge/Frontend-Next.js-black)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)

Weaver is a powerful research agent that helps you organize, analyze, and synthesize information using an infinite canvas interface and advanced RAG (Retrieval-Augmented Generation) capabilities.

## ✨ Features

- **🧠 Advanced RAG Engine**: Context-aware information retrieval using Long Context LLMs.
- **🎨 Infinite Canvas**: A visual workspace to organize your thoughts, citations, and notes.
- **📄 Document Processing**: Automatic PDF parsing, OCR, and knowledge graph extraction.
- **🔄 Real-time Sync**: WebSocket-based synchronization for collaborative research.
- **🤖 Autonomous Tasks**: Background workers handle document processing, graph extraction, and cleanup.
- **🔌 Model Agnostic**: Powered by OpenRouter, supporting various LLMs (Claude, GPT-4, etc.).

## 🛠️ Tech Stack

- **Backend**: Python 3, FastAPI, SQLAlchemy, AsyncIO.
- **Frontend**: Next.js, React, TypeScript.
- **Infrastructure**: Docker, PostgreSQL, Redis.
- **AI/LLM**: OpenRouter API, Long Context handling.

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** & **npm**
- **Poppler** (for PDF processing)
  - macOS: `brew install poppler`
  - Ubuntu: `sudo apt-get install poppler-utils`

### Installation

Weaver provides a convenient `Makefile` to handle dependencies.

1. **Clone the repository** (if you haven't already).

2. **Setup the environment**:
   ```bash
   make setup
   ```
   This will:
   - Check for system dependencies.
   - Create a Python virtual environment.
   - Install backend and frontend dependencies.
   - Create a `.env` file from `.env.example`.

3. **Configure Environment Variables**:
   Edit the `.env` file and add your API keys (e.g., `OPENROUTER_API_KEY`).

### Running the Application

You can run the backend and frontend separately or together.

**Option 1: Development Mode (Parallel)**
```bash
make dev
```
*Note: This might require two terminal windows or `parallel` installed.*

**Option 2: Separate Terminals**

*Terminal 1 (Backend):*
```bash
make run-backend
```

*Terminal 2 (Frontend):*
```bash
make run-frontend
```

 Access the application at `http://localhost:3000` and the API docs at `http://localhost:8000/docs`.

## 🧪 Testing & Linting

- Run tests: `make test`
- Run linters: `make lint`

## 🤝 Contributing

Contributions are welcome! Please read our [AGENTS.md](AGENTS.md) for coding conventions and instructions if you are an AI assistant.

## 📄 License

This project is dual-licensed:

- **Open Source**: [AGPL-3.0](LICENSE-AGPL) - Use freely, but you must open-source your application
- **Commercial**: Contact for closed-source use - Email: 819110812@qq.com

See [LICENSE](LICENSE) for details.
