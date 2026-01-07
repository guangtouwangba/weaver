'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { CloseIcon, CheckCircleIcon, ErrorIcon, InfoIcon } from '@/components/ui/icons';
import { colors } from '@/components/ui/tokens';

// =============================================================================
// Types
// =============================================================================

type ToastType = 'success' | 'error' | 'info' | 'loading';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number; // 0 = persistent (for loading)
}

interface ToastContextValue {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, 'id'>) => string;
  hideToast: (id: string) => void;
  updateToast: (id: string, updates: Partial<Omit<Toast, 'id'>>) => void;
  // Convenience methods
  success: (title: string, message?: string) => string;
  error: (title: string, message?: string) => string;
  info: (title: string, message?: string) => string;
  loading: (title: string, message?: string) => string;
}

// =============================================================================
// Context
// =============================================================================

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

// =============================================================================
// Toast Item Component
// =============================================================================

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

function ToastItem({
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

// =============================================================================
// Toast Container Component
// =============================================================================

function ToastContainer({ toasts, onClose }: { toasts: Toast[]; onClose: (id: string) => void }) {
  if (typeof window === 'undefined') return null;

  return createPortal(
    <>
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
          @keyframes spin {
            to {
              transform: rotate(360deg);
            }
          }
        `}
      </style>
      <div
        style={{
          position: 'fixed',
          top: 16,
          right: 16,
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={() => onClose(toast.id)} />
        ))}
      </div>
    </>,
    document.body
  );
}

// =============================================================================
// Provider
// =============================================================================

let toastIdCounter = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${++toastIdCounter}`;
    const newToast: Toast = { ...toast, id };

    setToasts((prev) => [...prev, newToast]);

    // Auto-hide after duration (default 5s, 0 = persistent)
    const duration = toast.duration ?? (toast.type === 'loading' ? 0 : 5000);
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }

    return id;
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const updateToast = useCallback((id: string, updates: Partial<Omit<Toast, 'id'>>) => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...updates } : t))
    );

    // If updating to non-loading type, set auto-hide
    if (updates.type && updates.type !== 'loading') {
      const duration = updates.duration ?? 5000;
      if (duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        }, duration);
      }
    }
  }, []);

  // Convenience methods
  const success = useCallback(
    (title: string, message?: string) => showToast({ type: 'success', title, message }),
    [showToast]
  );

  const error = useCallback(
    (title: string, message?: string) => showToast({ type: 'error', title, message }),
    [showToast]
  );

  const info = useCallback(
    (title: string, message?: string) => showToast({ type: 'info', title, message }),
    [showToast]
  );

  const loading = useCallback(
    (title: string, message?: string) => showToast({ type: 'loading', title, message, duration: 0 }),
    [showToast]
  );

  const value: ToastContextValue = {
    toasts,
    showToast,
    hideToast,
    updateToast,
    success,
    error,
    info,
    loading,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onClose={hideToast} />
    </ToastContext.Provider>
  );
}

