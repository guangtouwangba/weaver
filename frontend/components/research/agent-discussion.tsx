"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  MessageSquare, 
  ThumbsUp, 
  ThumbsDown, 
  Copy,
  Share,
  Bookmark,
  Zap,
  Clock,
  CheckCircle,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  Users,
  Brain
} from "lucide-react"

export interface DiscussionRound {
  id: string
  roundNumber: number
  agentName: string
  agentType: "mit_researcher" | "google_engineer" | "industry_expert" | "paper_analyst"
  content: string
  timestamp: Date
  status: "pending" | "active" | "completed"
  insights?: string[]
  references?: string[]
  agreement?: "agree" | "disagree" | "neutral"
  confidence: number
  tokensUsed?: number
}

export interface DiscussionThread {
  id: string
  topic: string
  query: string
  rounds: DiscussionRound[]
  status: "planning" | "active" | "completed" | "paused"
  consensus?: string
  keyFindings?: string[]
  nextSteps?: string[]
  startedAt: Date
  completedAt?: Date
}

interface AgentDiscussionProps {
  discussion: DiscussionThread
  isLive?: boolean
  className?: string
  onRoundInteraction?: (roundId: string, action: "like" | "dislike" | "bookmark") => void
}

const agentProfiles = {
  mit_researcher: {
    name: "MIT研究员",
    avatar: "🎓",
    color: "bg-blue-500",
    role: "学术研究专家",
    expertise: ["理论分析", "方法验证", "学术严谨性"]
  },
  google_engineer: {
    name: "Google工程师", 
    avatar: "⚙️",
    color: "bg-green-500",
    role: "工程实践专家",
    expertise: ["系统设计", "性能优化", "可扩展性"]
  },
  industry_expert: {
    name: "行业专家",
    avatar: "💼", 
    color: "bg-purple-500",
    role: "商业应用专家",
    expertise: ["市场分析", "商业价值", "产业趋势"]
  },
  paper_analyst: {
    name: "论文分析师",
    avatar: "📊",
    color: "bg-orange-500", 
    role: "文献分析专家",
    expertise: ["文献综述", "方法比较", "实验分析"]
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case "pending": return <Clock className="h-3 w-3 text-gray-500" />
    case "active": return <Zap className="h-3 w-3 text-blue-500 animate-pulse" />
    case "completed": return <CheckCircle className="h-3 w-3 text-green-500" />
    default: return <AlertTriangle className="h-3 w-3 text-yellow-500" />
  }
}

const getAgreementIcon = (agreement?: string) => {
  switch (agreement) {
    case "agree": return <ThumbsUp className="h-3 w-3 text-green-500" />
    case "disagree": return <ThumbsDown className="h-3 w-3 text-red-500" />
    default: return null
  }
}

