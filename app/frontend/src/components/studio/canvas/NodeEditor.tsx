'use client';

import React, { useState, useEffect, useRef } from 'react';
import { TextField as UiTextField } from '@/components/ui/composites';
import { Surface, Stack, IconButton } from '@/components/ui';
import { colors } from '@/components/ui/tokens';
import { CheckIcon, CloseIcon } from '@/components/ui/icons';
import { CanvasNode } from '@/lib/api';

interface NodeEditorProps {
    node: CanvasNode;
    viewport: { x: number; y: number; scale: number };
    onSave: (nodeId: string, updates: { title: string; content: string }) => void;
    onCancel: () => void;
}

export default function NodeEditor({ node, viewport, onSave, onCancel }: NodeEditorProps) {
    // Initialize state from props. The key prop on the parent usage should handle resetting state when node changes.
    // However, if we want to be safe without relying on key, we can use an effect, but we must avoid the lint error.
    // The previous implementation used an effect to sync props to state which caused the error.
    // A better pattern is to use a key on the component instance in the parent.
    // Assuming the parent handles key={node.id}, we can just initialize state.
    const [title, setTitle] = useState(node.title || '');
    const [content, setContent] = useState(node.content || '');
    const titleInputRef = useRef<HTMLInputElement>(null);
    const [prevNodeId, setPrevNodeId] = useState(node.id);

    // Sync state if node prop changes (pattern: derived state with mirroring)
    if (node.id !== prevNodeId) {
        setTitle(node.title || '');
        setContent(node.content || '');
        setPrevNodeId(node.id);
    }

    useEffect(() => {
        // Focus title input on mount
        if (titleInputRef.current) {
            titleInputRef.current.focus();
        }
    }, []);

    const handleSave = () => {
        onSave(node.id, { title, content });
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        e.stopPropagation(); // Prevent canvas hotkeys

        // Save on Ctrl+Enter or Cmd+Enter
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            handleSave();
            return;
        }

        // Cancel on Esc
        if (e.key === 'Escape') {
            onCancel();
            return;
        }
    };

    // Calculate screen position
    const screenX = node.x * viewport.scale + viewport.x;
    const screenY = node.y * viewport.scale + viewport.y;
    const width = (node.width || 280) * viewport.scale;
    const height = (node.height || 200) * viewport.scale;

    // Font sizes scaled
    const titleFontSize = Math.max(14 * viewport.scale, 12);
    const contentFontSize = Math.max(12 * viewport.scale, 10);

    return (
        <Surface
            elevation={4}
            radius="lg"
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
            style={{
                position: 'absolute',
                top: screenY,
                left: screenX,
                width: width,
                height: height,
                zIndex: 2000,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                border: `2px solid ${colors.primary[500]}`,
                animation: 'fadeIn 0.1s ease-out',
            }}
        >
            {/* Header / Title */}
            <Stack
                direction="row"
                gap={1}
                style={{
                    padding: 8,
                    borderBottom: `1px solid ${colors.border.default}`,
                    backgroundColor: colors.background.subtle,
                }}
            >
                <UiTextField
                    ref={titleInputRef}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Title"
                    fullWidth
                    style={{ border: 'none', padding: 0, backgroundColor: 'transparent', boxShadow: 'none' }}
                    inputStyle={{ fontSize: titleFontSize, fontWeight: 700, padding: 0 }}
                />
            </Stack>

            {/* Content */}
            <div style={{ padding: 8, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                <UiTextField
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Content..."
                    multiline
                    fullWidth
                    minRows={3}
                    style={{ flexGrow: 1, border: 'none', padding: 0, backgroundColor: 'transparent', boxShadow: 'none' }}
                    inputStyle={{ fontSize: contentFontSize, lineHeight: 1.5, height: '100%', padding: 0, resize: 'none' }}
                />
            </div>

            {/* Actions Footer */}
            <Stack
                direction="row"
                justify="end"
                gap={1}
                style={{
                    padding: 8,
                    backgroundColor: colors.background.subtle,
                    borderTop: `1px solid ${colors.border.default}`,
                }}
            >
                <IconButton
                    size="sm"
                    variant="ghost"
                    onClick={onCancel}
                    style={{ color: colors.text.secondary, width: 24, height: 24 }}
                >
                    <CloseIcon size={16} />
                </IconButton>
                <IconButton
                    size="sm"
                    onClick={handleSave}
                    style={{
                        backgroundColor: colors.primary[500],
                        color: 'white',
                        width: 24,
                        height: 24,
                    }}
                >
                    <CheckIcon size={16} />
                </IconButton>
            </Stack>
            <style>{`
                @keyframes fadeIn {
                    from { opacity: 0; transform: scale(0.95); }
                    to { opacity: 1; transform: scale(1); }
                }
            `}</style>
        </Surface>
    );
}
