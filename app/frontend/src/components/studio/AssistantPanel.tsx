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
  GripHorizontal,
} from "lucide-react";
import { useStudio } from '@/contexts/StudioContext';
import { chatApi, Citation } from '@/lib/api';

// Helper function to parse XML cite tags and render with clickable citations
function renderContentWithCitations(
  content: string,
  citations: Citation[] | undefined,
  onCitationClick: (citation: Citation) => void
): React.ReactNode {
  // If no content, return empty
  if (!content) return null;

  // Pattern to match <cite doc_id="doc_XX" quote="...">conclusion</cite>
  const citePattern = /<cite\s+doc_id="(doc_\d+)"\s+quote="([^"]+)">([^<]+)<\/cite>/g;
  
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match;
  let keyIndex = 0;

  while ((match = citePattern.exec(content)) !== null) {
    // Add text before the citation
    if (match.index > lastIndex) {
      parts.push(
        <span key={`text-${keyIndex++}`}>
          {content.slice(lastIndex, match.index)}
        </span>
      );
    }

    const docId = match[1];  // doc_01
    const quote = match[2];  // Original quote
    const conclusion = match[3];  // LLM conclusion

    // Find the matching citation with location info
    const citationData = citations?.find(c => c.doc_id === docId && c.quote === quote);

    // Render as clickable citation
    parts.push(
      <Tooltip 
        key={`cite-${keyIndex++}`}
        title={
          <Box sx={{ maxWidth: 300 }}>
            <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
              Source: {docId}
              {citationData?.page_number && ` (Page ${citationData.page_number})`}
            </Typography>
            <Typography variant="caption" sx={{ fontStyle: 'italic', display: 'block' }}>
              "{quote.length > 100 ? quote.slice(0, 100) + '...' : quote}"
            </Typography>
          </Box>
        }
      >
        <Box
          component="span"
          onClick={() => {
            if (citationData) {
              onCitationClick(citationData);
            }
          }}
          sx={{
            color: 'primary.main',
            cursor: citationData ? 'pointer' : 'default',
            textDecoration: 'underline',
            textDecorationStyle: 'dotted',
            textUnderlineOffset: '2px',
            '&:hover': {
              color: 'primary.dark',
              bgcolor: 'primary.50',
              borderRadius: '2px',
            },
          }}
        >
          {conclusion}
        </Box>
      </Tooltip>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < content.length) {
    parts.push(
      <span key={`text-${keyIndex++}`}>
        {content.slice(lastIndex)}
      </span>
    );
  }

  // If no citations found, return original content
  if (parts.length === 0) {
    return content;
  }

  return <>{parts}</>;
}

interface AssistantPanelProps {
  visible: boolean;
  width: number;
  onToggle: () => void;
}

export default function AssistantPanel({ visible, width, onToggle }: AssistantPanelProps) {
  const { projectId, chatMessages, setChatMessages, activeDocumentId, addNodeToCanvas, navigateToSource, setDragPreview, dragContentRef } = useStudio();
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
              timestamp: new Date(),
              query: userInput,
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
            } else if (chunk.type === 'citation' && chunk.data) {
                // Handle single citation event from Mega-Prompt mode
                flushSync(() => {
                  setChatMessages(prev => prev.map(m => 
                      m.id === aiMsgId 
                        ? { ...m, citations: [...(m.citations || []), chunk.data as Citation] } 
                        : m
                  ));
                });
            } else if (chunk.type === 'citations' && chunk.citations) {
                // Handle all citations at end of response
                flushSync(() => {
                  setChatMessages(prev => prev.map(m => 
                      m.id === aiMsgId 
                        ? { ...m, citations: chunk.citations } 
                        : m
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
      <Box sx={{ width: 40, height: '100vh', borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: '#FAFAFA' }}>
        <Box sx={{ height: 48, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider', flexShrink: 0 }}>
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
    <Box sx={{ width, height: '100vh', flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', bgcolor: '#FAFAFA', overflow: 'hidden' }}>
      {/* Header */}
      <Box 
        sx={{ 
            height: 48, 
            borderBottom: '1px solid', borderColor: 'divider', 
            display: 'flex', alignItems: 'center', px: 3, justifyContent: 'space-between',
            flexShrink: 0
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
              {msg.role === 'ai' && msg.content ? (
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'primary.main' }}>
                    <Bot size={14} />
                    <Typography variant="caption" fontWeight="bold">
                      AI Assistant
                    </Typography>
                  </Box>
                  {/* Drag handle - only this area is draggable to keep text selection intact */}
                  <Tooltip title="Drag answer to Canvas">
                    <IconButton
                      size="small"
                      sx={{ 
                        cursor: 'grab', 
                        color: 'text.secondary',
                        '&:hover': { color: 'text.primary', bgcolor: 'action.hover' },
                      }}
                      draggable
                      onDragStart={(e) => {
                        const selection = window.getSelection();
                        const selectedText = selection && selection.toString().trim().length > 0 
                          ? selection.toString()
                          : undefined;
                        const content = selectedText || msg.content;

                        // Cache content for drag preview
                        dragContentRef.current = content;
                        setDragPreview({ x: 0, y: 0, content });

                        const payload = {
                          type: 'ai_response',
                          content,
                          source: {
                            type: 'chat',
                            messageId: msg.id,
                            timestamp: msg.timestamp.toISOString(),
                            query: msg.query || '',
                          },
                        };

                        e.dataTransfer.effectAllowed = 'copy';
                        e.dataTransfer.setData('application/json', JSON.stringify(payload));
                        e.dataTransfer.setData('text/plain', content);
                      }}
                      onDragEnd={() => {
                        dragContentRef.current = null;
                        setDragPreview(null);
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                    >
                      <GripHorizontal size={14} />
                    </IconButton>
                  </Tooltip>
                </Box>
              ) : null}

              {msg.role === 'ai' && !msg.content && isLoading ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CircularProgress size={12} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    Thinking...
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" component="div" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, minHeight: '1.5em' }}>
                  {msg.role === 'ai' && msg.content 
                    ? renderContentWithCitations(
                        msg.content, 
                        msg.citations,
                        (citation) => {
                          // Navigate to the document and page when citation is clicked
                          if (citation.document_id && citation.page_number) {
                            navigateToSource(citation.document_id, citation.page_number, citation.quote);
                          }
                        }
                      )
                    : (msg.content || (msg.role === 'ai' ? '...' : ''))
                  }
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
