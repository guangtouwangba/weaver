"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Play,
  Square,
  AlertTriangle,
  FileText,
  Database,
  Zap
} from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { TaskStatus, TaskProgress } from "@/lib/api"

interface TaskProgressComponentProps {
  taskStatus: TaskStatus | null
  taskProgress: TaskProgress | null
  isLoading: boolean
  error: string | null
  onCancel?: () => void
  showCancelButton?: boolean
  compact?: boolean
}

export function TaskProgressComponent({
  taskStatus,
  taskProgress,
  isLoading,
  error,
  onCancel,
  showCancelButton = true,
  compact = false
}: TaskProgressComponentProps) {
  if (!taskStatus && !isLoading && !error) {
    return null
  }

  const getStatusIcon = () => {
    if (error || taskStatus?.state === 'FAILURE') {
      return <XCircle className="h-4 w-4 text-red-500" />
    }
    if (taskStatus?.state === 'SUCCESS') {
      return <CheckCircle className="h-4 w-4 text-green-500" />
    }
    if (taskStatus?.state === 'REVOKED') {
      return <Square className="h-4 w-4 text-gray-500" />
    }
    if (isLoading || taskStatus?.state === 'PROGRESS' || taskStatus?.state === 'PENDING') {
      return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />
    }
    return <Clock className="h-4 w-4 text-gray-500" />
  }

  const getStatusBadge = () => {
    if (error || taskStatus?.state === 'FAILURE') {
      return <Badge variant="destructive">Failed</Badge>
    }
    if (taskStatus?.state === 'SUCCESS') {
      return <Badge variant="default">Completed</Badge>
    }
    if (taskStatus?.state === 'REVOKED') {
      return <Badge variant="secondary">Cancelled</Badge>
    }
    if (taskStatus?.state === 'PROGRESS') {
      return <Badge variant="secondary">Running</Badge>
    }
    if (taskStatus?.state === 'PENDING') {
      return <Badge variant="secondary">Starting</Badge>
    }
    return <Badge variant="secondary">Unknown</Badge>
  }

  const getProgressPercentage = () => {
    return taskProgress?.progress_percentage || taskStatus?.progress_percentage || 0
  }

  const formatTimeEstimate = (seconds: number | null) => {
    if (!seconds) return 'Unknown'
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`
    return `${Math.round(seconds / 3600)}h`
  }

  if (compact) {
    return (
      <div className="flex items-center space-x-2">
        {getStatusIcon()}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            {getStatusBadge()}
            <Progress value={getProgressPercentage()} className="flex-1" />
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {Math.round(getProgressPercentage())}%
            </span>
          </div>
          {taskProgress?.current_step && (
            <div className="text-xs text-muted-foreground mt-1">
              {taskProgress.current_step}
            </div>
          )}
        </div>
        {showCancelButton && onCancel && (taskStatus?.state === 'PROGRESS' || taskStatus?.state === 'PENDING') && (
          <Button variant="outline" size="sm" onClick={onCancel}>
            <Square className="h-3 w-3" />
          </Button>
        )}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <CardTitle className="text-lg">Task Progress</CardTitle>
            {getStatusBadge()}
          </div>
          {showCancelButton && onCancel && (taskStatus?.state === 'PROGRESS' || taskStatus?.state === 'PENDING') && (
            <Button variant="outline" size="sm" onClick={onCancel}>
              <Square className="mr-2 h-4 w-4" />
              Cancel
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{Math.round(getProgressPercentage())}%</span>
          </div>
          <Progress value={getProgressPercentage()} className="w-full" />
        </div>

        {/* Current Step */}
        {taskProgress?.current_step && (
          <div className="space-y-1">
            <div className="text-sm font-medium">Current Step</div>
            <div className="text-sm text-muted-foreground">{taskProgress.current_step}</div>
          </div>
        )}

        {/* Time Information */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          {taskProgress?.time_elapsed && (
            <div>
              <div className="font-medium">Time Elapsed</div>
              <div className="text-muted-foreground">
                {formatTimeEstimate(taskProgress.time_elapsed)}
              </div>
            </div>
          )}
          {taskProgress?.eta && (
            <div>
              <div className="font-medium">Estimated Remaining</div>
              <div className="text-muted-foreground">
                {formatTimeEstimate(taskProgress.eta)}
              </div>
            </div>
          )}
        </div>

        {/* Metrics */}
        {taskProgress && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-blue-500" />
              <div>
                <div className="font-medium">{taskProgress.papers_found}</div>
                <div className="text-muted-foreground">Found</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Play className="h-4 w-4 text-green-500" />
              <div>
                <div className="font-medium">{taskProgress.papers_processed}</div>
                <div className="text-muted-foreground">Processed</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Database className="h-4 w-4 text-purple-500" />
              <div>
                <div className="font-medium">{taskProgress.papers_embedded}</div>
                <div className="text-muted-foreground">Embedded</div>
              </div>
            </div>
            
            {(taskProgress.embedding_errors > 0 || taskProgress.vector_db_errors > 0) && (
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-red-500" />
                <div>
                  <div className="font-medium text-red-600">
                    {taskProgress.embedding_errors + taskProgress.vector_db_errors}
                  </div>
                  <div className="text-muted-foreground">Errors</div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded">
            <div className="flex items-center space-x-2 text-destructive">
              <AlertTriangle className="h-4 w-4" />
              <span className="font-medium">Error</span>
            </div>
            <div className="text-sm text-destructive mt-1">{error}</div>
          </div>
        )}

        {/* Task Result */}
        {taskStatus?.result && (
          <div className="p-3 bg-green-50 border border-green-200 rounded">
            <div className="flex items-center space-x-2 text-green-700">
              <CheckCircle className="h-4 w-4" />
              <span className="font-medium">Task Completed</span>
            </div>
            <div className="text-sm text-green-600 mt-1">
              {typeof taskStatus.result === 'string' 
                ? taskStatus.result 
                : JSON.stringify(taskStatus.result, null, 2)
              }
            </div>
          </div>
        )}

        {/* Task ID */}
        {taskStatus?.task_id && (
          <div className="text-xs text-muted-foreground">
            Task ID: <code className="bg-muted px-1 py-0.5 rounded">{taskStatus.task_id}</code>
          </div>
        )}
      </CardContent>
    </Card>
  )
}