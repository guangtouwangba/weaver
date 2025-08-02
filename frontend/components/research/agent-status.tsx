"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { 
  Brain, 
  Loader2, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Zap,
  User,
  Code,
  TrendingUp,
  FileText
} from "lucide-react"

export interface Agent {
  id: string
  name: string
  role: string
  description: string
  status: "idle" | "working" | "completed" | "error"
  progress?: number
  currentTask?: string
  expertise: string[]
  model: string
  provider: "openai" | "deepseek" | "anthropic"
  tokensUsed?: number
  lastActive?: Date
}

interface AgentStatusProps {
  agents: Agent[]
  className?: string
}

const agentIcons = {
  "MIT研究员": User,
  "Google工程师": Code,
  "行业专家": TrendingUp,
  "论文分析师": FileText
}

const statusColors = {
  idle: "bg-gray-500",
  working: "bg-blue-500 animate-pulse",
  completed: "bg-green-500",
  error: "bg-red-500"
}

const statusLabels = {
  idle: "待命",
  working: "工作中",
  completed: "已完成",
  error: "错误"
}

const providerLogos = {
  openai: "🤖",
  deepseek: "🔮", 
  anthropic: "🧠"
}

export function AgentStatus({ agents, className }: AgentStatusProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Brain className="h-5 w-5" />
          AI专家团队状态
        </h3>
        <Badge variant="outline">
          {agents.filter(a => a.status === "working").length} / {agents.length} 活跃
        </Badge>
      </div>

      <div className="grid gap-3">
        {agents.map((agent) => {
          const IconComponent = agentIcons[agent.name as keyof typeof agentIcons] || User
          
          return (
            <Card key={agent.id} className={`transition-all duration-200 ${
              agent.status === "working" ? "ring-2 ring-blue-200 shadow-md" : ""
            }`}>
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  {/* Agent Avatar */}
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                      <IconComponent className="h-5 w-5" />
                    </div>
                    <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-background ${
                      statusColors[agent.status]
                    }`} />
                  </div>

                  {/* Agent Info */}
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{agent.name}</h4>
                        <p className="text-xs text-muted-foreground">{agent.role}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs">{providerLogos[agent.provider]}</span>
                        <Badge variant={agent.status === "working" ? "default" : "secondary"} className="text-xs">
                          {statusLabels[agent.status]}
                        </Badge>
                      </div>
                    </div>

                    {/* Current Task */}
                    {agent.currentTask && (
                      <div className="flex items-center gap-2">
                        {agent.status === "working" && (
                          <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
                        )}
                        <span className="text-xs text-muted-foreground">
                          {agent.currentTask}
                        </span>
                      </div>
                    )}

                    {/* Progress Bar */}
                    {agent.status === "working" && agent.progress !== undefined && (
                      <Progress value={agent.progress} className="h-1" />
                    )}

                    {/* Agent Details */}
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <span>模型: {agent.model}</span>
                        {agent.tokensUsed && (
                          <span>• 已用 {agent.tokensUsed.toLocaleString()} tokens</span>
                        )}
                      </div>
                      {agent.lastActive && (
                        <span>
                          最后活跃: {agent.lastActive.toLocaleTimeString()}
                        </span>
                      )}
                    </div>

                    {/* Expertise Tags */}
                    <div className="flex flex-wrap gap-1">
                      {agent.expertise.slice(0, 3).map((skill) => (
                        <Badge key={skill} variant="outline" className="text-xs py-0">
                          {skill}
                        </Badge>
                      ))}
                      {agent.expertise.length > 3 && (
                        <Badge variant="outline" className="text-xs py-0">
                          +{agent.expertise.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

export function AgentStatusCompact({ agents, className }: AgentStatusProps) {
  const workingAgents = agents.filter(a => a.status === "working")
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex -space-x-2">
        {agents.slice(0, 4).map((agent) => {
          const IconComponent = agentIcons[agent.name as keyof typeof agentIcons] || User
          return (
            <div
              key={agent.id}
              className={`w-8 h-8 rounded-full bg-muted border-2 border-background flex items-center justify-center relative ${
                agent.status === "working" ? "ring-2 ring-blue-400" : ""
              }`}
              title={`${agent.name} - ${statusLabels[agent.status]}`}
            >
              <IconComponent className="h-4 w-4" />
              <div className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-background ${
                statusColors[agent.status]
              }`} />
            </div>
          )
        })}
      </div>
      
      {workingAgents.length > 0 && (
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>{workingAgents.length} 个代理工作中</span>
        </div>
      )}
    </div>
  )
}