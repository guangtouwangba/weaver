"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
// import { ScrollArea } from '@/components/ui/scroll-area' // Component not implemented
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface ElasticsearchLog {
  job_run_id: string
  job_id: string
  job_name: string
  timestamp: string
  level: string
  message: string
  step?: string
  paper_id?: string
  error_code?: string
  duration_ms?: number
  details?: any
}

interface ElasticsearchLogViewerProps {
  jobRunId?: string
  jobId?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export function ElasticsearchLogViewer({ 
  jobRunId, 
  jobId, 
  autoRefresh = false, 
  refreshInterval = 10000 
}: ElasticsearchLogViewerProps) {
  const [logs, setLogs] = useState<ElasticsearchLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const [stepFilter, setStepFilter] = useState<string>('ALL')
  const [startTime, setStartTime] = useState<string>('')
  const [endTime, setEndTime] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(autoRefresh)
  const [activeTab, setActiveTab] = useState('logs')

  const fetchLogs = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (jobRunId) params.append('job_run_id', jobRunId)
      if (jobId) params.append('job_id', jobId)
      if (levelFilter !== 'ALL') params.append('level', levelFilter)
      if (stepFilter !== 'ALL') params.append('step', stepFilter)
      if (startTime) params.append('start_time', startTime)
      if (endTime) params.append('end_time', endTime)
      if (searchQuery) params.append('query', searchQuery)

      const response = await fetch(`/api/elasticsearch/search/logs?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.statusText}`)
      }

      const data = await response.json()
      setLogs(data.logs || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs')
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const params = new URLSearchParams()
      if (jobRunId) params.append('job_run_id', jobRunId)
      if (jobId) params.append('job_id', jobId)

      const [statsResponse, errorResponse, perfResponse] = await Promise.all([
        fetch(`/api/elasticsearch/analytics/log-statistics?${params.toString()}`),
        fetch(`/api/elasticsearch/analytics/error-analysis?${params.toString()}`),
        fetch(`/api/elasticsearch/analytics/performance-metrics?${params.toString()}`)
      ])

      const [stats, errorAnalysis, perfMetrics] = await Promise.all([
        statsResponse.ok ? statsResponse.json() : null,
        errorResponse.ok ? errorResponse.json() : null,
        perfResponse.ok ? perfResponse.json() : null
      ])

      return { stats, errorAnalysis, perfMetrics }
    } catch (err) {
      console.error('Failed to fetch analytics:', err)
      return { stats: null, errorAnalysis: null, perfMetrics: null }
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [jobRunId, jobId, levelFilter, stepFilter, startTime, endTime, searchQuery])

  useEffect(() => {
    if (!autoRefreshEnabled) return

    const interval = setInterval(() => {
      fetchLogs()
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefreshEnabled, refreshInterval])

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
          <span>Elasticsearch Logs</span>
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
        
        <div className="flex gap-2 flex-wrap">
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
          
          <Input
            placeholder="Search query..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-48"
          />
          
          <Input
            type="datetime-local"
            placeholder="Start time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            className="w-48"
          />
          
          <Input
            type="datetime-local"
            placeholder="End time"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            className="w-48"
          />
        </div>
      </CardHeader>
      
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
            {error}
          </div>
        )}
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>
          
          <TabsContent value="logs">
            <div className="h-96 overflow-y-auto">
              <div className="space-y-2">
                {logs.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    {loading ? 'Loading logs...' : 'No logs found'}
                  </div>
                ) : (
                  logs.map((log, index) => (
                    <div key={index} className="border rounded p-3 space-y-2">
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
                      
                      {log.job_name && (
                        <div className="text-xs text-gray-500">
                          Job: {log.job_name}
                        </div>
                      )}
                      
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
          </TabsContent>
          
          <TabsContent value="analytics">
            <ElasticsearchAnalytics 
              jobRunId={jobRunId} 
              jobId={jobId} 
            />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

function ElasticsearchAnalytics({ jobRunId, jobId }: { jobRunId?: string, jobId?: string }) {
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        const params = new URLSearchParams()
        if (jobRunId) params.append('job_run_id', jobRunId)
        if (jobId) params.append('job_id', jobId)

        const [statsResponse, errorResponse, perfResponse] = await Promise.all([
          fetch(`/api/elasticsearch/analytics/log-statistics?${params.toString()}`),
          fetch(`/api/elasticsearch/analytics/error-analysis?${params.toString()}`),
          fetch(`/api/elasticsearch/analytics/performance-metrics?${params.toString()}`)
        ])

        const [stats, errorAnalysis, perfMetrics] = await Promise.all([
          statsResponse.ok ? statsResponse.json() : null,
          errorResponse.ok ? errorResponse.json() : null,
          perfResponse.ok ? perfResponse.json() : null
        ])

        setAnalytics({ stats, errorAnalysis, perfMetrics })
      } catch (err) {
        console.error('Failed to fetch analytics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [jobRunId, jobId])

  if (loading) {
    return <div className="text-center py-8">Loading analytics...</div>
  }

  if (!analytics) {
    return <div className="text-center py-8 text-gray-500">No analytics available</div>
  }

  return (
    <div className="space-y-4">
      {analytics.stats && (
        <Card>
          <CardHeader>
            <CardTitle>Log Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
              {JSON.stringify(analytics.stats, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
      
      {analytics.errorAnalysis && (
        <Card>
          <CardHeader>
            <CardTitle>Error Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
              {JSON.stringify(analytics.errorAnalysis, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
      
      {analytics.perfMetrics && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">
              {JSON.stringify(analytics.perfMetrics, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 