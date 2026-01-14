'use client';

/**
 * Custom hook for Canvas WebSocket connection
 *
 * Provides real-time updates for:
 * - Multi-client canvas synchronization
 * - Node/edge update notifications
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import {
  getAuthenticatedWebSocketUrl,
  CanvasWebSocketEvent,
  CanvasNode,
  CanvasEdge,
  CanvasSection,
} from '@/lib/api';

export interface UseCanvasWebSocketOptions {
  projectId: string;
  enabled?: boolean;
  onNodeAdded?: (
    nodeId: string,
    nodeData: Partial<CanvasNode>,
    messageIds?: string[]
  ) => void;
  onNodeUpdated?: (nodeId: string, nodeData: Partial<CanvasNode>) => void;
  onNodeDeleted?: (nodeId: string) => void;
  onEdgeAdded?: (
    edgeId: string,
    sourceId: string,
    targetId: string,
    edgeData?: Partial<CanvasEdge>
  ) => void;
  onBatchUpdate?: (
    nodes: CanvasNode[],
    edges: CanvasEdge[],
    sections?: CanvasSection[]
  ) => void;
  onConnectionStatusChange?: (
    status: 'connecting' | 'connected' | 'disconnected' | 'error'
  ) => void;
}

export interface UseCanvasWebSocketReturn {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  reconnect: () => void;
  disconnect: () => void;
}

export function useCanvasWebSocket(
  options: UseCanvasWebSocketOptions
): UseCanvasWebSocketReturn {
  const { projectId, enabled = true } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<
    'connecting' | 'connected' | 'disconnected' | 'error'
  >('disconnected');

  // Store callbacks in refs to avoid reconnection on callback changes
  const callbacksRef = useRef(options);

  useEffect(() => {
    callbacksRef.current = options;
  });

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

  // Use a ref for the connect function to allow recursive calls in onclose
  const connectRef = useRef<(() => Promise<void>) | null>(null);

  // Connect to WebSocket - only depends on projectId and enabled
  const connect = useCallback(async () => {
    if (!projectId || !enabled) return;

    cleanup();

    const wsUrl = await getAuthenticatedWebSocketUrl(
      `/ws/projects/${projectId}/canvas`
    );
    console.log('[Canvas WS] Connecting to:', wsUrl);

    setConnectionStatus('connecting');
    callbacksRef.current.onConnectionStatusChange?.('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[Canvas WS] Connected');
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
          console.debug('[Canvas WS] Pong received');
          return;
        }

        try {
          const data: CanvasWebSocketEvent = JSON.parse(event.data);
          console.log('[Canvas WS] Event:', data.type, data);

          // Use current callbacks from ref
          const callbacks = callbacksRef.current;

          switch (data.type) {
            case 'node_added':
              if (data.node_id && data.node_data) {
                callbacks.onNodeAdded?.(
                  data.node_id,
                  data.node_data,
                  data.message_ids
                );
              }
              break;

            case 'node_updated':
              if (data.node_id && data.node_data) {
                callbacks.onNodeUpdated?.(data.node_id, data.node_data);
              }
              break;

            case 'node_deleted':
              if (data.node_id) {
                callbacks.onNodeDeleted?.(data.node_id);
              }
              break;

            case 'edge_added':
              // eslint-disable-next-line @typescript-eslint/ban-ts-comment
              // @ts-ignore
              if (data.edge_id && data.source_id && data.target_id) {
                callbacks.onEdgeAdded?.(
                  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                  // @ts-ignore
                  data.edge_id,
                  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                  // @ts-ignore
                  data.source_id,
                  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                  // @ts-ignore
                  data.target_id,
                  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                  // @ts-ignore
                  data.edge_data
                );
              }
              break;

            case 'canvas_batch_update':
              callbacks.onBatchUpdate?.(
                data.nodes || [],
                data.edges || [],
                data.sections
              );
              break;

            default:
              console.log('[Canvas WS] Unknown event type:', data.type);
          }
        } catch (e) {
          console.error('[Canvas WS] Failed to parse message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[Canvas WS] Error:', error);
        setConnectionStatus('error');
        callbacksRef.current.onConnectionStatusChange?.('error');
      };

      ws.onclose = (event) => {
        console.log('[Canvas WS] Disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        callbacksRef.current.onConnectionStatusChange?.('disconnected');

        // Auto-reconnect after 5 seconds (unless manually disconnected)
        if (enabled && event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[Canvas WS] Attempting to reconnect...');
            if (connectRef.current) {
              connectRef.current();
            }
          }, 5000);
        }
      };
    } catch (error) {
      console.error('[Canvas WS] Failed to create WebSocket:', error);
      setConnectionStatus('error');
      callbacksRef.current.onConnectionStatusChange?.('error');
    }
  }, [projectId, enabled, cleanup]);

  // Update ref when connect changes
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // Reconnect function
  const reconnect = useCallback(() => {
    console.log('[Canvas WS] Manual reconnect requested');
    connect();
  }, [connect]);

  // Disconnect function
  const disconnect = useCallback(() => {
    console.log('[Canvas WS] Manual disconnect requested');
    cleanup();
    setConnectionStatus('disconnected');
    callbacksRef.current.onConnectionStatusChange?.('disconnected');
  }, [cleanup]);

  // Connect on mount and when projectId changes
  useEffect(() => {
    if (enabled && projectId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      connect();
    }

    return () => {
      cleanup();
    };
  }, [projectId, enabled, connect, cleanup]);

  return {
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    reconnect,
    disconnect,
  };
}

export default useCanvasWebSocket;
