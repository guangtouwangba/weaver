'use client';

/**
 * ActionConfirmationPanel - UI for reviewing and confirming AI-suggested canvas actions
 * 
 * Displays pending actions in a floating panel where users can:
 * - Review each action
 * - Execute individual actions
 * - Execute all actions at once
 * - Reject/dismiss actions
 */

import React from 'react';
import { colors, radii, shadows, fontSize, fontWeight, spacing } from '@/components/ui/tokens';
import { PendingAction } from '@/hooks/useCanvasAgent';

interface ActionConfirmationPanelProps {
  /** List of pending actions to display */
  pendingActions: PendingAction[];
  /** Execute a single action */
  onExecute: (actionId: string) => void;
  /** Execute all pending actions */
  onExecuteAll: () => void;
  /** Reject/dismiss a single action */
  onReject: (actionId: string) => void;
  /** Clear all actions */
  onClear: () => void;
  /** Position of the panel */
  position?: 'bottom-right' | 'top-right' | 'bottom-left';
}

export default function ActionConfirmationPanel({
  pendingActions,
  onExecute,
  onExecuteAll,
  onReject,
  onClear,
  position = 'bottom-right',
}: ActionConfirmationPanelProps) {
  // Filter to only show pending actions
  const pending = pendingActions.filter(a => a.status === 'pending');
  const executed = pendingActions.filter(a => a.status === 'executed');
  const rejected = pendingActions.filter(a => a.status === 'rejected');

  if (pendingActions.length === 0) {
    return null;
  }

  const positionStyles = {
    'bottom-right': { bottom: 100, right: 24 },
    'top-right': { top: 80, right: 24 },
    'bottom-left': { bottom: 100, left: 24 },
  };

  return (
    <div
      style={{
        position: 'fixed',
        ...positionStyles[position],
        width: 340,
        maxHeight: 400,
        backgroundColor: colors.background.paper,
        borderRadius: radii.xl,
        boxShadow: shadows.xl,
        border: `1px solid ${colors.border.default}`,
        overflow: 'hidden',
        zIndex: 1200,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: `${spacing[3]} ${spacing[4]}`,
          borderBottom: `1px solid ${colors.border.default}`,
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing[2] }}>
          <span style={{ fontSize: '18px' }}>✨</span>
          <span style={{
            fontSize: fontSize.sm,
            fontWeight: fontWeight.semibold,
            color: colors.text.primary,
          }}>
            AI Suggested Actions
          </span>
          {pending.length > 0 && (
            <span style={{
              backgroundColor: colors.primary[500],
              color: '#fff',
              fontSize: fontSize.xs,
              fontWeight: fontWeight.medium,
              padding: `2px 8px`,
              borderRadius: radii.full,
            }}>
              {pending.length}
            </span>
          )}
        </div>
        
        <button
          onClick={onClear}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: fontSize.lg,
            color: colors.text.muted,
            padding: spacing[1],
          }}
          title="Clear all"
        >
          ×
        </button>
      </div>

      {/* Action List */}
      <div
        style={{
          maxHeight: 280,
          overflowY: 'auto',
          padding: spacing[2],
        }}
      >
        {pendingActions.map(action => (
          <ActionItem
            key={action.id}
            action={action}
            onExecute={() => onExecute(action.id)}
            onReject={() => onReject(action.id)}
          />
        ))}
      </div>

      {/* Footer with bulk actions */}
      {pending.length > 0 && (
        <div
          style={{
            padding: spacing[3],
            borderTop: `1px solid ${colors.border.default}`,
            backgroundColor: colors.neutral[50],
            display: 'flex',
            gap: spacing[2],
          }}
        >
          <button
            onClick={onExecuteAll}
            style={{
              flex: 1,
              padding: `${spacing[2]} ${spacing[3]}`,
              backgroundColor: colors.primary[500],
              color: '#fff',
              border: 'none',
              borderRadius: radii.md,
              fontSize: fontSize.sm,
              fontWeight: fontWeight.medium,
              cursor: 'pointer',
            }}
          >
            Execute All ({pending.length})
          </button>
          <button
            onClick={onClear}
            style={{
              padding: `${spacing[2]} ${spacing[3]}`,
              backgroundColor: 'transparent',
              color: colors.text.secondary,
              border: `1px solid ${colors.border.default}`,
              borderRadius: radii.md,
              fontSize: fontSize.sm,
              cursor: 'pointer',
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Summary if there are executed/rejected */}
      {pending.length === 0 && (executed.length > 0 || rejected.length > 0) && (
        <div
          style={{
            padding: spacing[3],
            borderTop: `1px solid ${colors.border.default}`,
            backgroundColor: colors.neutral[50],
            textAlign: 'center',
          }}
        >
          <span style={{ fontSize: fontSize.xs, color: colors.text.secondary }}>
            {executed.length > 0 && `✓ ${executed.length} executed`}
            {executed.length > 0 && rejected.length > 0 && ' • '}
            {rejected.length > 0 && `✗ ${rejected.length} dismissed`}
          </span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// ActionItem Component
// ============================================================================

interface ActionItemProps {
  action: PendingAction;
  onExecute: () => void;
  onReject: () => void;
}

function ActionItem({ action, onExecute, onReject }: ActionItemProps) {
  const isPending = action.status === 'pending';
  const isExecuted = action.status === 'executed';
  const isRejected = action.status === 'rejected';

  return (
    <div
      style={{
        padding: spacing[3],
        marginBottom: spacing[2],
        backgroundColor: isPending 
          ? colors.background.paper 
          : isExecuted 
          ? 'rgba(34, 197, 94, 0.05)'
          : 'rgba(156, 163, 175, 0.1)',
        borderRadius: radii.lg,
        border: `1px solid ${
          isPending 
            ? colors.border.default 
            : isExecuted 
            ? colors.success[200]
            : colors.neutral[200]
        }`,
        opacity: isPending ? 1 : 0.7,
      }}
    >
      {/* Action Description */}
      <div style={{
        fontSize: fontSize.sm,
        color: colors.text.primary,
        marginBottom: spacing[1],
        display: 'flex',
        alignItems: 'center',
        gap: spacing[2],
      }}>
        <span>
          {isExecuted ? '✓' : isRejected ? '✗' : '→'}
        </span>
        <span>{action.description}</span>
      </div>

      {/* Command Preview */}
      <div style={{
        fontFamily: 'monospace',
        fontSize: fontSize.xs,
        color: colors.text.muted,
        backgroundColor: colors.neutral[100],
        padding: `${spacing[1]} ${spacing[2]}`,
        borderRadius: radii.sm,
        marginBottom: isPending ? spacing[2] : 0,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}>
        {action.command}
      </div>

      {/* Action Buttons */}
      {isPending && (
        <div style={{ display: 'flex', gap: spacing[2] }}>
          <button
            onClick={onExecute}
            style={{
              flex: 1,
              padding: `${spacing[1]} ${spacing[2]}`,
              backgroundColor: colors.success[500],
              color: '#fff',
              border: 'none',
              borderRadius: radii.sm,
              fontSize: fontSize.xs,
              fontWeight: fontWeight.medium,
              cursor: 'pointer',
            }}
          >
            Execute
          </button>
          <button
            onClick={onReject}
            style={{
              padding: `${spacing[1]} ${spacing[2]}`,
              backgroundColor: 'transparent',
              color: colors.text.muted,
              border: `1px solid ${colors.border.default}`,
              borderRadius: radii.sm,
              fontSize: fontSize.xs,
              cursor: 'pointer',
            }}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}

