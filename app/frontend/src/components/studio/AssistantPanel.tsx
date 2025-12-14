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
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Menu,
  MenuItem,
  Tabs,
  Tab,
} from "@mui/material";
import { 
  Bot,
  PanelRightClose,
  PanelRightOpen,
  Send,
  Link as LinkIcon,
  ChevronDown,
  ChevronUp,
  GripHorizontal,
  Brain,
  ExternalLink,
  Plus,
  Cloud,
  Lock,
  MessageSquare,
  MoreVertical,
  Trash2,
  Edit2,
  ChevronLeft,
  ChevronRight,
  List as ListIcon,
  History,
} from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { useStudio } from '@/contexts/StudioContext';
import { chatApi, Citation, ChatSession, ProjectDocument } from '@/lib/api';

// Helper function to clean up content before rendering
function cleanContent(content: string): string {
  if (!content) return '';
  return content
    .replace(/<document[^>]*>/g, '')
    .replace(/<\/document>/g, '')
    .replace(/document id:\s*[a-f0-9-]+/gi, '');
}

// Citation component for use with ReactMarkdown
interface CitationRendererProps {
  docId: string;
  quote: string;
  children: React.ReactNode;
  citations: Citation[] | undefined;
  documents: ProjectDocument[];
  onCitationClick: (citation: Citation) => void;
}

function CitationRenderer({ docId, quote, children, citations, documents, onCitationClick }: CitationRendererProps) {
  // Improved matching: try exact match first, then fallback to doc_id only
  let citationData = citations?.find(c => c.doc_id === docId && c.quote === quote);
  if (!citationData) {
    citationData = citations?.find(c => c.doc_id === docId);
  }
  
  // Get filename: from citation, or fallback to documents list
  const filename = citationData?.filename 
    || documents.find(d => d.id === citationData?.document_id)?.filename
    || docId;
  
  return (
    <Tooltip 
      title={
        <Box sx={{ maxWidth: 300 }}>
          <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5 }}>
            Source: {filename}
            {citationData?.page_number && ` (Page ${citationData.page_number})`}
          </Typography>
          <Typography variant="caption" sx={{ fontStyle: 'italic', display: 'block' }}>
            &ldquo;{quote.length > 100 ? quote.slice(0, 100) + '...' : quote}&rdquo;
          </Typography>
        </Box>
      }
    >
      <Box
        component="span"
        draggable
        onDragStart={(e) => {
          const payload = {
            sourceType: 'citation',
            content: `"${quote}"`,
            sourceTitle: filename,
            sourceId: citationData?.document_id,
            pageNumber: citationData?.page_number,
            tags: ['#citation']
          };
          
          e.dataTransfer.effectAllowed = 'copy';
          e.dataTransfer.setData('application/json', JSON.stringify(payload));
          e.dataTransfer.setData('text/plain', quote);
          e.stopPropagation();
        }}
        onClick={() => {
          if (citationData) {
            onCitationClick(citationData);
          }
        }}
        sx={{
          color: 'primary.main',
          cursor: 'grab',
          textDecoration: 'underline',
          textDecorationStyle: 'dotted',
          textUnderlineOffset: '2px',
          '&:hover': {
            color: 'primary.dark',
            bgcolor: 'primary.50',
            borderRadius: '2px',
          },
          '&:active': {
            cursor: 'grabbing',
          },
        }}
      >
        {children}
      </Box>
    </Tooltip>
  );
}

// Markdown content renderer with citation support
interface MarkdownContentProps {
  content: string;
  citations?: Citation[];
  documents: ProjectDocument[];
  onCitationClick: (citation: Citation) => void;
}

