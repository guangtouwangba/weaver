'use client';

/**
 * ThinkingPathGenerator Component
 * 
 * Automatically generates thinking path nodes from chat conversations.
 * 
 * Features:
 * - WebSocket integration for real-time updates
 * - Multi-client synchronization
 * - Optimistic UI for pending nodes
 * - Node <-> Message bidirectional linking
 */

import { useCallback, useEffect, useState } from 'react';
import { Box, Chip, IconButton, Tooltip, CircularProgress } from '@mui/material';
import { Brain, RefreshCw, Link2, X, Layout, Trash2 } from 'lucide-react';
import { useStudio } from '@/contexts/StudioContext';
import useCanvasWebSocket from '@/hooks/useCanvasWebSocket';
import { CanvasNode, CanvasEdge, CanvasSection, thinkingPathApi } from '@/lib/api';
import { layoutThinkingPath } from '@/lib/layout';

interface ThinkingPathGeneratorProps {
  onStatusChange?: (status: 'idle' | 'analyzing' | 'error') => void;
}

// Pending node state (for optimistic UI)
interface PendingNode {
  messageId: string;
  tempId: string;
  status: 'pending' | 'analyzing' | 'error';
  errorMessage?: string;
}

export default function ThinkingPathGenerator({
  onStatusChange,
}: ThinkingPathGeneratorProps) {
  const {
    projectId,
    chatMessages,
    canvasNodes,
    setCanvasNodes,
    canvasEdges,
    setCanvasEdges,
    canvasSections,
    setCanvasSections,
    switchView,
    autoThinkingPathEnabled,
    clearCanvas,
    currentView,
  } = useStudio();

  const [pendingNodes, setPendingNodes] = useState<Map<string, PendingNode>>(new Map());
  const [lastProcessedMessageId, setLastProcessedMessageId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Handle node added from WebSocket
  const handleNodeAdded = useCallback(
    (nodeId: string, nodeData: Partial<CanvasNode>, messageIds?: string[]) => {
      console.log('[ThinkingPath] Node added:', nodeId, messageIds);
      
      // Remove pending node if exists
      if (messageIds?.length) {
        setPendingNodes((prev) => {
          const next = new Map(prev);
          messageIds.forEach((msgId) => next.delete(msgId));
          return next;
        });
      }

      // Add node to canvas
      const newNode: CanvasNode = {
        id: nodeId,
        type: nodeData.type || 'card',
        title: nodeData.title || '',
        content: nodeData.content || '',
        x: nodeData.x || 0,
        y: nodeData.y || 0,
        width: nodeData.width || 280,
        height: nodeData.height || 200,
        color: nodeData.color || 'blue',
        tags: nodeData.tags || ['#thinking-path'],
        viewType: 'thinking',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        ...nodeData,
      };

      setCanvasNodes((prev) => {
        // Check if node already exists
        if (prev.some((n) => n.id === nodeId)) {
          return prev;
        }
        return [...prev, newNode];
      });
    },
    [setCanvasNodes]
  );

  // Handle node updated from WebSocket
  const handleNodeUpdated = useCallback(
    (nodeId: string, nodeData: Partial<CanvasNode>) => {
      console.log('[ThinkingPath] Node updated:', nodeId);
      
      setCanvasNodes((prev) =>
        prev.map((node) =>
          node.id === nodeId
            ? { ...node, ...nodeData, updatedAt: new Date().toISOString() }
            : node
        )
      );
    },
    [setCanvasNodes]
  );

  // Handle node deleted from WebSocket
  const handleNodeDeleted = useCallback(
    (nodeId: string) => {
      console.log('[ThinkingPath] Node deleted:', nodeId);
      
      setCanvasNodes((prev) => prev.filter((node) => node.id !== nodeId));
      setCanvasEdges((prev) =>
        prev.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
      );
    },
    [setCanvasNodes, setCanvasEdges]
  );

  // Handle edge added from WebSocket
  const handleEdgeAdded = useCallback(
    (edgeId: string, sourceId: string, targetId: string) => {
      console.log('[ThinkingPath] Edge added:', edgeId);
      
      setCanvasEdges((prev) => {
        // Check if edge already exists
        if (prev.some((e) => e.id === edgeId)) {
          return prev;
        }
        return [...prev, { id: edgeId, source: sourceId, target: targetId }];
      });
    },
    [setCanvasEdges]
  );

  // Handle thinking path analyzing status
  const handleThinkingPathAnalyzing = useCallback(
    (messageId: string) => {
      console.log('[ThinkingPath] Analyzing:', messageId);
      setIsAnalyzing(true);
      onStatusChange?.('analyzing');
      
      // Add to pending nodes with analyzing status
      setPendingNodes((prev) => {
        const next = new Map(prev);
        next.set(messageId, {
          messageId,
          tempId: `temp-${messageId}`,
          status: 'analyzing',
        });
        return next;
      });
    },
    [onStatusChange]
  );

  // Handle thinking path analyzed result
  const handleThinkingPathAnalyzed = useCallback(
    (
      messageId: string,
      nodes: CanvasNode[],
      edges: CanvasEdge[],
      duplicateOf?: string
    ) => {
      console.log('[ThinkingPath] Analyzed:', messageId, nodes.length, 'nodes');
      setIsAnalyzing(false);
      onStatusChange?.('idle');
      
      // Remove pending node
      setPendingNodes((prev) => {
        const next = new Map(prev);
        next.delete(messageId);
        return next;
      });

      // Add nodes (if not already handled by individual events)
      if (nodes.length > 0) {
        setCanvasNodes((prev) => {
          const existingIds = new Set(prev.map((n) => n.id));
          const newNodes = nodes.filter((n) => !existingIds.has(n.id));
          const allNodes = [...prev, ...newNodes];

          // Apply auto-layout to thinking path nodes
          const thinkingNodes = allNodes.filter(
            (n) => n.viewType === 'thinking' || n.tags?.includes('#thinking-path')
          );
          const otherNodes = allNodes.filter(
            (n) => n.viewType !== 'thinking' && !n.tags?.includes('#thinking-path')
          );

          if (thinkingNodes.length > 0) {
            // Merge current edges with new edges for layout calculation
            // Note: using canvasEdges from closure, might be slightly stale but sufficient for layout
            const allEdges = [...canvasEdges, ...edges];
            const layoutedNodes = layoutThinkingPath(thinkingNodes, allEdges);
            return [...otherNodes, ...layoutedNodes];
          }

          return allNodes;
        });
      }

      // Add edges
      if (edges.length > 0) {
        setCanvasEdges((prev) => {
          const existingIds = new Set(prev.map((e) => e.id));
          const newEdges = edges.filter((e) => !existingIds.has(e.id));
          return [...prev, ...newEdges];
        });
      }

      // Update last processed message
      setLastProcessedMessageId(messageId);
    },
    [setCanvasNodes, setCanvasEdges, onStatusChange, canvasEdges]
  );

  // Handle thinking path error
  const handleThinkingPathError = useCallback(
    (messageId: string, error: string) => {
      console.error('[ThinkingPath] Error:', messageId, error);
      setIsAnalyzing(false);
      onStatusChange?.('error');
      
      // Update pending node with error status
      setPendingNodes((prev) => {
        const next = new Map(prev);
        const pending = next.get(messageId);
        if (pending) {
          next.set(messageId, {
            ...pending,
            status: 'error',
            errorMessage: error,
          });
        }
        return next;
      });
    },
    [onStatusChange]
  );

  // Handle batch update
  const handleBatchUpdate = useCallback(
    (nodes: CanvasNode[], edges: CanvasEdge[], sections?: CanvasSection[]) => {
      console.log('[ThinkingPath] Batch update:', nodes.length, 'nodes');
      
      // Replace thinking path nodes
      setCanvasNodes((prev) => {
        const nonThinkingNodes = prev.filter(
          (n) => n.viewType !== 'thinking' && !n.tags?.includes('#thinking-path')
        );
        
        // Run auto-layout
        const layoutedNodes = layoutThinkingPath(nodes, edges);
        return [...nonThinkingNodes, ...layoutedNodes];
      });

      // Replace edges for thinking path
      setCanvasEdges((prev) => {
        const thinkingNodeIds = new Set(nodes.map((n) => n.id));
        const nonThinkingEdges = prev.filter(
          (e) => !thinkingNodeIds.has(e.source) && !thinkingNodeIds.has(e.target)
        );
        return [...nonThinkingEdges, ...edges];
      });

      // Update sections if provided
      if (sections) {
        setCanvasSections((prev) => {
          const nonThinkingSections = prev.filter((s) => s.viewType !== 'thinking');
          return [...nonThinkingSections, ...sections];
        });
      }
    },
    [setCanvasNodes, setCanvasEdges, setCanvasSections]
  );

  // WebSocket connection
  const { isConnected, connectionStatus, reconnect } = useCanvasWebSocket({
    projectId,
    enabled: autoThinkingPathEnabled,
    onNodeAdded: handleNodeAdded,
    onNodeUpdated: handleNodeUpdated,
    onNodeDeleted: handleNodeDeleted,
    onEdgeAdded: handleEdgeAdded,
    onThinkingPathAnalyzing: handleThinkingPathAnalyzing,
    onThinkingPathAnalyzed: handleThinkingPathAnalyzed,
    onThinkingPathError: handleThinkingPathError,
    onBatchUpdate: handleBatchUpdate,
  });

  // Manual analysis trigger
  const triggerAnalysis = useCallback(async () => {
    if (!projectId || isAnalyzing) return;

    try {
      setIsAnalyzing(true);
      onStatusChange?.('analyzing');
      
      const result = await thinkingPathApi.analyze(projectId);
      console.log('[ThinkingPath] Manual analysis result:', result);
      
      if (result.error) {
        console.error('[ThinkingPath] Analysis error:', result.error);
        onStatusChange?.('error');
      } else {
        onStatusChange?.('idle');
      }
    } catch (error) {
      console.error('[ThinkingPath] Analysis failed:', error);
      onStatusChange?.('error');
    } finally {
      setIsAnalyzing(false);
    }
  }, [projectId, isAnalyzing, onStatusChange]);

  // Connection status indicator (optional, for debugging)
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  // Don't render anything if disabled
  if (!autoThinkingPathEnabled) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 16,
        right: 16,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        zIndex: 1000,
      }}
    >
      {/* Connection status */}
      <Tooltip title={`WebSocket: ${connectionStatus}`}>
        <Chip
          size="small"
          icon={<Brain size={14} />}
          label={isAnalyzing ? 'Analyzing...' : 'Auto'}
          color={getStatusColor()}
          variant="outlined"
          sx={{ opacity: 0.8 }}
        />
      </Tooltip>

      {/* Analyzing indicator */}
      {isAnalyzing && (
        <CircularProgress size={16} sx={{ ml: 1 }} />
      )}

      {/* Pending nodes count */}
      {pendingNodes.size > 0 && (
        <Chip
          size="small"
          label={`${pendingNodes.size} pending`}
          color="warning"
          variant="outlined"
        />
      )}

      {/* Reconnect button (if disconnected) */}
      {connectionStatus === 'disconnected' && (
        <Tooltip title="Reconnect WebSocket">
          <IconButton size="small" onClick={reconnect}>
            <RefreshCw size={16} />
          </IconButton>
        </Tooltip>
      )}

      {/* Manual analysis trigger */}
      <Tooltip title="Analyze conversation">
        <IconButton
          size="small"
          onClick={triggerAnalysis}
          disabled={isAnalyzing}
        >
          <Link2 size={16} />
        </IconButton>
      </Tooltip>

      {/* Re-layout trigger */}
      <Tooltip title="Re-organize Layout">
        <IconButton
          size="small"
          onClick={() => {
            setCanvasNodes((prev) => {
              const thinkingNodes = prev.filter(
                (n) => n.viewType === 'thinking' || n.tags?.includes('#thinking-path')
              );
              const otherNodes = prev.filter(
                (n) => n.viewType !== 'thinking' && !n.tags?.includes('#thinking-path')
              );
              
              if (thinkingNodes.length > 0) {
                const layoutedNodes = layoutThinkingPath(thinkingNodes, canvasEdges);
                return [...otherNodes, ...layoutedNodes];
              }
              return prev;
            });
          }}
        >
          <Layout size={16} />
        </IconButton>
      </Tooltip>

      {/* Clear Canvas button */}
      <Tooltip title={`Clear ${currentView === 'thinking' ? 'Thinking Path' : 'Free Canvas'}`}>
        <IconButton
          size="small"
          onClick={async () => {
            // Capture current view at click time to handle tab switching edge case
            const viewToClear = currentView;
            const viewName = viewToClear === 'thinking' ? 'Thinking Path' : 'Free Canvas';
            
            const confirmed = window.confirm(
              `Are you sure you want to clear all nodes from the ${viewName}? This action cannot be undone.`
            );
            if (confirmed) {
              try {
                await clearCanvas(viewToClear);
              } catch (error) {
                console.error('Failed to clear canvas:', error);
              }
            }
          }}
          sx={{ color: 'error.main' }}
        >
          <Trash2 size={16} />
        </IconButton>
      </Tooltip>
    </Box>
  );
}
