"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Brain, Search, Plus, Clock, BookOpen, Users } from "lucide-react"
import Link from "next/link"

export default function ResearchPage() {
  const [query, setQuery] = useState("")

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
        <Button size="lg" className="gap-2">
          <Plus className="h-4 w-4" />
          开始新研究
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
              className="text-base"
            />
            <div className="flex gap-2">
              <Button className="gap-2">
                <Search className="h-4 w-4" />
                开始分析
              </Button>
              <Button variant="outline">
                使用高级搜索
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
                  onClick={() => setQuery(suggestion)}
                  className="text-xs"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
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
                    <Button size="sm" variant="outline">
                      查看详情
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