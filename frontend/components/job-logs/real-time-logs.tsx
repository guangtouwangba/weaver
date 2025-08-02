"use client"

import { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { 
  Play, 
  Pause, 
  Download, 
  Search, 
  Filter,
  RefreshCw,
  Terminal,
  ArrowDown,
  Trash2,
  WifiOff,
  Wifi
} from "lucide-react"
import { toast } from "sonner"
import { format } from "date-fns"
import { formatDateTime } from "@/lib/utils"
import { useJobLogs } from "@/lib/hooks/api-hooks"
import { useWebSocketLogs } from "@/hooks/use-websocket-logs"
import { VirtualLogViewer } from "./virtual-log-viewer"
import type { LogEntry } from "@/lib/api"

interface RealTimeLogsProps {
  jobId: string
  runId?: string
  isRunning: boolean
}

const LOG_BUFFER_SIZE = 1000 // Maximum number of logs to keep in memory

export function RealTimeLogs({ jobId, runId, isRunning }: RealTimeLogsProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [levelFilter, setLevelFilter] = useState<string>("ALL")
  const [autoScroll, setAutoScroll] = useState(true)
  const [showScrollButton, setShowScrollButton] = useState(false)
  
  const containerRef = useRef<HTMLDivElement>(null)

  // Fetch historical logs
  const { 
    data: historicalLogs, 
    error: logsError, 
    isLoading: logsLoading,
    mutate: refreshLogs
  } = useJobLogs(
    jobId,
    0,
    500, // Get last 500 historical logs
    levelFilter !== "ALL" ? levelFilter : undefined,
    searchTerm || undefined
  )

  // WebSocket connection for real-time logs
  const {
    isConnected,
    lastMessage,
    connectionState,
    reconnectCount,
    connect,
    disconnect
  } = useWebSocketLogs({
    jobId,
    enabled: isRunning && !isPaused,
    onMessage: (logEntry) => {
      setLogs(prevLogs => {
        const newLogs = [...prevLogs, logEntry]
        // Keep buffer size under control
        if (newLogs.length > LOG_BUFFER_SIZE) {
          return newLogs.slice(-LOG_BUFFER_SIZE)
        }
        return newLogs
      })
    },
    onConnect: () => {
      console.log('WebSocket connected for real-time logs')
      toast.success('Connected to live logs')
    },
    onDisconnect: () => {
      console.log('WebSocket disconnected')
    },
    onError: (error) => {
      console.error('WebSocket error:', error)
      toast.error('Connection error - retrying...')
    }
  })

  // Combine historical logs with real-time logs
  const allLogs = useMemo(() => {
    const historical = Array.isArray(historicalLogs) ? historicalLogs : []
    const realTime = Array.isArray(logs) ? logs : []
    
    // Merge and deduplicate by id, sort by timestamp
    const combined = [...historical, ...realTime]
    const uniqueLogsMap = new Map()
    
    combined.forEach(log => {
      if (log && log.id) {
        uniqueLogsMap.set(log.id, log)
      }
    })
    
    return Array.from(uniqueLogsMap.values())
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  }, [historicalLogs, logs])

  // Filter logs based on search term and level
  const filteredLogs = useMemo(() => {
    let filtered = Array.isArray(allLogs) ? allLogs : []

    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase()
      filtered = filtered.filter(log => 
        (log?.message?.toLowerCase?.() || '').includes(searchLower) ||
        (log?.context && JSON.stringify(log.context).toLowerCase().includes(searchLower))
      )
    }

    if (levelFilter !== "ALL") {
      filtered = filtered.filter(log => log?.level === levelFilter)
    }

    return filtered
  }, [allLogs, searchTerm, levelFilter])

  // Load historical logs when component mounts or filters change
  useEffect(() => {
    refreshLogs()
  }, [jobId, refreshLogs])

  const handleTogglePause = useCallback(() => {
    setIsPaused(prev => {
      const newPaused = !prev
      if (newPaused) {
        disconnect()
        toast.info('Live logs paused')
      } else {
        connect()
        toast.info('Live logs resumed')
      }
      return newPaused
    })
  }, [connect, disconnect])

  const handleToggleAutoScroll = useCallback(() => {
    setAutoScroll(prev => !prev)
  }, [])

  const handleScrollToBottom = useCallback(() => {
    // This will be handled by the VirtualLogViewer
    setShowScrollButton(false)
  }, [])

  const handleExportLogs = useCallback(() => {
    const logsText = (Array.isArray(filteredLogs) ? filteredLogs : []).map(log => 
      `[${formatDateTime(log?.timestamp || Date.now())}] ${log?.level || 'UNKNOWN'}: ${log?.message || ''}${
        log?.context ? '\n' + JSON.stringify(log.context, null, 2) : ''
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
  }, [filteredLogs, jobId])

  const handleClearLogs = useCallback(() => {
    setLogs([])
    toast.success('Real-time logs cleared')
  }, [])

  const handleRefreshLogs = useCallback(() => {
    refreshLogs()
    toast.success('Historical logs refreshed')
  }, [refreshLogs])

  // Connection status info
  const getConnectionStatusInfo = () => {
    switch (connectionState) {
      case 'connected':
        return { icon: Wifi, color: 'text-green-500', text: 'Connected' }
      case 'connecting':
        return { icon: RefreshCw, color: 'text-yellow-500', text: 'Connecting...' }
      case 'error':
        return { icon: WifiOff, color: 'text-red-500', text: 'Connection Error' }
      default:
        return { icon: WifiOff, color: 'text-gray-500', text: 'Disconnected' }
    }
  }

  const statusInfo = getConnectionStatusInfo()

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
            {connectionState === 'connecting' && (
              <Badge variant="secondary" className="text-xs">
                <RefreshCw className="w-2 h-2 mr-1 animate-spin" />
                Connecting...
              </Badge>
            )}
            {reconnectCount > 0 && (
              <Badge variant="outline" className="text-xs">
                Retry #{reconnectCount}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshLogs}
              disabled={logsLoading}
            >
              <RefreshCw className={`h-4 w-4 ${logsLoading ? 'animate-spin' : ''}`} />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleTogglePause}
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
            
            {showScrollButton && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleScrollToBottom}
              >
                <ArrowDown className="h-4 w-4" />
              </Button>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportLogs}
              disabled={filteredLogs.length === 0}
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
              <Trash2 className="h-4 w-4" />
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
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="relative">
          {logsLoading && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10">
              <div className="flex items-center space-x-2 text-white">
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Loading logs...</span>
              </div>
            </div>
          )}
          
          {logsError && (
            <div className="bg-red-900/20 border border-red-500/50 p-4 m-4 rounded">
              <div className="text-red-400 text-sm">
                Failed to load logs: {logsError.message}
              </div>
            </div>
          )}
          
          <VirtualLogViewer
            logs={filteredLogs}
            height={400}
            autoScroll={autoScroll}
            onScrollToBottom={() => setShowScrollButton(false)}
          />
        </div>
        
        {/* Status Bar */}
        <div className="flex items-center justify-between px-4 py-2 bg-muted/50 text-xs text-muted-foreground border-t">
          <div className="flex items-center space-x-4">
            <span>{filteredLogs.length} log entries ({allLogs.length} total)</span>
            {searchTerm && (
              <span>Filtered by: "{searchTerm}"</span>
            )}
            {levelFilter !== "ALL" && (
              <span>Level: {levelFilter}</span>
            )}
            {logs.length >= LOG_BUFFER_SIZE && (
              <span className="text-yellow-600">Buffer limit reached</span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <statusInfo.icon className={`w-2 h-2 ${statusInfo.color} ${connectionState === 'connecting' ? 'animate-spin' : ''}`} />
            <span>{statusInfo.text}</span>
            {isRunning && !isPaused && (
              <span className="text-green-600">• Live</span>
            )}
            {isPaused && (
              <span className="text-yellow-600">• Paused</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}