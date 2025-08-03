"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { 
  ArrowLeft,
  Calendar,
  Users,
  BookOpen,
  FileText,
  Star,
  Share,
  Download,
  Edit,
  Archive,
  Play,
  Pause,
  Brain,
  TrendingUp,
  Clock,
  Target,
  Lightbulb,
  ExternalLink,
  MessageSquare,
  Settings
} from "lucide-react"
import Link from "next/link"

// 模拟项目数据
const getProjectById = (id: string) => {
  const projects = {
    "1": {
      id: "1",
      title: "深度学习在自然语言处理中的最新进展",
      description: "分析2024年最新的Transformer架构改进和应用实践，探索大语言模型的发展趋势和技术突破",
      status: "completed",
      priority: "high",
      createdAt: "2024-01-15",
      updatedAt: "2024-01-20",
      completedAt: "2024-01-20",
      query: "深度学习 自然语言处理 Transformer 2024 大语言模型",
      papersCount: 24,
      agentsUsed: ["MIT研究员", "Google工程师", "论文分析师"],
      keyFindings: [
        "Transformer架构在效率上有了显著提升，新的注意力机制减少了50%的计算量",
        "多模态融合成为新的研究热点，文本-图像-音频的统一模型架构日趋成熟",
        "模型压缩技术取得重要突破，知识蒸馏和量化技术使大模型可在移动设备运行",
        "指令微调和人类偏好对齐技术显著提升了模型的可控性和安全性",
        "上下文学习能力的提升使模型能够处理更复杂的推理任务"
      ],
      tags: ["深度学习", "NLP", "Transformer", "大语言模型"],
      isStarred: true,
      collaborators: ["张三", "李四"],
      progress: 100,
      totalHours: 48,
      papers: [
        {
          id: "p1",
          title: "Attention Is All You Need",
          authors: ["Vaswani, A.", "Shazeer, N."],
          relevanceScore: 0.95,
          status: "analyzed"
        },
        {
          id: "p2", 
          title: "BERT: Pre-training of Deep Bidirectional Transformers",
          authors: ["Devlin, J.", "Chang, M."],
          relevanceScore: 0.88,
          status: "analyzed"
        }
      ],
      timeline: [
        {
          date: "2024-01-15",
          event: "项目创建",
          description: "启动深度学习在NLP领域的最新进展研究"
        },
        {
          date: "2024-01-16", 
          event: "论文检索完成",
          description: "AI代理团队检索到24篇相关论文"
        },
        {
          date: "2024-01-18",
          event: "AI分析完成",
          description: "三个AI代理完成论文深度分析"
        },
        {
          date: "2024-01-20",
          event: "项目完成",
          description: "生成最终研究报告和关键发现"
        }
      ],
      agentContributions: [
        {
          agentName: "MIT研究员",
          avatar: "🎓",
          tasksCompleted: 8,
          keyInsights: [
            "理论分析显示新注意力机制的数学原理",
            "验证了多头注意力的收敛性改进"
          ]
        },
        {
          agentName: "Google工程师", 
          avatar: "⚙️",
          tasksCompleted: 12,
          keyInsights: [
            "工程实践角度分析了模型部署的性能优化",
            "提出了分布式训练的改进方案"
          ]
        },
        {
          agentName: "论文分析师",
          avatar: "📊", 
          tasksCompleted: 15,
          keyInsights: [
            "系统性分析了24篇论文的方法学差异",
            "构建了技术发展的时间轴和影响力图谱"
          ]
        }
      ]
    }
  }
  
  return projects[id as keyof typeof projects]
}

