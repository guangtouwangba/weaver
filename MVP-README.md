# 研究论文系统 MVP

## 概述

这是一个简化版的研究论文分析系统，实现了核心的MVP功能：

**核心流程：** 关键词搜索 → ArXiv论文检索 → PDF下载存储 → RAG智能对话

## 功能特性

### ✅ 已实现功能

1. **论文搜索**
   - 基于关键词搜索ArXiv学术论文
   - 自动解析论文元数据（标题、作者、摘要等）
   - 本地SQLite数据库存储

2. **PDF管理**
   - 自动下载论文PDF文件
   - 本地文件系统存储
   - 下载状态跟踪

3. **RAG对话**
   - 基于已搜索论文的智能问答
   - 简单的相关性评分算法
   - 论文引用和参考

4. **Web界面**
   - 简洁的搜索界面
   - 实时对话界面
   - 论文结果展示

### 🎯 核心价值

- **极简架构**: 单文件后端服务器，无复杂依赖
- **快速启动**: 一键启动脚本，5分钟部署
- **本地优先**: 数据本地存储，隐私安全
- **渐进增强**: 可在此基础上逐步扩展功能

## 快速开始

### 0. 一键启动（最简单）

```bash
./start-full-mvp.sh
```

这个脚本会自动检查环境、启动后端和前端，适合快速体验。

### 1. 环境检查（推荐第一步）

```bash
./check-env.sh
```

这个脚本会检查你的Python和conda环境，并推荐最适合的启动方式。

### 2. 启动后端服务

```bash
# 方式1：Conda环境（推荐，最稳定）
./start-mvp-conda.sh

# 方式2：venv环境（更新版本）  
./start-mvp-simple.sh

# 方式3：使用requirements文件
./start-mvp.sh

# 方式4：手动启动
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx pydantic python-multipart
python simple_mvp_server.py
```

**重要提示：**
- **Python 3.13用户**: 推荐使用conda方案 (`./start-mvp-conda.sh`)
- **Python 3.8-3.12用户**: 可使用任何方案
- 如果遇到依赖冲突，优先尝试conda方案

### 3. 启动前端

```bash
# 使用启动脚本（推荐）
./start-frontend.sh

# 或手动启动
cd frontend
npm install
npm run dev
```

### 4. 访问系统

- 前端界面: http://localhost:3000/mvp
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 使用流程

### 1. 搜索论文

1. 在搜索框输入英文关键词（如：`deep learning`）
2. 选择搜索数量（1-100篇，可手动输入或点击快捷按钮）
3. 点击"搜索"按钮
4. 系统从ArXiv检索相关论文
5. 自动下载PDF并保存到本地
6. 显示论文列表和元数据

### 2. RAG对话

1. 基于已搜索的论文进行提问
2. 支持中英文问答
3. 系统基于论文内容生成回答
4. 显示相关论文参考

## 技术架构

### 后端 (backend/simple_mvp_server.py)

```
FastAPI 服务器
├── ArXiv API 集成
├── SQLite 数据库
├── PDF 下载器
└── 简单RAG检索
```

**核心组件：**
- `SimpleArxivClient`: ArXiv论文搜索
- `SimplePaperDB`: SQLite数据库管理
- `SimplePDFDownloader`: PDF文件下载
- `SimpleRAGRetriever`: 基础RAG检索

### 前端 (frontend/app/mvp/page.tsx)

```
React 组件
├── 论文搜索界面
├── RAG对话界面
├── 结果展示组件
└── 状态管理
```

### 数据存储

```
papers.db (SQLite)
├── papers 表: 论文元数据
├── paper_content 表: 论文内容分块
└── downloaded_papers/: PDF文件目录
```

## API接口

### POST /search
搜索论文并保存到本地

```json
{
  "query": "deep learning",
  "max_results": 10
}
```

### POST /chat
基于论文进行RAG对话

```json
{
  "query": "什么是深度学习？",
  "topic": "deep learning"
}
```

### GET /papers
列出本地论文

### GET /health
健康检查

## 文件结构

```
research-agent-rag/
├── backend/
│   ├── simple_mvp_server.py    # MVP后端服务器
│   ├── papers.db               # SQLite数据库
│   └── downloaded_papers/      # PDF文件目录
├── frontend/
│   └── app/mvp/page.tsx        # MVP前端页面
├── requirements-mvp.txt        # 最小依赖
├── start-mvp.sh               # 启动脚本
└── MVP-README.md              # 本文档
```

## 扩展方向

### 短期优化
1. **改进RAG算法**: 使用embedding向量检索
2. **PDF文本提取**: 解析PDF内容进行全文检索
3. **多语言支持**: 支持中文论文和查询
4. **UI优化**: 改进用户界面和交互体验

### 中期功能
1. **用户系统**: 多用户支持和数据隔离
2. **项目管理**: 论文分组和项目组织
3. **高级搜索**: 筛选条件和排序选项
4. **导出功能**: 论文列表和对话记录导出

### 长期规划
1. **AI代理**: 集成专业分析代理
2. **协作功能**: 团队共享和讨论
3. **可视化**: 论文关系图和趋势分析
4. **云服务**: 云端部署和同步

## 依赖说明

### 后端依赖 (requirements-mvp.txt)
- `fastapi`: Web框架
- `uvicorn`: ASGI服务器
- `httpx`: HTTP客户端
- `pydantic`: 数据验证

### 前端依赖
- Next.js (已有)
- 现有UI组件库

## 故障排除

### 常见问题

1. **Python 3.13兼容性问题**
   - 推荐使用 `./start-mvp-conda.sh` (创建Python 3.11环境)
   - 或使用 `./start-mvp-simple.sh` (最新依赖版本)
   - Python 3.13对某些库有兼容性问题

2. **ArXiv API超时**
   - 检查网络连接
   - 等待重试，API有速率限制

3. **PDF下载失败**
   - 检查磁盘空间
   - 某些论文可能不提供PDF

4. **数据库权限错误**
   - 确保目录写权限
   - 检查SQLite文件权限

5. **虚拟环境问题**
   - 删除venv-mvp目录重新创建
   - 使用Python 3.8+版本

### 开发调试

```bash
# 查看后端日志
cd backend && python simple_mvp_server.py

# 检查数据库
sqlite3 papers.db ".tables"

# 测试API
curl http://localhost:8000/health
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交PR到main分支
4. 确保测试通过

## 许可证

MIT License - 详见LICENSE文件