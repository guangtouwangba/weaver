'use client';

import { useState, useCallback } from 'react';
import {
  Stack,
  Surface,
  IconButton,
  Spinner,
} from '@/components/ui';
import { colors, radii, fontSize } from '@/components/ui/tokens';
import {
  AutoAwesomeIcon,
  ArrowUpwardIcon,
} from '@/components/ui/icons';
import { isCommand, parseCommand } from '@/lib/commandParser';
import { useCanvasDispatch } from '@/hooks/useCanvasDispatch';
import CommandPalette from './CommandPalette';

interface ChatOverlayProps {
  onSendMessage: (message: string) => void;
}

export default function ChatOverlay({ onSendMessage }: ChatOverlayProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);
  const { dispatch } = useCanvasDispatch();

  // Handle command execution
  const executeCommand = useCallback((commandInput: string) => {
    const result = parseCommand(commandInput);
    
    if (!result.success) {
      // Show error feedback
      setCommandFeedback(result.error || 'Invalid command');
      setTimeout(() => setCommandFeedback(null), 3000);
      return false;
    }
    
    if (result.action) {
      // Execute the action
      const actionResult = dispatch(result.action);
      if (actionResult.success) {
        setCommandFeedback(`✓ Command executed: ${result.action.type}`);
      } else {
        setCommandFeedback(`✗ ${actionResult.error}`);
      }
      setTimeout(() => setCommandFeedback(null), 2000);
      return true;
    } else if (result.error) {
      // Help text - show as feedback
      setCommandFeedback(result.error);
      setTimeout(() => setCommandFeedback(null), 5000);
      return true;
    }
    
    return false;
  }, [dispatch]);

  const handleSend = async () => {
    if (input.trim() && !isLoading) {
      // Check if this is a slash command
      if (isCommand(input)) {
        const executed = executeCommand(input);
        if (executed) {
          setInput('');
          setShowCommandPalette(false);
          return;
        }
        // If command failed to execute, don't send as chat message
        return;
      }
      
      // Regular chat message
      setIsLoading(true);
      try {
        await onSendMessage(input);
        setInput('');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInput(value);
    
    // Show command palette when typing /
    if (value === '/' || (value.startsWith('/') && !value.includes(' '))) {
      setShowCommandPalette(true);
    } else if (!value.startsWith('/')) {
      setShowCommandPalette(false);
    }
  };

  const handleCommandSelect = (command: string) => {
    setInput(command);
    setShowCommandPalette(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    // Let command palette handle its own keys when open
    if (showCommandPalette && ['ArrowUp', 'ArrowDown', 'Tab'].includes(e.key)) {
      return; // CommandPalette handles these
    }
    
    if (e.key === 'Escape') {
      setShowCommandPalette(false);
      return;
    }
    
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        width: '100%',
        maxWidth: 600,
        paddingLeft: 16,
        paddingRight: 16,
      }}
    >
      {/* Command Palette - positioned above the input */}
      {showCommandPalette && (
        <div style={{ position: 'relative', marginBottom: 8 }}>
          <CommandPalette
            input={input}
            onSelect={handleCommandSelect}
            onClose={() => setShowCommandPalette(false)}
          />
        </div>
      )}

      {/* Main Input Container with Purple Border */}
      <Surface
        elevation={2}
        style={{
          borderRadius: radii.lg,
          border: '1px solid rgba(139, 92, 246, 0.3)',
          padding: 20,
        }}
      >
        {/* Input Field with Sparkle Icon */}
        <Stack
          direction="row"
          align="center"
          gap={1}
          style={{
            backgroundColor: colors.background.subtle,
            borderRadius: radii.lg,
            paddingLeft: 16,
            paddingRight: 16,
            paddingTop: 12,
            paddingBottom: 12,
            border: `1px solid ${colors.border.muted}`,
          }}
        >
          <AutoAwesomeIcon size={18} style={{ color: 'rgba(139, 92, 246, 0.8)', flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Ask a question or type / for commands..."
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            disabled={isLoading}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              background: 'transparent',
              fontSize: fontSize.sm,
              color: colors.text.primary,
            }}
          />
          {isLoading ? (
            <Spinner size="sm" color="primary" />
          ) : (
            <IconButton
              size="sm"
              onClick={handleSend}
              disabled={!input.trim()}
              style={{
                backgroundColor: 'rgba(139, 92, 246, 1)',
                color: '#fff',
                borderRadius: radii.md,
                cursor: !input.trim() ? 'default' : 'pointer',
                opacity: !input.trim() ? 0.5 : 1,
              }}
            >
              <ArrowUpwardIcon size={18} />
            </IconButton>
          )}
        </Stack>

        {/* Command Feedback */}
        {commandFeedback && (
          <div
            style={{
              marginTop: 8,
              padding: '8px 12px',
              backgroundColor: commandFeedback.startsWith('✓') 
                ? 'rgba(34, 197, 94, 0.1)' 
                : commandFeedback.startsWith('✗')
                ? 'rgba(239, 68, 68, 0.1)'
                : 'rgba(139, 92, 246, 0.1)',
              borderRadius: radii.md,
              fontSize: fontSize.xs,
              color: commandFeedback.startsWith('✓')
                ? colors.success[600]
                : commandFeedback.startsWith('✗')
                ? colors.error[600]
                : colors.text.secondary,
              whiteSpace: 'pre-wrap',
            }}
          >
            {commandFeedback}
          </div>
        )}
      </Surface>

      {/* Status Text */}
      <div style={{ textAlign: 'center', marginTop: 16 }}>
        <Text variant="caption" color="secondary" style={{ fontSize: '0.7rem' }}>
          Type / for commands • Results are generated by AI
        </Text>
      </div>
    </div>
  );
}
