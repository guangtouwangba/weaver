import React, { ReactNode } from 'react';
import { CloseIcon, CheckCircleIcon, ErrorIcon, InfoIcon } from '@/components/ui/icons';
import { colors } from '@/components/ui/tokens';

export type ToastType = 'success' | 'error' | 'info' | 'loading';

export interface Toast {
    id: string;
    type: ToastType;
    title: string;
    message?: string;
    duration?: number; // 0 = persistent (for loading)
}

const toastStyles: Record<ToastType, { bg: string; border: string; icon: ReactNode }> = {
    success: {
        bg: '#ECFDF5',
        border: '#10B981',
        icon: <CheckCircleIcon size={20} style={{ color: '#10B981' }} />,
    },
    error: {
        bg: '#FEF2F2',
        border: '#EF4444',
        icon: <ErrorIcon size={20} style={{ color: '#EF4444' }} />,
    },
    info: {
        bg: '#EFF6FF',
        border: '#3B82F6',
        icon: <InfoIcon size={20} style={{ color: '#3B82F6' }} />,
    },
    loading: {
        bg: '#F5F3FF',
        border: '#8B5CF6',
        icon: (
            <div
                style={{
                    width: 20,
                    height: 20,
                    border: '2px solid #E9D5FF',
                    borderTopColor: '#8B5CF6',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                }}
            />
        ),
    },
};

export function ToastItem({
    toast,
    onClose,
}: {
    toast: Toast;
    onClose: () => void;
}) {
    const style = toastStyles[toast.type];

    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                padding: '12px 16px',
                backgroundColor: style.bg,
                borderLeft: `4px solid ${style.border}`,
                borderRadius: 8,
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                minWidth: 300,
                maxWidth: 400,
                animation: 'slideIn 0.3s ease-out',
            }}
        >
            <div style={{ flexShrink: 0, marginTop: 2 }}>{style.icon}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
                <div
                    style={{
                        fontWeight: 600,
                        fontSize: 14,
                        color: colors.text.primary,
                        marginBottom: toast.message ? 4 : 0,
                    }}
                >
                    {toast.title}
                </div>
                {toast.message && (
                    <div
                        style={{
                            fontSize: 13,
                            color: colors.text.secondary,
                            lineHeight: 1.4,
                        }}
                    >
                        {toast.message}
                    </div>
                )}
            </div>
            {toast.type !== 'loading' && (
                <button
                    onClick={onClose}
                    style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: 4,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: colors.text.secondary,
                        borderRadius: 4,
                        transition: 'background 0.2s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(0,0,0,0.05)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
                >
                    <CloseIcon size={16} />
                </button>
            )}
        </div>
    );
}
