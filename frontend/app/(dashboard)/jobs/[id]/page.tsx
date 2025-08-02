"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  RefreshCw, 
  Settings, 
  Clock,
  Calendar,
  FileText,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ExternalLink
} from "lucide-react"
import { useCronJob, useJobStatus, useJobRuns, useCronJobMutations } from "@/lib/hooks/api-hooks"
import { formatDistanceToNow, format } from "date-fns"
import { parseUTCDate, formatLocalDateTime } from "@/lib/utils"
import { toast } from "sonner"
import type { JobRun } from "@/lib/api"
import { RealTimeLogs } from "@/components/job-logs/real-time-logs"
import { useTaskTracker } from "@/hooks/use-task-tracker"
import { TaskProgressComponent } from "@/components/task/task-progress"

export default function JobDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const jobId = params.id as string
  
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState("overview")
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  
  // Set initial tab based on URL parameter
  useEffect(() => {
    const tabParam = searchParams.get('tab')
    if (tabParam && ['overview', 'history', 'logs', 'configuration'].includes(tabParam)) {
      setActiveTab(tabParam)
    }
  }, [searchParams])
  
  // Fetch data using SWR hooks
  const { data: job, error: jobError, isLoading: jobLoading, mutate: refreshJob } = useCronJob(jobId)
  const { data: jobStatus, error: statusError, isLoading: statusLoading, mutate: refreshStatus } = useJobStatus(jobId)
  const { data: jobRuns, error: runsError, isLoading: runsLoading, mutate: refreshRuns } = useJobRuns(jobId)
  const { triggerCronJob, toggleCronJob } = useCronJobMutations()

  // Task tracker for async job execution
  const {
    taskStatus,
    taskProgress,
    isLoading: taskLoading,
    error: taskError,
    startTracking,
    stopTracking,
    cancelTask,
    isActive: taskActive
  } = useTaskTracker({
    onComplete: (result) => {
      console.log('Task completed:', result)
      setIsRunning(false)
      setCurrentTaskId(null)
      // Refresh job data after completion
      setTimeout(() => {
        refreshStatus()
        refreshRuns()
      }, 1000)
    },
    onError: (error) => {
      console.error('Task failed:', error)
      setIsRunning(false)
      setCurrentTaskId(null)
    },
    onProgress: (progress) => {
      console.log('Task progress:', progress)
    }
  })

  // Auto-refresh when job is running
  useEffect(() => {
    if (jobStatus?.latest_run?.status === 'running') {
      setIsRunning(true)
      const interval = setInterval(() => {
        refreshStatus()
        refreshRuns()
      }, 2000) // Refresh every 2 seconds when running

      return () => clearInterval(interval)
    } else {
      setIsRunning(false)
    }
  }, [jobStatus?.latest_run?.status, refreshStatus, refreshRuns])

  const handleRunNow = async () => {
    try {
      setIsRunning(true)
      const response = await triggerCronJob(jobId)
      
      // Store task ID and start tracking
      if (response.task_id) {
        setCurrentTaskId(response.task_id)
        startTracking(response.task_id)
        toast.success("Job execution started", {
          description: "Task is now running in the background"
        })
      } else {
        // Fallback for non-async response
        toast.success("Job execution started")
        setTimeout(() => {
          refreshStatus()
          refreshRuns()
          setIsRunning(false)
        }, 2000)
      }
    } catch (error: any) {
      console.error("Failed to trigger job:", error)
      toast.error(error.message || "Failed to start job execution")
      setIsRunning(false)
    }
  }

  const handleToggleJob = async () => {
    try {
      await toggleCronJob(jobId)
      toast.success(job?.enabled ? "Job paused" : "Job resumed")
      refreshJob()
    } catch (error: any) {
      console.error("Failed to toggle job:", error)
      toast.error(error.message || "Failed to toggle job status")
    }
  }

  const handleRefresh = async () => {
    await Promise.all([
      refreshJob(),
      refreshStatus(),
      refreshRuns()
    ])
  }

  const handleTabChange = (value: string) => {
    setActiveTab(value)
    // Update URL without page reload
    const url = new URL(window.location.href)
    url.searchParams.set('tab', value)
    window.history.replaceState({}, '', url.toString())
  }

  // Loading state
  if (jobLoading || statusLoading) {
    return (
      <div className="flex flex-col">
        <Header 
          title="Job Details" 
          description="Loading job information..."
          action={
            <Button onClick={() => router.back()} variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          }
        />
        <div className="flex-1 p-6">
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <div className="h-4 bg-muted animate-pulse rounded w-1/3" />
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="h-3 bg-muted animate-pulse rounded" />
                    <div className="h-3 bg-muted animate-pulse rounded w-2/3" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (jobError || statusError) {
    return (
      <div className="flex flex-col">
        <Header 
          title="Job Details" 
          description="Failed to load job information"
          action={
            <Button onClick={() => router.back()} variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          }
        />
        <div className="flex-1 p-6">
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <div className="text-center">
                <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  Failed to load job details. Please try again.
                </p>
                <Button onClick={handleRefresh} variant="outline" className="mt-4">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="flex flex-col">
        <Header 
          title="Job Not Found" 
          description="The requested job could not be found"
          action={
            <Button onClick={() => router.back()} variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          }
        />
      </div>
    )
  }

  const latestRun = jobStatus?.latest_run
  const stats = jobStatus?.statistics || {
    total_runs: 0,
    successful_runs: 0,
    failed_runs: 0,
    success_rate: 0
  }

  return (
    <div className="flex flex-col">
      <Header 
        title={job.name}
        description={`Keywords: ${job.keywords.join(", ")}`}
        action={
          <div className="flex items-center space-x-2">
            {isRunning && (
              <div className="flex items-center space-x-2 text-sm text-blue-600">
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Running...</span>
              </div>
            )}
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button 
              onClick={handleRunNow} 
              disabled={isRunning}
              size="sm"
            >
              <Play className={`mr-2 h-4 w-4 ${isRunning ? 'animate-spin' : ''}`} />
              {isRunning ? 'Running...' : 'Run Now'}
            </Button>
            <Button 
              onClick={handleToggleJob} 
              variant={job.enabled ? 'destructive' : 'default'}
              size="sm"
            >
              {job.enabled ? (
                <>
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Resume
                </>
              )}
            </Button>
            <Button onClick={() => router.back()} variant="outline" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          </div>
        }
      />
      
      <div className="flex-1 p-6 space-y-6 overflow-auto">
        {/* Status Overview */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Status</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <Badge variant={job.enabled ? 'default' : 'secondary'}>
                  {job.enabled ? 'Active' : 'Paused'}
                </Badge>
                {latestRun && (
                  <Badge variant={
                    latestRun.status === 'completed' ? 'default' :
                    latestRun.status === 'running' ? 'secondary' :
                    latestRun.status === 'failed' ? 'destructive' : 'secondary'
                  }>
                    {latestRun.status}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{Math.round(stats.success_rate)}%</div>
              <p className="text-xs text-muted-foreground">
                {stats.successful_runs} of {stats.total_runs} runs
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
                {latestRun?.papers_processed || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {latestRun?.papers_found || 0} found, {latestRun?.papers_skipped || 0} skipped
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Last Run</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium">
                {latestRun?.started_at ? 
                  formatDistanceToNow(parseUTCDate(latestRun.started_at), { addSuffix: true }) : 
                  'Never'
                }
              </div>
              <p className="text-xs text-muted-foreground">
                {latestRun?.completed_at ? 
                  `Duration: ${Math.round((parseUTCDate(latestRun.completed_at).getTime() - parseUTCDate(latestRun.started_at).getTime()) / 1000)}s` :
                  latestRun?.status === 'running' ? 'In progress...' : ''
                }
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabbed Content */}
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="history">Run History</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="configuration">Configuration</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            {/* Task Progress */}
            {(taskActive || taskStatus || taskError) && (
              <TaskProgressComponent
                taskStatus={taskStatus}
                taskProgress={taskProgress}
                isLoading={taskLoading}
                error={taskError}
                onCancel={cancelTask}
                showCancelButton={true}
              />
            )}

            {/* Current Run Status */}
            {latestRun && latestRun.status === 'running' && !taskActive && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    <span>Current Execution</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span>Started:</span>
                      <span>{formatLocalDateTime(latestRun.started_at, 'PPpp')}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Papers Found:</span>
                      <span>{latestRun.papers_found}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Papers Processed:</span>
                      <span>{latestRun.papers_processed}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Papers Embedded:</span>
                      <span>{latestRun.papers_embedded}</span>
                    </div>
                    {latestRun.embedding_errors > 0 && (
                      <div className="flex justify-between text-sm text-destructive">
                        <span>Embedding Errors:</span>
                        <span>{latestRun.embedding_errors}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Job Schedule Information */}
            <Card>
              <CardHeader>
                <CardTitle>Schedule Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span>Schedule:</span>
                    <span>
                      {job.cron_expression || 
                       (job.interval_hours ? `Every ${job.interval_hours} hours` : 'Not scheduled')}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Max Papers per Run:</span>
                    <span>{job.max_papers_per_run}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Vector Database:</span>
                    <span className="capitalize">{job.vector_db_provider}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Embedding Model:</span>
                    <span>{job.embedding_model}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Execution History</CardTitle>
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
                            {run.status === 'completed' ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : run.status === 'failed' ? (
                              <XCircle className="h-4 w-4 text-red-500" />
                            ) : run.status === 'running' ? (
                              <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
                            ) : (
                              <Clock className="h-4 w-4 text-gray-500" />
                            )}
                            <Badge variant={
                              run.status === 'completed' ? 'default' :
                              run.status === 'running' ? 'secondary' :
                              run.status === 'failed' ? 'destructive' : 'secondary'
                            }>
                              {run.status}
                            </Badge>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {formatLocalDateTime(run.started_at, 'PPpp')}
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
                                `${Math.round((parseUTCDate(run.completed_at).getTime() - parseUTCDate(run.started_at).getTime()) / 1000)}s` :
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
                    No execution history found
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="logs" className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-lg font-medium">Job Logs</h3>
                <p className="text-sm text-muted-foreground">
                  View real-time and historical logs for this job
                </p>
              </div>
              <Button 
                onClick={() => router.push(`/jobs/${jobId}/logs`)}
                variant="outline"
                size="sm"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                Full Screen Logs
              </Button>
            </div>
            <RealTimeLogs 
              jobId={jobId} 
              runId={latestRun?.id} 
              isRunning={isRunning}
            />
          </TabsContent>

          <TabsContent value="configuration" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Job Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Job Name</label>
                    <div className="text-sm text-muted-foreground">{job.name}</div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Keywords</label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {job.keywords.map((keyword, index) => (
                        <Badge key={index} variant="outline">{keyword}</Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Schedule</label>
                    <div className="text-sm text-muted-foreground">
                      {job.cron_expression || `Every ${job.interval_hours} hours`}
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Vector Database Provider</label>
                    <div className="text-sm text-muted-foreground capitalize">{job.vector_db_provider}</div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Embedding Provider</label>
                    <div className="text-sm text-muted-foreground">{job.embedding_provider}</div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Embedding Model</label>
                    <div className="text-sm text-muted-foreground">{job.embedding_model}</div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Max Papers per Run</label>
                    <div className="text-sm text-muted-foreground">{job.max_papers_per_run}</div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Created</label>
                    <div className="text-sm text-muted-foreground">
                      {formatLocalDateTime(job.created_at, 'PPpp')}
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Last Updated</label>
                    <div className="text-sm text-muted-foreground">
                      {formatLocalDateTime(job.updated_at, 'PPpp')}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}