'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  IconButton, 
  TextField,
  Tooltip,
  CircularProgress,
  Button,
} from "@mui/material";
import { 
  Bot,
  PanelRightClose,
  PanelRightOpen,
  Send,
  Link as LinkIcon,
  Plus
} from "lucide-react";
import { useStudio } from '@/contexts/StudioContext';
import { chatApi } from '@/lib/api';

interface AssistantPanelProps {
  visible: boolean;
  width: number;
  onToggle: () => void;
}

export default function AssistantPanel({ visible, width, onToggle }: AssistantPanelProps) {
  const { projectId, chatMessages, setChatMessages, activeDocumentId, addNodeToCanvas } = useStudio();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToBottom, [chatMessages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMsg = {
        id: Date.now().toString(),
        role: 'user' as const,
        content: input,
        timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
        // Prepare AI message placeholder
        const aiMsgId = (Date.now() + 1).toString();
        setChatMessages(prev => [...prev, {
            id: aiMsgId,
            role: 'ai',
            content: '',
            timestamp: new Date()
        }]);

        // Stream response
        // Note: chatApi.stream is an async generator
        for await (const chunk of chatApi.stream(projectId, { message: userMsg.content, document_id: activeDocumentId || undefined })) {
            if (chunk.type === 'token') {
                setChatMessages(prev => prev.map(m => 
                    m.id === aiMsgId ? { ...m, content: m.content + (chunk.content || '') } : m
                ));
            } else if (chunk.type === 'sources') {
                setChatMessages(prev => prev.map(m => 
                    m.id === aiMsgId ? { ...m, sources: chunk.sources } : m
                ));
            }
        }
    } catch (err) {
        console.error("Chat error:", err);
        // Add error message
        setChatMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'ai',
            content: 'Sorry, I encountered an error processing your request.',
            timestamp: new Date()
        }]);
    } finally {
        setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleAddToCanvas = (content: string, sourceId?: string) => {
    addNodeToCanvas({
      type: 'card',
      title: 'AI Insight',
      content: content,
      x: 100, // Default position, will be adjusted by user or improved logic
      y: 100,
      width: 280,
      height: 200,
      color: 'blue',
      tags: ['#ai'],
      sourceId: sourceId
    });
  };

  if (!visible) {
    return (
      <Box sx={{ width: 40, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: '#FAFAFA' }}>
        <Box sx={{ height: 48, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
          <Tooltip title="Expand (⌘.)" placement="right">
            <IconButton onClick={onToggle} size="small"><PanelRightOpen size={18} /></IconButton>
          </Tooltip>
        </Box>
        <Box sx={{ py: 2 }}>
          <Tooltip title="AI Assistant" placement="right">
            <Box sx={{ p: 1, borderRadius: 1, bgcolor: '#ECFDF5', cursor: 'pointer' }} onClick={onToggle}>
              <Bot size={16} className="text-emerald-600" />
            </Box>
          </Tooltip>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ width, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', bgcolor: '#FAFAFA', overflow: 'hidden' }}>
      {/* Header */}
      <Box 
        sx={{ 
            height: 48, 
            borderBottom: '1px solid', borderColor: 'divider', 
            display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#10B981' }} />
          <Typography variant="subtitle2" color="text.secondary">Assistant</Typography>
        </Box>
        <Tooltip title="Collapse (⌘.)"><IconButton size="small" onClick={onToggle}><PanelRightClose size={14} /></IconButton></Tooltip>
      </Box>
      
      {/* Messages */}
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {chatMessages.map((msg) => (
          <Box key={msg.id} sx={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '90%' }}>
            <Paper 
                elevation={0} 
                sx={{ 
                    p: 2, 
                    borderRadius: 2, 
                    bgcolor: msg.role === 'user' ? '#EBF5FF' : '#fff',
                    border: msg.role === 'ai' ? '1px solid #E5E7EB' : 'none',
                    color: msg.role === 'user' ? '#1E40AF' : 'text.primary'
                }}
            >
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.content}</Typography>
              
              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <Box sx={{ mt: 2, pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ mb: 1, display: 'block' }}>Sources:</Typography>
                    {msg.sources.map((source, idx) => (
                        <Box key={idx} sx={{ display: 'flex', gap: 1, mb: 1, p: 1, bgcolor: '#F9FAFB', borderRadius: 1, fontSize: 11 }}>
                            <LinkIcon size={12} className="text-gray-400 flex-shrink-0 mt-0.5" />
                            <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.4 }}>
                                "...{source.snippet.slice(0, 100)}..." (Page {source.page_number})
                            </Typography>
                        </Box>
                    ))}
                </Box>
              )}

              {/* Action Buttons for AI messages */}
              {msg.role === 'ai' && (
                  <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                      <Button 
                        size="small" 
                        startIcon={<Plus size={12} />} 
                        onClick={() => handleAddToCanvas(msg.content)}
                        sx={{ fontSize: 10, textTransform: 'none', color: 'text.secondary' }}
                      >
                        Add to Canvas
                      </Button>
                  </Box>
              )}
            </Paper>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>
      
      {/* Input */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#fff' }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', bgcolor: '#F3F4F6', borderRadius: 2, px: 2, py: 1 }}>
          <TextField 
            fullWidth 
            placeholder="Ask about this document..." 
            variant="standard" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            InputProps={{ disableUnderline: true, style: { fontSize: 14 } }} 
          />
          {isLoading ? (
            <CircularProgress size={16} />
          ) : (
            <IconButton size="small" color="primary" onClick={handleSend} disabled={!input.trim()}><Send size={16} /></IconButton>
          )}
        </Box>
      </Box>
    </Box>
  );
}
