'use client';

import { useState } from 'react';
import { 
  Box, 
  Paper, 
  InputBase, 
  IconButton, 
} from "@mui/material";
import { 
  SendIcon, 
  AutoAwesomeIcon, 
  BoltIcon 
} from '@/components/ui/icons';

interface ChatOverlayProps {
  onSendMessage: (message: string) => void;
}

export default function ChatOverlay({ onSendMessage }: ChatOverlayProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
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
        bottom: 32,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 1000,
        width: '100%',
        maxWidth: 600,
        px: 2,
      }}
    >
      <Paper
        elevation={4}
        sx={{
          p: '4px 8px',
          display: 'flex',
          alignItems: 'center',
          borderRadius: 24,
          border: '1px solid',
          borderColor: 'divider',
          boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
        }}
      >
        <IconButton sx={{ p: 1, color: 'text.secondary' }}>
          <BoltIcon size="md" />
        </IconButton>
        <IconButton sx={{ p: 1, color: 'text.secondary' }}>
          <AutoAwesomeIcon size="md" />
        </IconButton>
        
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="Ask Weaver anything..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
        />
        
        <IconButton 
          onClick={handleSend}
          disabled={!input.trim()}
          sx={{ 
            p: 1, 
            color: input.trim() ? 'primary.main' : 'action.disabled' 
          }}
        >
          <SendIcon size="md" />
        </IconButton>
      </Paper>
    </Box>
  );
}

