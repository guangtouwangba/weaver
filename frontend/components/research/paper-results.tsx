"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  BookOpen, 
  ExternalLink, 
  Star, 
  Download, 
  Eye, 
  Calendar,
  Users,
  TrendingUp,
  Filter,
  SortAsc,
  Grid,
  List,
  Bookmark,
  Share,
  MessageSquare
} from "lucide-react"

export interface Paper {
  id: string
  title: string
  authors: string[]
  abstract: string
  publishedDate: string
  arxivId?: string
  doi?: string
  venue?: string
  citationCount: number
  relevanceScore: number
  categories: string[]
  pdfUrl?: string
  tags?: string[]
  isBookmarked?: boolean
  agentInsights?: AgentInsight[]
}

export interface AgentInsight {
  agentName: string
  agentType: "mit_researcher" | "google_engineer" | "industry_expert" | "paper_analyst"
  insight: string
  rating: number
  highlights: string[]
}

interface PaperResultsProps {
  papers: Paper[]
  isLoading?: boolean
  searchQuery?: string
  totalResults?: number
  className?: string
  onPaperSelect?: (paper: Paper) => void
  onBookmark?: (paperId: string) => void
  onShare?: (paper: Paper) => void
}

export function PaperResults({ 
  papers, 
  isLoading, 
  searchQuery,
  totalResults,
  className,
  onPaperSelect,
  onBookmark,
  onShare
}: PaperResultsProps) {
  const [viewMode, setViewMode] = useState<"grid" | "list">("list")
  const [sortBy, setSortBy] = useState<"relevance" | "date" | "citations">("relevance")

  const sortedPapers = [...papers].sort((a, b) => {
    switch (sortBy) {
      case "date":
        return new Date(b.publishedDate).getTime() - new Date(a.publishedDate).getTime()
      case "citations":
        return b.citationCount - a.citationCount
      case "relevance":
      default:
        return b.relevanceScore - a.relevanceScore
    }
  })

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return "bg-green-500"
    if (score >= 0.6) return "bg-yellow-500"
    return "bg-gray-500"
  }

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case "mit_researcher": return "🎓"
      case "google_engineer": return "⚙️"
      case "industry_expert": return "💼"
      case "paper_analyst": return "📊"
      default: return "🤖"
    }
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span className="text-sm text-muted-foreground">搜索相关论文中...</span>
            </div>
            <Progress value={33} className="w-full" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Results Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">搜索结果</h3>
          {searchQuery && (
            <p className="text-sm text-muted-foreground">
              "{searchQuery}" 的相关论文 {totalResults && `(共 ${totalResults} 篇)`}
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-1" />
            筛选
          </Button>
          
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="relevance">相关性</option>
            <option value="date">发布时间</option>
            <option value="citations">引用次数</option>
          </select>

          <div className="flex border rounded">
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("list")}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm" 
              onClick={() => setViewMode("grid")}
            >
              <Grid className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Results Grid/List */}
      <div className={`grid gap-4 ${
        viewMode === "grid" ? "md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"
      }`}>
        {sortedPapers.map((paper) => (
          <Card key={paper.id} className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base leading-tight line-clamp-2">
                  {paper.title}
                </CardTitle>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <div 
                    className={`w-2 h-2 rounded-full ${getRelevanceColor(paper.relevanceScore)}`}
                    title={`相关性: ${Math.round(paper.relevanceScore * 100)}%`}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onBookmark?.(paper.id)
                    }}
                  >
                    <Bookmark className={`h-4 w-4 ${paper.isBookmarked ? "fill-current" : ""}`} />
                  </Button>
                </div>
              </div>
              
              <CardDescription className="text-sm">
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                  <Users className="h-3 w-3" />
                  <span className="line-clamp-1">{paper.authors.slice(0, 3).join(", ")}</span>
                  {paper.authors.length > 3 && <span>等</span>}
                </div>
                
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(paper.publishedDate).getFullYear()}
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    {paper.citationCount} 引用
                  </span>
                  {paper.venue && (
                    <span className="flex items-center gap-1">
                      <BookOpen className="h-3 w-3" />
                      {paper.venue}
                    </span>
                  )}
                </div>
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3">
              {/* Abstract */}
              <p className="text-sm text-muted-foreground line-clamp-3">
                {paper.abstract}
              </p>

              {/* Categories */}
              <div className="flex flex-wrap gap-1">
                {paper.categories.slice(0, 3).map((category) => (
                  <Badge key={category} variant="secondary" className="text-xs">
                    {category}
                  </Badge>
                ))}
                {paper.categories.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{paper.categories.length - 3}
                  </Badge>
                )}
              </div>

              {/* Agent Insights */}
              {paper.agentInsights && paper.agentInsights.length > 0 && (
                <div className="space-y-2">
                  <h5 className="text-xs font-medium">AI专家观点:</h5>
                  <div className="space-y-1">
                    {paper.agentInsights.slice(0, 2).map((insight, index) => (
                      <div key={index} className="flex items-start gap-2">
                        <span className="text-xs">{getAgentIcon(insight.agentType)}</span>
                        <div className="flex-1">
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {insight.insight}
                          </p>
                          <div className="flex items-center gap-1 mt-1">
                            {[...Array(5)].map((_, i) => (
                              <Star key={i} className={`h-2 w-2 ${
                                i < insight.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                              }`} />
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-between pt-2 border-t">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {Math.round(paper.relevanceScore * 100)}% 相关
                  </Badge>
                  {paper.arxivId && (
                    <Badge variant="outline" className="text-xs">
                      arXiv
                    </Badge>
                  )}
                </div>
                
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" onClick={() => onPaperSelect?.(paper)}>
                    <Eye className="h-3 w-3" />
                  </Button>
                  
                  {paper.pdfUrl && (
                    <Button variant="ghost" size="sm" asChild>
                      <a href={paper.pdfUrl} target="_blank" rel="noopener noreferrer">
                        <Download className="h-3 w-3" />
                      </a>
                    </Button>
                  )}
                  
                  <Button variant="ghost" size="sm" onClick={() => onShare?.(paper)}>
                    <Share className="h-3 w-3" />
                  </Button>
                  
                  <Button variant="ghost" size="sm">
                    <MessageSquare className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Load More */}
      {papers.length > 0 && (
        <div className="flex justify-center pt-4">
          <Button variant="outline">
            加载更多论文
          </Button>
        </div>
      )}
    </div>
  )
}