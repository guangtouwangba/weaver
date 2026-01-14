/**
 * useCanvasAgent - Hook for AI-generated canvas commands
 * 
 * Parses AI responses for slash commands and manages pending actions
 * that require user confirmation.
 */

import { useState, useCallback } from 'react';
import { parseCommand, isCommand } from '@/lib/commandParser';
import { CanvasAction } from '@/lib/canvasActions';
import { useCanvasDispatch } from './useCanvasDispatch';

// ============================================================================
// Types
// ============================================================================

export interface PendingAction {
  id: string;
  command: string;
  action: CanvasAction;
  description: string;
  status: 'pending' | 'executed' | 'rejected';
}

interface UseCanvasAgentResult {
  /** List of pending actions awaiting user confirmation */
  pendingActions: PendingAction[];
  /** Parse AI response and extract commands */
  parseAIResponse: (response: string) => PendingAction[];
  /** Execute a specific pending action */
  executeAction: (actionId: string) => boolean;
  /** Execute all pending actions */
  executeAllActions: () => { success: number; failed: number };
  /** Reject/dismiss a pending action */
  rejectAction: (actionId: string) => void;
  /** Clear all pending actions */
  clearPendingActions: () => void;
  /** Check if there are any pending actions */
  hasPendingActions: boolean;
}

// ============================================================================
// Command Extraction
// ============================================================================

/**
 * Extract slash commands from AI response text
 * Supports commands in inline code blocks or plain text
 */
function extractCommands(text: string): string[] {
  const commands: string[] = [];
  
  // Match commands in inline code blocks: `/<command>`
  const codeBlockRegex = /`(\/[a-z-]+[^`]*)`/gi;
  let match;
  while ((match = codeBlockRegex.exec(text)) !== null) {
    commands.push(match[1].trim());
  }
  
  // Match standalone commands at start of line
  const lineRegex = /^(\/[a-z-]+.*?)$/gm;
  while ((match = lineRegex.exec(text)) !== null) {
    const cmd = match[1].trim();
    // Avoid duplicates from code blocks
    if (!commands.includes(cmd)) {
      commands.push(cmd);
    }
  }
  
  return commands;
}

/**
 * Generate a human-readable description for an action
 */
function describeAction(action: CanvasAction): string {
  switch (action.type) {
    case 'addNode':
      return `Add node: "${action.payload.content || action.payload.title || 'New note'}"`;
    case 'deleteNode':
      return `Delete node: ${action.payload.nodeId}`;
    case 'deleteNodes':
      return `Delete ${action.payload.nodeIds.length} nodes`;
    case 'updateNode':
      return `Update node: ${action.payload.nodeId}`;
    case 'moveNode':
      return `Move node to (${action.payload.x}, ${action.payload.y})`;
    case 'addEdge':
      return `Connect: ${action.payload.source} → ${action.payload.target}${action.payload.label ? ` (${action.payload.label})` : ''}`;
    case 'deleteEdge':
      return `Remove connection: ${action.payload.edgeId}`;
    case 'zoomIn':
      return 'Zoom in';
    case 'zoomOut':
      return 'Zoom out';
    case 'zoomTo':
      return `Zoom to ${Math.round(action.payload.scale * 100)}%`;
    case 'fitToContent':
      return 'Fit content in view';
    case 'generateContent':
      return `Generate ${action.payload.contentType}`;
    case 'synthesizeNodes':
      return `Synthesize ${action.payload.nodeIds.length} nodes (${action.payload.mode} mode)`;
    default:
      return `Action: ${action.type}`;
  }
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useCanvasAgent(): UseCanvasAgentResult {
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const { dispatch } = useCanvasDispatch();

  const parseAIResponse = useCallback((response: string): PendingAction[] => {
    const commands = extractCommands(response);
    const newPendingActions: PendingAction[] = [];

    for (const command of commands) {
      if (!isCommand(command)) continue;

      const result = parseCommand(command);
      
      if (result.success && result.action) {
        newPendingActions.push({
          id: `action-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          command,
          action: result.action,
          description: describeAction(result.action),
          status: 'pending',
        });
      }
    }

    setPendingActions(prev => [...prev, ...newPendingActions]);
    return newPendingActions;
  }, []);

  const executeAction = useCallback((actionId: string): boolean => {
    const action = pendingActions.find(a => a.id === actionId);
    if (!action || action.status !== 'pending') {
      return false;
    }

    const result = dispatch(action.action);
    
    setPendingActions(prev =>
      prev.map(a =>
        a.id === actionId
          ? { ...a, status: result.success ? 'executed' : 'rejected' }
          : a
      )
    );

    return result.success;
  }, [pendingActions, dispatch]);

  const executeAllActions = useCallback((): { success: number; failed: number } => {
    let success = 0;
    let failed = 0;

    const pending = pendingActions.filter(a => a.status === 'pending');
    
    for (const action of pending) {
      const result = dispatch(action.action);
      if (result.success) {
        success++;
      } else {
        failed++;
      }
    }

    // Update all statuses
    setPendingActions(prev =>
      prev.map(a => {
        if (a.status !== 'pending') return a;
        const result = dispatch(a.action);
        return { ...a, status: result.success ? 'executed' : 'rejected' };
      })
    );

    return { success, failed };
  }, [pendingActions, dispatch]);

  const rejectAction = useCallback((actionId: string) => {
    setPendingActions(prev =>
      prev.map(a =>
        a.id === actionId ? { ...a, status: 'rejected' } : a
      )
    );
  }, []);

  const clearPendingActions = useCallback(() => {
    setPendingActions([]);
  }, []);

  return {
    pendingActions,
    parseAIResponse,
    executeAction,
    executeAllActions,
    rejectAction,
    clearPendingActions,
    hasPendingActions: pendingActions.some(a => a.status === 'pending'),
  };
}
