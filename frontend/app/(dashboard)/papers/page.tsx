"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  BookOpen, 
  Search, 
  Filter,
  Star,
  Download,
  ExternalLink,
  Calendar,
  Users,
  TrendingUp,
  Tag,
  Grid,
  List,
  SortAsc,
  Plus,
  Import,
  Bookmark,
  Share,
  Eye,
  MessageSquare,
  MoreHorizontal
} from "lucide-react"

interface Paper {
  id: string
  title: string
  authors: string[]
  abstract: string
  publishedDate: string
  arxivId?: string
  doi?: string
  venue?: string
  citationCount: number
  categories: string[]
  tags: string[]
  isBookmarked: boolean
  isRead: boolean
  rating?: number
  notes?: string
  addedAt: string
  source: "arxiv" | "manual" | "imported"
  pdfUrl?: string
  citationStyle?: string
  relatedPapers?: string[]
}

interface Collection {
  id: string
  name: string
  description: string
  paperCount: number
  color: string
  isDefault: boolean
}

export default function PapersPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCollection, setSelectedCollection] = useState<string>("all")
  const [viewMode, setViewMode] = useState<"grid" | "list">("list")
  const [sortBy, setSortBy] = useState<"added" | "published" | "citations" | "title">("added")
  const [filterBy, setFilterBy] = useState<"all" | "bookmarked" | "unread" | "rated">("all")

  const collections: Collection[] = [
    {
      id: "all",
      name: "全部论文",
      description: "所有收藏的论文",
      paperCount: 127,
      color: "bg-blue-500",
      isDefault: true
    },
    {
      id: "ml",
      name: "机器学习",
      description: "机器学习相关论文",
      paperCount: 45,
      color: "bg-green-500",
      isDefault: false
    },
    {
      id: "nlp",
      name: "自然语言处理",
      description: "NLP和语言模型",
      paperCount: 38,
      color: "bg-purple-500", 
      isDefault: false
    },
    {
      id: "cv",
      name: "计算机视觉",
      description: "图像和视频处理",
      paperCount: 29,
      color: "bg-orange-500",
      isDefault: false
    },
    {
      id: "reading",
      name: "待阅读",
      description: "计划阅读的论文",
      paperCount: 15,
      color: "bg-yellow-500",
      isDefault: false
    }
  ]

  const papers: Paper[] = [
    {
      id: "1",
      title: "Attention Is All You Need",
      authors: ["Vaswani, A.", "Shazeer, N.", "Parmar, N.", "Uszkoreit, J."],
      abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
      publishedDate: "2017-06-12",
      arxivId: "1706.03762",
      venue: "NIPS 2017",
      citationCount: 25487,
      categories: ["cs.CL", "cs.AI"],
      tags: ["transformer", "attention", "neural networks"],
      isBookmarked: true,
      isRead: true,
      rating: 5,
      addedAt: "2024-01-15",
      source: "arxiv",
      pdfUrl: "https://arxiv.org/pdf/1706.03762.pdf"
    },
    {
      id: "2",
      title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
      authors: ["Devlin, J.", "Chang, M.", "Lee, K.", "Toutanova, K."],
      abstract: "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations...",
      publishedDate: "2018-10-11",
      arxivId: "1810.04805",
      venue: "NAACL 2019",
      citationCount: 18923,
      categories: ["cs.CL"],
      tags: ["bert", "pre-training", "language model"],
      isBookmarked: true,
      isRead: false,
      addedAt: "2024-01-14",
      source: "arxiv"
    },
    {
      id: "3",
      title: "GPT-4 Technical Report",
      authors: ["OpenAI"],
      abstract: "We report the development of GPT-4, a large-scale, multimodal model which exhibits human-level performance...",
      publishedDate: "2023-03-15",
      arxivId: "2303.08774",
      citationCount: 2847,
      categories: ["cs.CL", "cs.AI"],
      tags: ["gpt-4", "large language model", "multimodal"],
      isBookmarked: false,
      isRead: true,
      rating: 4,
      addedAt: "2024-01-12",
      source: "arxiv"
    }
  ]

  const filteredPapers = papers
    .filter(paper => {
      if (searchQuery && !paper.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !paper.authors.some(author => author.toLowerCase().includes(searchQuery.toLowerCase()))) {
        return false
      }
      if (filterBy === "bookmarked" && !paper.isBookmarked) return false
      if (filterBy === "unread" && paper.isRead) return false
      if (filterBy === "rated" && !paper.rating) return false
      return true
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "published":
          return new Date(b.publishedDate).getTime() - new Date(a.publishedDate).getTime()
        case "citations":
          return b.citationCount - a.citationCount
        case "title":
          return a.title.localeCompare(b.title)
        case "added":
        default:
          return new Date(b.addedAt).getTime() - new Date(a.addedAt).getTime()
      }
    })

  const currentCollection = collections.find(c => c.id === selectedCollection) || collections[0]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">论文库</h1>
          <p className="text-muted-foreground">
            管理和组织您收藏的学术论文
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Import className="h-4 w-4" />
            导入论文
          </Button>
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            添加论文
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Collections Sidebar */}
        <div className="col-span-3 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">论文集合</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="space-y-1">
                {collections.map((collection) => (
                  <button
                    key={collection.id}
                    onClick={() => setSelectedCollection(collection.id)}
                    className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-accent transition-colors ${
                      selectedCollection === collection.id ? "bg-accent" : ""
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full ${collection.color}`} />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{collection.name}</p>
                      <p className="text-xs text-muted-foreground">{collection.paperCount} 篇</p>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">统计信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">{papers.length}</div>
                  <div className="text-xs text-muted-foreground">总论文</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{papers.filter(p => p.isBookmarked).length}</div>
                  <div className="text-xs text-muted-foreground">已收藏</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{papers.filter(p => !p.isRead).length}</div>
                  <div className="text-xs text-muted-foreground">未阅读</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{papers.filter(p => p.rating).length}</div>
                  <div className="text-xs text-muted-foreground">已评分</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="col-span-9 space-y-4">
          {/* Collection Header */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full ${currentCollection.color}`} />
                  <div>
                    <h2 className="text-xl font-semibold">{currentCollection.name}</h2>
                    <p className="text-sm text-muted-foreground">{currentCollection.description}</p>
                  </div>
                </div>
                <Badge variant="outline">
                  {currentCollection.paperCount} 篇论文
                </Badge>
              </div>
            </CardHeader>
          </Card>

          {/* Filters and Controls */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="flex-1 max-w-sm">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="搜索论文标题、作者..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                </div>
                
                <select 
                  value={filterBy} 
                  onChange={(e) => setFilterBy(e.target.value as any)}
                  className="text-sm border rounded px-3 py-2"
                >
                  <option value="all">全部论文</option>
                  <option value="bookmarked">已收藏</option>
                  <option value="unread">未阅读</option>
                  <option value="rated">已评分</option>
                </select>

                <select 
                  value={sortBy} 
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="text-sm border rounded px-3 py-2"
                >
                  <option value="added">添加时间</option>
                  <option value="published">发布时间</option>
                  <option value="citations">引用次数</option>
                  <option value="title">标题</option>
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
            </CardContent>
          </Card>

          {/* Papers List/Grid */}
          <div className={`grid gap-4 ${
            viewMode === "grid" ? "md:grid-cols-2" : "grid-cols-1"
          }`}>
            {filteredPapers.map((paper) => (
              <Card key={paper.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <CardTitle className="text-base leading-tight line-clamp-2">
                        {paper.title}
                      </CardTitle>
                      <CardDescription className="text-sm mt-2">
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                          <Users className="h-3 w-3" />
                          <span className="line-clamp-1">
                            {paper.authors.slice(0, 3).join(", ")}
                            {paper.authors.length > 3 && " 等"}
                          </span>
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
                    </div>
                    
                    <div className="flex items-center gap-1 flex-shrink-0">
                      {paper.isBookmarked && (
                        <Bookmark className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                      )}
                      {!paper.isRead && (
                        <div className="w-2 h-2 rounded-full bg-blue-500" title="未阅读" />
                      )}
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3">
                  {/* Abstract */}
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {paper.abstract}
                  </p>

                  {/* Rating */}
                  {paper.rating && (
                    <div className="flex items-center gap-1">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} className={`h-3 w-3 ${
                          i < paper.rating! ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
                        }`} />
                      ))}
                      <span className="text-xs text-muted-foreground ml-1">
                        ({paper.rating}/5)
                      </span>
                    </div>
                  )}

                  {/* Categories and Tags */}
                  <div className="flex flex-wrap gap-1">
                    {paper.categories.slice(0, 2).map((category) => (
                      <Badge key={category} variant="secondary" className="text-xs">
                        {category}
                      </Badge>
                    ))}
                    {paper.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-2 border-t">
                    <div className="flex items-center gap-2">
                      {paper.arxivId && (
                        <Badge variant="outline" className="text-xs">
                          arXiv
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        {paper.source}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm" title="查看详情">
                        <Eye className="h-3 w-3" />
                      </Button>
                      
                      {paper.pdfUrl && (
                        <Button variant="ghost" size="sm" title="下载PDF" asChild>
                          <a href={paper.pdfUrl} target="_blank" rel="noopener noreferrer">
                            <Download className="h-3 w-3" />
                          </a>
                        </Button>
                      )}
                      
                      <Button variant="ghost" size="sm" title="分享">
                        <Share className="h-3 w-3" />
                      </Button>
                      
                      <Button variant="ghost" size="sm" title="讨论">
                        <MessageSquare className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Empty State */}
          {filteredPapers.length === 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center space-y-4">
                  <BookOpen className="h-12 w-12 text-muted-foreground mx-auto" />
                  <div>
                    <h3 className="text-lg font-medium">暂无论文</h3>
                    <p className="text-muted-foreground">
                      {searchQuery ? "没有找到匹配的论文" : "开始添加您的第一篇论文"}
                    </p>
                  </div>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    添加论文
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}