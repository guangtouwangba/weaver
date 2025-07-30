"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { 
  Play, 
  Pause, 
  Download, 
  Search, 
  Filter,
  RefreshCw,
  Terminal
} from "lucide-react"
import { toast } from "sonner"
import { format } from "date-fns"

interface LogEntry {
  id: string
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  message: string
  context?: Record<string, any>
}

interface RealTimeLogsProps {
  jobId: string
  runId?: string
  isRunning: boolean
}

export function RealTimeLogs({ jobId, runId, isRunning }: RealTimeLogsProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [levelFilter, setLevelFilter] = useState<string>("ALL")
  const [autoScroll, setAutoScroll] = useState(true)
  
  const wsRef = useRef<WebSocket | null>(null)
  const logsEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [filteredLogs, autoScroll])

  // Filter logs based on search term and level
  useEffect(() => {
    let filtered = logs

    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.context && JSON.stringify(log.context).toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    if (levelFilter !== "ALL") {
      filtered = filtered.filter(log => log.level === levelFilter)
    }

    setFilteredLogs(filtered)
  }, [logs, searchTerm, levelFilter])

  // Setup WebSocket connection for real-time logs
  useEffect(() => {
    if (!isRunning || !runId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000'
    const wsUrl = `${protocol}//${host}/api/cronjobs/${jobId}/runs/${runId}/logs/stream`

    try {
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        setIsConnected(true)
        console.log('WebSocket connected for logs')
      }

      wsRef.current.onmessage = (event) => {
        if (isPaused) return

        try {
          const logEntry: LogEntry = JSON.parse(event.data)
          setLogs(prev => [...prev, logEntry])
        } catch (error) {
          console.error('Failed to parse log entry:', error)
        }
      }

      wsRef.current.onclose = () => {
        setIsConnected(false)
        console.log('WebSocket disconnected')
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [jobId, runId, isRunning, isPaused])

  const handleScrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleToggleAutoScroll = () => {
    setAutoScroll(!autoScroll)
    if (!autoScroll) {
      handleScrollToBottom()
    }
  }

  const handleExportLogs = () => {
    const logsText = filteredLogs.map(log => 
      `[${format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}] ${log.level}: ${log.message}${
        log.context ? '\n' + JSON.stringify(log.context, null, 2) : ''
      }`
    ).join('\n\n')

    const blob = new Blob([logsText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `job-${jobId}-logs-${format(new Date(), 'yyyy-MM-dd-HH-mm-ss')}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    toast.success('Logs exported successfully')
  }

  const handleClearLogs = () => {
    setLogs([])
    toast.success('Logs cleared')
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'DEBUG': return 'text-gray-500'
      case 'INFO': return 'text-blue-600'
      case 'WARNING': return 'text-yellow-600'
      case 'ERROR': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getLevelBadgeVariant = (level: string) => {
    switch (level) {
      case 'DEBUG': return 'secondary' as const
      case 'INFO': return 'default' as const
      case 'WARNING': return 'secondary' as const
      case 'ERROR': return 'destructive' as const
      default: return 'secondary' as const
    }
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Terminal className="h-5 w-5" />
            <CardTitle>Real-time Logs</CardTitle>
            {isConnected && (
              <Badge variant="default" className="text-xs">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
                Live
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPaused(!isPaused)}
              disabled={!isRunning}
            >
              {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
              {isPaused ? 'Resume' : 'Pause'}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleToggleAutoScroll}
            >
              {autoScroll ? 'Disable Auto-scroll' : 'Enable Auto-scroll'}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportLogs}
              disabled={logs.length === 0}
            >
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearLogs}
              disabled={logs.length === 0}
            >
              Clear
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-4 pt-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="px-3 py-2 border border-input rounded-md text-sm"
            >
              <option value="ALL">All Levels</option>
              <option value="DEBUG">Debug</option>
              <option value="INFO">Info</option>
              <option value="WARNING">Warning</option>
              <option value="ERROR">Error</option>
            </select>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div 
          ref={containerRef}
          className="h-96 overflow-y-auto bg-black text-green-400 font-mono text-sm p-4 space-y-1"
          style={{ scrollBehavior: 'smooth' }}
        >
          {filteredLogs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              {isRunning ? (
                <div className="flex items-center justify-center space-x-2">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Waiting for logs...</span>
                </div>
              ) : (
                <span>No logs available. Start a job to see real-time logs.</span>
              )}
            </div>
          ) : (
            filteredLogs.map((log, index) => (
              <div key={`${log.id}-${index}`} className="flex items-start space-x-3 py-1">
                <span className="text-gray-400 text-xs whitespace-nowrap">
                  {format(new Date(log.timestamp), 'HH:mm:ss.SSS')}
                </span>
                
                <Badge 
                  variant={getLevelBadgeVariant(log.level)} 
                  className="text-xs min-w-fit"
                >
                  {log.level}
                </Badge>
                
                <div className="flex-1 min-w-0">
                  <div className={`whitespace-pre-wrap break-words ${getLevelColor(log.level)}`}>
                    {log.message}
                  </div>
                  
                  {log.context && (
                    <details className="mt-1">
                      <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-300">
                        Context
                      </summary>
                      <pre className="text-xs text-gray-500 mt-1 pl-4 border-l border-gray-700">
                        {JSON.stringify(log.context, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
        
        {/* Status Bar */}
        <div className="flex items-center justify-between px-4 py-2 bg-muted/50 text-xs text-muted-foreground border-t">
          <div className="flex items-center space-x-4">
            <span>{filteredLogs.length} log entries</span>
            {searchTerm && (
              <span>Filtered by: "{searchTerm}"</span>
            )}
            {levelFilter !== "ALL" && (
              <span>Level: {levelFilter}</span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}