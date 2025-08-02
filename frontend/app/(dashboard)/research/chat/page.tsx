"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { 
  Brain, 
  Send, 
  BookOpen, 
  Users, 
  Clock, 
  Settings,
  Loader2,
  User,
  Bot
} from "lucide-react"

interface Message {
  id: string
  type: "user" | "agent" | "system"
  content: string
  agentName?: string
  agentType?: "mit_researcher" | "google_engineer" | "industry_expert" | "paper_analyst"
  timestamp: Date
  papers?: Paper[]
}

interface Paper {
  id: string
  title: string
  authors: string[]
  abstract: string
  publishedDate: string
  arxivId: string
  relevanceScore: number
}

export default function ResearchChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "system",
      content: "欢迎使用AI协作研究台！请描述您的研究问题，专业AI代理团队将为您分析相关论文。",
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [activeAgents, setActiveAgents] = useState<string[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const agents = [
    {
      id: "mit_researcher",
      name: "MIT研究员",
      role: "学术研究专家",
      status: "ready",
      color: "bg-blue-500"
    },
    {
      id: "google_engineer", 
      name: "Google工程师",
      role: "工程实践专家",
      status: "ready",
      color: "bg-green-500"
    },
    {
      id: "industry_expert",
      name: "行业专家",
      role: "商业应用专家", 
      status: "ready",
      color: "bg-purple-500"
    },
    {
      id: "paper_analyst",
      name: "论文分析师",
      role: "文献分析专家",
      status: "ready", 
      color: "bg-orange-500"
    }
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)
    setActiveAgents(["paper_analyst"])

    // 模拟AI响应
    setTimeout(() => {
      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "agent",
        content: "我正在搜索相关论文，请稍候...",
        agentName: "论文分析师",
        agentType: "paper_analyst",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, agentMessage])
      
      setTimeout(() => {
        const resultsMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: "agent", 
          content: "我找到了15篇相关论文，现在邀请其他专家一起分析。",
          agentName: "论文分析师",
          agentType: "paper_analyst",
          timestamp: new Date(),
          papers: [
            {
              id: "1",
              title: "Attention Is All You Need",
              authors: ["Vaswani, A.", "Shazeer, N."],
              abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
              publishedDate: "2017-06-12",
              arxivId: "1706.03762",
              relevanceScore: 0.95
            }
          ]
        }
        setMessages(prev => [...prev, resultsMessage])
        setActiveAgents(["mit_researcher", "google_engineer"])
        setIsLoading(false)
      }, 2000)
    }, 1000)
  }

  const getAgentIcon = (agentType?: string) => {
    switch (agentType) {
      case "mit_researcher":
        return "🎓"
      case "google_engineer":
        return "⚙️"
      case "industry_expert":
        return "💼"
      case "paper_analyst":
        return "📊"
      default:
        return "🤖"
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                <CardTitle>AI协作研究对话</CardTitle>
              </div>
              <div className="flex items-center gap-2">
                {activeAgents.length > 0 && (
                  <Badge variant="secondary" className="gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    {activeAgents.length} 个代理工作中
                  </Badge>
                )}
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0">
            {/* Messages */}
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.type === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.type !== "user" && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm">
                          {message.type === "agent" ? getAgentIcon(message.agentType) : "🤖"}
                        </div>
                      </div>
                    )}
                    
                    <div className={`flex flex-col space-y-1 max-w-[70%] ${
                      message.type === "user" ? "items-end" : "items-start"
                    }`}>
                      {message.agentName && (
                        <span className="text-xs font-medium text-muted-foreground">
                          {message.agentName}
                        </span>
                      )}
                      
                      <div className={`rounded-lg p-3 ${
                        message.type === "user"
                          ? "bg-primary text-primary-foreground"
                          : message.type === "system"
                          ? "bg-muted text-muted-foreground"
                          : "bg-card border"
                      }`}>
                        <p className="text-sm">{message.content}</p>
                        
                        {message.papers && message.papers.length > 0 && (
                          <div className="mt-3 space-y-2">
                            {message.papers.map((paper) => (
                              <div key={paper.id} className="border rounded p-2 bg-background">
                                <div className="flex items-start justify-between gap-2">
                                  <div className="flex-1">
                                    <h4 className="font-medium text-sm">{paper.title}</h4>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      {paper.authors.join(", ")}
                                    </p>
                                  </div>
                                  <Badge variant="outline" className="text-xs">
                                    {Math.round(paper.relevanceScore * 100)}%
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      <span className="text-xs text-muted-foreground">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>

                    {message.type === "user" && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                          <User className="h-4 w-4 text-primary-foreground" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div ref={messagesEndRef} />
            </ScrollArea>

            <Separator />

            {/* Input Area */}
            <div className="p-4">
              <div className="flex gap-2">
                <Input
                  placeholder="描述您的研究问题或继续对话..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSend()}
                  disabled={isLoading}
                />
                <Button 
                  onClick={handleSend} 
                  disabled={isLoading || !inputValue.trim()}
                  size="icon"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Agents Panel */}
      <div className="w-80">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              AI专家团队
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                  activeAgents.includes(agent.id) 
                    ? "bg-accent border-primary" 
                    : "hover:bg-accent/50"
                }`}
              >
                <div className={`w-3 h-3 rounded-full ${agent.color}`} />
                <div className="flex-1">
                  <p className="font-medium text-sm">{agent.name}</p>
                  <p className="text-xs text-muted-foreground">{agent.role}</p>
                </div>
                <div className="flex items-center gap-1">
                  {activeAgents.includes(agent.id) ? (
                    <Loader2 className="h-3 w-3 animate-spin text-primary" />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-base">快速操作</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" size="sm" className="w-full justify-start">
              <BookOpen className="h-4 w-4 mr-2" />
              浏览论文库
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start">
              <Clock className="h-4 w-4 mr-2" />
              查看历史对话
            </Button>
            <Button variant="outline" size="sm" className="w-full justify-start">
              <Settings className="h-4 w-4 mr-2" />
              代理设置
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}