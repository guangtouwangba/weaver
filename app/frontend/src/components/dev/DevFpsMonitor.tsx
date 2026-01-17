'use client';

import {
  useEffect,
  useRef,
  useCallback,
  createContext,
  useContext,
  useState,
} from 'react';
import Stats from 'stats.js';

/**
 * FPS Monitor Context
 * Provides begin/end methods to canvas components for measuring render performance
 */
interface FpsMonitorContextType {
  isVisible: boolean;
  toggle: () => void;
  begin: () => void;
  end: () => void;
}

const FpsMonitorContext = createContext<FpsMonitorContextType>({
  isVisible: false,
  toggle: () => {},
  begin: () => {},
  end: () => {},
});

export const useFpsMonitor = () => useContext(FpsMonitorContext);

/**
 * Development-only FPS monitor provider using stats.js
 * Only renders in development mode (NODE_ENV === 'development')
 *
 * Features:
 * - Press 'F' key to toggle visibility
 * - Provides begin/end methods for canvas components to measure render cycles
 */
export function FpsMonitorProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const statsRef = useRef<Stats | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  // Initialize stats.js
  useEffect(() => {
    // Only run in development mode
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    const stats = new Stats();
    stats.showPanel(0); // 0: fps, 1: ms, 2: mb

    // Position the widget in top-left corner
    stats.dom.style.position = 'fixed';
    stats.dom.style.left = '0';
    stats.dom.style.top = '0';
    stats.dom.style.zIndex = '9999';
    stats.dom.style.display = 'none'; // Hidden by default

    document.body.appendChild(stats.dom);
    statsRef.current = stats;

    return () => {
      if (
        statsRef.current?.dom &&
        document.body.contains(statsRef.current.dom)
      ) {
        document.body.removeChild(statsRef.current.dom);
      }
    };
  }, []);

  // Keyboard toggle (F key)
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input field
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        (e.target as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      // Toggle on 'F' key (without modifiers)
      if (
        e.key.toLowerCase() === 'f' &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey
      ) {
        e.preventDefault();
        setIsVisible((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Update visibility
  useEffect(() => {
    if (statsRef.current?.dom) {
      statsRef.current.dom.style.display = isVisible ? 'block' : 'none';
    }
  }, [isVisible]);

  const toggle = useCallback(() => {
    setIsVisible((prev) => !prev);
  }, []);

  const begin = useCallback(() => {
    if (isVisible && statsRef.current) {
      statsRef.current.begin();
    }
  }, [isVisible]);

  const end = useCallback(() => {
    if (isVisible && statsRef.current) {
      statsRef.current.end();
    }
  }, [isVisible]);

  const contextValue: FpsMonitorContextType = {
    isVisible,
    toggle,
    begin,
    end,
  };

  return (
    <FpsMonitorContext.Provider value={contextValue}>
      {children}
    </FpsMonitorContext.Provider>
  );
}

/**
 * Legacy component for backward compatibility
 * Now just a wrapper that doesn't render anything (the provider handles everything)
 */
export function DevFpsMonitor() {
  return null;
}

export default FpsMonitorProvider;
