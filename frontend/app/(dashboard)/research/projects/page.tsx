"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  FolderOpen, 
  Plus, 
  Search, 
  Filter,
  MoreHorizontal,
  Calendar,
  Users,
  BookOpen,
  Clock,
  TrendingUp,
  Star,
  Archive,
  Trash2,
  Edit,
  Share,
  Download,
  Eye
} from "lucide-react"
import Link from "next/link"

interface ResearchProject {
  id: string
  title: string
  description: string
  status: "draft" | "active" | "completed" | "archived"
  priority: "low" | "medium" | "high"
  createdAt: string
  updatedAt: string
  completedAt?: string
  query: string
  papersCount: number
  agentsUsed: string[]
  keyFindings?: string[]
  tags: string[]
  isStarred: boolean
  collaborators?: string[]
  progress: number
}

export default function ResearchProjectsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<"all" | "draft" | "active" | "completed" | "archived">("all")
  const [sortBy, setSortBy] = useState<"updated" | "created" | "title" | "progress">("updated")

  const projects: ResearchProject[] = [
    {
      id: "1",
      title: "深度学习在自然语言处理中的最新进展",
      description: "分析2024年最新的Transformer架构改进和应用实践",
      status: "completed",
      priority: "high",
      createdAt: "2024-01-15",
      updatedAt: "2024-01-20",
      completedAt: "2024-01-20",
      query: "深度学习 自然语言处理 Transformer 2024",
      papersCount: 24,
      agentsUsed: ["MIT研究员", "Google工程师", "论文分析师"],
      keyFindings: [
        "Transformer架构在效率上有了显著提升",
        "多模态融合成为新的研究热点",
        "模型压缩技术取得重要突破"
      ],
      tags: ["深度学习", "NLP", "Transformer"],
      isStarred: true,
      progress: 100
    },
    {
      id: "2",
      title: "量子计算在机器学习中的应用前景",
      description: "探索量子算法对传统ML模型的加速效果和实用性分析",
      status: "active",
      priority: "medium",
      createdAt: "2024-01-14",
      updatedAt: "2024-01-22",
      query: "量子计算 机器学习 量子算法",
      papersCount: 16,
      agentsUsed: ["MIT研究员", "行业专家"],
      tags: ["量子计算", "机器学习"],
      isStarred: false,
      progress: 65
    },
    {
      id: "3",
      title: "联邦学习的隐私保护机制研究",
      description: "分析联邦学习中的隐私保护技术和安全威胁应对策略",
      status: "draft",
      priority: "high",
      createdAt: "2024-01-12",
      updatedAt: "2024-01-16",
      query: "联邦学习 隐私保护 差分隐私",
      papersCount: 8,
      agentsUsed: ["MIT研究员"],
      tags: ["联邦学习", "隐私保护", "安全"],
      isStarred: true,
      progress: 30
    }
  ]

  const filteredProjects = projects
    .filter(project => {
      if (statusFilter !== "all" && project.status !== statusFilter) return false
      if (searchQuery && !project.title.toLowerCase().includes(searchQuery.toLowerCase())) return false
      return true
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "title": return a.title.localeCompare(b.title)
        case "created": return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        case "progress": return b.progress - a.progress
        case "updated":
        default:
          return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      }
    })

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

  const stats = {
    total: projects.length,
    active: projects.filter(p => p.status === "active").length,
    completed: projects.filter(p => p.status === "completed").length,
    draft: projects.filter(p => p.status === "draft").length
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">研究项目</h1>
          <p className="text-muted-foreground">
            管理和跟踪您的AI协作研究项目
          </p>
        </div>
        <Button className="gap-2" asChild>
          <Link href="/research/projects/new">
            <Plus className="h-4 w-4" />
            新建项目
          </Link>
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <FolderOpen className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-muted-foreground">总项目</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-yellow-600" />
              <div>
                <p className="text-2xl font-bold">{stats.active}</p>
                <p className="text-xs text-muted-foreground">进行中</p>
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
              <Edit className="h-4 w-4 text-gray-600" />
              <div>
                <p className="text-2xl font-bold">{stats.draft}</p>
                <p className="text-xs text-muted-foreground">草稿</p>
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
              placeholder="搜索项目..."
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
          <option value="active">进行中</option>
          <option value="completed">已完成</option>
          <option value="archived">已归档</option>
        </select>

        <select 
          value={sortBy} 
          onChange={(e) => setSortBy(e.target.value as any)}
          className="text-sm border rounded px-3 py-2"
        >
          <option value="updated">最近更新</option>
          <option value="created">创建时间</option>
          <option value="title">项目名称</option>
          <option value="progress">进度</option>
        </select>

        <Button variant="outline" size="sm">
          <Filter className="h-4 w-4 mr-1" />
          高级筛选
        </Button>
      </div>

      {/* Projects Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredProjects.map((project) => (
          <Card key={project.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(project.status)}`} />
                    <CardTitle className="text-base line-clamp-2">
                      {project.title}
                    </CardTitle>
                    {project.isStarred && (
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    )}
                  </div>
                  <CardDescription className="text-sm line-clamp-2">
                    {project.description}
                  </CardDescription>
                </div>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Progress */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">进度</span>
                  <span className="font-medium">{project.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div 
                    className="bg-blue-600 h-1.5 rounded-full transition-all" 
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
              </div>

              {/* Metadata */}
              <div className="space-y-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <BookOpen className="h-3 w-3" />
                    {project.papersCount} 篇论文
                  </span>
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {project.agentsUsed.length} 个代理
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  更新于 {new Date(project.updatedAt).toLocaleDateString()}
                </div>
              </div>

              {/* Status and Priority */}
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {getStatusLabel(project.status)}
                </Badge>
                <Badge className={`text-xs ${getPriorityColor(project.priority)}`}>
                  {project.priority === "high" ? "高优先级" : 
                   project.priority === "medium" ? "中优先级" : "低优先级"}
                </Badge>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {project.tags.slice(0, 3).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {project.tags.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{project.tags.length - 3}
                  </Badge>
                )}
              </div>

              {/* Key Findings Preview */}
              {project.keyFindings && project.keyFindings.length > 0 && (
                <div className="bg-muted rounded p-2">
                  <p className="text-xs font-medium mb-1">关键发现:</p>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {project.keyFindings[0]}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" asChild title="查看详情">
                    <Link href={`/research/projects/${project.id}`}>
                      <Eye className="h-3 w-3" />
                    </Link>
                  </Button>
                  <Button variant="ghost" size="sm" title="编辑项目">
                    <Edit className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" title="分享项目">
                    <Share className="h-3 w-3" />
                  </Button>
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" title="下载报告">
                    <Download className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" title="归档项目">
                    <Archive className="h-3 w-3" />
                  </Button>
                </div>
                <Button variant="outline" size="sm" asChild>
                  <Link href={`/research/projects/${project.id}`}>
                    查看详情
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredProjects.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <FolderOpen className="h-12 w-12 text-muted-foreground mx-auto" />
              <div>
                <h3 className="text-lg font-medium">暂无项目</h3>
                <p className="text-muted-foreground">
                  {searchQuery ? "没有找到匹配的项目" : "开始创建您的第一个研究项目"}
                </p>
              </div>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                新建项目
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}