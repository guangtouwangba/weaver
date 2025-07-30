"use client"

import { Header } from "@/components/layout/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { CreateJobForm } from "@/components/forms/create-job-form"
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
import { useDashboardStats, useHealthStatus, useCronJobs, useCronJobMutations, useAvailableProviders } from "@/lib/hooks/api-hooks"
import { formatDistanceToNow } from "date-fns"
import { useState } from "react"

export default function DashboardPage() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isCreateJobOpen, setIsCreateJobOpen] = useState(false)
  
  // Fetch data using SWR hooks
  const { data: stats, error: statsError, isLoading: statsLoading, mutate: mutateStats } = useDashboardStats()
  const { data: health, error: healthError, isLoading: healthLoading, mutate: mutateHealth } = useHealthStatus()
  const { data: jobs, error: jobsError, isLoading: jobsLoading, mutate: mutateCronJobs } = useCronJobs(0, 10) // Get first 10 jobs for recent jobs
  const { data: providers } = useAvailableProviders()
  const { createCronJob } = useCronJobMutations()

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await Promise.all([
        mutateStats(),
        mutateHealth(),
        mutateCronJobs()
      ])
    } finally {
      setIsRefreshing(false)
    }
  }

  const [isCreatingJob, setIsCreatingJob] = useState(false)

  const handleCreateJob = async (values: any) => {
    if (isCreatingJob) return // Prevent duplicate submissions
    
    setIsCreatingJob(true)
    try {
      // Transform form values to match API schema
      const jobData = {
        name: values.name,
        keywords: values.keywords,
        cron_expression: values.schedule === 'daily' ? '0 0 * * *' : 
                        values.schedule === 'weekly' ? '0 0 * * 0' :
                        values.schedule === 'bi-weekly' ? '0 0 */14 * *' :
                        values.schedule === 'monthly' ? '0 0 1 * *' :
                        values.schedule === 'custom' ? values.customCron : undefined,
        interval_hours: values.schedule === 'daily' ? 24 : 
                       values.schedule === 'weekly' ? 168 :
                       values.schedule === 'bi-weekly' ? 336 :
                       values.schedule === 'monthly' ? 720 : 
                       values.schedule === 'custom' ? undefined : undefined,
        enabled: true,
        max_papers_per_run: values.maxPapers,
        embedding_provider: values.embeddingModel?.split('-')[0] || 'openai',
        embedding_model: values.embeddingModel || 'text-embedding-3-small',
        vector_db_provider: values.vectorDb || 'chroma',
        vector_db_config: {}
      }

      await createCronJob(jobData)
      await mutateCronJobs() // Refresh the jobs list
      setIsCreateJobOpen(false)
    } catch (error) {
      console.error('Failed to create job:', error)
      // You might want to show a toast notification here
    } finally {
      setIsCreatingJob(false)
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
                  <div className="h-4 bg-muted animate-pulse rounded" />
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
            <Button onClick={() => setIsCreateJobOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Job
            </Button>
          </div>
        }
      />
      
      <div className="flex-1 p-6 space-y-6 overflow-auto">
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
                        Created {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button variant="outline" size="sm">
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No jobs created yet</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mt-2"
                  onClick={() => setIsCreateJobOpen(true)}
                >
                  Create your first job
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Create Job Dialog */}
      <Dialog open={isCreateJobOpen} onOpenChange={setIsCreateJobOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Cronjob</DialogTitle>
            <DialogDescription>
              Set up an automated job to collect research papers based on your keywords.
            </DialogDescription>
          </DialogHeader>
          <CreateJobForm 
            onSubmit={handleCreateJob}
            onCancel={() => setIsCreateJobOpen(false)}
            providers={providers}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}