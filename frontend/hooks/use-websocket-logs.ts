'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import type { LogEntry } from '@/lib/api'

export interface UseWebSocketLogsOptions {
  jobId: string
  enabled?: boolean
  onMessage?: (log: LogEntry) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  reconnectAttempts?: number
  reconnectInterval?: number
}

export interface UseWebSocketLogsReturn {
  isConnected: boolean
  lastMessage: LogEntry | null
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error'
  reconnectCount: number
  connect: () => void
  disconnect: () => void
}

export function useWebSocketLogs({
  jobId,
  enabled = true,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
  reconnectAttempts = 5,
  reconnectInterval = 3000
}: UseWebSocketLogsOptions): UseWebSocketLogsReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<LogEntry | null>(null)
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [reconnectCount, setReconnectCount] = useState(0)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isReconnectingRef = useRef(false)
  const mountedRef = useRef(true)

  // Clean up on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false
    }
  }, [])

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000'
    return `${protocol}//${host}/ws/cronjobs/${jobId}/logs`
  }, [jobId])

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  const disconnect = useCallback(() => {
    clearReconnectTimeout()
    isReconnectingRef.current = false
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setConnectionState('disconnected')
  }, [clearReconnectTimeout])

  const attemptReconnect = useCallback(() => {
    if (!mountedRef.current || !enabled || isReconnectingRef.current) {
      return
    }

    if (reconnectCount >= reconnectAttempts) {
      console.log('Max reconnection attempts reached')
      setConnectionState('error')
      return
    }

    isReconnectingRef.current = true
    setConnectionState('connecting')
    
    console.log(`Attempting to reconnect... (${reconnectCount + 1}/${reconnectAttempts})`)
    
    reconnectTimeoutRef.current = setTimeout(() => {
      if (mountedRef.current && enabled) {
        setReconnectCount(prev => prev + 1)
        connect()
      }
      isReconnectingRef.current = false
    }, reconnectInterval)
  }, [reconnectCount, reconnectAttempts, reconnectInterval, enabled])

  const connect = useCallback(() => {
    if (!enabled || wsRef.current) {
      return
    }

    try {
      setConnectionState('connecting')
      const wsUrl = getWebSocketUrl()
      
      console.log('Connecting to WebSocket:', wsUrl)
      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        if (!mountedRef.current) return
        
        console.log('WebSocket connected')
        setIsConnected(true)
        setConnectionState('connected')
        setReconnectCount(0)
        isReconnectingRef.current = false
        onConnect?.()
      }

      wsRef.current.onmessage = (event) => {
        if (!mountedRef.current) return
        
        try {
          const logEntry: LogEntry = JSON.parse(event.data)
          setLastMessage(logEntry)
          onMessage?.(logEntry)
        } catch (error) {
          console.error('Failed to parse log message:', error)
        }
      }

      wsRef.current.onclose = (event) => {
        if (!mountedRef.current) return
        
        console.log('WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        wsRef.current = null
        onDisconnect?.()

        // Only attempt reconnect if it wasn't a clean close and we're still enabled
        if (enabled && event.code !== 1000 && !isReconnectingRef.current) {
          attemptReconnect()
        } else {
          setConnectionState('disconnected')
        }
      }

      wsRef.current.onerror = (error) => {
        if (!mountedRef.current) return
        
        console.error('WebSocket error:', error)
        setConnectionState('error')
        onError?.(error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionState('error')
    }
  }, [enabled, getWebSocketUrl, onConnect, onMessage, onDisconnect, onError, attemptReconnect])

  // Auto-connect when enabled
  useEffect(() => {
    if (enabled && !wsRef.current) {
      connect()
    } else if (!enabled) {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [enabled, connect, disconnect])

  // Cleanup on jobId change
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [jobId, disconnect])

  return {
    isConnected,
    lastMessage,
    connectionState,
    reconnectCount,
    connect,
    disconnect
  }
}