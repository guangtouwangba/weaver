'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { ToastItem, Toast } from '@/components/ui';

// =============================================================================
// Types
// =============================================================================

interface NotificationContextValue {
  notifications: Toast[];
  showNotification: (notification: Omit<Toast, 'id'>) => string;
  hideNotification: (id: string) => void;
  updateNotification: (id: string, updates: Partial<Omit<Toast, 'id'>>) => void;
  // Convenience methods
  success: (title: string, message?: string) => string;
  error: (title: string, message?: string) => string;
  info: (title: string, message?: string) => string;
  loading: (title: string, message?: string) => string;
}

// =============================================================================
// Context
// =============================================================================

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function useNotification(): NotificationContextValue {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
}

// =============================================================================
// Toast Container Component
// =============================================================================

function NotificationContainer({ notifications, onClose }: { notifications: Toast[]; onClose: (id: string) => void }) {
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
        {notifications.map((notification) => (
          <ToastItem key={notification.id} toast={notification} onClose={() => onClose(notification.id)} />
        ))}
      </div>
    </>,
    document.body
  );
}

// =============================================================================
// Provider
// =============================================================================

let notificationIdCounter = 0;

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Toast[]>([]);

  const showNotification = useCallback((notification: Omit<Toast, 'id'>) => {
    const id = `notification-${++notificationIdCounter}`;
    const newNotification: Toast = { ...notification, id };

    setNotifications((prev) => [...prev, newNotification]);

    // Auto-hide after duration (default 5s, 0 = persistent)
    const duration = notification.duration ?? (notification.type === 'loading' ? 0 : 5000);
    if (duration > 0) {
      setTimeout(() => {
        setNotifications((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }

    return id;
  }, []);

  const hideNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const updateNotification = useCallback((id: string, updates: Partial<Omit<Toast, 'id'>>) => {
    setNotifications((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...updates } : t))
    );

    // If updating to non-loading type, set auto-hide
    if (updates.type && updates.type !== 'loading') {
      const duration = updates.duration ?? 5000;
      if (duration > 0) {
        setTimeout(() => {
          setNotifications((prev) => prev.filter((t) => t.id !== id));
        }, duration);
      }
    }
  }, []);

  // Convenience methods
  const success = useCallback(
    (title: string, message?: string) => showNotification({ type: 'success', title, message }),
    [showNotification]
  );

  const error = useCallback(
    (title: string, message?: string) => showNotification({ type: 'error', title, message }),
    [showNotification]
  );

  const info = useCallback(
    (title: string, message?: string) => showNotification({ type: 'info', title, message }),
    [showNotification]
  );

  const loading = useCallback(
    (title: string, message?: string) => showNotification({ type: 'loading', title, message, duration: 0 }),
    [showNotification]
  );

  const value: NotificationContextValue = {
    notifications,
    showNotification,
    hideNotification,
    updateNotification,
    success,
    error,
    info,
    loading,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationContainer notifications={notifications} onClose={hideNotification} />
    </NotificationContext.Provider>
  );
}
