"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
// import { ScrollArea } from '@/components/ui/scroll-area' // Component not implemented
import { apiClient } from '@/lib/api'

interface JobLog {
  id: string
  job_run_id: string
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  message: string
  details?: any
  step?: string
  paper_id?: string
  error_code?: string
  duration_ms?: number
  logger_name?: string
}

interface JobLogViewerProps {
  jobRunId: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export function JobLogViewer({ jobRunId, autoRefresh = true, refreshInterval = 5000 }: JobLogViewerProps) {
  const [logs, setLogs] = useState<JobLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const [stepFilter, setStepFilter] = useState<string>('ALL')
  const [lastLogId, setLastLogId] = useState<string | null>(null)
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(autoRefresh)

  const fetchLogs = async (incremental = false) => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (levelFilter !== 'ALL') params.append('level', levelFilter)
      if (stepFilter !== 'ALL') params.append('step', stepFilter)
      if (incremental && lastLogId) params.append('last_log_id', lastLogId)

      const endpoint = incremental 
        ? `/api/job-logs/job-runs/${jobRunId}/logs/realtime?${params.toString()}`
        : `/api/job-logs/job-runs/${jobRunId}/logs?${params.toString()}`

      const response = await fetch(endpoint)
      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.statusText}`)
      }

      const data = await response.json()
      
      if (incremental) {
        // For incremental updates, append new logs
        setLogs(prevLogs => [...data.logs, ...prevLogs])
        if (data.last_log_id) {
          setLastLogId(data.last_log_id)
        }
      } else {
        // For full refresh, replace logs
        setLogs(data.logs)
        if (data.logs.length > 0) {
          setLastLogId(data.logs[0].id)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [jobRunId, levelFilter, stepFilter])

  useEffect(() => {
    if (!autoRefreshEnabled) return

    const interval = setInterval(() => {
      fetchLogs(true)
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefreshEnabled, refreshInterval, lastLogId])

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
      case 'CRITICAL':
        return 'bg-red-100 text-red-800'
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-800'
      case 'INFO':
        return 'bg-blue-100 text-blue-800'
      case 'DEBUG':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const formatDuration = (durationMs?: number) => {
    if (!durationMs) return null
    if (durationMs < 1000) return `${durationMs}ms`
    return `${(durationMs / 1000).toFixed(2)}s`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Job Logs</span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchLogs()}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
            <Button
              variant={autoRefreshEnabled ? "default" : "outline"}
              size="sm"
              onClick={() => setAutoRefreshEnabled(!autoRefreshEnabled)}
            >
              {autoRefreshEnabled ? 'Auto On' : 'Auto Off'}
            </Button>
          </div>
        </CardTitle>
        <div className="flex gap-2">
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Levels</SelectItem>
              <SelectItem value="DEBUG">Debug</SelectItem>
              <SelectItem value="INFO">Info</SelectItem>
              <SelectItem value="WARNING">Warning</SelectItem>
              <SelectItem value="ERROR">Error</SelectItem>
              <SelectItem value="CRITICAL">Critical</SelectItem>
            </SelectContent>
          </Select>
          <Select value={stepFilter} onValueChange={setStepFilter}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Steps</SelectItem>
              <SelectItem value="Fetching papers from ArXiv">Fetching Papers</SelectItem>
              <SelectItem value="Filtering existing papers">Filtering Papers</SelectItem>
              <SelectItem value="Processing papers">Processing Papers</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
            {error}
          </div>
        )}
        
        <div className="h-96 overflow-y-auto">
          <div className="space-y-2">
            {logs.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                {loading ? 'Loading logs...' : 'No logs found'}
              </div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="border rounded p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={getLevelColor(log.level)}>
                        {log.level}
                      </Badge>
                      <span className="text-sm text-gray-600">
                        {formatTimestamp(log.timestamp)}
                      </span>
                      {log.duration_ms && (
                        <Badge variant="outline" className="text-xs">
                          {formatDuration(log.duration_ms)}
                        </Badge>
                      )}
                    </div>
                    {log.step && (
                      <Badge variant="secondary" className="text-xs">
                        {log.step}
                      </Badge>
                    )}
                  </div>
                  
                  <div className="text-sm">
                    <p className="font-mono">{log.message}</p>
                  </div>
                  
                  {log.paper_id && (
                    <div className="text-xs text-gray-500">
                      Paper: {log.paper_id}
                    </div>
                  )}
                  
                  {log.error_code && (
                    <div className="text-xs text-red-500">
                      Error Code: {log.error_code}
                    </div>
                  )}
                  
                  {log.details && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-gray-500">
                        Details
                      </summary>
                      <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 