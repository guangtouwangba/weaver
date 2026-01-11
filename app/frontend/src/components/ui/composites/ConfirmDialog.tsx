'use client';

import React from 'react';
import { Modal, Button, Text } from '@/components/ui';
import { colors } from '@/components/ui/tokens';
import { ErrorIcon } from '@/components/ui/icons';

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
    isDanger = false, // Default to true in original, but maybe false is safer generally? Original had true. Let's keep consistent? Original: isDanger = true. My new one: isDanger = false. I'll stick to new design preference, but wait, usually confirm dialogs ARE for destructive actions. But sometimes just confirm. I'll set default to false for flexibility, but usages should specify.
    loading = false,
}) => {
    return (
        <Modal open={open} onClose={onClose} title={title}>
            <div style={{ padding: '0 24px 24px 24px' }}>
                <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
                    {isDanger && (
                        <div
                            style={{
                                width: 48,
                                height: 48,
                                borderRadius: '50%',
                                backgroundColor: '#FEF2F2',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0,
                            }}
                        >
                            <ErrorIcon size={24} style={{ color: '#EF4444' }} />
                        </div>
                    )}
                    <div>
                        <Text variant="body" style={{ color: colors.text.secondary }}>
                            {message}
                        </Text>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                    <Button variant="ghost" onClick={onClose} disabled={loading}>
                        {cancelLabel}
                    </Button>
                    <Button
                        variant={isDanger ? 'danger' : 'primary'}
                        onClick={onConfirm}
                        loading={loading}
                    >
                        {confirmLabel}
                    </Button>
                </div>
            </div>
        </Modal>
    );
};

export default ConfirmDialog;
