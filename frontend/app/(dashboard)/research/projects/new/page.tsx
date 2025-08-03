"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  ArrowLeft,
  Plus,
  X,
  Brain,
  Target,
  Users,
  Calendar,
  Tag,
  Lightbulb,
  Search,
  BookOpen
} from "lucide-react"
import Link from "next/link"

export default function NewProjectPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    query: "",
    priority: "medium",
    tags: [] as string[],
    selectedAgents: [] as string[]
  })
  const [newTag, setNewTag] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const availableAgents = [
    {
      id: "mit_researcher",
      name: "MIT研究员",
      description: "学术研究和理论分析专家",
      avatar: "🎓",
      recommended: true
    },
    {
      id: "google_engineer", 
      name: "Google工程师",
      description: "工程实践和技术实现专家",
      avatar: "⚙️",
      recommended: true
    },
    {
      id: "industry_expert",
      name: "行业专家",
      description: "商业应用和市场分析专家",
      avatar: "💼",
      recommended: false
    },
    {
      id: "paper_analyst",
      name: "论文分析师",
      description: "文献分析和方法比较专家",
      avatar: "📊",
      recommended: true
    }
  ]

  const suggestedQueries = [
    "深度学习在自然语言处理中的最新进展",
    "量子计算在机器学习中的应用",
    "联邦学习的隐私保护机制",
    "强化学习在自动驾驶中的应用",
    "图神经网络在推荐系统中的创新",
    "多模态学习的最新突破"
  ]

  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }))
      setNewTag("")
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }))
  }

  const handleAgentToggle = (agentId: string) => {
    setFormData(prev => ({
      ...prev,
      selectedAgents: prev.selectedAgents.includes(agentId)
        ? prev.selectedAgents.filter(id => id !== agentId)
        : [...prev.selectedAgents, agentId]
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    // 模拟提交过程
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 这里应该调用实际的API
    console.log("Creating project:", formData)
    
    // 重定向到项目详情页面（假设新项目ID为'new-project-id'）
    router.push('/research/projects/1')
  }

  const isFormValid = formData.title.trim() && formData.query.trim() && formData.selectedAgents.length > 0

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/research/projects">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            返回项目列表
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">创建新的研究项目</h1>
          <p className="text-muted-foreground">设置您的AI协作研究项目</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              基本信息
            </CardTitle>
            <CardDescription>
              设置项目的基本信息和研究目标
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">项目标题 *</label>
              <Input
                placeholder="例如：深度学习在自然语言处理中的最新进展"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                required
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">项目描述</label>
              <Textarea
                placeholder="详细描述您的研究目标、期望产出和关注重点..."
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">优先级</label>
              <div className="flex gap-2">
                {["low", "medium", "high"].map((priority) => (
                  <Button
                    key={priority}
                    type="button"
                    variant={formData.priority === priority ? "default" : "outline"}
                    size="sm"
                    onClick={() => setFormData(prev => ({ ...prev, priority }))}
                  >
                    {priority === "high" ? "高优先级" : 
                     priority === "medium" ? "中优先级" : "低优先级"}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Research Query */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              研究查询
            </CardTitle>
            <CardDescription>
              定义您的研究问题和关键词，AI将据此检索相关论文
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">研究查询 *</label>
              <Textarea
                placeholder="输入您的研究问题和关键词，例如：深度学习 自然语言处理 Transformer 2024"
                value={formData.query}
                onChange={(e) => setFormData(prev => ({ ...prev, query: e.target.value }))}
                rows={2}
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">建议的研究主题</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {suggestedQueries.map((query, index) => (
                  <Button
                    key={index}
                    type="button"
                    variant="outline"
                    size="sm"
                    className="justify-start text-left h-auto py-2 px-3"
                    onClick={() => setFormData(prev => ({ ...prev, query }))}
                  >
                    <BookOpen className="h-3 w-3 mr-2 flex-shrink-0" />
                    <span className="text-xs">{query}</span>
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Agents Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              AI专家团队
            </CardTitle>
            <CardDescription>
              选择参与研究的AI代理，每个代理都有不同的专业领域和分析视角
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {availableAgents.map((agent) => (
                <div
                  key={agent.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    formData.selectedAgents.includes(agent.id)
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50"
                  }`}
                  onClick={() => handleAgentToggle(agent.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="text-2xl">{agent.avatar}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{agent.name}</h4>
                        {agent.recommended && (
                          <Badge variant="secondary" className="text-xs">
                            推荐
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {agent.description}
                      </p>
                    </div>
                    <div className={`w-4 h-4 border rounded flex items-center justify-center ${
                      formData.selectedAgents.includes(agent.id)
                        ? "bg-primary border-primary"
                        : "border-border"
                    }`}>
                      {formData.selectedAgents.includes(agent.id) && (
                        <div className="w-2 h-2 bg-white rounded-sm" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {formData.selectedAgents.length === 0 && (
              <p className="text-sm text-red-500">至少选择一个AI代理</p>
            )}
          </CardContent>
        </Card>

        {/* Tags */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              标签管理
            </CardTitle>
            <CardDescription>
              添加标签来更好地组织和分类您的项目
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="添加标签..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
              />
              <Button type="button" onClick={handleAddTag} disabled={!newTag.trim()}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            
            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="gap-1">
                    {tag}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-auto p-0 w-4 h-4"
                      onClick={() => handleRemoveTag(tag)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Project Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              项目预览
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-muted rounded-lg p-4 space-y-3">
              <h4 className="font-medium">
                {formData.title || "项目标题"}
              </h4>
              {formData.description && (
                <p className="text-sm text-muted-foreground">
                  {formData.description}
                </p>
              )}
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  {formData.selectedAgents.length} 个AI代理
                </span>
                <span className="flex items-center gap-1">
                  <Tag className="h-3 w-3" />
                  {formData.tags.length} 个标签
                </span>
                <Badge variant="outline" className="text-xs">
                  {formData.priority === "high" ? "高优先级" : 
                   formData.priority === "medium" ? "中优先级" : "低优先级"}
                </Badge>
              </div>
              {formData.query && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs font-medium text-muted-foreground mb-1">研究查询:</p>
                  <p className="text-sm">{formData.query}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Form Actions */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" asChild>
            <Link href="/research/projects">
              取消
            </Link>
          </Button>
          <Button 
            type="submit" 
            disabled={!isFormValid || isSubmitting}
            className="gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                创建中...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4" />
                创建项目
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}