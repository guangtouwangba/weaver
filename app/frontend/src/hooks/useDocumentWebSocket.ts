'use client';

/**
 * Custom hook for Document WebSocket connection
 *
 * Provides real-time updates for document processing status,
 * replacing the previous polling mechanism.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { getWebSocketUrl, DocumentWebSocketEvent } from '@/lib/api';

export interface UseDocumentWebSocketOptions {
  projectId: string;
  enabled?: boolean;
  onDocumentStatusChange?: (event: DocumentWebSocketEvent) => void;
  onConnectionStatusChange?: (
    status: 'connecting' | 'connected' | 'disconnected' | 'error'
  ) => void;
}

export interface UseDocumentWebSocketReturn {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  reconnect: () => void;
  disconnect: () => void;
}

export function useDocumentWebSocket(
  options: UseDocumentWebSocketOptions
): UseDocumentWebSocketReturn {
  const { projectId, enabled = true } = options;

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

  // Connect to WebSocket - only depends on projectId and enabled
  const connect = useCallback(() => {
    if (!projectId || !enabled) return;

    cleanup();

    const wsUrl = `${getWebSocketUrl()}/ws/projects/${projectId}/documents`;
    console.log('[Document WS] Connecting to:', wsUrl);

    setConnectionStatus('connecting');
    callbacksRef.current.onConnectionStatusChange?.('connecting');

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[Document WS] Connected');
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
          console.debug('[Document WS] Pong received');
          return;
        }

        try {
          const data: DocumentWebSocketEvent = JSON.parse(event.data);
          console.log('[Document WS] Event:', data.type, data);

          // Use current callbacks from ref
          const callbacks = callbacksRef.current;

          if (data.type === 'document_status') {
            callbacks.onDocumentStatusChange?.(data);
          }
        } catch (e) {
          console.error('[Document WS] Failed to parse message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[Document WS] Error:', error);
        setConnectionStatus('error');
        callbacksRef.current.onConnectionStatusChange?.('error');
      };

      ws.onclose = (event) => {
        console.log('[Document WS] Disconnected:', event.code, event.reason);
        setConnectionStatus('disconnected');
        callbacksRef.current.onConnectionStatusChange?.('disconnected');

        // Auto-reconnect after 5 seconds (unless manually disconnected)
        if (enabled && event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[Document WS] Attempting to reconnect...');
            connect();
          }, 5000);
        }
      };
    } catch (error) {
      console.error('[Document WS] Failed to create WebSocket:', error);
      setConnectionStatus('error');
      callbacksRef.current.onConnectionStatusChange?.('error');
    }
  }, [projectId, enabled, cleanup]);

  // Reconnect function
  const reconnect = useCallback(() => {
    console.log('[Document WS] Manual reconnect requested');
    connect();
  }, [connect]);

  // Disconnect function
  const disconnect = useCallback(() => {
    console.log('[Document WS] Manual disconnect requested');
    cleanup();
    setConnectionStatus('disconnected');
    callbacksRef.current.onConnectionStatusChange?.('disconnected');
  }, [cleanup]);

  // Connect on mount and when projectId changes
  // Only reconnect when projectId or enabled changes, NOT when callbacks change
  useEffect(() => {
    if (enabled && projectId) {
      connect();
    }

    return () => {
      cleanup();
    };
  }, [projectId, enabled]); // Removed connect and cleanup from deps - they are stable

  return {
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    reconnect,
    disconnect,
  };
}

export default useDocumentWebSocket;















