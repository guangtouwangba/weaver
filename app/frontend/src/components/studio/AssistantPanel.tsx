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
  Cloud,
  Lock,
  MessageSquare,
  MoreVertIcon,
  DeleteIcon,
  EditIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ViewListIcon,
  HistoryIcon,
  AddIcon,
} from '@/components/ui/icons';
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
    setHighlightedMessageId,
    // Session management
    chatSessions,
    activeSessionId,
    sessionsLoading,
    createChatSession,
    switchChatSession,
    updateChatSessionTitle,
    deleteChatSession,
    // Cross-boundary drag from Konva canvas
    crossBoundaryDragNode,
    setCrossBoundaryDragNode,
  } = useStudio();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Context Nodes State
  interface ContextNode {
    id: string;
    title: string;
    content: string;
    sourceMessageId?: string;
  }
  const [contextNodes, setContextNodes] = useState<ContextNode[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputAreaRef = useRef<HTMLDivElement>(null);
  
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

  // Handle cross-boundary drag from Konva canvas
  useEffect(() => {
    const handleGlobalMouseUp = (e: MouseEvent) => {
      // Check if there's a cross-boundary drag node from Konva canvas
      if (!crossBoundaryDragNode) return;
      
      // Check if mouse is over the input area
      const inputArea = inputAreaRef.current;
      if (!inputArea) return;
      
      const rect = inputArea.getBoundingClientRect();
      const isOverInputArea = e.clientX >= rect.left && e.clientX <= rect.right &&
                              e.clientY >= rect.top && e.clientY <= rect.bottom;
      
      if (isOverInputArea) {
        // Add node to context (check for duplicates)
        if (!contextNodes.some(n => n.id === crossBoundaryDragNode.id)) {
          setContextNodes(prev => [...prev, {
            id: crossBoundaryDragNode.id,
            title: crossBoundaryDragNode.title,
            content: crossBoundaryDragNode.content,
            sourceMessageId: crossBoundaryDragNode.sourceMessageId,
          }]);
        }
      }
      
      // Clear the cross-boundary drag state
      setCrossBoundaryDragNode(null);
    };

    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, [crossBoundaryDragNode, contextNodes, setCrossBoundaryDragNode]);

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
      node.messageIds?.includes(messageId)
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

  // Scroll to a specific message
  const scrollToMessage = (messageId: string) => {
    const element = document.getElementById(`message-${messageId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setHighlightedMessageId(messageId);
      // Clear highlight after animation
      setTimeout(() => setHighlightedMessageId(null), 2000);
    }
  };

  const handleSend = async () => {
    if ((!input.trim() && contextNodes.length === 0) || isLoading) return;
    
    const currentContextNodes = [...contextNodes]; // Capture current nodes
    
    const userMsg = {
        id: Date.now().toString(),
        role: 'user' as const,
        content: input,
        timestamp: new Date(),
        // Save context nodes with the user message for display
        contextNodes: currentContextNodes.length > 0 ? currentContextNodes.map(n => ({
          id: n.id,
          title: n.title,
          content: n.content,
        })) : undefined,
    };
    
    const userInput = input;
    
    setInput('');
    setContextNodes([]); // Clear context nodes immediately
    setIsLoading(true);

    // Add user message
    setChatMessages(prev => [...prev, userMsg]);

    // Note: Draft node creation removed - backend now handles creating Question nodes
    // with proper edges to Answer nodes via ThinkingPathService

    // Prepare AI message ID outside try block so it's accessible in catch
    const aiMsgId = (Date.now() + 1).toString();

    try {
        // Prepare AI message placeholder with loading indicator
        setChatMessages(prev => [...prev, {
            id: aiMsgId,
            role: 'ai',
            content: '',
            timestamp: new Date(),
            query: userInput,
        }]);

        // Stream response with session_id and context_nodes (full content)
        for await (const chunk of chatApi.stream(projectId, { 
          message: userInput, 
          document_id: activeDocumentId || undefined,
          session_id: activeSessionId || undefined,
          context_nodes: currentContextNodes.length > 0 ? currentContextNodes.map(n => ({
            id: n.id,
            title: n.title,
            content: n.content,
          })) : undefined,
        })) {
            if (chunk.type === 'token' && chunk.content) {
                // Update message content - avoid flushSync in loops to prevent max update depth
                setChatMessages(prev => prev.map(m => 
                    m.id === aiMsgId 
                      ? { ...m, content: (m.content || '') + chunk.content } 
                      : m
                ));
            } else if (chunk.type === 'sources') {
                setChatMessages(prev => prev.map(m => 
                    m.id === aiMsgId ? { ...m, sources: chunk.sources } : m
                ));
            } else if (chunk.type === 'citation' && chunk.data) {
                // Handle single citation event from Mega-Prompt mode
                setChatMessages(prev => prev.map(m => 
                    m.id === aiMsgId 
                      ? { ...m, citations: [...(m.citations || []), chunk.data as Citation] } 
                      : m
                ));
            } else if (chunk.type === 'citations' && chunk.citations) {
                // Handle all citations at end of response
                setChatMessages(prev => prev.map(m => 
                    m.id === aiMsgId 
                      ? { ...m, citations: chunk.citations } 
                      : m
                ));
            } else if (chunk.type === 'done') {
                // Final scroll when done
                setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 0);
            } else if (chunk.type === 'error') {
                setChatMessages(prev => prev.map(m => 
                    m.id === aiMsgId 
                      ? { ...m, content: (m.content || '') + `\n\n[Error: ${chunk.content || 'Unknown error'}]` } 
                      : m
                ));
            }
        }
    } catch (err) {
        console.error("Chat error:", err);
        // Update error message - aiMsgId is now in scope
        setChatMessages(prev => prev.map(m => 
            m.id === aiMsgId 
              ? { ...m, content: (m.content || '') + `\n\nSorry, I encountered an error: ${err instanceof Error ? err.message : 'Unknown error'}` }
              : m
        ));
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

  // Drag & Drop Handlers for Input Area
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const jsonData = e.dataTransfer.getData('application/json');
    if (!jsonData) return;
    
    try {
      const data = JSON.parse(jsonData);
      if (data.type === 'canvas_node') {
        // Check for duplicates
        if (!contextNodes.some(n => n.id === data.id)) {
          setContextNodes(prev => [...prev, {
            id: data.id,
            title: data.title,
            content: data.content,
            sourceMessageId: data.sourceMessageId
          }]);
        }
      }
    } catch (err) {
      console.error('Failed to parse dropped data:', err);
    }
  };

  const removeContextNode = (nodeId: string) => {
    setContextNodes(prev => prev.filter(n => n.id !== nodeId));
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
                <CommentMui sx={{ fontSize: 15 }} />
                <span>Chat</span>
              </Box>
            } 
          />
          <Tab 
            value="history" 
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HistoryMui sx={{ fontSize: 15 }} />
                <span>History</span>
              </Box>
            } 
          />
        </Tabs>
        
        <Box sx={{ display: 'flex', gap: 0.5 }}>
           <Tooltip title="New Chat">
             <IconButton size="small" onClick={() => handleCreateSession(false)}>
               <AddIcon size="md" />
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
                           <MoreVertIcon size={14} />
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
                        <CommentMui sx={{ fontSize: 32, opacity: 0.2, marginBottom: 1 }} />
                        <Typography variant="body2">No conversations yet</Typography>
                        <Button 
                          variant="outlined" 
                          size="small" 
                          startIcon={<AddIcon size="sm" />} 
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
                      
                      {/* Context Nodes - Show referenced nodes for user messages */}
                      {msg.role === 'user' && msg.contextNodes && msg.contextNodes.length > 0 && (
                        <Box sx={{ mt: 1.5, pt: 1.5, borderTop: '1px dashed', borderColor: 'divider' }}>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                            <PsychologyMui sx={{ fontSize: 12 }} />
                            Referenced {msg.contextNodes.length} {msg.contextNodes.length === 1 ? 'node' : 'nodes'}:
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {msg.contextNodes.map((node) => (
                              <Tooltip 
                                key={node.id} 
                                title={
                                  <Box sx={{ maxWidth: 300 }}>
                                    <Typography variant="caption" fontWeight="bold">{node.title}</Typography>
                                    <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.9 }}>
                                      {node.content.length > 200 ? node.content.substring(0, 200) + '...' : node.content}
                                    </Typography>
                                  </Box>
                                }
                                arrow
                                placement="top"
                              >
                                <Chip
                                  label={node.title.length > 25 ? node.title.substring(0, 25) + '...' : node.title}
                                  size="small"
                                  icon={<PsychologyMui sx={{ fontSize: 10 }} />}
                                  sx={{
                                    height: 22,
                                    fontSize: '0.7rem',
                                    bgcolor: 'rgba(139, 92, 246, 0.1)',
                                    color: '#7C3AED',
                                    borderColor: 'rgba(139, 92, 246, 0.3)',
                                    borderWidth: 1,
                                    borderStyle: 'solid',
                                    '& .MuiChip-icon': { color: '#7C3AED' },
                                  }}
                                />
                              </Tooltip>
                            ))}
                          </Box>
                        </Box>
                      )}
                      
                      {/* Sources - Styled as small chips/cards instead of generic collapsible */}
                      {msg.sources && msg.sources.length > 0 && (
                        <Box sx={{ mt: 1.5 }}>
                          <Button
                            size="small"
                            onClick={() => toggleSources(msg.id)}
                            startIcon={<LinkIcon size={12} />}
                            endIcon={expandedSources.has(msg.id) ? <ExpandLessMui sx={{ fontSize: 12 }} /> : <ExpandMoreMui sx={{ fontSize: 12 }} />}
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
                              startIcon={<PsychologyMui sx={{ fontSize: 12 }} />} 
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
             <Box ref={inputAreaRef} sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#fff' }}>
               {/* Context Chips Area */}
               {contextNodes.length > 0 && (
                 <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1.5 }}>
                   {contextNodes.map(node => (
                     <Tooltip key={node.id} title={node.sourceMessageId ? "Click to view source message" : node.title}>
                       <Chip
                         label={node.title.length > 20 ? node.title.substring(0, 20) + '...' : node.title}
                         onDelete={() => removeContextNode(node.id)}
                         onClick={() => node.sourceMessageId && scrollToMessage(node.sourceMessageId)}
                         icon={<PsychologyMui sx={{ fontSize: 14 }} />}
                         size="small"
                         sx={{ 
                           maxWidth: '100%',
                           bgcolor: 'primary.50',
                           color: 'primary.700',
                           borderColor: 'primary.100',
                           borderWidth: 1,
                           borderStyle: 'solid',
                           '& .MuiChip-deleteIcon': {
                             color: 'primary.400',
                             '&:hover': { color: 'primary.700' }
                           },
                           cursor: node.sourceMessageId ? 'pointer' : 'default',
                           '&:hover': node.sourceMessageId ? {
                             bgcolor: 'primary.100',
                           } : {}
                         }}
                       />
                     </Tooltip>
                   ))}
                 </Box>
               )}
               
              <Box 
                sx={{ 
                  display: 'flex', 
                  gap: 1, 
                  alignItems: 'center', 
                  bgcolor: (isDragOver || crossBoundaryDragNode) ? 'primary.50' : '#F3F4F6', 
                  borderRadius: 2, 
                  px: 2, 
                  py: 1,
                  border: (isDragOver || crossBoundaryDragNode) ? '2px dashed' : '2px solid',
                  borderColor: (isDragOver || crossBoundaryDragNode) ? 'primary.main' : 'transparent',
                  transition: 'all 0.2s ease',
                }}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                 <TextField 
                   fullWidth 
                   placeholder={contextNodes.length > 0 ? "Ask about selected nodes..." : "Ask me anything... (Drag nodes here for context)"}
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
                   <IconButton size="small" color="primary" onClick={handleSend} disabled={!input.trim() && contextNodes.length === 0}><Send size={16} /></IconButton>
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
          <EditMui sx={{ fontSize: 14, marginRight: 1 }} />
          Rename
        </MenuItem>
        <MenuItem onClick={handleDeleteSessionConfirm} sx={{ color: 'error.main' }}>
          <DeleteMui sx={{ fontSize: 14, marginRight: 1 }} />
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