function MarkdownContent({ content, citations, documents, onCitationClick }: MarkdownContentProps) {
  const cleaned = cleanContent(content);
  
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        // Custom citation renderer
        cite: ({ node, ...props }) => {
          const docId = (node?.properties?.docId as string) || (node?.properties?.doc_id as string) || '';
          const quote = (node?.properties?.quote as string) || '';
          return (
            <CitationRenderer
              docId={docId}
              quote={quote}
              citations={citations}
              documents={documents}
              onCitationClick={onCitationClick}
            >
              {props.children}
            </CitationRenderer>
          );
        },
        // Style paragraphs
        p: ({ children }) => (
          <Typography variant="body2" component="p" sx={{ mb: 1, '&:last-child': { mb: 0 } }}>
            {children}
          </Typography>
        ),
        // Style lists
        ul: ({ children }) => (
          <Box component="ul" sx={{ pl: 2, mb: 1, '& li': { mb: 0.5 } }}>
            {children}
          </Box>
        ),
        ol: ({ children }) => (
          <Box component="ol" sx={{ pl: 2, mb: 1, '& li': { mb: 0.5 } }}>
            {children}
          </Box>
        ),
        li: ({ children }) => (
          <Typography variant="body2" component="li">
            {children}
          </Typography>
        ),
        // Style code blocks
        code: ({ className, children, ...props }) => {
          const isInline = !className;
          if (isInline) {
            return (
              <Box
                component="code"
                sx={{
                  bgcolor: 'grey.100',
                  px: 0.5,
                  py: 0.25,
                  borderRadius: 0.5,
                  fontSize: '0.85em',
                  fontFamily: 'monospace',
                }}
              >
                {children}
              </Box>
            );
          }
          return (
            <Box
              component="pre"
              sx={{
                bgcolor: 'grey.100',
                p: 1.5,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.85em',
                fontFamily: 'monospace',
                mb: 1,
              }}
            >
              <code className={className} {...props}>
                {children}
              </code>
            </Box>
          );
        },
        // Style headings
        h1: ({ children }) => <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>{children}</Typography>,
        h2: ({ children }) => <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>{children}</Typography>,
        h3: ({ children }) => <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>{children}</Typography>,
        // Style blockquotes
        blockquote: ({ children }) => (
          <Box
            sx={{
              borderLeft: '3px solid',
              borderColor: 'grey.300',
              pl: 2,
              py: 0.5,
              my: 1,
              color: 'text.secondary',
              fontStyle: 'italic',
            }}
          >
            {children}
          </Box>
        ),
        // Style strong/bold
        strong: ({ children }) => <strong>{children}</strong>,
        // Style emphasis/italic
        em: ({ children }) => <em>{children}</em>,
        // Style links
        a: ({ href, children }) => (
          <Box
            component="a"
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              color: 'primary.main',
              textDecoration: 'underline',
              '&:hover': { color: 'primary.dark' },
            }}
          >
            {children}
          </Box>
        ),
      }}
    >
      {cleaned}
    </ReactMarkdown>
  );
}

interface AssistantPanelProps {
  visible: boolean;
  width: number;
  onToggle: () => void;
}

