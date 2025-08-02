'use client'

import React, { useMemo, useCallback, useRef, useEffect } from 'react'
import { FixedSizeList as List } from 'react-window'
import { Badge } from '@/components/ui/badge'
import { formatTime } from '@/lib/utils'
import type { LogEntry } from '@/lib/api'

interface VirtualLogViewerProps {
  logs: LogEntry[]
  height: number
  itemHeight?: number
  autoScroll?: boolean
  onScrollToBottom?: () => void
}

interface LogItemProps {
  index: number
  style: React.CSSProperties
  data: {
    logs: LogEntry[]
    getLevelColor: (level: string) => string
    getLevelBadgeVariant: (level: string) => 'default' | 'secondary' | 'destructive'
  }
}

const LogItem: React.FC<LogItemProps> = ({ index, style, data }) => {
  const { logs, getLevelColor, getLevelBadgeVariant } = data
  const log = logs[index]

  if (!log) return null

  return (
    <div style={style} className="flex items-start space-x-3 py-1 px-4 font-mono text-sm">
      <span className="text-gray-400 text-xs whitespace-nowrap min-w-fit">
        {formatTime(log.timestamp)}
      </span>
      
      <Badge 
        variant={getLevelBadgeVariant(log.level)} 
        className="text-xs min-w-fit shrink-0"
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
  )
}

export const VirtualLogViewer: React.FC<VirtualLogViewerProps> = ({
  logs,
  height,
  itemHeight = 40,
  autoScroll = true,
  onScrollToBottom
}) => {
  const listRef = useRef<List>(null)
  const shouldAutoScrollRef = useRef(autoScroll)

  // Update auto-scroll preference
  useEffect(() => {
    shouldAutoScrollRef.current = autoScroll
  }, [autoScroll])

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (shouldAutoScrollRef.current && logs.length > 0 && listRef.current) {
      listRef.current.scrollToItem(logs.length - 1, 'end')
    }
  }, [logs.length])

  const getLevelColor = useCallback((level: string) => {
    switch (level) {
      case 'DEBUG': return 'text-gray-500'
      case 'INFO': return 'text-blue-400'
      case 'WARNING': return 'text-yellow-400'
      case 'ERROR': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }, [])

  const getLevelBadgeVariant = useCallback((level: string) => {
    switch (level) {
      case 'DEBUG': return 'secondary' as const
      case 'INFO': return 'default' as const
      case 'WARNING': return 'secondary' as const
      case 'ERROR': return 'destructive' as const
      default: return 'secondary' as const
    }
  }, [])

  const itemData = useMemo(() => ({
    logs,
    getLevelColor,
    getLevelBadgeVariant
  }), [logs, getLevelColor, getLevelBadgeVariant])

  const handleScroll = useCallback(({ scrollOffset, scrollUpdateWasRequested }) => {
    if (!scrollUpdateWasRequested) {
      const maxScroll = Math.max(0, (logs.length * itemHeight) - height)
      const isAtBottom = scrollOffset >= maxScroll - 50 // 50px threshold
      
      if (isAtBottom) {
        onScrollToBottom?.()
      }
    }
  }, [logs.length, itemHeight, height, onScrollToBottom])

  if (logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <div className="text-lg mb-2">No logs available</div>
          <div className="text-sm">Logs will appear here when the job runs</div>
        </div>
      </div>
    )
  }

  return (
    <List
      ref={listRef}
      height={height}
      width="100%"
      itemCount={logs.length}
      itemSize={itemHeight}
      itemData={itemData}
      onScroll={handleScroll}
      className="bg-black text-green-400"
    >
      {LogItem}
    </List>
  )
}