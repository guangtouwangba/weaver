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
  InputBase,
  Fade,
  Fab,
} from "@mui/material";
import {
  BotIcon,
  PanelRightCloseIcon,
  PanelRightOpenIcon,
  SendIcon,
  LinkIcon,
  ExpandMoreIcon,
  ExpandLessIcon,
  GripHorizontalIcon,
  BrainIcon,
  ExternalLinkIcon,
  CloudIcon,
  LockIcon,
  MessageSquareIcon,
  MoreVertIcon,
  DeleteIcon,
  EditIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ViewListIcon,
  HistoryIcon,
  AddIcon,
  AutoAwesomeIcon,
  ArrowUpwardIcon,
} from '@/components/ui/icons';
import {
  PictureAsPdf as PdfIcon,
  Close as CloseIcon,
  FlashOn as FlashIcon,
  KeyboardArrowDown as ChevronDownIcon,
  KeyboardArrowUp as ChevronUpIcon
} from '@mui/icons-material';
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

  // Collapsible Context State
  const [isContextCollapsed, setIsContextCollapsed] = useState(false);

  // Session menu state
  const [sessionMenuAnchor, setSessionMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedSessionForMenu, setSelectedSessionForMenu] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);

  // Get active session object
  const activeSession = chatSessions.find(s => s.id === activeSessionId);
  const activeDocument = documents.find(d => d.id === activeDocumentId);

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

      // Handle Canvas Node Drop
      if (data.type === 'canvas_node' || data.type === 'node') {
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
      // Handle Document Drop (from Resource List)
      else if (data.type === 'document') {
        if (!contextNodes.some(n => n.id === data.documentId)) {
          setContextNodes(prev => [...prev, {
            id: data.documentId,
            title: data.title,
            content: `[Document] ${data.title} (${data.pageCount || 0} pages)`,
            sourceMessageId: undefined
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
      <Box sx={{ position: 'absolute', left: 24, bottom: 24, zIndex: 100 }}>
        <Tooltip title="AI Assistant" placement="right">
          <Fab color="primary" onClick={onToggle}>
            <BotIcon size={24} />
          </Fab>
        </Tooltip>
      </Box>
    );
  }

  // Session management handlers (Keep these for future use or hidden menu)
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
    <Box sx={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      zIndex: 900, // Raised to sit above GenerationOutputsOverlay (z-index 50) for drag-drop
      pointerEvents: 'none',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'flex-end',
      alignItems: 'center',
      pb: 4, // Padding bottom
      px: 3,
    }}>

      {/* Floating Stack Container */}
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        width: '100%',
        maxWidth: '700px',
        alignItems: 'stretch' // Ensure children take full width
      }}>

        {/* 1. File Card (Top of Stack) */}
        {activeDocument && (
          <Fade in={true}>
            <Paper
              elevation={2}
              sx={{
                pointerEvents: 'auto',
                p: 2,
                borderRadius: 3, // Approx 12px
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                bgcolor: '#fff',
                alignSelf: 'flex-start', // Align to left of the stack
                border: '1px solid',
                borderColor: 'rgba(0,0,0,0.05)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                mb: 1
              }}
            >
              <Box sx={{
                width: 42,
                height: 42,
                borderRadius: 1.5,
                bgcolor: '#FEF2F2', // Light red bg
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#EF4444' // Red icon
              }}>
                <PdfIcon />
              </Box>
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="subtitle2" noWrap fontWeight={700} sx={{ color: '#111827' }}>
                  {activeDocument.filename}
                </Typography>
                <Typography variant="caption" sx={{ color: '#9CA3AF' }}>
                  2.4 MB
                </Typography>
              </Box>
            </Paper>
          </Fade>
        )}

        {/* 2. Recent Context Card (Middle - Collapsible) */}
        <Paper
          elevation={0}
          sx={{
            pointerEvents: 'auto',
            display: 'flex',
            flexDirection: 'column',
            borderRadius: 4, // More rounded
            bgcolor: 'rgba(255, 255, 255, 0.9)', // Glassmorphism
            backdropFilter: 'blur(12px)',
            border: '1px solid',
            borderColor: 'rgba(255,255,255,0.5)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.05)',
            overflow: 'hidden',
            transition: 'all 0.3s ease'
          }}
        >
          {/* Header */}
          <Box
            sx={{
              px: 3,
              py: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'rgba(0,0,0,0.02)' }
            }}
            onClick={() => setIsContextCollapsed(!isContextCollapsed)}
          >
            <Typography variant="caption" fontWeight={700} sx={{ color: '#9CA3AF', letterSpacing: '1px' }}>
              RECENT CONTEXT
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton size="small">
                {isContextCollapsed ? <ChevronUpIcon fontSize="small" /> : <ChevronDownIcon fontSize="small" />}
              </IconButton>
              <IconButton size="small" onClick={(e) => { e.stopPropagation(); onToggle(); }}>
                <CloseIcon fontSize="small" sx={{ fontSize: 16 }} />
              </IconButton>
            </Box>
          </Box>

          {/* Messages (Collapsible Content) */}
          <Collapse in={!isContextCollapsed}>
            <Box sx={{ flex: 1, overflowY: 'auto', maxHeight: '350px', px: 3, pb: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
              {chatMessages.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', py: 2, textAlign: 'center' }}>
                  No recent context. Drop a file or start typing.
                </Typography>
              )}
              {chatMessages.slice(-3).map((msg) => ( // Show only recent messages
                <Box key={msg.id} sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                  {msg.role === 'ai' ? (
                    <Box sx={{
                      width: 24, height: 24,
                      borderRadius: '50%',
                      bgcolor: 'primary.main',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, mt: 0.5
                    }}>
                      <BotIcon size={14} sx={{ color: 'white' }} />
                    </Box>
                  ) : (
                    <Box sx={{
                      width: 24, height: 24,
                      borderRadius: '50%',
                      bgcolor: 'grey.200',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, mt: 0.5
                    }}>
                      <Typography variant="caption" fontWeight={700}>AL</Typography>
                    </Box>
                  )}

                  <Box sx={{ flex: 1 }}>
                    <MarkdownContent
                      content={msg.content || (msg.role === 'ai' && isLoading ? 'Thinking...' : '')}
                      citations={msg.citations}
                      documents={documents}
                      onCitationClick={() => { }}
                    />
                  </Box>
                </Box>
              ))}
            </Box>
          </Collapse>
        </Paper>

        {/* 3. Input Pill (Bottom) */}
        <Paper
          ref={inputAreaRef}
          elevation={4}
          component="div"
          sx={{
            pointerEvents: 'auto',
            p: '6px',
            display: 'flex',
            flexDirection: 'column', // Changed to column to stack chips + input
            width: '100%',
            // Smooth transition for border radius: Pill (999) -> Soft Rect (24)
            borderRadius: contextNodes.length > 0 ? '24px' : '999px',
            bgcolor: '#fff',
            borderWidth: '2px',
            borderStyle: isDragOver ? 'dashed' : 'solid',
            borderColor: isDragOver ? 'primary.main' : 'rgba(0,0,0,0.08)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: isDragOver
              ? '0 8px 32px rgba(99, 102, 241, 0.15)'
              : '0 4px 20px rgba(0,0,0,0.06)',
            '&:hover': {
              borderColor: isDragOver ? 'primary.main' : 'rgba(0,0,0,0.12)',
              boxShadow: isDragOver
                ? '0 8px 32px rgba(99, 102, 241, 0.15)'
                : '0 8px 24px rgba(0,0,0,0.08)',
            }
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {/* Context Nodes (Now Inside Input Container) */}
          {contextNodes.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', px: 2, pt: 1.5, pb: 0.5, width: '100%' }}>
              {contextNodes.map(node => (
                <Chip
                  key={node.id}
                  label={node.title}
                  onDelete={() => removeContextNode(node.id)}
                  size="small"
                  sx={{
                    height: 28,
                    bgcolor: '#F3F4F6',
                    border: '1px solid',
                    borderColor: 'rgba(0,0,0,0.05)',
                    color: '#374151',
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: '#E5E7EB',
                      borderColor: 'rgba(0,0,0,0.1)',
                    },
                    '& .MuiChip-label': { px: 1.5, fontSize: '0.8rem', fontWeight: 500 },
                    '& .MuiChip-deleteIcon': {
                      color: 'rgba(0,0,0,0.4)',
                      '&:hover': { color: '#EF4444' }
                    }
                  }}
                />
              ))}
            </Box>
          )}

          {/* Input Row */}
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            <Box sx={{
              ml: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6366F1'
            }}>
              <FlashIcon />
            </Box>

            <InputBase
              sx={{ ml: 2, flex: 1, color: '#4B5563', fontWeight: 500 }}
              placeholder={contextNodes.length > 0 ? "Ask about these documents..." : "Drop to analyze..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              onKeyDown={handleKeyDown}
            />

            <IconButton
              type="button"
              sx={{
                bgcolor: '#4F46E5',
                color: 'white',
                width: 40, height: 40,
                '&:hover': { bgcolor: '#4338CA' },
                boxShadow: '0 2px 8px rgba(79, 70, 229, 0.4)'
              }}
              onClick={handleSend}
              disabled={!input.trim() && contextNodes.length === 0}
            >
              {isLoading ? <CircularProgress size={20} color="inherit" /> : <AddIcon size={24} />}
            </IconButton>
          </Box>
        </Paper>

      </Box>

      {/* Hidden Dialogs/Menus */}
      <Menu
        anchorEl={sessionMenuAnchor}
        open={Boolean(sessionMenuAnchor)}
        onClose={handleSessionMenuClose}
      >
        <MenuItem onClick={handleStartEditSession}>Rename</MenuItem>
        <MenuItem onClick={handleDeleteSessionConfirm} sx={{ color: 'error.main' }}>Delete</MenuItem>
      </Menu>

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Conversation?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteSession} color="error">Delete</Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
}