export function AgentDiscussion({ 
  discussion, 
  isLive, 
  className,
  onRoundInteraction
}: AgentDiscussionProps) {
  const [selectedView, setSelectedView] = useState<"timeline" | "consensus" | "insights">("timeline")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isLive) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [discussion.rounds, isLive])

  const activeRounds = discussion.rounds.filter(r => r.status === "active")
  const completedRounds = discussion.rounds.filter(r => r.status === "completed")
  const consensusItems = discussion.rounds.filter(r => r.agreement === "agree")
  const disagreements = discussion.rounds.filter(r => r.agreement === "disagree")

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              AI专家讨论
            </CardTitle>
            <CardDescription>{discussion.topic}</CardDescription>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant={discussion.status === "active" ? "default" : "secondary"}>
              {discussion.status === "active" ? "进行中" : 
               discussion.status === "completed" ? "已完成" : "准备中"}
            </Badge>
            {isLive && (
              <Badge variant="destructive" className="animate-pulse">
                实时
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <Tabs value={selectedView} onValueChange={(v) => setSelectedView(v as any)}>
          <div className="px-6 pb-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="timeline">讨论时线</TabsTrigger>
              <TabsTrigger value="consensus">共识观点</TabsTrigger>
              <TabsTrigger value="insights">关键洞察</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="timeline" className="mt-0">
            <ScrollArea className="h-[600px] px-6">
              <div className="space-y-4">
                {discussion.rounds.map((round, index) => {
                  const agent = agentProfiles[round.agentType]
                  const isLastActive = index === discussion.rounds.length - 1 && round.status === "active"
                  
                  return (
                    <div key={round.id} className={`flex gap-3 ${
                      isLastActive ? "animate-pulse" : ""
                    }`}>
                      {/* Agent Avatar */}
                      <div className="flex-shrink-0">
                        <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-white text-sm relative`}>
                          {agent.avatar}
                          <div className="absolute -bottom-1 -right-1">
                            {getStatusIcon(round.status)}
                          </div>
                        </div>
                      </div>

                      {/* Message Content */}
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{agent.name}</span>
                          <Badge variant="outline" className="text-xs">
                            轮次 {round.roundNumber}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {round.timestamp.toLocaleTimeString()}
                          </span>
                          {getAgreementIcon(round.agreement)}
                        </div>

                        <div className="bg-muted rounded-lg p-3">
                          <p className="text-sm leading-relaxed">{round.content}</p>
                          
                          {/* Insights */}
                          {round.insights && round.insights.length > 0 && (
                            <div className="mt-3 space-y-1">
                              <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground">
                                <Lightbulb className="h-3 w-3" />
                                关键观点:
                              </div>
                              {round.insights.map((insight, i) => (
                                <div key={i} className="text-xs text-muted-foreground bg-background rounded px-2 py-1">
                                  • {insight}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* References */}
                          {round.references && round.references.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {round.references.map((ref, i) => (
                                <Badge key={i} variant="outline" className="text-xs">
                                  {ref}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Round Actions */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Brain className="h-3 w-3" />
                              <span>置信度: {Math.round(round.confidence * 100)}%</span>
                            </div>
                            {round.tokensUsed && (
                              <div className="text-xs text-muted-foreground">
                                {round.tokensUsed} tokens
                              </div>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-1">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => onRoundInteraction?.(round.id, "like")}
                            >
                              <ThumbsUp className="h-3 w-3" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => onRoundInteraction?.(round.id, "dislike")}
                            >
                              <ThumbsDown className="h-3 w-3" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => onRoundInteraction?.(round.id, "bookmark")}
                            >
                              <Bookmark className="h-3 w-3" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="consensus" className="mt-0">
            <div className="px-6 space-y-4">
              {/* Consensus Points */}
              {consensusItems.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    共识观点 ({consensusItems.length})
                  </h4>
                  {consensusItems.map((round) => {
                    const agent = agentProfiles[round.agentType]
                    return (
                      <div key={round.id} className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm">{agent.avatar}</span>
                          <span className="font-medium text-sm">{agent.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {Math.round(round.confidence * 100)}% 确信
                          </Badge>
                        </div>
                        <p className="text-sm">{round.content}</p>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Disagreements */}
              {disagreements.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    分歧观点 ({disagreements.length})
                  </h4>
                  {disagreements.map((round) => {
                    const agent = agentProfiles[round.agentType]
                    return (
                      <div key={round.id} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm">{agent.avatar}</span>
                          <span className="font-medium text-sm">{agent.name}</span>
                          <Badge variant="outline" className="text-xs">
                            争议观点
                          </Badge>
                        </div>
                        <p className="text-sm">{round.content}</p>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Final Consensus */}
              {discussion.consensus && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <Users className="h-4 w-4 text-blue-500" />
                    最终共识
                  </h4>
                  <p className="text-sm">{discussion.consensus}</p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="insights" className="mt-0">
            <div className="px-6 space-y-4">
              {/* Key Findings */}
              {discussion.keyFindings && discussion.keyFindings.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-yellow-500" />
                    关键发现
                  </h4>
                  {discussion.keyFindings.map((finding, index) => (
                    <div key={index} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <p className="text-sm">{finding}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Next Steps */}
              {discussion.nextSteps && discussion.nextSteps.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-blue-500" />
                    建议的后续步骤
                  </h4>
                  {discussion.nextSteps.map((step, index) => (
                    <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <p className="text-sm">{step}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Discussion Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-muted rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold">{discussion.rounds.length}</div>
                  <div className="text-xs text-muted-foreground">讨论轮次</div>
                </div>
                <div className="bg-muted rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold">{activeRounds.length}</div>
                  <div className="text-xs text-muted-foreground">活跃代理</div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}