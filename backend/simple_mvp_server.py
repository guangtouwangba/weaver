"""
简化版MVP服务器 - 基本功能：关键词搜索 -> ArXiv论文 -> 本地存储 -> RAG检索
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import sqlite3
import json
import httpx
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import uvicorn

# 添加后端目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据模型
class SearchRequest(BaseModel):
    query: str
    max_results: int  # 用户必须指定搜索数量

class SearchResponse(BaseModel):
    success: bool
    papers: List[Dict[str, Any]]
    total_found: int
    message: str = ""

class ChatRequest(BaseModel):
    query: str
    topic: str = ""

class ChatResponse(BaseModel):
    success: bool
    response: str
    relevant_papers: List[Dict[str, Any]]
    message: str = ""

class PaperInfo(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    published: str
    pdf_url: str
    local_path: Optional[str] = None

# 简化的ArXiv客户端
class SimpleArxivClient:
    def __init__(self):
        self.base_url = "https://export.arxiv.org/api/query"
    
    async def search_papers(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """搜索ArXiv论文"""
        try:
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                # 解析XML响应
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                papers = []
                for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                    paper = self._parse_entry(entry)
                    if paper:
                        papers.append(paper)
                
                return papers
                
        except httpx.HTTPStatusError as e:
            logger.error(f"ArXiv API HTTP错误: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.TimeoutException:
            logger.error("ArXiv API请求超时")
            return []
        except Exception as e:
            logger.error(f"ArXiv搜索失败: {e}")
            return []
    
    def _parse_entry(self, entry) -> Optional[Dict[str, Any]]:
        """解析单个论文条目"""
        try:
            # 提取基本信息
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
            abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
            published = entry.find('{http://www.w3.org/2005/Atom}published').text
            
            # 提取ArXiv ID
            arxiv_id = entry.find('{http://www.w3.org/2005/Atom}id').text.split('/')[-1]
            
            # 提取作者
            authors = []
            for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                name = author.find('{http://www.w3.org/2005/Atom}name').text
                authors.append(name)
            
            # PDF链接
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            return {
                'id': str(uuid.uuid4()),
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'arxiv_id': arxiv_id,
                'published': published,
                'pdf_url': pdf_url,
                'local_path': None
            }
            
        except Exception as e:
            logger.error(f"解析论文条目失败: {e}")
            return None

# 简化的数据库管理
class SimplePaperDB:
    def __init__(self, db_path: str = "papers.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    arxiv_id TEXT UNIQUE,
                    published TEXT,
                    pdf_url TEXT,
                    local_path TEXT,
                    topic TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS paper_content (
                    paper_id TEXT,
                    chunk_id TEXT,
                    content TEXT,
                    embedding TEXT,
                    FOREIGN KEY (paper_id) REFERENCES papers (id)
                )
            ''')
    
    def save_paper(self, paper: Dict[str, Any], topic: str = "") -> bool:
        """保存论文到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO papers 
                    (id, title, authors, abstract, arxiv_id, published, pdf_url, local_path, topic)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    paper['id'],
                    paper['title'],
                    json.dumps(paper['authors']),
                    paper['abstract'],
                    paper['arxiv_id'],
                    paper['published'],
                    paper['pdf_url'],
                    paper.get('local_path'),
                    topic
                ))
            return True
        except Exception as e:
            logger.error(f"保存论文失败: {e}")
            return False
    
    def search_papers(self, query: str, topic: str = "") -> List[Dict[str, Any]]:
        """搜索本地论文"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 构建查询条件
                where_conditions = []
                params = []
                
                if query:
                    where_conditions.append("(title LIKE ? OR abstract LIKE ?)")
                    query_param = f"%{query}%"
                    params.extend([query_param, query_param])
                
                if topic:
                    where_conditions.append("topic = ?")
                    params.append(topic)
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                cursor = conn.execute(f'''
                    SELECT id, title, authors, abstract, arxiv_id, published, pdf_url, local_path, topic
                    FROM papers 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT 20
                ''', params)
                
                papers = []
                for row in cursor.fetchall():
                    paper = {
                        'id': row[0],
                        'title': row[1],
                        'authors': json.loads(row[2]),
                        'abstract': row[3],
                        'arxiv_id': row[4],
                        'published': row[5],
                        'pdf_url': row[6],
                        'local_path': row[7],
                        'topic': row[8]
                    }
                    papers.append(paper)
                
                return papers
                
        except Exception as e:
            logger.error(f"搜索论文失败: {e}")
            return []
    
    def get_papers_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """根据主题获取论文"""
        return self.search_papers("", topic)

# 简化的PDF下载器
class SimplePDFDownloader:
    def __init__(self, download_dir: str = "downloaded_papers"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    async def download_pdf(self, paper: Dict[str, Any]) -> Optional[str]:
        """下载PDF文件"""
        try:
            filename = f"{paper['arxiv_id']}.pdf"
            file_path = self.download_dir / filename
            
            # 如果文件已存在，直接返回路径
            if file_path.exists():
                return str(file_path)
            
            # 下载PDF
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(paper['pdf_url'], timeout=60)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"PDF下载成功: {filename}")
                return str(file_path)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"PDF下载HTTP错误: {e.response.status_code} - {paper['pdf_url']}")
            return None
        except httpx.TimeoutException:
            logger.error(f"PDF下载超时: {paper['pdf_url']}")
            return None
        except Exception as e:
            logger.error(f"PDF下载失败: {e}")
            return None

# 简化的RAG检索
class SimpleRAGRetriever:
    def __init__(self, db: SimplePaperDB):
        self.db = db
    
    def search_relevant_papers(self, query: str, topic: str = "", max_results: int = 5) -> List[Dict[str, Any]]:
        """检索相关论文（简化版本，基于关键词匹配）"""
        papers = self.db.search_papers(query, topic)
        
        # 简单的相关性评分（基于关键词匹配）
        scored_papers = []
        query_words = set(query.lower().split())
        
        for paper in papers:
            score = 0
            title_words = set(paper['title'].lower().split())
            abstract_words = set(paper['abstract'].lower().split())
            
            # 计算标题匹配度
            title_matches = len(query_words & title_words)
            score += title_matches * 2  # 标题匹配权重更高
            
            # 计算摘要匹配度
            abstract_matches = len(query_words & abstract_words)
            score += abstract_matches
            
            if score > 0:
                paper['relevance_score'] = score / len(query_words)
                scored_papers.append(paper)
        
        # 按相关性排序
        scored_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_papers[:max_results]
    
    def generate_response(self, query: str, papers: List[Dict[str, Any]]) -> str:
        """生成基于论文的回答（简化版本）"""
        if not papers:
            return "没有找到相关的论文来回答您的问题。"
        
        # 简单的摘要生成
        response = f"基于 {len(papers)} 篇相关论文的分析：\n\n"
        
        for i, paper in enumerate(papers[:3], 1):
            response += f"{i}. **{paper['title']}**\n"
            response += f"   作者: {', '.join(paper['authors'][:3])}{'等' if len(paper['authors']) > 3 else ''}\n"
            
            # 提取摘要中的关键信息
            abstract = paper['abstract'][:200] + "..." if len(paper['abstract']) > 200 else paper['abstract']
            response += f"   摘要: {abstract}\n\n"
        
        response += f"如需了解更多细节，建议查看完整论文内容。"
        return response

# 创建FastAPI应用
app = FastAPI(
    title="简化版研究论文系统",
    description="MVP版本：关键词搜索 -> ArXiv论文 -> 本地存储 -> RAG检索",
    version="0.1.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
arxiv_client = SimpleArxivClient()
paper_db = SimplePaperDB()
pdf_downloader = SimplePDFDownloader()
rag_retriever = SimpleRAGRetriever(paper_db)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "简化版研究论文系统 MVP",
        "version": "0.1.0",
        "endpoints": {
            "search": "/search",
            "chat": "/chat", 
            "papers": "/papers",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }

@app.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """搜索论文并保存到本地数据库"""
    try:
        # 验证搜索数量
        if request.max_results < 1 or request.max_results > 100:
            raise HTTPException(status_code=400, detail="搜索数量必须在1-100之间")
            
        logger.info(f"搜索论文: {request.query}, 数量: {request.max_results}")
        
        # 先搜索本地数据库
        local_papers = paper_db.search_papers(request.query)
        
        # 如果本地论文不足，从ArXiv搜索
        if len(local_papers) < request.max_results:
            remaining = request.max_results - len(local_papers)
            arxiv_papers = await arxiv_client.search_papers(request.query, remaining)
            
            # 保存新论文到数据库
            for paper in arxiv_papers:
                paper_db.save_paper(paper, topic=request.query)
                
                # 异步下载PDF（不等待）
                asyncio.create_task(download_paper_async(paper))
            
            # 合并结果
            all_papers = local_papers + arxiv_papers
        else:
            all_papers = local_papers[:request.max_results]
        
        return SearchResponse(
            success=True,
            papers=all_papers,
            total_found=len(all_papers),
            message=f"找到 {len(all_papers)} 篇论文"
        )
        
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_with_papers(request: ChatRequest):
    """基于论文进行RAG对话"""
    try:
        logger.info(f"RAG对话: {request.query}")
        
        # 检索相关论文
        relevant_papers = rag_retriever.search_relevant_papers(
            request.query, 
            request.topic,
            max_results=5
        )
        
        # 生成回答
        response_text = rag_retriever.generate_response(request.query, relevant_papers)
        
        return ChatResponse(
            success=True,
            response=response_text,
            relevant_papers=relevant_papers,
            message=f"基于 {len(relevant_papers)} 篇论文生成回答"
        )
        
    except Exception as e:
        logger.error(f"对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")

@app.get("/papers")
async def list_papers(topic: str = "", limit: int = 20):
    """列出本地论文"""
    try:
        if topic:
            papers = paper_db.get_papers_by_topic(topic)
        else:
            papers = paper_db.search_papers("", "")
        
        return {
            "success": True,
            "papers": papers[:limit],
            "total": len(papers)
        }
        
    except Exception as e:
        logger.error(f"获取论文列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取论文失败: {str(e)}")

@app.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        all_papers = paper_db.search_papers("", "")
        topics = {}
        pdf_downloaded = 0
        
        for paper in all_papers:
            topic = paper.get('topic', 'unknown')
            topics[topic] = topics.get(topic, 0) + 1
            if paper.get('local_path'):
                pdf_downloaded += 1
        
        return {
            "success": True,
            "stats": {
                "total_papers": len(all_papers),
                "pdf_downloaded": pdf_downloaded,
                "topics": topics
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

async def download_paper_async(paper: Dict[str, Any]):
    """异步下载PDF任务"""
    try:
        local_path = await pdf_downloader.download_pdf(paper)
        if local_path:
            # 更新数据库中的本地路径
            with sqlite3.connect(paper_db.db_path) as conn:
                conn.execute(
                    "UPDATE papers SET local_path = ? WHERE id = ?",
                    (local_path, paper['id'])
                )
    except Exception as e:
        logger.error(f"异步下载PDF失败: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "simple_mvp_server:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )