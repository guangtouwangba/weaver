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
  Search,
  Calendar,
  BookOpen,
  Users,
  Brain,
  Settings,
  Filter,
  Plus,
  X,
  Target,
  Zap
} from "lucide-react"
import Link from "next/link"

export default function AdvancedSearchPage() {
  const router = useRouter()
  const [searchConfig, setSearchConfig] = useState({
    query: "",
    keywords: [] as string[],
    authors: "",
    venue: "",
    yearFrom: "",
    yearTo: "",
    citationMin: "",
    categories: [] as string[],
    sortBy: "relevance",
    maxResults: "20",
    includeDrafts: false,
    onlyOpenAccess: false
  })
  const [newKeyword, setNewKeyword] = useState("")
  const [isSearching, setIsSearching] = useState(false)

  const availableCategories = [
    "cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.RO",
    "stat.ML", "eess.IV", "q-bio.NC", "physics.data-an"
  ]

  const suggestedKeywords = [
    "deep learning", "transformer", "attention mechanism", "neural network",
    "machine learning", "artificial intelligence", "natural language processing",
    "computer vision", "reinforcement learning", "federated learning"
  ]

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !searchConfig.keywords.includes(newKeyword.trim())) {
      setSearchConfig(prev => ({
        ...prev,
        keywords: [...prev.keywords, newKeyword.trim()]
      }))
      setNewKeyword("")
    }
  }

  const handleRemoveKeyword = (keyword: string) => {
    setSearchConfig(prev => ({
      ...prev,
      keywords: prev.keywords.filter(k => k !== keyword)
    }))
  }

  const handleCategoryToggle = (category: string) => {
    setSearchConfig(prev => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category]
    }))
  }

  const handleSearch = async () => {
    setIsSearching(true)
    
    // 构建搜索查询
    const queryParts = []
    if (searchConfig.query.trim()) queryParts.push(searchConfig.query.trim())
    if (searchConfig.keywords.length > 0) queryParts.push(...searchConfig.keywords)
    
    const finalQuery = queryParts.join(" ")
    
    // 模拟搜索延迟
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 跳转到对话界面
    router.push('/research/chat?query=' + encodeURIComponent(finalQuery))
  }

  const isFormValid = searchConfig.query.trim() || searchConfig.keywords.length > 0

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/research">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            返回研究台
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold">高级研究搜索</h1>
          <p className="text-muted-foreground">精确定制您的学术研究搜索条件</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Search Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Query */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                研究查询
              </CardTitle>
              <CardDescription>
                描述您的研究问题或输入相关关键词
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">主要查询</label>
                <Textarea
                  placeholder="例如：深度学习在自然语言处理中的应用和最新进展..."
                  value={searchConfig.query}
                  onChange={(e) => setSearchConfig(prev => ({ ...prev, query: e.target.value }))}
                  rows={3}
                />
              </div>

              <div className="space-y-3">
                <label className="text-sm font-medium">关键词</label>
                <div className="flex gap-2">
                  <Input
                    placeholder="添加关键词..."
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), handleAddKeyword())}
                  />
                  <Button type="button" onClick={handleAddKeyword} disabled={!newKeyword.trim()}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                
                {searchConfig.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {searchConfig.keywords.map((keyword) => (
                      <Badge key={keyword} variant="secondary" className="gap-1">
                        {keyword}
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-auto p-0 w-3 h-3"
                          onClick={() => handleRemoveKeyword(keyword)}
                        >
                          <X className="h-2 w-2" />
                        </Button>
                      </Badge>
                    ))}
                  </div>
                )}

                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">建议关键词：</p>
                  <div className="flex flex-wrap gap-1">
                    {suggestedKeywords.map((suggestion) => (
                      <Button
                        key={suggestion}
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-auto py-1 px-2 text-xs"
                        onClick={() => setNewKeyword(suggestion)}
                      >
                        {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="h-5 w-5" />
                搜索筛选
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">作者</label>
                  <Input
                    placeholder="例如：Zhang, Li"
                    value={searchConfig.authors}
                    onChange={(e) => setSearchConfig(prev => ({ ...prev, authors: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">发表期刊/会议</label>
                  <Input
                    placeholder="例如：NIPS, ICLR"
                    value={searchConfig.venue}
                    onChange={(e) => setSearchConfig(prev => ({ ...prev, venue: e.target.value }))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">发表年份（从）</label>
                  <Input
                    type="number"
                    placeholder="2020"
                    value={searchConfig.yearFrom}
                    onChange={(e) => setSearchConfig(prev => ({ ...prev, yearFrom: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">发表年份（到）</label>
                  <Input
                    type="number"
                    placeholder="2024"
                    value={searchConfig.yearTo}
                    onChange={(e) => setSearchConfig(prev => ({ ...prev, yearTo: e.target.value }))}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">最小引用次数</label>
                <Input
                  type="number"
                  placeholder="例如：10"
                  value={searchConfig.citationMin}
                  onChange={(e) => setSearchConfig(prev => ({ ...prev, citationMin: e.target.value }))}
                />
              </div>

              <div className="space-y-3">
                <label className="text-sm font-medium">学科分类</label>
                <div className="grid grid-cols-3 gap-2">
                  {availableCategories.map((category) => (
                    <Button
                      key={category}
                      type="button"
                      variant={searchConfig.categories.includes(category) ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleCategoryToggle(category)}
                      className="text-xs"
                    >
                      {category}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Search Options */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                搜索选项
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">排序方式</label>
                  <select 
                    value={searchConfig.sortBy}
                    onChange={(e) => setSearchConfig(prev => ({ ...prev, sortBy: e.target.value }))}
                    className="w-full p-2 border rounded text-sm"
                  >
                    <option value="relevance">相关性</option>
                    <option value="date">发布时间</option>
                    <option value="citations">引用次数</option>
                    <option value="title">标题</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">最大结果数</label>
                  <select 
                    value={searchConfig.maxResults}
                    onChange={(e) => setSearchConfig(prev => ({ ...prev, maxResults: e.target.value }))}
                    className="w-full p-2 border rounded text-sm"
                  >
                    <option value="10">10 篇</option>
                    <option value="20">20 篇</option>
                    <option value="50">50 篇</option>
                    <option value="100">100 篇</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">其他选项</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={searchConfig.includeDrafts}
                      onChange={(e) => setSearchConfig(prev => ({ ...prev, includeDrafts: e.target.checked }))}
                    />
                    包含预印本论文
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={searchConfig.onlyOpenAccess}
                      onChange={(e) => setSearchConfig(prev => ({ ...prev, onlyOpenAccess: e.target.checked }))}
                    />
                    仅开放获取论文
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search Summary & Actions */}
        <div className="space-y-6">
          {/* Search Preview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">搜索预览</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="bg-muted rounded-lg p-3 space-y-2">
                {searchConfig.query && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">主查询:</p>
                    <p className="text-sm">{searchConfig.query}</p>
                  </div>
                )}
                
                {searchConfig.keywords.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">关键词:</p>
                    <div className="flex flex-wrap gap-1">
                      {searchConfig.keywords.map(keyword => (
                        <Badge key={keyword} variant="outline" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {searchConfig.categories.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">分类:</p>
                    <div className="flex flex-wrap gap-1">
                      {searchConfig.categories.map(cat => (
                        <Badge key={cat} variant="secondary" className="text-xs">
                          {cat}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-xs text-muted-foreground">
                  <p>• 最多 {searchConfig.maxResults} 个结果</p>
                  <p>• 按{searchConfig.sortBy === 'relevance' ? '相关性' : 
                            searchConfig.sortBy === 'date' ? '发布时间' : 
                            searchConfig.sortBy === 'citations' ? '引用次数' : '标题'}排序</p>
                  {(searchConfig.yearFrom || searchConfig.yearTo) && (
                    <p>• 年份范围: {searchConfig.yearFrom || '不限'} - {searchConfig.yearTo || '不限'}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardContent className="pt-6 space-y-3">
              <Button 
                onClick={handleSearch}
                disabled={!isFormValid || isSearching}
                className="w-full gap-2"
              >
                {isSearching ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    搜索中...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" />
                    开始搜索分析
                  </>
                )}
              </Button>
              
              <Button variant="outline" className="w-full gap-2" asChild>
                <Link href="/research">
                  返回简单搜索
                </Link>
              </Button>
            </CardContent>
          </Card>

          {/* Tips */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Zap className="h-4 w-4" />
                搜索技巧
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="space-y-1">
                <p className="font-medium">关键词组合:</p>
                <p className="text-muted-foreground text-xs">
                  • 使用英文关键词获得更好的结果<br/>
                  • 组合通用词和专业术语<br/>
                  • 避免过于宽泛的词汇
                </p>
              </div>
              
              <div className="space-y-1">
                <p className="font-medium">时间范围:</p>
                <p className="text-muted-foreground text-xs">
                  • 近3年论文通常更具时效性<br/>
                  • 经典论文可能引用次数更高
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}