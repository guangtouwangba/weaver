/**
 * WebSocket hook for real-time analysis progress updates
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { apiClient, AnalysisProgressMessage } from '@/lib/api'

export interface AnalysisProgress {
  step: string
  progress: number
  status: string
  message: string
  papers: any[]
  agentInsights: Record<string, any>
}

export interface UseAnalysisWebSocketOptions {
  analysisId: string | null
  onProgress?: (progress: AnalysisProgress) => void
  onPapersFound?: (papers: any[]) => void
  onAgentInsight?: (agentName: string, insight: string) => void
  onCompleted?: (results: any) => void
  onError?: (error: string) => void
  autoReconnect?: boolean
  reconnectInterval?: number
}

export interface UseAnalysisWebSocketReturn {
  isConnected: boolean
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error'
  lastMessage: AnalysisProgressMessage | null
  error: string | null
  connect: () => void
  disconnect: () => void
  sendMessage: (message: any) => void
}

export const useAnalysisWebSocket = (
  options: UseAnalysisWebSocketOptions
): UseAnalysisWebSocketReturn => {
  const {
    analysisId,
    onProgress,
    onPapersFound,
    onAgentInsight,
    onCompleted,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [lastMessage, setLastMessage] = useState<AnalysisProgressMessage | null>(null)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (!analysisId || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      setConnectionStatus('connecting')
      setError(null)

      const ws = apiClient.createAnalysisWebSocket(analysisId)
      if (!ws) {
        throw new Error('Failed to create WebSocket connection')
      }

      ws.onopen = () => {
        console.log(`Analysis WebSocket connected for analysis ${analysisId}`)
        setIsConnected(true)
        setConnectionStatus('connected')
        setError(null)
        reconnectAttemptsRef.current = 0

        // Send initial ping to confirm connection
        ws.send(JSON.stringify({ type: 'ping' }))
      }

      ws.onmessage = (event) => {
        try {
          const message: AnalysisProgressMessage = JSON.parse(event.data)
          setLastMessage(message)

          // Handle different message types
          switch (message.type) {
            case 'progress':
              if (onProgress) {
                onProgress({
                  step: message.data.step || '',
                  progress: message.data.progress || 0,
                  status: message.data.status || 'running',
                  message: message.data.message || '',
                  papers: message.data.current_papers || [],
                  agentInsights: message.data.agent_insights || {}
                })
              }
              break

            case 'papers':
              if (onPapersFound && message.data.papers) {
                onPapersFound(message.data.papers)
              }
              break

            case 'agent_insight':
              if (onAgentInsight && message.data.agent_name && message.data.insight) {
                onAgentInsight(message.data.agent_name, message.data.insight)
              }
              break

            case 'completed':
              if (onCompleted) {
                onCompleted(message.data)
              }
              break

            case 'error':
              const errorMsg = message.data.error || 'Analysis error occurred'
              setError(errorMsg)
              if (onError) {
                onError(errorMsg)
              }
              break

            case 'connected':
              console.log('Analysis WebSocket connection confirmed')
              break

            case 'pong':
              // Handle heartbeat response
              break

            default:
              console.log('Received unknown message type:', message.type)
          }
        } catch (parseError) {
          console.error('Failed to parse WebSocket message:', parseError)
          setError('Failed to parse server message')
        }
      }

      ws.onclose = (event) => {
        console.log(`Analysis WebSocket closed for analysis ${analysisId}`, event.code, event.reason)
        setIsConnected(false)
        setConnectionStatus('disconnected')

        // Attempt to reconnect if enabled and within limits
        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionStatus('error')
          setError('Maximum reconnection attempts reached')
        }
      }

      ws.onerror = (event) => {
        console.error('Analysis WebSocket error:', event)
        setConnectionStatus('error')
        setError('WebSocket connection error')
        if (onError) {
          onError('WebSocket connection error')
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      setConnectionStatus('error')
      setError(error instanceof Error ? error.message : 'Connection failed')
    }
  }, [analysisId, onProgress, onPapersFound, onAgentInsight, onCompleted, onError, autoReconnect, reconnectInterval])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setIsConnected(false)
    setConnectionStatus('disconnected')
    reconnectAttemptsRef.current = 0
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected, cannot send message')
    }
  }, [])

  // Effect to handle connection when analysisId changes
  useEffect(() => {
    if (analysisId) {
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [analysisId, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return

    const heartbeatInterval = setInterval(() => {
      sendMessage({ type: 'ping' })
    }, 30000) // Send ping every 30 seconds

    return () => clearInterval(heartbeatInterval)
  }, [isConnected, sendMessage])

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    error,
    connect,
    disconnect,
    sendMessage
  }
}