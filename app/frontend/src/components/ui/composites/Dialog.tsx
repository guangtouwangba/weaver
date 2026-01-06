'use client';

import React from 'react';
import { Modal, Stack, Text, IconButton, Button } from '@/components/ui'; // Check if Button is exported from ui root
import { CloseIcon } from '@/components/ui/icons';
import { colors } from '@/components/ui/tokens';

/**
 * Dialog Component
 *
 * Modal dialog with consistent styling.
 * Re-implemented using design system primitives (Modal).
 */

export interface DialogProps {
    /** Dialog title */
    title?: React.ReactNode;
    /** Dialog body content */
    children?: React.ReactNode;
    /** Footer actions */
    actions?: React.ReactNode;
    /** Whether to show close button */
    showCloseButton?: boolean;
    /** Close handler */
    onClose: () => void;
    /** Dialog size */
    size?: 'sm' | 'md' | 'lg' | 'xl';
    /** Whether the dialog is open */
    open: boolean;
}

export const Dialog = React.forwardRef<HTMLDivElement, DialogProps>(
    function Dialog(
        {
            title,
            children,
            actions,
            showCloseButton = true,
            onClose,
            size = 'md',
            open,
        },
        ref
    ) {
        return (
            <Modal
                open={open}
                onClose={onClose}
                size={size}
                showCloseButton={false} // We implement our own header
            >
                {/* Header */}
                {(title || showCloseButton) && (
                    <Stack
                        direction="row"
                        justify="between"
                        align="center"
                        style={{
                            padding: '16px 24px',
                            borderBottom: `1px solid ${colors.border.default}`,
                        }}
                    >
                        {title && (
                            <Text variant="h5" color="primary">
                                {title}
                            </Text>
                        )}
                        {!title && <div />}
                        {showCloseButton && (
                            <IconButton
                                size="sm"
                                variant="ghost"
                                onClick={onClose}
                                aria-label="Close"
                            >
                                <CloseIcon size={16} />
                            </IconButton>
                        )}
                    </Stack>
                )}

                {/* Content */}
                {children && (
                    <div style={{ padding: 24 }}>
                        {children}
                    </div>
                )}

                {/* Actions */}
                {actions && (
                    <div
                        style={{
                            padding: '16px 24px',
                            borderTop: `1px solid ${colors.border.default}`,
                            display: 'flex',
                            justifyContent: 'flex-end',
                            gap: 16,
                        }}
                    >
                        {actions}
                    </div>
                )}
            </Modal>
        );
    }
);

Dialog.displayName = 'Dialog';

export default Dialog;
