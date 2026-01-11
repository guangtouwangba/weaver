'use client';

import React from 'react';
import { Dialog, Button, Text } from '@/components/ui';

export interface ConfirmDialogProps {
    /** Whether the dialog is open */
    open: boolean;
    /** Close handler */
    onClose: () => void;
    /** Confirm handler (can be async) */
    onConfirm: () => void | Promise<void>;
    /** Dialog title */
    title: string;
    /** Description message */
    message: string;
    /** Label for the confirm button */
    confirmLabel?: string;
    /** Label for the cancel button */
    cancelLabel?: string;
    /** Whether to use the danger variant for the confirm button */
    isDanger?: boolean;
    /** Whether an action is currently in progress */
    loading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
    open,
    onClose,
    onConfirm,
    title,
    message,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    isDanger = true,
    loading = false,
}) => {
    const handleConfirm = async () => {
        await onConfirm();
    };

    return (
        <Dialog
            open={open}
            onClose={onClose}
            title={title}
            size="sm"
            actions={
                <>
                    <Button
                        variant="ghost"
                        onClick={onClose}
                        disabled={loading}
                    >
                        {cancelLabel}
                    </Button>
                    <Button
                        variant={isDanger ? 'danger' : 'primary'}
                        onClick={handleConfirm}
                        loading={loading}
                    >
                        {confirmLabel}
                    </Button>
                </>
            }
        >
            <div style={{ padding: 24 }}>
                <Text variant="body" color="secondary">
                    {message}
                </Text>
            </div>
        </Dialog>
    );
};

export default ConfirmDialog;
