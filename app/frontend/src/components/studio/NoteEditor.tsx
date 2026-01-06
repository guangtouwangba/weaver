'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { colors, radii, shadows, fontSize, fontWeight, spacing } from '@/components/ui/tokens';

export interface NoteData {
    id?: string;
    title: string;
    content: string;
}

interface NoteEditorProps {
    /** Initial note data for editing, or undefined for new note */
    initialData?: NoteData;
    /** Called when the editor should close and save */
    onSave: (data: NoteData) => void;
    /** Called when the editor is cancelled (no save) */
    onCancel: () => void;
    /** Position for the resulting note card on canvas */
    position?: { x: number; y: number };
}

/**
 * NoteEditor - A modal for creating/editing notes.
 * Auto-saves when clicking outside (blur behavior).
 */
export default function NoteEditor({
    initialData,
    onSave,
    onCancel,
}: NoteEditorProps) {
    const [title, setTitle] = useState(initialData?.title || '');
    const [content, setContent] = useState(initialData?.content || '');
    const modalRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLTextAreaElement>(null);

    // Focus the content textarea on mount
    useEffect(() => {
        if (contentRef.current) {
            contentRef.current.focus();
        }
    }, []);

    const handleSave = useCallback(() => {
        // Only save if there's some content
        if (title.trim() || content.trim()) {
            onSave({
                id: initialData?.id,
                title: title.trim() || 'Untitled Note',
                content: content.trim(),
            });
        } else {
            onCancel();
        }
    }, [title, content, initialData?.id, onSave, onCancel]);

    // Handle backdrop click (auto-save on blur)
    const handleBackdropClick = useCallback((e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            handleSave();
        }
    }, [handleSave]);

    // Handle Escape key to cancel
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                handleSave(); // Save on Escape too, per auto-save philosophy
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [handleSave]);

    return (
        <div
            onClick={handleBackdropClick}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1400,
            }}
        >
            <div
                ref={modalRef}
                style={{
                    width: '100%',
                    maxWidth: 600,
                    maxHeight: '80vh',
                    backgroundColor: colors.background.paper,
                    borderRadius: radii.xl,
                    boxShadow: shadows.xl,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                }}
            >
                {/* Editor Header */}
                <div
                    style={{
                        padding: spacing[4],
                        borderBottom: `1px solid ${colors.border.default}`,
                    }}
                >
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Note Title"
                        style={{
                            width: '100%',
                            border: 'none',
                            outline: 'none',
                            fontSize: fontSize.xl,
                            fontWeight: fontWeight.semibold,
                            color: colors.text.primary,
                            backgroundColor: 'transparent',
                        }}
                    />
                </div>

                {/* Editor Content */}
                <div
                    style={{
                        flex: 1,
                        padding: spacing[4],
                        overflow: 'auto',
                    }}
                >
                    <textarea
                        ref={contentRef}
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="Start writing your note..."
                        style={{
                            width: '100%',
                            minHeight: 300,
                            border: 'none',
                            outline: 'none',
                            resize: 'none',
                            fontSize: fontSize.base,
                            lineHeight: 1.6,
                            color: colors.text.primary,
                            backgroundColor: 'transparent',
                            fontFamily: 'inherit',
                        }}
                    />
                </div>

                {/* Editor Footer / Hint */}
                <div
                    style={{
                        padding: `${spacing[2]} ${spacing[4]}`,
                        borderTop: `1px solid ${colors.border.default}`,
                        backgroundColor: colors.neutral[50],
                    }}
                >
                    <span
                        style={{
                            fontSize: fontSize.xs,
                            color: colors.text.secondary,
                        }}
                    >
                        Click outside to save • Esc to close
                    </span>
                </div>
            </div>
        </div>
    );
}
