'use client';

/**
 * ThinkingIndicator Component
 * 
 * Displays real-time AI processing status during chat response generation.
 * Shows animated states for different processing steps (rewriting, retrieving, etc.)
 * 
 * macOS-inspired design with smooth animations and subtle visual feedback.
 */

import { useEffect, useState, useRef } from 'react';
import { Stack, Text } from '@/components/ui';
import { colors } from '@/components/ui/tokens';

// Processing step configuration
const STEP_CONFIG: Record<string, { 
  icon: string; 
  label: string;
  color: string;
}> = {
  rewriting: {
    icon: '✨',
    label: 'Refining question',
    color: colors.primary[500],
  },
  memory: {
    icon: '🧠',
    label: 'Recalling context',
    color: colors.info[500],
  },
  analyzing: {
    icon: '🔍',
    label: 'Understanding intent',
    color: colors.primary[400],
  },
  retrieving: {
    icon: '📚',
    label: 'Searching knowledge',
    color: colors.success[500],
  },
  ranking: {
    icon: '📊',
    label: 'Ranking results',
    color: colors.warning[500],
  },
  generating: {
    icon: '💭',
    label: 'Generating response',
    color: colors.primary[500],
  },
};

interface ThinkingIndicatorProps {
  step?: string;
  message?: string;
  isActive?: boolean;
}

export default function ThinkingIndicator({ 
  step, 
  message, 
  isActive = true 
}: ThinkingIndicatorProps) {
  const [dots, setDots] = useState('');
  const [showTransition, setShowTransition] = useState(false);
  const prevStepRef = useRef<string | undefined>(step);
  
  // Animate dots
  useEffect(() => {
    if (!isActive) return;
    
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 400);
    
    return () => clearInterval(interval);
  }, [isActive]);
  
  // Trigger transition animation when step changes
  useEffect(() => {
    if (prevStepRef.current !== step && step) {
      setShowTransition(true);
      const timeout = setTimeout(() => setShowTransition(false), 300);
      prevStepRef.current = step;
      return () => clearTimeout(timeout);
    }
  }, [step]);
  
  if (!isActive) return null;
  
  const config = step ? STEP_CONFIG[step] : null;
  const displayMessage = message || config?.label || 'Thinking';
  const displayIcon = config?.icon || '🤔';
  const accentColor = config?.color || colors.primary[500];
  
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 12px',
        borderRadius: 20,
        background: `linear-gradient(135deg, ${colors.primary[50]} 0%, ${colors.neutral[50]} 100%)`,
        border: `1px solid ${colors.primary[100]}`,
        boxShadow: '0 2px 8px rgba(124, 58, 237, 0.08)',
        transform: showTransition ? 'scale(1.02)' : 'scale(1)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        overflow: 'hidden',
      }}
    >
      {/* Animated Icon */}
      <span
        style={{
          fontSize: 14,
          animation: 'pulse-gentle 2s ease-in-out infinite',
          display: 'inline-block',
        }}
      >
        {displayIcon}
      </span>
      
      {/* Status Text */}
      <Text
        variant="caption"
        style={{
          color: colors.neutral[600],
          fontWeight: 500,
          whiteSpace: 'nowrap',
        }}
      >
        {displayMessage}
        <span style={{ 
          color: accentColor,
          fontWeight: 600,
          minWidth: 20,
          display: 'inline-block',
        }}>
          {dots}
        </span>
      </Text>
      
      {/* Animated Progress Bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 2,
          background: colors.primary[100],
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: '30%',
            background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
            animation: 'thinking-shimmer 1.5s ease-in-out infinite',
          }}
        />
      </div>
      
      {/* CSS Keyframes */}
      <style jsx>{`
        @keyframes pulse-gentle {
          0%, 100% { 
            opacity: 1;
            transform: scale(1);
          }
          50% { 
            opacity: 0.7;
            transform: scale(1.1);
          }
        }
        
        @keyframes thinking-shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(400%); }
        }
      `}</style>
    </div>
  );
}

/**
 * Compact inline version for message bubbles
 */
export function ThinkingIndicatorInline({ 
  step,
  message,
}: { 
  step?: string;
  message?: string;
}) {
  const config = step ? STEP_CONFIG[step] : null;
  const displayMessage = message || config?.label || 'Thinking';
  
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        color: colors.neutral[500],
        fontSize: 14,
      }}
    >
      <span
        style={{
          display: 'inline-flex',
          gap: 3,
        }}
      >
        <span style={{ animation: 'bounce-dot 1.4s ease-in-out infinite', animationDelay: '0s' }}>•</span>
        <span style={{ animation: 'bounce-dot 1.4s ease-in-out infinite', animationDelay: '0.2s' }}>•</span>
        <span style={{ animation: 'bounce-dot 1.4s ease-in-out infinite', animationDelay: '0.4s' }}>•</span>
      </span>
      <span style={{ opacity: 0.8 }}>{displayMessage}</span>
      
      <style jsx>{`
        @keyframes bounce-dot {
          0%, 80%, 100% { 
            transform: translateY(0);
            opacity: 0.4;
          }
          40% { 
            transform: translateY(-4px);
            opacity: 1;
          }
        }
      `}</style>
    </span>
  );
}

