"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { 
  FileText, 
  Download, 
  Share, 
  Eye, 
  Edit,
  Plus,
  Search,
  Filter,
  Calendar,
  Users,
  BookOpen,
  TrendingUp,
  Star,
  Copy,
  RefreshCw,
  Settings,
  MoreHorizontal,
  FileDown,
  Mail,
  Link,
  Printer
} from "lucide-react"

interface ResearchReport {
  id: string
  title: string
  description: string
  projectId: string
  projectTitle: string
  status: "draft" | "generating" | "completed" | "published"
  createdAt: string
  updatedAt: string
  publishedAt?: string
  author: string
  collaborators?: string[]
  wordCount: number
  sections: ReportSection[]
  papersAnalyzed: number
  agentsUsed: string[]
  keyFindings: string[]
  tags: string[]
  isStarred: boolean
  downloadCount: number
  shareCount: number
  format: "markdown" | "pdf" | "word" | "latex"
}

interface ReportSection {
  id: string
  title: string
  content: string
  type: "summary" | "analysis" | "findings" | "conclusions" | "references"
  order: number
  agentContributions?: {
    agentName: string
    contribution: string
  }[]
}

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<"all" | "draft" | "completed" | "published">("all")
  const [sortBy, setSortBy] = useState<"updated" | "created" | "title" | "downloads">("updated")

  const reports: ResearchReport[] = [
    {
      id: "1",
      title: "深度学习在自然语言处理中的最新进展：2024年度综述",
      description: "对2024年深度学习和NLP领域的重要突破进行全面分析",
      projectId: "proj-1",
      projectTitle: "深度学习在自然语言处理中的最新进展",
      status: "completed",
      createdAt: "2024-01-15",
      updatedAt: "2024-01-20",
      publishedAt: "2024-01-20",
      author: "研究团队",
      wordCount: 8547,
      sections: [
        {
          id: "s1",
          title: "执行摘要",
          content: "本研究分析了2024年深度学习在自然语言处理领域的重要进展...",
          type: "summary",
          order: 1
        },
        {
          id: "s2", 
          title: "技术分析",
          content: "通过对24篇核心论文的深入分析，我们发现...",
          type: "analysis",
          order: 2
        }
      ],
      papersAnalyzed: 24,
      agentsUsed: ["MIT研究员", "Google工程师", "论文分析师"],
      keyFindings: [
        "Transformer架构效率提升显著",
        "多模态融合成为新趋势",
        "模型压缩技术取得突破"
      ],
      tags: ["深度学习", "NLP", "综述"],
      isStarred: true,
      downloadCount: 156,
      shareCount: 23,
      format: "markdown"
    },
    {
      id: "2",
      title: "量子计算在机器学习中的应用前景分析",
      description: "探索量子算法对传统机器学习模型的潜在影响",
      projectId: "proj-2", 
      projectTitle: "量子计算在机器学习中的应用前景",
      status: "generating",
      createdAt: "2024-01-14",
      updatedAt: "2024-01-22",
      author: "研究团队",
      wordCount: 3200,
      sections: [],
      papersAnalyzed: 16,
      agentsUsed: ["MIT研究员", "行业专家"],
      keyFindings: [],
      tags: ["量子计算", "机器学习"],
      isStarred: false,
      downloadCount: 0,
      shareCount: 0,
      format: "markdown"
    },
    {
      id: "3",
      title: "联邦学习隐私保护机制研究报告",
      description: "分析联邦学习中的隐私保护技术现状和发展趋势",
      projectId: "proj-3",
      projectTitle: "联邦学习的隐私保护机制研究", 
      status: "draft",
      createdAt: "2024-01-12",
      updatedAt: "2024-01-16",
      author: "研究团队",
      wordCount: 1850,
      sections: [],
      papersAnalyzed: 8,
      agentsUsed: ["MIT研究员"],
      keyFindings: [],
      tags: ["联邦学习", "隐私保护"],
      isStarred: true,
      downloadCount: 0,
      shareCount: 0,
      format: "markdown"
    }
  ]

  const filteredReports = reports
    .filter(report => {
      if (statusFilter !== "all" && report.status !== statusFilter) return false
      if (searchQuery && !report.title.toLowerCase().includes(searchQuery.toLowerCase())) return false
      return true
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "created":
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        case "title":
          return a.title.localeCompare(b.title)
        case "downloads":
          return b.downloadCount - a.downloadCount
        case "updated":
        default:
          return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      }
    })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-500"
      case "published": return "bg-blue-500"
      case "generating": return "bg-yellow-500 animate-pulse"
      case "draft": return "bg-gray-500"
      default: return "bg-gray-400"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "completed": return "已完成"
      case "published": return "已发布"
      case "generating": return "生成中"
      case "draft": return "草稿"
      default: return status
    }
  }

  const stats = {
    total: reports.length,
    completed: reports.filter(r => r.status === "completed").length,
    published: reports.filter(r => r.status === "published").length,
    generating: reports.filter(r => r.status === "generating").length
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">研究报告</h1>
          <p className="text-muted-foreground">
            生成和管理AI协作研究的分析报告
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          生成新报告
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-muted-foreground">总报告</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-2xl font-bold">{stats.completed}</p>
                <p className="text-xs text-muted-foreground">已完成</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Share className="h-4 w-4 text-purple-600" />
              <div>
                <p className="text-2xl font-bold">{stats.published}</p>
                <p className="text-xs text-muted-foreground">已发布</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <RefreshCw className="h-4 w-4 text-yellow-600" />
              <div>
                <p className="text-2xl font-bold">{stats.generating}</p>
                <p className="text-xs text-muted-foreground">生成中</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex items-center gap-4">
        <div className="flex-1 max-w-sm">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="搜索报告..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
        </div>
        
        <select 
          value={statusFilter} 
          onChange={(e) => setStatusFilter(e.target.value as any)}
          className="text-sm border rounded px-3 py-2"
        >
          <option value="all">全部状态</option>
          <option value="draft">草稿</option>
          <option value="generating">生成中</option>
          <option value="completed">已完成</option>
          <option value="published">已发布</option>
        </select>

        <select 
          value={sortBy} 
          onChange={(e) => setSortBy(e.target.value as any)}
          className="text-sm border rounded px-3 py-2"
        >
          <option value="updated">最近更新</option>
          <option value="created">创建时间</option>
          <option value="title">报告标题</option>
          <option value="downloads">下载次数</option>
        </select>

        <Button variant="outline" size="sm">
          <Filter className="h-4 w-4 mr-1" />
          高级筛选
        </Button>
      </div>

      {/* Reports Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredReports.map((report) => (
          <Card key={report.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(report.status)}`} />
                    <CardTitle className="text-base line-clamp-2">
                      {report.title}
                    </CardTitle>
                    {report.isStarred && (
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    )}
                  </div>
                  <CardDescription className="text-sm line-clamp-2">
                    {report.description}
                  </CardDescription>
                </div>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Project Link */}
              <div className="text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  来源项目: {report.projectTitle}
                </span>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <FileText className="h-3 w-3" />
                    <span>{report.wordCount.toLocaleString()} 字</span>
                  </div>
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <BookOpen className="h-3 w-3" />
                    <span>{report.papersAnalyzed} 篇论文</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Download className="h-3 w-3" />
                    <span>{report.downloadCount} 下载</span>
                  </div>
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Share className="h-3 w-3" />
                    <span>{report.shareCount} 分享</span>
                  </div>
                </div>
              </div>

              {/* Agents Used */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">参与代理:</p>
                <div className="flex flex-wrap gap-1">
                  {report.agentsUsed.map((agent) => (
                    <Badge key={agent} variant="secondary" className="text-xs">
                      {agent}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Key Findings Preview */}
              {report.keyFindings.length > 0 && (
                <div className="bg-muted rounded p-2">
                  <p className="text-xs font-medium mb-1">关键发现:</p>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {report.keyFindings[0]}
                  </p>
                  {report.keyFindings.length > 1 && (
                    <p className="text-xs text-muted-foreground mt-1">
                      +{report.keyFindings.length - 1} 项更多发现
                    </p>
                  )}
                </div>
              )}

              {/* Status and Tags */}
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {getStatusLabel(report.status)}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {report.format.toUpperCase()}
                </Badge>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {report.tags.slice(0, 3).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {report.tags.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{report.tags.length - 3}
                  </Badge>
                )}
              </div>

              {/* Updated Time */}
              <div className="text-xs text-muted-foreground">
                更新于 {new Date(report.updatedAt).toLocaleDateString()}
                {report.publishedAt && (
                  <span> • 发布于 {new Date(report.publishedAt).toLocaleDateString()}</span>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" title="查看报告">
                    <Eye className="h-3 w-3" />
                  </Button>
                  {report.status !== "generating" && (
                    <Button variant="ghost" size="sm" title="编辑">
                      <Edit className="h-3 w-3" />
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" title="复制">
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
                
                <div className="flex items-center gap-1">
                  {report.status === "completed" || report.status === "published" ? (
                    <>
                      <Button variant="ghost" size="sm" title="下载">
                        <Download className="h-3 w-3" />
                      </Button>
                      <Button variant="ghost" size="sm" title="分享">
                        <Share className="h-3 w-3" />
                      </Button>
                    </>
                  ) : report.status === "generating" ? (
                    <Button variant="ghost" size="sm" disabled>
                      <RefreshCw className="h-3 w-3 animate-spin" />
                    </Button>
                  ) : (
                    <Button variant="ghost" size="sm" title="继续编辑">
                      <Edit className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredReports.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto" />
              <div>
                <h3 className="text-lg font-medium">暂无报告</h3>
                <p className="text-muted-foreground">
                  {searchQuery ? "没有找到匹配的报告" : "开始生成您的第一份研究报告"}
                </p>
              </div>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                生成新报告
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col gap-2">
              <FileDown className="h-6 w-6" />
              <span className="text-sm">批量导出</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2">
              <Mail className="h-6 w-6" />
              <span className="text-sm">邮件发送</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2">
              <Link className="h-6 w-6" />
              <span className="text-sm">生成链接</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2">
              <Printer className="h-6 w-6" />
              <span className="text-sm">打印预览</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}