export default function ProjectDetailPage() {
  const params = useParams()
  const projectId = params.id as string
  const [activeTab, setActiveTab] = useState("overview")
  
  const project = getProjectById(projectId)
  
  if (!project) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h3 className="text-lg font-medium">项目未找到</h3>
          <p className="text-muted-foreground">请检查项目ID是否正确</p>
          <Link href="/research/projects">
            <Button className="mt-4">返回项目列表</Button>
          </Link>
        </div>
      </div>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-500"
      case "active": return "bg-blue-500"
      case "draft": return "bg-yellow-500"
      case "archived": return "bg-gray-500"
      default: return "bg-gray-400"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "completed": return "已完成"
      case "active": return "进行中"
      case "draft": return "草稿"
      case "archived": return "已归档"
      default: return status
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "text-red-600 bg-red-50"
      case "medium": return "text-yellow-600 bg-yellow-50"
      case "low": return "text-green-600 bg-green-50"
      default: return "text-gray-600 bg-gray-50"
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/research/projects">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            返回项目列表
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(project.status)}`} />
            <h1 className="text-2xl font-bold">{project.title}</h1>
            {project.isStarred && (
              <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
            )}
          </div>
          <p className="text-muted-foreground mt-1">{project.description}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Share className="h-4 w-4" />
            分享
          </Button>
          <Button variant="outline" className="gap-2">
            <Download className="h-4 w-4" />
            导出
          </Button>
          <Button className="gap-2">
            <Edit className="h-4 w-4" />
            编辑项目
          </Button>
        </div>
      </div>

      {/* Status Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{project.progress}%</div>
              <div className="text-sm text-muted-foreground">完成进度</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{project.papersCount}</div>
              <div className="text-sm text-muted-foreground">分析论文</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{project.agentsUsed.length}</div>
              <div className="text-sm text-muted-foreground">参与代理</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{project.keyFindings.length}</div>
              <div className="text-sm text-muted-foreground">关键发现</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600">{project.totalHours}h</div>
              <div className="text-sm text-muted-foreground">投入时间</div>
            </div>
            <div className="text-center">
              <Badge className={getPriorityColor(project.priority)}>
                {project.priority === "high" ? "高优先级" : 
                 project.priority === "medium" ? "中优先级" : "低优先级"}
              </Badge>
              <div className="text-sm text-muted-foreground mt-1">优先级</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">项目概览</TabsTrigger>
          <TabsTrigger value="papers">论文分析</TabsTrigger>
          <TabsTrigger value="agents">AI协作</TabsTrigger>
          <TabsTrigger value="findings">研究发现</TabsTrigger>
          <TabsTrigger value="timeline">项目时线</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Project Info */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  项目信息
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">状态</span>
                    <Badge variant="outline">{getStatusLabel(project.status)}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">创建时间</span>
                    <span className="text-sm text-muted-foreground">
                      {new Date(project.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">更新时间</span>
                    <span className="text-sm text-muted-foreground">
                      {new Date(project.updatedAt).toLocaleDateString()}
                    </span>
                  </div>
                  {project.completedAt && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">完成时间</span>
                      <span className="text-sm text-muted-foreground">
                        {new Date(project.completedAt).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                  <Separator />
                  <div>
                    <span className="text-sm font-medium">研究查询</span>
                    <p className="text-sm text-muted-foreground mt-1">{project.query}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Team & Collaboration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  团队协作
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium mb-2">AI代理团队</h4>
                  <div className="flex flex-wrap gap-2">
                    {project.agentsUsed.map((agent) => (
                      <Badge key={agent} variant="secondary">
                        {agent}
                      </Badge>
                    ))}
                  </div>
                </div>
                {project.collaborators && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">协作者</h4>
                    <div className="flex flex-wrap gap-2">
                      {project.collaborators.map((collaborator) => (
                        <Badge key={collaborator} variant="outline">
                          {collaborator}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                <div>
                  <h4 className="text-sm font-medium mb-2">标签</h4>
                  <div className="flex flex-wrap gap-2">
                    {project.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Progress Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                进度概览
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">整体进度</span>
                  <span className="text-sm font-bold">{project.progress}%</span>
                </div>
                <Progress value={project.progress} className="h-2" />
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="text-lg font-bold text-blue-600">{project.papersCount}</div>
                    <div className="text-xs text-blue-800">论文已分析</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="text-lg font-bold text-green-600">{project.keyFindings.length}</div>
                    <div className="text-xs text-green-800">关键发现</div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 rounded-lg">
                    <div className="text-lg font-bold text-purple-600">{project.agentsUsed.length}</div>
                    <div className="text-xs text-purple-800">AI代理参与</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="papers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                分析论文列表
              </CardTitle>
              <CardDescription>
                共分析了 {project.papersCount} 篇相关论文
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {project.papers.map((paper, index) => (
                  <div key={paper.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium">{paper.title}</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          {paper.authors.join(", ")}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {Math.round(paper.relevanceScore * 100)}% 相关
                        </Badge>
                        <Badge variant={paper.status === "analyzed" ? "default" : "secondary"}>
                          {paper.status === "analyzed" ? "已分析" : "待分析"}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
                <div className="text-center py-4 text-muted-foreground">
                  <p>显示前 {project.papers.length} 篇论文，共 {project.papersCount} 篇</p>
                  <Button variant="outline" className="mt-2">
                    查看全部论文
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid gap-4">
            {project.agentContributions.map((agent) => (
              <Card key={agent.agentName}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <span className="text-2xl">{agent.avatar}</span>
                    <div>
                      <h3 className="text-lg">{agent.agentName}</h3>
                      <p className="text-sm text-muted-foreground">
                        完成 {agent.tasksCompleted} 个分析任务
                      </p>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <h4 className="font-medium flex items-center gap-2">
                      <Lightbulb className="h-4 w-4" />
                      关键洞察
                    </h4>
                    <div className="space-y-2">
                      {agent.keyInsights.map((insight, index) => (
                        <div key={index} className="bg-muted rounded p-3">
                          <p className="text-sm">{insight}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="findings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                研究发现
              </CardTitle>
              <CardDescription>
                AI代理团队总结的 {project.keyFindings.length} 个关键发现
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {project.keyFindings.map((finding, index) => (
                  <div key={index} className="border-l-4 border-blue-500 bg-blue-50 p-4 rounded-r-lg">
                    <div className="flex items-start gap-3">
                      <div className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                        {index + 1}
                      </div>
                      <p className="text-sm leading-relaxed">{finding}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                项目时间线
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {project.timeline.map((event, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 bg-blue-500 rounded-full" />
                      {index < project.timeline.length - 1 && (
                        <div className="w-px h-16 bg-border mt-2" />
                      )}
                    </div>
                    <div className="flex-1 pb-8">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{event.event}</h4>
                        <Badge variant="outline" className="text-xs">
                          {new Date(event.date).toLocaleDateString()}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {event.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            <Button variant="outline" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              继续研究讨论
            </Button>
            <Button variant="outline" className="gap-2">
              <FileText className="h-4 w-4" />
              生成研究报告
            </Button>
            <Button variant="outline" className="gap-2">
              <BookOpen className="h-4 w-4" />
              添加更多论文
            </Button>
            <Button variant="outline" className="gap-2">
              <Brain className="h-4 w-4" />
              深度分析
            </Button>
            <Button variant="outline" className="gap-2">
              <Settings className="h-4 w-4" />
              项目设置
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}