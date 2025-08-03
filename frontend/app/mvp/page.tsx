"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  Search, 
  MessageCircle, 
  BookOpen, 
  Download,
  ExternalLink,
  Loader2,
  CheckCircle
} from "lucide-react"

interface Paper {
  id: string
  title: string
  authors: string[]
  abstract: string
  arxiv_id: string
  published: string
  pdf_url: string
  local_path?: string
  relevance_score?: number
}

interface SearchResponse {
  success: boolean
  papers: Paper[]
  total_found: number
  message: string
}

interface ChatResponse {
  success: boolean
  response: string
  relevant_papers: Paper[]
  message: string
}

export default function MVPPage() {
  // 搜索相关状态
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<Paper[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchMessage, setSearchMessage] = useState("")

  // 对话相关状态
  const [chatQuery, setChatQuery] = useState("")
  const [chatResponse, setChatResponse] = useState("")
  const [chatPapers, setChatPapers] = useState<Paper[]>([])
  const [isChatting, setIsChatting] = useState(false)
  const [currentTopic, setCurrentTopic] = useState("")

  // API base URL
  const API_BASE = "http://localhost:8000"

  // 搜索论文
  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setIsSearching(true)
    setSearchMessage("")
    
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery.trim(),
          max_results: 10
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: SearchResponse = await response.json()
      
      if (data.success) {
        setSearchResults(data.papers)
        setSearchMessage(data.message)
        setCurrentTopic(searchQuery.trim())
      } else {
        setSearchMessage("搜索失败")
      }

    } catch (error) {
      console.error("搜索失败:", error)
      setSearchMessage("搜索失败，请检查网络连接")
    } finally {
      setIsSearching(false)
    }
  }

  // RAG对话
  const handleChat = async () => {
    if (!chatQuery.trim()) return

    setIsChatting(true)
    
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: chatQuery.trim(),
          topic: currentTopic
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: ChatResponse = await response.json()
      
      if (data.success) {
        setChatResponse(data.response)
        setChatPapers(data.relevant_papers)
      } else {
        setChatResponse("对话失败，请重试")
      }

    } catch (error) {
      console.error("对话失败:", error)
      setChatResponse("对话失败，请检查网络连接")
    } finally {
      setIsChatting(false)
    }
  }

  // 处理回车键
  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isSearching) {
      handleSearch()
    }
  }

  const handleChatKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey && !isChatting) {
      handleChat()
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* 标题 */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">研究论文系统 MVP</h1>
        <p className="text-muted-foreground">
          关键词搜索 → ArXiv论文 → 本地存储 → RAG检索对话
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 左侧：论文搜索 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                论文搜索
              </CardTitle>
              <CardDescription>
                输入关键词搜索ArXiv论文，自动下载并保存到本地
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="例如：deep learning, natural language processing..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={handleSearchKeyPress}
                  className="flex-1"
                />
                <Button 
                  onClick={handleSearch}
                  disabled={!searchQuery.trim() || isSearching}
                >
                  {isSearching ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                </Button>
              </div>
              
              {searchMessage && (
                <div className="text-sm text-muted-foreground">
                  {searchMessage}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 搜索结果 */}
          {searchResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    搜索结果
                  </span>
                  <Badge variant="secondary">
                    {searchResults.length} 篇论文
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {searchResults.map((paper) => (
                    <div key={paper.id} className="border rounded-lg p-4 space-y-2">
                      <h4 className="font-medium text-sm leading-tight">
                        {paper.title}
                      </h4>
                      <p className="text-xs text-muted-foreground">
                        {paper.authors.slice(0, 3).join(", ")}
                        {paper.authors.length > 3 && " 等"}
                      </p>
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {paper.abstract}
                      </p>
                      <div className="flex items-center justify-between text-xs">
                        <Badge variant="outline">
                          {paper.arxiv_id}
                        </Badge>
                        <div className="flex gap-2">
                          {paper.local_path && (
                            <Badge variant="secondary" className="gap-1">
                              <CheckCircle className="h-3 w-3" />
                              已下载
                            </Badge>
                          )}
                          <a 
                            href={paper.pdf_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 hover:underline"
                          >
                            <ExternalLink className="h-3 w-3" />
                            PDF
                          </a>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 右侧：RAG对话 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageCircle className="h-5 w-5" />
                RAG对话
              </CardTitle>
              <CardDescription>
                基于已搜索的论文进行智能对话
                {currentTopic && ` (当前主题: ${currentTopic})`}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="询问关于论文的问题... (Ctrl+Enter发送)"
                value={chatQuery}
                onChange={(e) => setChatQuery(e.target.value)}
                onKeyPress={handleChatKeyPress}
                rows={3}
                className="resize-none"
              />
              <Button 
                onClick={handleChat}
                disabled={!chatQuery.trim() || isChatting}
                className="w-full"
              >
                {isChatting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    分析中...
                  </>
                ) : (
                  <>
                    <MessageCircle className="h-4 w-4 mr-2" />
                    发送询问
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* 对话回复 */}
          {chatResponse && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">AI回复</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-sm">
                      {chatResponse}
                    </div>
                  </div>
                  
                  {chatPapers.length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h5 className="font-medium text-sm mb-2 flex items-center gap-2">
                          <BookOpen className="h-4 w-4" />
                          参考论文 ({chatPapers.length} 篇)
                        </h5>
                        <div className="space-y-2">
                          {chatPapers.map((paper) => (
                            <div key={paper.id} className="border rounded p-2 text-xs">
                              <div className="font-medium line-clamp-1">
                                {paper.title}
                              </div>
                              <div className="text-muted-foreground">
                                {paper.authors.slice(0, 2).join(", ")}
                                {paper.authors.length > 2 && " 等"}
                                {paper.relevance_score && (
                                  <span className="ml-2">
                                    (相关度: {(paper.relevance_score * 100).toFixed(0)}%)
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* 使用说明 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">使用说明</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h6 className="font-medium mb-2">1. 搜索论文</h6>
              <ul className="space-y-1 text-muted-foreground">
                <li>• 输入英文关键词搜索ArXiv论文</li>
                <li>• 系统自动下载PDF到本地</li>
                <li>• 论文保存在SQLite数据库</li>
              </ul>
            </div>
            <div>
              <h6 className="font-medium mb-2">2. RAG对话</h6>
              <ul className="space-y-1 text-muted-foreground">
                <li>• 基于已搜索的论文内容对话</li>
                <li>• 支持中英文问答</li>
                <li>• 显示相关论文参考</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}