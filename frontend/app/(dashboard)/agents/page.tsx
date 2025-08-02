"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Users, 
  Settings, 
  Activity,
  Brain,
  Zap,
  TrendingUp,
  Clock,
  Star,
  AlertCircle,
  CheckCircle,
  User,
  Code,
  FileText,
  BarChart3,
  MessageSquare,
  RefreshCw,
  Pause,
  Play,
  MoreHorizontal
} from "lucide-react"

interface AgentProfile {
  id: string
  name: string
  role: string
  description: string
  avatar: string
  expertise: string[]
  model: string
  provider: "openai" | "deepseek" | "anthropic"
  status: "online" | "busy" | "offline" | "maintenance"
  performance: {
    tasksCompleted: number
    successRate: number
    avgResponseTime: number
    tokensUsed: number
    rating: number
    totalSessions: number
  }
  capabilities: string[]
  limitations: string[]
  lastActive: string
  isEnabled: boolean
  configuration: {
    temperature: number
    maxTokens: number
    topP: number
    frequencyPenalty: number
  }
}

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("overview")

  const agents: AgentProfile[] = [
    {
      id: "mit_researcher",
      name: "MIT研究员",
      role: "学术研究专家", 
      description: "专注于理论分析、方法验证和学术严谨性的AI研究助手",
      avatar: "🎓",
      expertise: ["理论分析", "方法验证", "学术写作", "文献综述", "统计分析"],
      model: "gpt-4-turbo",
      provider: "openai",
      status: "online",
      performance: {
        tasksCompleted: 156,
        successRate: 94.2,
        avgResponseTime: 2.3,
        tokensUsed: 892340,
        rating: 4.8,
        totalSessions: 89
      },
      capabilities: [
        "深度论文分析",
        "理论框架构建", 
        "学术写作指导",
        "研究方法评估",
        "统计数据解读"
      ],
      limitations: [
        "工程实现细节较弱",
        "商业应用分析有限",
        "响应时间较长"
      ],
      lastActive: "2024-01-22T10:30:00Z",
      isEnabled: true,
      configuration: {
        temperature: 0.7,
        maxTokens: 4096,
        topP: 0.9,
        frequencyPenalty: 0.1
      }
    },
    {
      id: "google_engineer",
      name: "Google工程师",
      role: "工程实践专家",
      description: "专注于系统设计、性能优化和可扩展性的工程实践专家",
      avatar: "⚙️",
      expertise: ["系统设计", "性能优化", "可扩展性", "工程实践", "代码审查"],
      model: "claude-3-sonnet",
      provider: "anthropic",
      status: "online",
      performance: {
        tasksCompleted: 203,
        successRate: 96.8,
        avgResponseTime: 1.8,
        tokensUsed: 1205670,
        rating: 4.9,
        totalSessions: 127
      },
      capabilities: [
        "系统架构设计",
        "性能瓶颈分析",
        "代码质量评估",
        "技术栈选型",
        "工程最佳实践"
      ],
      limitations: [
        "学术理论深度有限",
        "商业策略分析较弱"
      ],
      lastActive: "2024-01-22T11:15:00Z",
      isEnabled: true,
      configuration: {
        temperature: 0.6,
        maxTokens: 8192,
        topP: 0.8,
        frequencyPenalty: 0.0
      }
    },
    {
      id: "industry_expert",
      name: "行业专家",
      role: "商业应用专家",
      description: "专注于市场分析、商业价值评估和产业趋势的行业专家",
      avatar: "💼",
      expertise: ["市场分析", "商业价值", "产业趋势", "竞争分析", "商业模式"],
      model: "deepseek-chat", 
      provider: "deepseek",
      status: "busy",
      performance: {
        tasksCompleted: 87,
        successRate: 91.3,
        avgResponseTime: 3.1,
        tokensUsed: 456890,
        rating: 4.6,
        totalSessions: 52
      },
      capabilities: [
        "市场机会分析",
        "商业模式评估",
        "竞争态势分析",
        "投资价值评估",
        "产业发展趋势"
      ],
      limitations: [
        "技术细节分析有限",
        "学术理论深度不足",
        "响应时间较长"
      ],
      lastActive: "2024-01-22T09:45:00Z",
      isEnabled: true,
      configuration: {
        temperature: 0.8,
        maxTokens: 4096,
        topP: 0.9,
        frequencyPenalty: 0.2
      }
    },
    {
      id: "paper_analyst",
      name: "论文分析师",
      role: "文献分析专家",
      description: "专注于文献综述、方法比较和实验分析的论文分析专家",
      avatar: "📊",
      expertise: ["文献综述", "方法比较", "实验分析", "数据挖掘", "引用分析"],
      model: "gpt-4",
      provider: "openai", 
      status: "online",
      performance: {
        tasksCompleted: 312,
        successRate: 97.1,
        avgResponseTime: 2.1,
        tokensUsed: 1876540,
        rating: 4.9,
        totalSessions: 198
      },
      capabilities: [
        "论文质量评估",
        "研究方法比较",
        "实验设计分析",
        "数据可视化",
        "引用网络分析"
      ],
      limitations: [
        "工程实现建议有限",
        "商业应用分析较弱"
      ],
      lastActive: "2024-01-22T11:00:00Z",
      isEnabled: true,
      configuration: {
        temperature: 0.5,
        maxTokens: 6144,
        topP: 0.8,
        frequencyPenalty: 0.1
      }
    }
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online": return "bg-green-500"
      case "busy": return "bg-yellow-500"
      case "offline": return "bg-gray-500"
      case "maintenance": return "bg-red-500"
      default: return "bg-gray-400"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "online": return "在线"
      case "busy": return "忙碌"
      case "offline": return "离线"
      case "maintenance": return "维护中"
      default: return status
    }
  }

  const getProviderLogo = (provider: string) => {
    switch (provider) {
      case "openai": return "🤖"
      case "anthropic": return "🧠"
      case "deepseek": return "🔮"
      default: return "🔗"
    }
  }

  const totalStats = {
    tasksCompleted: agents.reduce((sum, agent) => sum + agent.performance.tasksCompleted, 0),
    avgSuccessRate: agents.reduce((sum, agent) => sum + agent.performance.successRate, 0) / agents.length,
    totalTokensUsed: agents.reduce((sum, agent) => sum + agent.performance.tokensUsed, 0),
    avgRating: agents.reduce((sum, agent) => sum + agent.performance.rating, 0) / agents.length
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI专家团队</h1>
          <p className="text-muted-foreground">
            管理和监控您的专业AI代理助手
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Settings className="h-4 w-4" />
            团队设置
          </Button>
          <Button className="gap-2">
            <RefreshCw className="h-4 w-4" />
            同步状态
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-2xl font-bold">{agents.length}</p>
                <p className="text-xs text-muted-foreground">AI代理</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-2xl font-bold">{totalStats.tasksCompleted}</p>
                <p className="text-xs text-muted-foreground">完成任务</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-purple-600" />
              <div>
                <p className="text-2xl font-bold">{Math.round(totalStats.avgSuccessRate)}%</p>
                <p className="text-xs text-muted-foreground">平均成功率</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Brain className="h-4 w-4 text-orange-600" />
              <div>
                <p className="text-2xl font-bold">{(totalStats.totalTokensUsed / 1000000).toFixed(1)}M</p>
                <p className="text-xs text-muted-foreground">Token使用量</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agents Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {agents.map((agent) => (
          <Card key={agent.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center text-2xl relative">
                    {agent.avatar}
                    <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-background ${
                      getStatusColor(agent.status)
                    }`} />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      {agent.role}
                      <span className="text-xs">•</span>
                      <span className="flex items-center gap-1">
                        {getProviderLogo(agent.provider)} {agent.model}
                      </span>
                    </CardDescription>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Badge variant={agent.status === "online" ? "default" : "secondary"}>
                    {getStatusLabel(agent.status)}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Description */}
              <p className="text-sm text-muted-foreground line-clamp-2">
                {agent.description}
              </p>

              {/* Performance Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">成功率</span>
                    <span className="font-medium">{agent.performance.successRate}%</span>
                  </div>
                  <Progress value={agent.performance.successRate} className="h-1" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">评分</span>
                    <div className="flex items-center gap-1">
                      <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                      <span className="font-medium">{agent.performance.rating}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-lg font-bold">{agent.performance.tasksCompleted}</div>
                  <div className="text-xs text-muted-foreground">完成任务</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{agent.performance.avgResponseTime}s</div>
                  <div className="text-xs text-muted-foreground">响应时间</div>
                </div>
                <div>
                  <div className="text-lg font-bold">{(agent.performance.tokensUsed / 1000).toFixed(0)}K</div>
                  <div className="text-xs text-muted-foreground">Token使用</div>
                </div>
              </div>

              {/* Expertise Tags */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">专业领域:</p>
                <div className="flex flex-wrap gap-1">
                  {agent.expertise.slice(0, 4).map((skill) => (
                    <Badge key={skill} variant="secondary" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                  {agent.expertise.length > 4 && (
                    <Badge variant="secondary" className="text-xs">
                      +{agent.expertise.length - 4}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>最后活跃: {new Date(agent.lastActive).toLocaleTimeString()}</span>
                </div>
                
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" title="查看详情">
                    <BarChart3 className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" title="对话测试">
                    <MessageSquare className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" title="配置">
                    <Settings className="h-3 w-3" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    title={agent.status === "online" ? "暂停" : "启动"}
                  >
                    {agent.status === "online" ? 
                      <Pause className="h-3 w-3" /> : 
                      <Play className="h-3 w-3" />
                    }
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Team Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle>团队表现概览</CardTitle>
          <CardDescription>AI代理团队的整体表现和协作效果</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="performance">
            <TabsList>
              <TabsTrigger value="performance">性能指标</TabsTrigger>
              <TabsTrigger value="usage">使用统计</TabsTrigger>
              <TabsTrigger value="collaboration">协作分析</TabsTrigger>
            </TabsList>
            
            <TabsContent value="performance" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-4">
                  <h4 className="font-medium">代理成功率对比</h4>
                  {agents.map((agent) => (
                    <div key={agent.id} className="flex items-center gap-3">
                      <span className="text-sm w-20">{agent.avatar} {agent.name}</span>
                      <div className="flex-1">
                        <Progress value={agent.performance.successRate} className="h-2" />
                      </div>
                      <span className="text-sm font-medium w-12">{agent.performance.successRate}%</span>
                    </div>
                  ))}
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium">响应时间对比</h4>
                  {agents.map((agent) => (
                    <div key={agent.id} className="flex items-center justify-between">
                      <span className="text-sm">{agent.avatar} {agent.name}</span>
                      <span className="text-sm font-medium">{agent.performance.avgResponseTime}s</span>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="usage" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardContent className="pt-6 text-center">
                    <div className="text-2xl font-bold">{totalStats.tasksCompleted}</div>
                    <div className="text-sm text-muted-foreground">总完成任务</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6 text-center">
                    <div className="text-2xl font-bold">{(totalStats.totalTokensUsed / 1000000).toFixed(1)}M</div>
                    <div className="text-sm text-muted-foreground">总Token消耗</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6 text-center">
                    <div className="text-2xl font-bold">{agents.reduce((sum, agent) => sum + agent.performance.totalSessions, 0)}</div>
                    <div className="text-sm text-muted-foreground">总会话次数</div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            
            <TabsContent value="collaboration" className="space-y-4">
              <div className="text-center py-8 text-muted-foreground">
                <Users className="h-12 w-12 mx-auto mb-4" />
                <p>协作分析功能开发中...</p>
                <p className="text-sm">将展示代理间的协作模式和效果评估</p>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}