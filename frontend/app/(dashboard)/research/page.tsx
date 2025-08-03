"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { apiClient, AnalysisRequest, QuickAnalysisRequest, ApiError } from "@/lib/api"
import { useAnalysisWebSocket, AnalysisProgress } from "@/hooks/use-analysis-websocket"
import { ApiErrorDisplay } from "@/components/ui/error-boundary"
import { ButtonLoading } from "@/components/ui/loading-state"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { 
  Brain, 
  Search, 
  Plus, 
  Clock, 
  BookOpen, 
  Users,
  Loader2,
  CheckCircle,
  ArrowRight,
  Sparkles,
  Zap,
  TrendingUp
} from "lucide-react"
import Link from "next/link"

export default function ResearchPage() {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState("")
  const [quickResults, setQuickResults] = useState<any[]>([])
  const [showResults, setShowResults] = useState(false)
  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [agentInsights, setAgentInsights] = useState<Record<string, string>>({})

  // WebSocket connection for real-time updates
  const { isConnected: wsConnected, error: wsError } = useAnalysisWebSocket({
    analysisId,
    onProgress: (progress: AnalysisProgress) => {
      setAnalysisProgress(progress.progress)
      setCurrentStep(progress.step)
      if (progress.papers.length > 0) {
        setQuickResults(progress.papers)
      }
      if (Object.keys(progress.agentInsights).length > 0) {
        setAgentInsights(prev => ({ ...prev, ...progress.agentInsights }))
      }
    },
    onPapersFound: (papers: any[]) => {
      setQuickResults(papers)
      setShowResults(true)
    },
    onAgentInsight: (agentName: string, insight: string) => {
      setAgentInsights(prev => ({ ...prev, [agentName]: insight }))
    },
    onCompleted: (results: any) => {
      setIsAnalyzing(false)
      setAnalysisProgress(100)
      setCurrentStep("分析完成")
      setShowResults(true)
      if (results.papers_found) {
        setQuickResults(results.papers_found)
      }
    },
    onError: (error: string) => {
      setError(error)
      setIsAnalyzing(false)
    }
  })

  const recentProjects = [
    {
      id: "1",
      title: "深度学习在自然语言处理中的最新进展",
      description: "分析2024年最新的Transformer架构改进",
      status: "completed",
      agentsUsed: ["MIT研究员", "Google工程师"],
      createdAt: "2024-01-15",
      papers: 12
    },
    {
      id: "2", 
      title: "量子计算在机器学习中的应用",
      description: "探索量子算法对传统ML模型的加速效果",
      status: "in_progress",
      agentsUsed: ["MIT研究员", "行业专家"],
      createdAt: "2024-01-14",
      papers: 8
    }
  ]

  const suggestedQueries = [
    "大语言模型的推理能力评估方法",
    "多模态学习在计算机视觉中的应用", 
    "联邦学习的隐私保护机制",
    "强化学习在自动驾驶中的最新突破"
  ]

  // 分析步骤配置
  const analysisSteps = [
    { id: 1, name: "论文检索", description: "搜索相关学术论文", duration: 2000 },
    { id: 2, name: "AI分析启动", description: "启动专业AI代理", duration: 1500 },
    { id: 3, name: "内容分析", description: "深度分析论文内容", duration: 3000 },
    { id: 4, name: "协作讨论", description: "AI代理协作讨论", duration: 2500 },
    { id: 5, name: "生成洞察", description: "总结关键发现", duration: 2000 }
  ]

  // 开始分析功能 - 使用真实API
  const handleStartAnalysis = async () => {
    if (!query.trim()) return

    setIsAnalyzing(true)
    setAnalysisProgress(0)
    setShowResults(false)
    setQuickResults([])
    setError(null)
    setAgentInsights({})

    try {
      // 首先进行快速分析获取初始结果
      const quickRequest: QuickAnalysisRequest = {
        query: query.trim(),
        max_papers: 10
      }

      const quickResponse = await apiClient.quickAnalysis(quickRequest)
      
      if (quickResponse.success && quickResponse.papers.length > 0) {
        // 显示快速结果
        setQuickResults(quickResponse.papers.map(paper => ({
          id: paper.id,
          title: paper.title,
          authors: Array.isArray(paper.authors) ? paper.authors : [paper.authors],
          relevance: paper.relevance_score || 0.8,
          summary: paper.abstract || paper.summary || ""
        })))
        setShowResults(true)
      }

      // 启动完整分析
      const analysisRequest: AnalysisRequest = {
        query: query.trim(),
        max_papers: 20,
        similarity_threshold: 0.5,
        enable_arxiv_fallback: true,
        selected_agents: ["mit_researcher", "paper_analyst", "google_engineer"]
      }

      const analysisResponse = await apiClient.startAnalysis(analysisRequest)
      
      // 设置分析ID以启动WebSocket连接
      setAnalysisId(analysisResponse.analysis_id)
      setCurrentStep(analysisResponse.current_step)
      
    } catch (error) {
      console.error("Analysis failed:", error)
      if (error instanceof ApiError) {
        setError(`分析失败: ${error.message}`)
      } else {
        setError("分析失败: 网络错误或服务器不可用")
      }
      setIsAnalyzing(false)
    }
  }

  // 继续深度分析
  const handleContinueAnalysis = () => {
    // 创建新项目并跳转到对话界面
    router.push('/research/chat?query=' + encodeURIComponent(query))
  }

  // 支持回车键快速启动
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isAnalyzing && query.trim()) {
      handleStartAnalysis()
    }
  }

  // 选择建议主题
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
    setShowResults(false)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI协作研究台</h1>
          <p className="text-muted-foreground">
            与专业AI代理团队一起探索学术前沿
          </p>
        </div>
        <Button size="lg" className="gap-2" asChild>
          <Link href="/research/projects/new">
            <Plus className="h-4 w-4" />
            开始新研究
          </Link>
        </Button>
      </div>

      {/* Quick Research Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            快速研究启动
          </CardTitle>
          <CardDescription>
            描述您的研究问题，AI代理团队将为您检索和分析相关论文
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Input
              placeholder="例如：深度学习在自然语言处理中的最新进展..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="text-base"
            />
            <div className="flex gap-2">
              <Button 
                className="gap-2" 
                onClick={handleStartAnalysis}
                disabled={!query.trim() || isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" />
                    开始分析
                  </>
                )}
              </Button>
              <Button variant="outline" asChild>
                <Link href="/research/advanced">
                  使用高级搜索
                </Link>
              </Button>
            </div>
          </div>
          
          {/* Suggested Queries */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">建议的研究主题：</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQueries.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <ApiErrorDisplay 
              error={error} 
              onDismiss={() => setError(null)}
              className="mt-4"
            />
          )}

          {/* Analysis Progress */}
          {isAnalyzing && (
            <div className="space-y-4 pt-4 border-t">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                <span className="text-sm font-medium">AI代理团队正在分析中...</span>
                {analysisId && (
                  <Badge variant="outline" className="text-xs">
                    {wsConnected ? "实时连接" : "连接中..."}
                  </Badge>
                )}
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{currentStep}</span>
                  <span className="font-medium">{Math.round(analysisProgress)}%</span>
                </div>
                <Progress value={analysisProgress} className="h-2" />
              </div>

              <div className="grid grid-cols-4 gap-2">
                {analysisSteps.map((step, index) => (
                  <div 
                    key={step.id}
                    className={`text-center p-2 rounded text-xs ${
                      analysisProgress >= ((index + 1) / analysisSteps.length) * 100
                        ? "bg-primary/10 text-primary"
                        : analysisProgress >= (index / analysisSteps.length) * 100
                        ? "bg-yellow-50 text-yellow-600"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {step.name}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick Results */}
          {showResults && quickResults.length > 0 && (
            <div className="space-y-4 pt-4 border-t">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium">快速分析结果</span>
                </div>
                <Badge variant="secondary" className="text-xs">
                  找到 {quickResults.length} 篇相关论文
                </Badge>
              </div>

              <div className="space-y-3">
                {quickResults.map((result) => (
                  <div key={result.id} className="border rounded-lg p-3 hover:bg-accent/50 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm line-clamp-1">{result.title}</h4>
                        <p className="text-xs text-muted-foreground mt-1">
                          {result.authors.join(", ")}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {result.summary}
                        </p>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {Math.round((result.relevance || result.relevance_score || 0.8) * 100)}% 相关
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-2">
                <Button onClick={handleContinueAnalysis} className="gap-2">
                  <Brain className="h-4 w-4" />
                  继续深度分析
                </Button>
                <Button variant="outline" className="gap-2">
                  <BookOpen className="h-4 w-4" />
                  查看所有论文
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Brain className="h-4 w-4 text-primary" />
              <div>
                <p className="text-2xl font-bold">4</p>
                <p className="text-xs text-muted-foreground">AI专家代理</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <BookOpen className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-2xl font-bold">1,247</p>
                <p className="text-xs text-muted-foreground">已分析论文</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">23</p>
                <p className="text-xs text-muted-foreground">研究项目</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-orange-600" />
              <div>
                <p className="text-2xl font-bold">2</p>
                <p className="text-xs text-muted-foreground">进行中项目</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">最近的研究项目</h2>
          <Link href="/research/projects">
            <Button variant="outline" size="sm">
              查看全部
            </Button>
          </Link>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2">
          {recentProjects.map((project) => (
            <Card key={project.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-base">{project.title}</CardTitle>
                    <CardDescription className="text-sm">
                      {project.description}
                    </CardDescription>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                    project.status === 'completed' 
                      ? 'bg-green-100 text-green-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {project.status === 'completed' ? '已完成' : '进行中'}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <BookOpen className="h-3 w-3" />
                      {project.papers} 篇论文
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {project.agentsUsed.join(", ")}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      创建于 {project.createdAt}
                    </span>
                    <Button size="sm" variant="outline" asChild>
                      <Link href={`/research/projects/${project.id}`}>
                        查看详情
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}