'use client';

import { useState, useRef, useEffect } from 'react';
import { flushSync } from 'react-dom';
import { 
  Box, 
  Typography, 
  Paper, 
  IconButton, 
  TextField,
  Tooltip,
  CircularProgress,
  Button,
  Collapse,
  Chip,
} from "@mui/material";
import { 
  Bot,
  PanelRightClose,
  PanelRightOpen,
  Send,
  Link as LinkIcon,
  Plus,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useStudio } from '@/contexts/StudioContext';
import { chatApi } from '@/lib/api';

interface AssistantPanelProps {
  visible: boolean;
  width: number;
  onToggle: () => void;
}

export default function AssistantPanel({ visible, width, onToggle }: AssistantPanelProps) {
  const { projectId, chatMessages, setChatMessages, activeDocumentId, addNodeToCanvas, navigateToSource } = useStudio();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToBottom, [chatMessages]);

  const toggleSources = (msgId: string) => {
    setExpandedSources(prev => {
      const next = new Set(prev);
      if (next.has(msgId)) {
        next.delete(msgId);
      } else {
        next.add(msgId);
      }
      return next;
    });
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMsg = {
        id: Date.now().toString(),
        role: 'user' as const,
        content: input,
        timestamp: new Date()
    };
    
    const userInput = input;
    setInput('');
    setIsLoading(true);

    // Add user message
    flushSync(() => {
      setChatMessages(prev => [...prev, userMsg]);
    });

    try {
        // Prepare AI message placeholder with loading indicator
        const aiMsgId = (Date.now() + 1).toString();
        flushSync(() => {
          setChatMessages(prev => [...prev, {
              id: aiMsgId,
              role: 'ai',
              content: '',
              timestamp: new Date()
          }]);
        });

        // Stream response
        for await (const chunk of chatApi.stream(projectId, { message: userInput, document_id: activeDocumentId || undefined })) {
            if (chunk.type === 'token' && chunk.content) {
                // Use flushSync to force immediate DOM update for real-time rendering
                flushSync(() => {
                  setChatMessages(prev => prev.map(m => 
                      m.id === aiMsgId 
                        ? { ...m, content: (m.content || '') + chunk.content } 
                        : m
                  ));
                });
                // Scroll to bottom after each token
                setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 0);
            } else if (chunk.type === 'sources') {
                flushSync(() => {
                  setChatMessages(prev => prev.map(m => 
                      m.id === aiMsgId ? { ...m, sources: chunk.sources } : m
                  ));
                });
            } else if (chunk.type === 'done') {
                // Final scroll when done
                setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 0);
            } else if (chunk.type === 'error') {
                flushSync(() => {
                  setChatMessages(prev => prev.map(m => 
                      m.id === aiMsgId 
                        ? { ...m, content: (m.content || '') + `\n\n[Error: ${chunk.content || 'Unknown error'}]` } 
                        : m
                  ));
                });
            }
        }
    } catch (err) {
        console.error("Chat error:", err);
        // Update error message
        flushSync(() => {
          setChatMessages(prev => prev.map(m => 
              m.id === aiMsgId 
                ? { ...m, content: (m.content || '') + `\n\nSorry, I encountered an error: ${err instanceof Error ? err.message : 'Unknown error'}` }
                : m
          ));
        });
    } finally {
        setIsLoading(false);
        // Final scroll
        setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 0);
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
              {msg.role === 'ai' && !msg.content && isLoading ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={12} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    Thinking...
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, minHeight: '1.5em' }}>
                  {msg.content || (msg.role === 'ai' ? '...' : '')}
                </Typography>
              )}
              
              {/* Sources - Collapsible */}
              {msg.sources && msg.sources.length > 0 && (
                <Box sx={{ mt: 1.5 }}>
                  <Button
                    size="small"
                    onClick={() => toggleSources(msg.id)}
                    startIcon={<LinkIcon size={12} />}
                    endIcon={expandedSources.has(msg.id) ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                    sx={{
                      textTransform: 'none',
                      fontSize: '0.7rem',
                      color: 'text.secondary',
                      minWidth: 'auto',
                      px: 1,
                      py: 0.25,
                      borderRadius: 1,
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    {msg.sources.length} {msg.sources.length === 1 ? 'source' : 'sources'}
                  </Button>
                  
                  <Collapse in={expandedSources.has(msg.id)}>
                    <Box sx={{ mt: 1, pt: 1.5, borderTop: '1px solid', borderColor: 'divider' }}>
                      {msg.sources.map((source, idx) => (
                        <Box
                          key={idx}
                          onClick={() => navigateToSource(source.document_id, source.page_number, source.snippet)}
                          sx={{
                            display: 'flex',
                            gap: 1.5,
                            mb: 1.5,
                            p: 1.5,
                            bgcolor: '#F9FAFB',
                            borderRadius: 1.5,
                            border: '1px solid',
                            borderColor: 'divider',
                            transition: 'all 0.2s',
                            cursor: 'pointer',
                            '&:hover': {
                              bgcolor: '#F3F4F6',
                              borderColor: 'primary.light',
                              boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                            },
                            '&:last-child': {
                              mb: 0,
                            },
                          }}
                        >
                          <LinkIcon size={14} className="text-gray-400 flex-shrink-0 mt-0.5" />
                          <Box sx={{ flex: 1, minWidth: 0 }}>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{
                                lineHeight: 1.6,
                                display: 'block',
                                wordBreak: 'break-word',
                                fontSize: '0.75rem',
                              }}
                            >
                              {source.snippet}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
                              <Chip
                                label={`Page ${source.page_number}`}
                                size="small"
                                sx={{
                                  height: 20,
                                  fontSize: '0.65rem',
                                  bgcolor: 'primary.50',
                                  color: 'primary.main',
                                  fontWeight: 500,
                                }}
                              />
                              {source.similarity !== undefined && (
                                <Chip
                                  label={`${(source.similarity * 100).toFixed(0)}% match`}
                                  size="small"
                                  sx={{
                                    height: 20,
                                    fontSize: '0.65rem',
                                    bgcolor: 'grey.100',
                                    color: 'text.secondary',
                                  }}
                                />
                              )}
                            </Box>
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  </Collapse>
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
