'use client';

/**
 * Custom hook for Output Generation WebSocket connection
 *
 * Provides real-time updates for output generation (mindmaps, summaries, etc.),
 * streaming node/edge additions as they are generated.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { getWebSocketUrl, OutputWebSocketEvent, MindmapNode, MindmapEdge } from '@/lib/api';

export interface UseOutputWebSocketOptions {
  projectId: string;
  taskId?: string | null;
  enabled?: boolean;
  onNodeAdded?: (nodeId: string, nodeData: MindmapNode) => void;
  onEdgeAdded?: (edgeId: string, edgeData: MindmapEdge) => void;
  onProgress?: (progress: number, message?: string) => void;
  onGenerationStarted?: (outputType: string) => void;
  onGenerationComplete?: (message?: string) => void;
  onGenerationError?: (error: string) => void;
  onLevelComplete?: (currentLevel: number, totalLevels: number) => void;
  onConnectionStatusChange?: (
    status: 'connecting' | 'connected' | 'disconnected' | 'error'
  ) => void;
}

export interface UseOutputWebSocketReturn {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  reconnect: () => void;
  disconnect: () => void;
}

export function useOutputWebSocket(
  options: UseOutputWebSocketOptions
): UseOutputWebSocketReturn {
  const { projectId, taskId, enabled = true } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    'connecting' | 'connected' | 'disconnected' | 'error'
  >('disconnected');

  // Store callbacks in refs to avoid reconnection on callback changes
  const callbacksRef = useRef(options);
  callbacksRef.current = options;

  // Cleanup function
  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!projectId || !enabled) return;

    cleanup();

    // Build URL with optional task_id query param
    let wsUrl = `${getWebSocketUrl()}/ws/projects/${projectId}/outputs`;
    if (taskId) {
      wsUrl += `?task_id=${taskId}`;
    }
    console.log('[Output WS] Connecting to:', wsUrl);

    setConnectionStatus('connecting');
    callbacksRef.current.onConnectionStatusChange?.('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[Output WS] Connected');
        setConnectionStatus('connected');
        callbacksRef.current.onConnectionStatusChange?.('connected');

        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000); // Ping every 30 seconds
      };

      ws.onmessage = (event) => {
        // Handle pong response
        if (event.data === 'pong') {
          console.debug('[Output WS] Pong received');
          return;
        }

        try {
          const data: OutputWebSocketEvent = JSON.parse(event.data);
          console.log('[Output WS] Event:', data.type, data);

          // Use current callbacks from ref
          const callbacks = callbacksRef.current;

          switch (data.type) {
            case 'generation_started':
              callbacks.onGenerationStarted?.(data.outputType || 'unknown');
              break;

            case 'generation_progress':
              callbacks.onProgress?.(data.progress || 0, data.message);
              break;

            case 'node_added':
              if (data.nodeId && data.nodeData) {
                callbacks.onNodeAdded?.(data.nodeId, data.nodeData as MindmapNode);
              }
              break;

            case 'edge_added':
              if (data.edgeId && data.edgeData) {
                callbacks.onEdgeAdded?.(data.edgeId, data.edgeData as MindmapEdge);
              }
              break;

            case 'level_complete':
              if (data.currentLevel !== undefined && data.totalLevels !== undefined) {
                callbacks.onLevelComplete?.(data.currentLevel, data.totalLevels);
              }
              break;

            case 'generation_complete':
              callbacks.onGenerationComplete?.(data.message);
              break;

            case 'generation_error':
              callbacks.onGenerationError?.(data.errorMessage || 'Unknown error');
              break;
          }
        } catch (e) {
          console.error('[Output WS] Failed to parse message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[Output WS] Error:', error);
        setConnectionStatus('error');
        callbacksRef.current.onConnectionStatusChange?.('error');
      };

      ws.onclose = (event) => {
        console.log('[Output WS] Disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        callbacksRef.current.onConnectionStatusChange?.('disconnected');

        // Auto-reconnect after 5 seconds (unless manually disconnected)
        if (enabled && event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[Output WS] Attempting to reconnect...');
            connect();
          }, 5000);
        }
      };
    } catch (error) {
      console.error('[Output WS] Failed to create WebSocket:', error);
      setConnectionStatus('error');
      callbacksRef.current.onConnectionStatusChange?.('error');
    }
  }, [projectId, taskId, enabled, cleanup]);

  // Reconnect function
  const reconnect = useCallback(() => {
    console.log('[Output WS] Manual reconnect requested');
    connect();
  }, [connect]);

  // Disconnect function
  const disconnect = useCallback(() => {
    console.log('[Output WS] Manual disconnect requested');
    cleanup();
    setConnectionStatus('disconnected');
    callbacksRef.current.onConnectionStatusChange?.('disconnected');
  }, [cleanup]);

  // Connect on mount and when projectId/taskId changes
  useEffect(() => {
    if (enabled && projectId) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [projectId, taskId, enabled]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    reconnect,
    disconnect,
  };
}

export default useOutputWebSocket;

