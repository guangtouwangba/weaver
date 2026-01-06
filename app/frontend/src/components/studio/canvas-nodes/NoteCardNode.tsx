'use client';

/**
 * NoteCardNode - A compact note card on the canvas.
 * Shows title and content preview, double-click to edit.
 */

import React, { memo, useRef, useEffect } from 'react';
import { Surface, Stack, Text, IconButton } from '@/components/ui';
import { colors, radii, shadows, fontSize, fontWeight } from '@/components/ui/tokens';
import { StickyNote2Icon, OpenWithIcon, DeleteIcon, EditIcon } from '@/components/ui/icons';

interface NoteCardNodeProps {
    id: string;
    'data-node-id'?: string;
    title: string;
    content: string;
    position: { x: number; y: number };
    viewport: { x: number; y: number; scale: number };
    onEdit: () => void;
    onDelete: () => void;
    onDragStart?: (e: React.MouseEvent) => void;
    isDragging?: boolean;
    color?: string;
}

function NoteCardNodeInner({
    id,
    'data-node-id': dataNodeId,
    title,
    content,
    position,
    viewport,
    onEdit,
    onDelete,
    onDragStart,
    isDragging = false,
    color = '#fef3c7', // Default warm yellow (amber-100)
}: NoteCardNodeProps) {
    // Performance tracking
    const renderCountRef = useRef(0);
    renderCountRef.current++;

    useEffect(() => {
        if (isDragging && renderCountRef.current % 10 === 0) {
            console.log(`[Perf][NoteCardNode ${id}] Render count: ${renderCountRef.current}`);
        }
    });

    // Convert canvas coordinates to screen coordinates
    const screenX = position.x * viewport.scale + viewport.x;
    const screenY = position.y * viewport.scale + viewport.y;

    const handleMouseDown = (e: React.MouseEvent) => {
        if (e.target instanceof HTMLElement) {
            // Skip if clicking on buttons
            if (e.target.closest('button')) {
                return;
            }
            if (e.target.closest('.drag-handle')) {
                onDragStart?.(e);
            }
        }
    };

    const handleDoubleClick = () => {
        onEdit();
    };

    // Truncate content for preview
    const previewContent = content.length > 100 ? content.slice(0, 100) + '...' : content;

    return (
        <Surface
            elevation={0}
            radius="md"
            bordered
            data-node-id={dataNodeId || id}
            onMouseDown={handleMouseDown}
            onDoubleClick={handleDoubleClick}
            style={{
                position: 'absolute',
                left: screenX,
                top: screenY,
                width: 220,
                padding: 12,
                backgroundColor: color,
                boxShadow: isDragging
                    ? '0 12px 40px rgba(234, 179, 8, 0.35)'
                    : shadows.md,
                cursor: isDragging ? 'grabbing' : 'default',
                transition: isDragging ? 'none' : 'box-shadow 0.2s, transform 0.2s',
                transform: `scale(${viewport.scale > 0.5 ? 1 : viewport.scale * 2})`,
                transformOrigin: 'top left',
                zIndex: isDragging ? 1000 : 50,
                borderColor: colors.warning[300],
            }}
        >
            {/* Header Row */}
            <Stack
                direction="row"
                align="start"
                justify="between"
                style={{ marginBottom: 8 }}
            >
                {/* Drag Handle Area */}
                <Stack
                    direction="row"
                    align="center"
                    gap={1}
                    className="drag-handle"
                    style={{
                        flex: 1,
                        minWidth: 0,
                        cursor: 'grab',
                        userSelect: 'none',
                    }}
                >
                    {/* Drag Indicator */}
                    <div
                        style={{
                            padding: 2,
                            borderRadius: radii.sm,
                            color: colors.warning[600],
                        }}
                    >
                        <OpenWithIcon size={12} />
                    </div>

                    {/* Note Icon */}
                    <div
                        style={{
                            width: 24,
                            height: 24,
                            borderRadius: radii.sm,
                            backgroundColor: colors.warning[400],
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            flexShrink: 0,
                        }}
                    >
                        <StickyNote2Icon size={14} />
                    </div>

                    {/* Title */}
                    <Text
                        variant="label"
                        truncate
                        style={{
                            flex: 1,
                            marginLeft: 4,
                            fontSize: fontSize.sm,
                            fontWeight: fontWeight.semibold,
                            color: colors.warning[900],
                        }}
                    >
                        {title || 'Untitled Note'}
                    </Text>
                </Stack>

                {/* Actions */}
                <Stack direction="row" gap={0} style={{ flexShrink: 0, gap: 2 }}>
                    <IconButton size="sm" variant="ghost" onClick={onEdit} title="Edit">
                        <EditIcon size={12} style={{ color: colors.warning[700] }} />
                    </IconButton>
                    <IconButton size="sm" variant="ghost" onClick={onDelete} title="Delete">
                        <DeleteIcon size={12} style={{ color: colors.warning[700] }} />
                    </IconButton>
                </Stack>
            </Stack>

            {/* Content Preview */}
            <Text
                variant="bodySmall"
                style={{
                    fontSize: fontSize.xs,
                    lineHeight: 1.5,
                    color: colors.warning[800],
                    display: '-webkit-box',
                    WebkitLineClamp: 4,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                }}
            >
                {previewContent || 'Double-click to edit...'}
            </Text>
        </Surface>
    );
}

/**
 * Memoized NoteCardNode
 */
const NoteCardNode = memo(NoteCardNodeInner, (prevProps, nextProps) => {
    return (
        prevProps.id === nextProps.id &&
        prevProps.title === nextProps.title &&
        prevProps.content === nextProps.content &&
        prevProps.position.x === nextProps.position.x &&
        prevProps.position.y === nextProps.position.y &&
        prevProps.viewport.x === nextProps.viewport.x &&
        prevProps.viewport.y === nextProps.viewport.y &&
        prevProps.viewport.scale === nextProps.viewport.scale &&
        prevProps.isDragging === nextProps.isDragging &&
        prevProps.color === nextProps.color
    );
});

NoteCardNode.displayName = 'NoteCardNode';

export default NoteCardNode;
