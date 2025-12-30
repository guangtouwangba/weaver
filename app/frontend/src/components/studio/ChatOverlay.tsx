'use client';

import { useState } from 'react';
import { 
  Box, 
  TextField,
  IconButton,
  Typography,
  Chip,
  CircularProgress,
} from "@mui/material";
import { 
  AutoAwesomeIcon,
  ArrowUpwardIcon,
  MessageSquareIcon,
} from '@/components/ui/icons';
import { useStudio } from '@/contexts/StudioContext';

interface ChatOverlayProps {
  onSendMessage: (message: string) => void;
}

export default function ChatOverlay({ onSendMessage }: ChatOverlayProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { activeSessionId, chatSessions } = useStudio();
  const activeSession = chatSessions.find(s => s.id === activeSessionId);

  const handleSend = async () => {
    if (input.trim() && !isLoading) {
      setIsLoading(true);
      try {
        await onSendMessage(input);
        setInput('');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        width: '100%',
        maxWidth: 600,
        px: 2,
      }}
    >
      {/* Main Input Container with Purple Border */}
      <Box
        sx={{
          border: '1px solid',
          borderColor: 'rgba(139, 92, 246, 0.3)',
          borderRadius: 3,
          bgcolor: '#fff',
          p: 2.5,
          transition: 'all 0.2s ease',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        }}
      >
        {/* Context Label and Chips */}
        {activeSessionId && activeSession && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
            <Typography
              variant="caption"
              sx={{
                color: 'text.secondary',
                fontSize: '0.75rem',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              CONTEXT:
            </Typography>
            <Chip
              label={activeSession.title.length > 25 ? activeSession.title.substring(0, 25) + '...' : activeSession.title}
              icon={<MessageSquareIcon size={12} sx={{ color: 'rgba(139, 92, 246, 0.8)' }} />}
              size="small"
              sx={{
                bgcolor: 'rgba(139, 92, 246, 0.1)',
                color: 'rgba(139, 92, 246, 0.9)',
                border: 'none',
                height: 24,
                fontSize: '0.75rem',
                fontWeight: 500,
              }}
            />
          </Box>
        )}

        {/* Input Field with Sparkle Icon */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            bgcolor: '#F9FAFB',
            borderRadius: 2,
            px: 2,
            py: 1.5,
            border: '1px solid',
            borderColor: 'rgba(0, 0, 0, 0.05)',
          }}
        >
          <AutoAwesomeIcon size={18} sx={{ color: 'rgba(139, 92, 246, 0.8)', flexShrink: 0 }} />
          <TextField
            fullWidth
            placeholder="Ask a follow-up question or drag a new resource..."
            variant="standard"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={isLoading}
            InputProps={{
              disableUnderline: true,
              style: {
                fontSize: 14,
                color: '#1F2937',
              }
            }}
            sx={{
              '& .MuiInputBase-input::placeholder': {
                color: '#9CA3AF',
                opacity: 1,
              }
            }}
          />
          {isLoading ? (
            <CircularProgress size={18} sx={{ color: 'rgba(139, 92, 246, 0.8)', flexShrink: 0 }} />
          ) : (
            <IconButton
              onClick={handleSend}
              disabled={!input.trim()}
              sx={{
                bgcolor: 'rgba(139, 92, 246, 1)',
                color: '#fff',
                width: 36,
                height: 36,
                borderRadius: 1.5,
                flexShrink: 0,
                '&:hover': {
                  bgcolor: 'rgba(139, 92, 246, 0.9)',
                },
                '&:disabled': {
                  bgcolor: 'rgba(139, 92, 246, 0.3)',
                  color: 'rgba(255, 255, 255, 0.5)',
                },
              }}
            >
              <ArrowUpwardIcon size={18} />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Status Text */}
      <Box sx={{ textAlign: 'center', mt: 2 }}>
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            fontSize: '0.7rem',
            fontWeight: 400,
          }}
        >
          Thinking Mode Active, • Results are generated by AI.
        </Typography>
      </Box>
    </Box>
  );
}

