/**
 * SourceContextPanel - Slide-out panel for viewing source references
 * 
 * Displays source references when a mindmap node is clicked for drilldown.
 * Supports multiple source types: documents (PDF), videos, audio, web links.
 */

'use client';

import React from 'react';
import { Stack, Text, IconButton, Surface, Button } from '@/components/ui/primitives';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { 
  CloseIcon, 
  DescriptionIcon,
  ExternalLinkIcon,
  LinkIcon,
} from '@/components/ui/icons';
import { Play, FileText, Globe } from 'lucide-react';
import { MindmapNode, SourceRef } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

interface SourceContextPanelProps {
  /** The node being drilled into */
  node: MindmapNode;
  /** Whether the panel is visible */
  isOpen: boolean;
  /** Called when user closes the panel */
  onClose: () => void;
  /** Called when user clicks to open a source reference */
  onOpenSource?: (sourceId: string, sourceType: string, location?: string, quote?: string) => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get icon and label for source type
 */
const getSourceTypeInfo = (sourceType: string): { icon: React.ReactNode; label: string; actionLabel: string } => {
  switch (sourceType) {
    case 'video':
      return { 
        icon: <Play size={18} />, 
        label: 'Video', 
        actionLabel: 'Play Video' 
      };
    case 'audio':
      return { 
        icon: <Play size={18} />, 
        label: 'Audio', 
        actionLabel: 'Play Audio' 
      };
    case 'web':
      return { 
        icon: <Globe size={18} />, 
        label: 'Web', 
        actionLabel: 'Visit Link' 
      };
    case 'node':
      return { 
        icon: <DescriptionIcon size={18} />, 
        label: 'Canvas Note', 
        actionLabel: 'Go to Note' 
      };
    case 'document':
    default:
      return { 
        icon: <FileText size={18} />, 
        label: 'Document', 
        actionLabel: 'Open PDF' 
      };
  }
};

/**
 * Format location for display
 */
const formatLocation = (sourceType: string, location?: string): string => {
  if (!location) return '';
  
  switch (sourceType) {
    case 'video':
    case 'audio': {
      const seconds = parseFloat(location);
      if (!isNaN(seconds)) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
      }
      return location;
    }
    case 'document':
      return `Page ${location}`;
    default:
      return location;
  }
};

// ============================================================================
// Source Reference Card
// ============================================================================

interface SourceRefCardProps {
  sourceRef: SourceRef;
  onOpen?: () => void;
}

const SourceRefCard: React.FC<SourceRefCardProps> = ({ sourceRef, onOpen }) => {
  const { icon, label, actionLabel } = getSourceTypeInfo(sourceRef.sourceType);
  const locationText = formatLocation(sourceRef.sourceType, sourceRef.location);
  
  // Truncate quote to 300 characters
  const displayQuote = sourceRef.quote.length > 300 
    ? sourceRef.quote.slice(0, 297) + '...' 
    : sourceRef.quote;

  return (
    <Surface
      elevation={0}
      style={{
        padding: 16,
        borderRadius: radii.md,
        border: `1px solid ${colors.border.default}`,
        backgroundColor: colors.background.default,
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        cursor: onOpen ? 'pointer' : 'default',
      }}
      onMouseEnter={(e) => {
        if (onOpen) {
          e.currentTarget.style.borderColor = colors.primary[300];
          e.currentTarget.style.boxShadow = shadows.sm;
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = colors.border.default;
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Header with icon and location */}
      <Stack direction="row" align="center" justify="space-between" style={{ marginBottom: 12 }}>
        <Stack direction="row" align="center" gap={8}>
          <div style={{ 
            color: colors.primary[600],
            display: 'flex',
            alignItems: 'center',
          }}>
            {icon}
          </div>
          <Text variant="caption" fontWeight={500} style={{ color: colors.text.secondary }}>
            {label}
          </Text>
          {locationText && (
            <>
              <Text variant="caption" style={{ color: colors.text.disabled }}>•</Text>
              <Text variant="caption" style={{ color: colors.text.secondary }}>
                {locationText}
              </Text>
            </>
          )}
        </Stack>
      </Stack>

      {/* Quoted text */}
      <div
        style={{
          padding: 12,
          backgroundColor: colors.neutral[50],
          borderRadius: radii.sm,
          borderLeft: `3px solid ${colors.primary[400]}`,
          marginBottom: 12,
        }}
      >
        <Text 
          variant="body" 
          style={{ 
            color: colors.text.secondary,
            fontStyle: 'italic',
            lineHeight: 1.6,
          }}
        >
          &ldquo;{displayQuote}&rdquo;
        </Text>
      </div>

      {/* Action button */}
      {onOpen && (
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onOpen();
          }}
          style={{
            gap: 6,
            width: '100%',
          }}
        >
          <ExternalLinkIcon size={14} />
          {actionLabel}
        </Button>
      )}
    </Surface>
  );
};

// ============================================================================
// Main Component
// ============================================================================

export const SourceContextPanel: React.FC<SourceContextPanelProps> = ({
  node,
  isOpen,
  onClose,
  onOpenSource,
}) => {
  const sourceRefs = node.sourceRefs || [];
  const hasSourceRefs = sourceRefs.length > 0;

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        bottom: 0,
        width: 360,
        backgroundColor: colors.background.paper,
        borderLeft: `1px solid ${colors.border.default}`,
        boxShadow: shadows.lg,
        transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.3s ease-out',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 100,
      }}
    >
      {/* Header */}
      <Surface
        elevation={0}
        style={{
          padding: 16,
          borderBottom: `1px solid ${colors.border.default}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <Text variant="caption" style={{ color: colors.text.disabled, marginBottom: 4, display: 'block' }}>
            Source References
          </Text>
          <Text 
            variant="body" 
            fontWeight={600} 
            style={{ 
              color: colors.text.primary,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {node.label}
          </Text>
        </div>
        <IconButton size="sm" onClick={onClose}>
          <CloseIcon size={18} />
        </IconButton>
      </Surface>

      {/* Content */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
        }}
      >
        {hasSourceRefs ? (
          <Stack gap={12}>
            {sourceRefs.map((ref, index) => (
              <SourceRefCard
                key={`${ref.sourceId}-${index}`}
                sourceRef={ref}
                onOpen={onOpenSource ? () => onOpenSource(ref.sourceId, ref.sourceType, ref.location, ref.quote) : undefined}
              />
            ))}
          </Stack>
        ) : (
          /* No source refs message */
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 32,
              textAlign: 'center',
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                backgroundColor: colors.neutral[100],
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 16,
              }}
            >
              <DescriptionIcon size={24} style={{ color: colors.text.disabled }} />
            </div>
            <Text variant="body" fontWeight={500} style={{ color: colors.text.secondary, marginBottom: 8 }}>
              No Source Available
            </Text>
            <Text variant="caption" style={{ color: colors.text.disabled }}>
              This concept is synthesized from multiple sections and doesn&apos;t have a direct source reference.
            </Text>
          </div>
        )}
      </div>
    </div>
  );
};

export default SourceContextPanel;