export default function AssistantPanel({ visible, width, onToggle }: AssistantPanelProps) {
  const { 
    projectId, 
    chatMessages, 
    setChatMessages, 
    activeDocumentId, 
    documents,
    switchView,
    navigateToSource, 
    setDragPreview, 
    dragContentRef,
    canvasNodes,
    navigateToNode,
    highlightedMessageId,
    // Session management
    chatSessions,
    activeSessionId,
    sessionsLoading,
    createChatSession,
    switchChatSession,
    updateChatSessionTitle,
    deleteChatSession,
  } = useStudio();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // View state: 'chat' or 'history' (instead of collapsible sidebar)
  const [activeView, setActiveView] = useState<'chat' | 'history'>('chat');
  
  // Session menu state
  const [sessionMenuAnchor, setSessionMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedSessionForMenu, setSelectedSessionForMenu] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  
  // Get active session object
  const activeSession = chatSessions.find(s => s.id === activeSessionId);

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

  // Find a canvas node linked to this message
  const findLinkedNode = (messageId: string) => {
    return canvasNodes.find(node => 
      node.messageIds?.includes(messageId) || 
      (node.viewType === 'thinking' && node.tags?.includes('#thinking-path'))
    );
  };

  // Handle click on "View in Thinking Path" button
  const handleViewInThinkingPath = (messageId: string) => {
    const linkedNode = findLinkedNode(messageId);
    if (linkedNode) {
      navigateToNode(linkedNode.id);
      switchView('thinking');
    } else {
      // If no linked node, switch to thinking view anyway
      switchView('thinking');
    }
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

        // Stream response with session_id
        for await (const chunk of chatApi.stream(projectId, { 
          message: userInput, 
          document_id: activeDocumentId || undefined,
          session_id: activeSessionId || undefined,
        })) {
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

  // Session management handlers
  const handleCreateSession = async (isShared: boolean) => {
    try {
      await createChatSession('New Conversation', isShared);
      setActiveView('chat'); // Switch to chat view
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleSessionMenuOpen = (event: React.MouseEvent<HTMLElement>, sessionId: string) => {
    event.stopPropagation();
    setSessionMenuAnchor(event.currentTarget);
    setSelectedSessionForMenu(sessionId);
  };

  const handleSessionMenuClose = () => {
    setSessionMenuAnchor(null);
    setSelectedSessionForMenu(null);
  };

  const handleStartEditSession = () => {
    const session = chatSessions.find(s => s.id === selectedSessionForMenu);
    if (session) {
      setEditingSessionId(session.id);
      setEditingTitle(session.title);
    }
    handleSessionMenuClose();
  };

  const handleSaveSessionTitle = async () => {
    if (editingSessionId && editingTitle.trim()) {
      try {
        await updateChatSessionTitle(editingSessionId, editingTitle.trim());
      } catch (error) {
        console.error('Failed to update session title:', error);
      }
    }
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleDeleteSessionConfirm = () => {
    setSessionToDelete(selectedSessionForMenu);
    setDeleteDialogOpen(true);
    handleSessionMenuClose();
  };

  const handleDeleteSession = async () => {
    if (sessionToDelete) {
      try {
        await deleteChatSession(sessionToDelete);
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
    setDeleteDialogOpen(false);
    setSessionToDelete(null);
  };

  // Format relative time
  const formatRelativeTime = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const handleSwitchSession = (id: string) => {
    switchChatSession(id);
    setActiveView('chat');
  };

  return (
    <Box sx={{ width, height: '100vh', flexShrink: 1, minWidth: 280, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', bgcolor: '#FAFAFA', overflow: 'hidden' }}>
      
      {/* Header with Tabs and Actions */}
      <Box sx={{ 
        height: 48, 
        borderBottom: '1px solid', 
        borderColor: 'divider', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        bgcolor: '#fff',
        pl: 0.5,
        pr: 1
      }}>
        <Tabs 
          value={activeView} 
          onChange={(_, v) => setActiveView(v)}
          sx={{ 
            minHeight: 48,
            '& .MuiTabs-indicator': { 
              backgroundColor: 'primary.main',
              height: 2,
              borderRadius: '2px 2px 0 0' 
            },
            '& .MuiTab-root': { 
              minHeight: 48, 
              fontSize: '0.8rem', 
              textTransform: 'none',
              fontWeight: 500,
              px: 2,
              color: 'text.secondary',
              '&.Mui-selected': { color: 'primary.main' }
            }
          }}
        >
          <Tab 
            value="chat" 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MessageSquare size={15} />
                <span>Chat</span>
              </Box>
            } 
          />
          <Tab 
            value="history" 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <History size={15} />
                <span>History</span>
              </Box>
            } 
          />
        </Tabs>
        
        <Box sx={{ display: 'flex', gap: 0.5 }}>
           <Tooltip title="New Chat">
             <IconButton size="small" onClick={() => handleCreateSession(false)}>
               <Plus size={18} />
             </IconButton>
           </Tooltip>
           <Tooltip title="Collapse (⌘.)">
             <IconButton size="small" onClick={onToggle}><PanelRightClose size={18} /></IconButton>
           </Tooltip>
        </Box>
      </Box>

      {/* Main Content Area */}
      <Box sx={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>
        
        {/* VIEW: HISTORY (SESSIONS) */}
        {activeView === 'history' && (
           <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#fff', animation: 'fadeIn 0.2s' }}>
             <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
               {sessionsLoading ? (
                 <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                   <CircularProgress size={20} />
                 </Box>
               ) : (
                 <List dense sx={{ py: 0 }}>
                   {chatSessions.map((session) => (
                     <ListItem
                       key={session.id}
                       disablePadding
                       secondaryAction={
                         <IconButton
                           edge="end"
                           size="small"
                           onClick={(e) => handleSessionMenuOpen(e, session.id)}
                           sx={{ opacity: 0.5, '&:hover': { opacity: 1 } }}
                         >
                           <MoreVertical size={14} />
                         </IconButton>
                       }
                       sx={{
                         borderBottom: '1px solid',
                         borderColor: 'divider',
                         '&:last-child': { borderBottom: 'none' },
                         bgcolor: session.id === activeSessionId ? 'primary.50' : 'transparent',
                         '&:hover': { bgcolor: session.id === activeSessionId ? 'primary.100' : 'action.hover' },
                       }}
                     >
                       <ListItemButton
                         onClick={() => handleSwitchSession(session.id)}
                         sx={{ py: 1.5, pr: 4 }}
                       >
                         <ListItemIcon sx={{ minWidth: 32 }}>
                           {session.is_shared ? (
                             <Cloud size={16} className="text-blue-500" />
                           ) : (
                             <Lock size={16} className="text-gray-500" />
                           )}
                         </ListItemIcon>
                         {editingSessionId === session.id ? (
                           <TextField
                             size="small"
                             value={editingTitle}
                             onChange={(e) => setEditingTitle(e.target.value)}
                             onBlur={handleSaveSessionTitle}
                             onKeyDown={(e) => {
                               if (e.key === 'Enter') handleSaveSessionTitle();
                               if (e.key === 'Escape') {
                                 setEditingSessionId(null);
                                 setEditingTitle('');
                               }
                             }}
                             autoFocus
                             sx={{ '& input': { fontSize: '0.85rem', py: 0.5 } }}
                           />
                         ) : (
                           <ListItemText
                             primary={session.title}
                             secondary={formatRelativeTime(session.last_message_at)}
                             primaryTypographyProps={{ 
                               variant: 'body2', 
                               fontWeight: session.id === activeSessionId ? 600 : 400,
                               noWrap: true,
                               sx: { fontSize: '0.85rem' }
                             }}
                             secondaryTypographyProps={{ variant: 'caption', fontSize: '0.7rem' }}
                           />
                         )}
                       </ListItemButton>
                     </ListItem>
                   ))}
                   {chatSessions.length === 0 && (
                      <Box sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
                        <MessageSquare size={32} style={{ opacity: 0.2, marginBottom: 8 }} />
                        <Typography variant="body2">No conversations yet</Typography>
                        <Button 
                          variant="outlined" 
                          size="small" 
                          startIcon={<Plus size={14} />} 
                          sx={{ mt: 2, textTransform: 'none' }}
                          onClick={() => handleCreateSession(false)}
                        >
                          Start Chat
                        </Button>
                      </Box>
                   )}
                 </List>
               )}
             </Box>
             
             {/* Legend */}
             <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#F9FAFB' }}>
               <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                 <Cloud size={12} className="text-blue-500" />
                 <Typography variant="caption" color="text.secondary">
                   Shared - synced across devices
                 </Typography>
               </Box>
               <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                 <Lock size={12} className="text-gray-500" />
                 <Typography variant="caption" color="text.secondary">
                   Private - this device only
                 </Typography>
               </Box>
             </Box>
           </Box>
        )}

        {/* VIEW: CHAT */}
        {activeView === 'chat' && (
           <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', animation: 'fadeIn 0.2s' }}>
             
             {/* Messages */}
             <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                {chatMessages.length === 0 && (
                  <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', opacity: 0.5 }}>
                     <Bot size={48} strokeWidth={1} style={{ marginBottom: 16 }} />
                     <Typography variant="body2" color="text.secondary">
                       Ask me anything about your documents
                     </Typography>
                  </Box>
                )}

                {chatMessages.map((msg) => {
                  const isHighlighted = highlightedMessageId === msg.id;
                  const linkedNode = findLinkedNode(msg.id);
                  
                  return (
                    <Box 
                      key={msg.id} 
                      id={`message-${msg.id}`}
                      sx={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '90%' }}
                    >
                      <Paper 
                        elevation={0} 
                        sx={{ 
                          p: 2, 
                          borderRadius: 2, 
                          bgcolor: msg.role === 'user' ? '#EBF5FF' : '#fff',
                          border: msg.role === 'ai' ? '1px solid #E5E7EB' : 'none',
                          color: msg.role === 'user' ? '#1E40AF' : 'text.primary',
                          ...(isHighlighted && {
                            boxShadow: '0 0 0 2px #3B82F6',
                            animation: 'highlightPulse 1.5s ease-in-out',
                            '@keyframes highlightPulse': {
                              '0%': { boxShadow: '0 0 0 2px #3B82F6' },
                              '50%': { boxShadow: '0 0 0 4px rgba(59, 130, 246, 0.5)' },
                              '100%': { boxShadow: '0 0 0 2px #3B82F6' },
                            },
                          }),
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
                        <Box sx={{ lineHeight: 1.6, minHeight: '1.5em', '& > *:first-of-type': { mt: 0 } }}>
                          {msg.role === 'ai' && msg.content
                            ? (
                              <MarkdownContent
                                content={msg.content}
                                citations={msg.citations}
                                documents={documents}
                                onCitationClick={(citation) => {
                                  if (citation.document_id) {
                                    const searchText = citation.quote?.slice(0, 30) || '';
                                    navigateToSource(
                                      citation.document_id,
                                      citation.page_number || 1,
                                      searchText
                                    );
                                  }
                                }}
                              />
                            )
                            : (
                              <Typography variant="body2" component="div" sx={{ whiteSpace: 'pre-wrap' }}>
                                {msg.content || (msg.role === 'ai' ? '...' : '')}
                              </Typography>
                            )
                          }
                        </Box>
                      )}
                      
                      {/* Sources - Styled as small chips/cards instead of generic collapsible */}
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
                              bgcolor: expandedSources.has(msg.id) ? 'action.selected' : 'transparent',
                            }}
                          >
                            {msg.sources.length} {msg.sources.length === 1 ? 'source' : 'sources'}
                          </Button>
                          
                          <Collapse in={expandedSources.has(msg.id)}>
                            <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                              {msg.sources.map((source, idx) => (
                                <Box
                                  key={idx}
                                  onClick={() => navigateToSource(source.document_id, source.page_number, source.snippet)}
                                  sx={{
                                    p: 1.5,
                                    bgcolor: '#F9FAFB',
                                    borderRadius: 1.5,
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                      bgcolor: '#fff',
                                      borderColor: 'primary.light',
                                      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                                    }
                                  }}
                                >
                                  <Box sx={{ display: 'flex', gap: 1, mb: 0.5 }}>
                                    <LinkIcon size={12} className="text-gray-400 mt-0.5" />
                                    <Typography variant="caption" color="text.primary" fontWeight={500}>
                                        Document {source.document_id.replace('doc_', '')}
                                    </Typography>
                                    <Box sx={{ flex: 1 }} />
                                    <Chip label={`p. ${source.page_number}`} size="small" sx={{ height: 16, fontSize: '0.6rem' }} />
                                  </Box>
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{
                                      lineHeight: 1.5,
                                      display: '-webkit-box',
                                      WebkitLineClamp: 3,
                                      WebkitBoxOrient: 'vertical',
                                      overflow: 'hidden',
                                      fontSize: '0.75rem',
                                    }}
                                  >
                                    "{source.snippet}"
                                  </Typography>
                                </Box>
                              ))}
                            </Box>
                          </Collapse>
                        </Box>
                      )}

                      {/* View in Thinking Path */}
                      {msg.role === 'ai' && linkedNode && (
                          <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                            <Button 
                              size="small" 
                              startIcon={<Brain size={12} />} 
                              onClick={() => handleViewInThinkingPath(msg.id)}
                              sx={{ 
                                fontSize: 10, 
                                textTransform: 'none', 
                                color: 'primary.main',
                                bgcolor: 'primary.50',
                                '&:hover': { bgcolor: 'primary.100' },
                              }}
                            >
                              View Node
                            </Button>
                          </Box>
                      )}
                      </Paper>
                    </Box>
                  );
                })}
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
        )}
      </Box>

      {/* Session Menu & Dialogs (Keep active globally) */}
      <Menu
        anchorEl={sessionMenuAnchor}
        open={Boolean(sessionMenuAnchor)}
        onClose={handleSessionMenuClose}
      >
        <MenuItem onClick={handleStartEditSession}>
          <Edit2 size={14} style={{ marginRight: 8 }} />
          Rename
        </MenuItem>
        <MenuItem onClick={handleDeleteSessionConfirm} sx={{ color: 'error.main' }}>
          <Trash2 size={14} style={{ marginRight: 8 }} />
          Delete
        </MenuItem>
      </Menu>

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Conversation?</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            This will permanently delete this conversation and all its messages. This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteSession} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    
    </Box>
  );
}