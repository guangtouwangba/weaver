'use client';

import React, { useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { colors, radii, shadows, fontWeight } from '../tokens';
import { Stack } from '../primitives/Stack';
import { Text } from '../primitives/Text';
import { IconButton } from '../primitives/IconButton';

/**
 * Modal Component
 *
 * A modal dialog for overlaying content.
 * Pure CSS implementation with React Portal.
 */

export interface ModalProps {
    /** Whether the modal is open */
    open: boolean;
    /** Callback when modal should close */
    onClose: () => void;
    /** Modal content */
    children: React.ReactNode;
    /** Size of the modal */
    size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
    /** Whether to close when clicking backdrop */
    closeOnBackdrop?: boolean;
    /** Whether to close when pressing Escape */
    closeOnEscape?: boolean;
    /** Whether to show a close button */
    showCloseButton?: boolean;
    /** Title for the modal header */
    title?: string;
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

const sizeConfig = {
    sm: { maxWidth: 400 },
    md: { maxWidth: 520 },
    lg: { maxWidth: 720 },
    xl: { maxWidth: 960 },
    full: { maxWidth: 'calc(100vw - 64px)' },
};

// Close icon SVG
const CloseIcon = () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
);

export function Modal({
    open,
    onClose,
    children,
    size = 'md',
    closeOnBackdrop = true,
    closeOnEscape = true,
    showCloseButton = false,
    title,
    className,
    style,
}: ModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);
    const config = sizeConfig[size];

    // Handle escape key
    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        if (e.key === 'Escape' && closeOnEscape) {
            onClose();
        }
    }, [closeOnEscape, onClose]);

    // Handle backdrop click
    const handleBackdropClick = (e: React.MouseEvent) => {
        if (closeOnBackdrop && e.target === e.currentTarget) {
            onClose();
        }
    };

    // Add/remove event listeners
    useEffect(() => {
        if (open) {
            document.addEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'hidden';
        }
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = '';
        };
    }, [open, handleKeyDown]);

    // Focus trap - focus modal when opened
    useEffect(() => {
        if (open && modalRef.current) {
            modalRef.current.focus();
        }
    }, [open]);

    if (!open) return null;

    // Use portal to render at document root
    if (typeof document === 'undefined') return null;

    return createPortal(
        <div
            onClick={handleBackdropClick}
            style={{
                position: 'fixed',
                inset: 0,
                zIndex: 1300,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 32,
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                backdropFilter: 'blur(4px)',
                animation: 'modalBackdropIn 0.2s ease-out',
            }}
        >
            <div
                ref={modalRef}
                tabIndex={-1}
                role="dialog"
                aria-modal="true"
                className={className}
                style={{
                    position: 'relative',
                    width: '100%',
                    maxWidth: config.maxWidth,
                    maxHeight: 'calc(100vh - 64px)',
                    backgroundColor: colors.background.paper,
                    borderRadius: radii.xl,
                    boxShadow: shadows.xl,
                    outline: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    animation: 'modalContentIn 0.2s ease-out',
                    ...style,
                }}
            >
                {/* Header with title and close button */}
                {(title || showCloseButton) && (
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '16px 24px',
                            borderBottom: `1px solid ${colors.border.default}`,
                        }}
                    >
                        {title && (
                            <Text variant="h6">{title}</Text>
                        )}
                        {!title && <div />}
                        {showCloseButton && (
                            <button
                                type="button"
                                onClick={onClose}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: 32,
                                    height: 32,
                                    padding: 0,
                                    border: 'none',
                                    borderRadius: radii.sm,
                                    backgroundColor: 'transparent',
                                    color: colors.text.secondary,
                                    cursor: 'pointer',
                                    transition: 'background-color 0.15s',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.backgroundColor = colors.neutral[100];
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.backgroundColor = 'transparent';
                                }}
                            >
                                <CloseIcon />
                            </button>
                        )}
                    </div>
                )}

                {/* Content */}
                <div style={{ flex: 1, overflow: 'auto' }}>
                    {children}
                </div>
            </div>

            <style>{`
        @keyframes modalBackdropIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes modalContentIn {
          from { 
            opacity: 0; 
            transform: scale(0.95) translateY(10px); 
          }
          to { 
            opacity: 1; 
            transform: scale(1) translateY(0); 
          }
        }
      `}</style>
        </div>,
        document.body
    );
}

// Compound components for more flexibility
export interface ModalHeaderProps {
    children: React.ReactNode;
    onClose?: () => void;
    showCloseButton?: boolean;
    style?: React.CSSProperties;
}

Modal.Header = function ModalHeader({ children, onClose, showCloseButton = true, style }: ModalHeaderProps) {
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 24px',
                borderBottom: `1px solid ${colors.border.default}`,
                ...style,
            }}
        >
            <div style={{ flex: 1 }}>{children}</div>
            {showCloseButton && onClose && (
                <button
                    type="button"
                    onClick={onClose}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 32,
                        height: 32,
                        padding: 0,
                        border: 'none',
                        borderRadius: radii.sm,
                        backgroundColor: 'transparent',
                        color: colors.text.secondary,
                        cursor: 'pointer',
                        marginLeft: 16,
                    }}
                >
                    <CloseIcon />
                </button>
            )}
        </div>
    );
};

export interface ModalContentProps {
    children: React.ReactNode;
    style?: React.CSSProperties;
}

Modal.Content = function ModalContent({ children, style }: ModalContentProps) {
    return (
        <div
            style={{
                padding: 24,
                flex: 1,
                overflow: 'auto',
                ...style,
            }}
        >
            {children}
        </div>
    );
};

export interface ModalFooterProps {
    children: React.ReactNode;
    style?: React.CSSProperties;
}

Modal.Footer = function ModalFooter({ children, style }: ModalFooterProps) {
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'flex-end',
                gap: 12,
                padding: '16px 24px',
                borderTop: `1px solid ${colors.border.default}`,
                ...style,
            }}
        >
            {children}
        </div>
    );
};

Modal.displayName = 'Modal';

export default Modal;
