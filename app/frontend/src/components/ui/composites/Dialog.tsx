'use client';

import React from 'react';
import {
    Dialog as MuiDialog,
    DialogProps as MuiDialogProps,
    DialogTitle,
    DialogContent,
    DialogActions,
} from '@mui/material';
import { Stack, Text, IconButton } from '../primitives';
import { CloseIcon } from '../icons';
import { colors, radii, shadows } from '../tokens';

/**
 * Dialog Component
 *
 * Modal dialog with consistent styling.
 * Wraps MUI Dialog with design system tokens.
 */

export interface DialogProps extends Omit<MuiDialogProps, 'title'> {
    /** Dialog title */
    title?: React.ReactNode;
    /** Dialog body content */
    children?: React.ReactNode;
    /** Footer actions */
    actions?: React.ReactNode;
    /** Whether to show close button */
    showCloseButton?: boolean;
    /** Close handler */
    onClose?: () => void;
    /** Dialog size */
    size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeMap = {
    sm: 400,
    md: 560,
    lg: 720,
    xl: 960,
};

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
            ...props
        },
        ref
    ) {
        return (
            <MuiDialog
                ref={ref}
                open={open}
                onClose={onClose}
                PaperProps={{
                    sx: {
                        width: '100%',
                        maxWidth: sizeMap[size],
                        borderRadius: `${radii.xl}px`,
                        boxShadow: shadows.xl,
                    },
                }}
                {...props}
            >
                {(title || showCloseButton) && (
                    <DialogTitle sx={{ p: 0 }}>
                        <Stack
                            direction="row"
                            justify="between"
                            align="center"
                            sx={{ px: 3, py: 2.5, borderBottom: `1px solid ${colors.border.default}` }}
                        >
                            {title && (
                                <Text variant="h5" color="primary">
                                    {title}
                                </Text>
                            )}
                            {showCloseButton && (
                                <IconButton
                                    size="sm"
                                    variant="ghost"
                                    onClick={onClose}
                                    aria-label="Close"
                                >
                                    <CloseIcon size="sm" />
                                </IconButton>
                            )}
                        </Stack>
                    </DialogTitle>
                )}

                {children && (
                    <DialogContent sx={{ px: 3, py: 3 }}>
                        {children}
                    </DialogContent>
                )}

                {actions && (
                    <DialogActions sx={{ px: 3, py: 2, borderTop: `1px solid ${colors.border.default}` }}>
                        <Stack direction="row" gap={2} justify="end">
                            {actions}
                        </Stack>
                    </DialogActions>
                )}
            </MuiDialog>
        );
    }
);

Dialog.displayName = 'Dialog';

export default Dialog;
