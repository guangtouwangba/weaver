"use client"

import { useState, useMemo } from "react"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { 
  Calendar, 
  Download, 
  Filter, 
  RefreshCw, 
  TrendingUp,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  BarChart3,
  Activity
} from "lucide-react"
import { useAllJobRuns, useHistoryStats, useCronJobs, useHistoryExport } from "@/lib/hooks/api-hooks"
import { formatDistanceToNow, format, parseISO, subDays } from "date-fns"
import { toast } from "sonner"
import type { JobRun, HistoryFilters } from "@/lib/api"

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState("overview")
  const [filters, setFilters] = useState<HistoryFilters>({
    limit: 50,
    skip: 0
  })
  const [statsPeriod, setStatsPeriod] = useState(30)
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  // Fetch data using hooks
  const { data: jobs, error: jobsError } = useCronJobs()
  const { data: jobRuns, error: runsError, isLoading: runsLoading, mutate: refreshRuns } = useAllJobRuns(filters)
  const { data: historyStats, error: statsError, isLoading: statsLoading, mutate: refreshStats } = useHistoryStats(statsPeriod)
  const { exportHistory } = useHistoryExport()
  
  // Memoized data processing
  const statusCounts = useMemo(() => {
    if (!jobRuns) return { completed: 0, failed: 0, running: 0, cancelled: 0 }
    
    return jobRuns.reduce((acc, run) => {
      acc[run.status as keyof typeof acc] = (acc[run.status as keyof typeof acc] || 0) + 1
      return acc
    }, { completed: 0, failed: 0, running: 0, cancelled: 0 })
  }, [jobRuns])
  
  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await Promise.all([refreshRuns(), refreshStats()])
      toast.success("Data refreshed successfully")
    } catch (error) {
      toast.error("Failed to refresh data")
    } finally {
      setIsRefreshing(false)
    }
  }
  
  const handleExport = async (format: 'csv' | 'json' = 'csv') => {
    try {
      await exportHistory({ ...filters, format })
      toast.success(`History exported as ${format.toUpperCase()}`)
    } catch (error: any) {
      toast.error(error.message || `Failed to export history`)
    }
  }
  
  const handleFilterChange = (key: keyof HistoryFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      skip: 0 // Reset pagination when filters change
    }))
  }
  
  // Helper function to get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'running':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
      case 'cancelled':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }
  
  return (
    <div className="flex flex-col">
      <Header 
        title="Execution History" 
        description="View and analyze job execution history and statistics"
        action={
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleExport('csv')}
            >
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => handleExport('json')}
            >
              <Download className="h-4 w-4 mr-2" />
              Export JSON
            </Button>
          </div>
        }
      />
      
      <div className="flex-1 p-6 space-y-6 overflow-auto">
        {/* Quick Stats Cards */}
        {historyStats && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{historyStats.global_statistics.total_runs}</div>
                <p className="text-xs text-muted-foreground">
                  Last {statsPeriod} days
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round(historyStats.global_statistics.success_rate)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  {historyStats.global_statistics.successful_runs} of {historyStats.global_statistics.total_runs} runs
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Papers Processed</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {historyStats.global_statistics.paper_statistics.total_processed}
                </div>
                <p className="text-xs text-muted-foreground">
                  {historyStats.global_statistics.paper_statistics.total_found} found
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Processing Rate</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round(historyStats.global_statistics.paper_statistics.processing_rate)}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Papers successfully processed
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabbed Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="runs">Job Runs</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="top-jobs">Top Jobs</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            {/* Current Status Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Current Status Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{statusCounts.completed}</div>
                    <div className="text-sm text-muted-foreground">Completed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{statusCounts.failed}</div>
                    <div className="text-sm text-muted-foreground">Failed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{statusCounts.running}</div>
                    <div className="text-sm text-muted-foreground">Running</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">{statusCounts.cancelled}</div>
                    <div className="text-sm text-muted-foreground">Cancelled</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Period Controls */}
            <Card>
              <CardHeader>
                <CardTitle>Statistics Period</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex space-x-2">
                  {[7, 30, 90, 365].map((days) => (
                    <Button
                      key={days}
                      variant={statsPeriod === days ? "default" : "outline"}
                      size="sm"
                      onClick={() => setStatsPeriod(days)}
                    >
                      {days} days
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="runs" className="space-y-4">
            {/* Filters */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Filter className="h-5 w-5" />
                  <span>Filters</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <Label htmlFor="status-filter">Status</Label>
                    <Select 
                      value={filters.status_filter || "all"} 
                      onValueChange={(value) => handleFilterChange('status_filter', value === 'all' ? undefined : value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All statuses" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All statuses</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                        <SelectItem value="running">Running</SelectItem>
                        <SelectItem value="cancelled">Cancelled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="job-filter">Job</Label>
                    <Select 
                      value={filters.job_id_filter || "all"} 
                      onValueChange={(value) => handleFilterChange('job_id_filter', value === 'all' ? undefined : value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All jobs" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All jobs</SelectItem>
                        {jobs?.map((job) => (
                          <SelectItem key={job.id} value={job.id}>
                            {job.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="start-date">Start Date</Label>
                    <Input
                      id="start-date"
                      type="date"
                      value={filters.start_date ? filters.start_date.split('T')[0] : ''}
                      onChange={(e) => handleFilterChange('start_date', e.target.value ? `${e.target.value}T00:00:00Z` : undefined)}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="end-date">End Date</Label>
                    <Input
                      id="end-date"
                      type="date"
                      value={filters.end_date ? filters.end_date.split('T')[0] : ''}
                      onChange={(e) => handleFilterChange('end_date', e.target.value ? `${e.target.value}T23:59:59Z` : undefined)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Job Runs List */}
            <Card>
              <CardHeader>
                <CardTitle>Job Runs</CardTitle>
              </CardHeader>
              <CardContent>
                {runsLoading ? (
                  <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="h-16 bg-muted animate-pulse rounded" />
                    ))}
                  </div>
                ) : jobRuns && jobRuns.length > 0 ? (
                  <div className="space-y-4">
                    {jobRuns.map((run: JobRun) => (
                      <div key={run.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(run.status)}
                            <Badge variant={
                              run.status === 'completed' ? 'default' :
                              run.status === 'running' ? 'secondary' :
                              run.status === 'failed' ? 'destructive' : 'secondary'
                            }>
                              {run.status}
                            </Badge>
                            {run.manual_trigger && (
                              <Badge variant="outline">Manual</Badge>
                            )}
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {format(new Date(run.started_at), 'PPpp')}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Found:</span>
                            <div className="font-medium">{run.papers_found}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Processed:</span>
                            <div className="font-medium">{run.papers_processed}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Embedded:</span>
                            <div className="font-medium">{run.papers_embedded}</div>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Duration:</span>
                            <div className="font-medium">
                              {run.completed_at ? 
                                `${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s` :
                                run.status === 'running' ? 'Running...' : 'N/A'
                              }
                            </div>
                          </div>
                        </div>
                        
                        {run.error_message && (
                          <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded">
                            <div className="text-sm text-destructive">
                              <strong>Error:</strong> {run.error_message}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No job runs found for the selected filters
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            {/* Daily Trends Chart - placeholder for now */}
            <Card>
              <CardHeader>
                <CardTitle>Daily Trends</CardTitle>
              </CardHeader>
              <CardContent>
                {historyStats?.daily_trends ? (
                  <div className="space-y-4">
                    <div className="text-sm text-muted-foreground">
                      Showing trends for the last {statsPeriod} days
                    </div>
                    {/* Simple trend display - could be enhanced with a chart library */}
                    <div className="space-y-2">
                      {historyStats.daily_trends.slice(-7).map((trend, index) => (
                        <div key={trend.date} className="flex items-center justify-between p-2 border rounded">
                          <div className="text-sm">
                            {format(parseISO(trend.date), 'MMM dd')}
                          </div>
                          <div className="flex space-x-4 text-sm">
                            <span className="text-green-600">{trend.successful_runs} success</span>
                            <span className="text-red-600">{trend.failed_runs} failed</span>
                            <span className="text-muted-foreground">{trend.papers_processed} papers</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No trend data available
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="top-jobs" className="space-y-4">
            {/* Top Performing Jobs */}
            <Card>
              <CardHeader>
                <CardTitle>Top Performing Jobs</CardTitle>
              </CardHeader>
              <CardContent>
                {historyStats?.top_performing_jobs ? (
                  <div className="space-y-4">
                    {historyStats.top_performing_jobs.map((job, index) => (
                      <div key={job.job_id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div className="text-2xl font-bold text-muted-foreground">
                            #{index + 1}
                          </div>
                          <div>
                            <div className="font-medium">{job.job_name}</div>
                            <div className="text-sm text-muted-foreground">
                              {job.total_runs} total runs • {Math.round(job.success_rate)}% success rate
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{job.recent_papers_processed}</div>
                          <div className="text-sm text-muted-foreground">papers processed</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No job performance data available
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}