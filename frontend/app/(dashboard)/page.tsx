"use client"

import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  FileText, 
  TrendingUp,
  Play,
  Plus,
  RefreshCw,
  AlertTriangle
} from "lucide-react"
import { formatNumber } from "@/lib/utils"
import { useDashboardStats, useHealthStatus, useCronJobs, useRefreshDashboard } from "@/lib/hooks/api-hooks"
import { formatDistanceToNow } from "date-fns"
import { useState } from "react"

export default function DashboardPage() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const refreshDashboard = useRefreshDashboard()
  
  // Fetch data using SWR hooks
  const { data: stats, error: statsError, isLoading: statsLoading } = useDashboardStats()
  const { data: health, error: healthError, isLoading: healthLoading } = useHealthStatus()
  const { data: jobs, error: jobsError, isLoading: jobsLoading } = useCronJobs(0, 10) // Get first 10 jobs for recent jobs

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await refreshDashboard()
    } finally {
      setIsRefreshing(false)
    }
  }

  // Loading state
  if (statsLoading || healthLoading || jobsLoading) {
    return (
      <div className="flex flex-col">
        <Header 
          title="Dashboard" 
          description="Monitor your research paper collection jobs"
          action={
            <Button disabled>
              <Plus className="mr-2 h-4 w-4" />
              New Job
            </Button>
          }
        />
        <div className="flex-1 p-6 space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-4 bg-muted animate-pulse rounded" />
                </CardHeader>
                <CardContent>
                  <div className="h-8 bg-muted animate-pulse rounded mb-2" />
                  <div className="h-3 bg-muted animate-pulse rounded" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (statsError || healthError || jobsError) {
    return (
      <div className="flex flex-col">
        <Header 
          title="Dashboard" 
          description="Monitor your research paper collection jobs"
          action={
            <Button onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          }
        />
        <div className="flex-1 p-6">
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <div className="text-center">
                <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  Failed to load dashboard data. Please check your connection and try again.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Get recent jobs (sort by updated_at or created_at)
  const recentJobs = jobs?.slice(0, 3) || []

  return (
    <div className="flex flex-col">
      <Header 
        title="Dashboard" 
        description="Monitor your research paper collection jobs"
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
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Job
            </Button>
          </div>
        }
      />
      
      <div className="flex-1 p-6 space-y-6">
        {/* Statistics Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_jobs || 0}</div>
              <p className="text-xs text-muted-foreground">
                {stats?.active_jobs || 0} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.success_rate || 0}%</div>
              <p className="text-xs text-muted-foreground">
                {stats?.completed_runs || 0} completed runs
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Papers Processed</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stats?.papers_processed || 0)}</div>
              <p className="text-xs text-muted-foreground">
                Total collected
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed Runs</CardTitle>
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.failed_runs || 0}</div>
              <p className="text-xs text-muted-foreground">
                Requires attention
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Jobs */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {recentJobs.length > 0 ? (
              <div className="space-y-4">
                {recentJobs.map((job) => (
                  <div key={job.id} className="flex items-center justify-between border-b pb-4 last:border-b-0 last:pb-0">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium">{job.name}</h4>
                        <Badge 
                          variant={
                            job.enabled ? 'default' : 'secondary'
                          }
                        >
                          {job.enabled ? 'Active' : 'Paused'}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Keywords: {job.keywords.slice(0, 3).join(", ")}
                        {job.keywords.length > 3 && ` +${job.keywords.length - 3} more`}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Updated: {formatDistanceToNow(new Date(job.updated_at), { addSuffix: true })}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button size="sm" variant="ghost">
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-sm text-muted-foreground">
                No jobs found. Create your first job to get started.
              </div>
            )}
          </CardContent>
        </Card>

        {/* System Status */}
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">API Server</span>
                  <Badge variant={health?.status === 'healthy' ? 'default' : 'destructive'}>
                    {health?.status === 'healthy' ? 'Online' : 'Offline'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Database</span>
                  <Badge variant={health?.database_status === 'healthy' ? 'default' : 'destructive'}>
                    {health?.database_status === 'healthy' ? 'Connected' : 'Disconnected'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Available Agents</span>
                  <span className="text-sm font-medium">{health?.agents_available?.length || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Uptime</span>
                  <span className="text-sm font-medium">
                    {health?.uptime_seconds 
                      ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`
                      : 'Unknown'
                    }
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button className="w-full justify-start" variant="outline">
                  <Plus className="mr-2 h-4 w-4" />
                  Create New Job
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <Play className="mr-2 h-4 w-4" />
                  Run All Jobs
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  <FileText className="mr-2 h-4 w-4" />
                  View Reports
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}