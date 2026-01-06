'use client';

import { useState, useRef, useEffect } from 'react';
// import { flushSync } from 'react-dom'; // removed as not strictly needed or can be replaced
import {
  Stack,
  Text,
  Surface,
  TextField, // Using composite
  Menu,
  MenuItem,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Modal,
  Spinner,
  Collapse
} from "@/components/ui";
import { colors, radii, shadows } from '@/components/ui/tokens';
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
  CheckIcon,
  CloseIcon,
  BoltIcon as FlashIcon // mapped
} from '@/components/ui/icons';
import {
  DescriptionIcon as PdfIcon
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
      title={ // Tooltip in UI might use 'content' or 'title' depending on impl. UI Tooltip uses 'title' or 'content'? Check types.
        // UI Tooltip uses 'title' from MUI? No, it's custom.
        // Previous code used 'content' prop for Tooltip. Let's check CanvasControls usage: <Tooltip title="..." ...>
        // Wait, UI Tooltip uses 'title' prop in CanvasControls. But in AssistantPanel original it used 'content' with Box?
        // "content={<Box ...>}"
        // If custom Tooltip supports 'content' for rich content, use that.
        // The UI primitives Tooltip wrapper seems to rely on MUI Tooltip?
        // Let's assume it supports 'title'. If rich content is needed, we might need a richer tooltip or just text.
        // Simplified for now:
        `Source: ${filename}${citationData?.page_number ? ` (Page ${citationData.page_number})` : ''}\n"${quote}"`
      }
    >
      <span
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
        style={{
          color: colors.primary[500],
          cursor: 'grab',
          textDecoration: 'underline',
          textDecorationStyle: 'dotted',
          textUnderlineOffset: '2px',
          backgroundColor: 'transparent',
          borderRadius: '2px',
        }}
        className="citation-link"
      >
        {children}
        <style>{`
            .citation-link:hover {
                color: ${colors.primary[600]};
                background-color: ${colors.primary[50]};
            }
            .citation-link:active {
                cursor: grabbing;
            }
        `}</style>
      </span>
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
          <Text variant="bodySmall" style={{ marginBottom: 8 }}>
            {children}
          </Text>
        ),
        // Style lists
        ul: ({ children }) => (
          <ul style={{ paddingLeft: 16, marginBottom: 8 }}>
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol style={{ paddingLeft: 16, marginBottom: 8 }}>
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li style={{ marginBottom: 4 }}>
            <Text variant="bodySmall">{children}</Text>
          </li>
        ),
        // Style code blocks
        code: ({ className, children, ...props }) => {
          const isInline = !className;
          if (isInline) {
            return (
              <div
                style={{
                  padding: '2px 4px',
                  backgroundColor: colors.neutral[100],
                  borderRadius: radii.sm,
                  fontSize: '0.85em',
                  fontFamily: 'monospace',
                }}
              >
                {children}
              </div>
            );
          }
          return (
            <div
              style={{
                padding: 12,
                backgroundColor: colors.neutral[100],
                borderRadius: radii.md,
                overflow: 'auto',
                fontSize: '0.85em',
                fontFamily: 'monospace',
                marginBottom: 8,
              }}
            >
              <code className={className} {...props}>
                {children}
              </code>
            </div>
          );
        },
        // Style headings
        h1: ({ children }) => <Text variant="h6" style={{ fontWeight: 600, marginBottom: 8 }}>{children}</Text>,
        h2: ({ children }) => <Text variant="label" style={{ fontWeight: 600, marginBottom: 8, fontSize: '1.1em' }}>{children}</Text>,
        h3: ({ children }) => <Text variant="label" style={{ fontWeight: 600, marginBottom: 4 }}>{children}</Text>,
        // Style blockquotes
        blockquote: ({ children }) => (
          <div
            style={{
              borderLeft: '3px solid',
              borderColor: colors.neutral[300],
              paddingLeft: 16,
              paddingTop: 4,
              paddingBottom: 4,
              marginTop: 8,
              marginBottom: 8,
              color: colors.text.secondary,
              fontStyle: 'italic',
            }}
          >
            {children}
          </div>
        ),
        // Style strong/bold
        strong: ({ children }) => <strong>{children}</strong>,
        // Style emphasis/italic
        em: ({ children }) => <em>{children}</em>,
        // Style links
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: colors.primary[500],
              textDecoration: 'underline',
            }}
          >
            {children}
          </a>
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
      <div style={{ position: 'absolute', left: 24, bottom: 24, zIndex: 100 }}>
        <Tooltip title="AI Assistant" placement="right">
          <IconButton
            variant="default"
            size="lg" // FAB equivalent
            onClick={onToggle}
            style={{ borderRadius: '50%', width: 56, height: 56 }}
          >
            <BotIcon size={24} />
          </IconButton>
        </Tooltip>
      </div>
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
    <div style={{
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
      paddingBottom: 32, // Padding bottom
      paddingLeft: 24,
      paddingRight: 24,
    }}>

      {/* Floating Stack Container */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        width: '100%',
        maxWidth: '700px',
        alignItems: 'stretch' // Ensure children take full width
      }}>

        {/* 1. File Card (Top of Stack) */}
        {activeDocument && (
          <Surface
            elevation={2}
            radius="md"
            style={{
              pointerEvents: 'auto',
              padding: 16,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              backgroundColor: '#fff',
              alignSelf: 'flex-start',
              border: '1px solid rgba(0,0,0,0.05)',
              marginBottom: 8
            }}
          >
            <div style={{
              width: 42,
              height: 42,
              borderRadius: 6,
              backgroundColor: '#FEF2F2',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#EF4444'
            }}>
              <PdfIcon size={24} />
            </div>
            <div style={{ minWidth: 0 }}>
              <Text variant="caption" style={{ fontWeight: 700, color: '#111827', display: 'block' }}>
                {activeDocument.filename}
              </Text>
              <Text variant="caption" style={{ color: '#9CA3AF' }}>
                2.4 MB
              </Text>
            </div>
          </Surface>
        )}

        {/* 2. Recent Context Card (Middle - Collapsible) */}
        <Surface
          elevation={1}
          radius="lg"
          style={{
            pointerEvents: 'auto',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255,255,255,0.5)',
            overflow: 'hidden',
            transition: 'all 0.3s ease'
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: '16px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
            }}
            onClick={() => setIsContextCollapsed(!isContextCollapsed)}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.02)'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <Text variant="caption" style={{ fontWeight: 700, color: '#9CA3AF', letterSpacing: '1px' }}>
              RECENT CONTEXT
            </Text>
            <div style={{ display: 'flex', gap: 8 }}>
              <IconButton size="sm" onClick={() => setIsContextCollapsed(!isContextCollapsed)}>
                {isContextCollapsed ? <ExpandLessIcon size={16} /> : <ExpandMoreIcon size={16} />}
              </IconButton>
              <IconButton size="sm" onClick={(e) => { e.stopPropagation(); onToggle(); }}>
                <CloseIcon size={16} />
              </IconButton>
            </div>
          </div>

          {/* Messages (Collapsible Content) */}
          <Collapse open={!isContextCollapsed}>
            <div style={{ flex: 1, overflowY: 'auto', maxHeight: '350px', padding: '0 24px 16px', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {chatMessages.length === 0 && (
                <Text variant="bodySmall" style={{ fontStyle: 'italic', padding: '16px 0', textAlign: 'center', color: '#6B7280' }}>
                  No recent context. Drop a file or start typing.
                </Text>
              )}
              {chatMessages.slice(-3).map((msg) => ( // Show only recent messages
                <div key={msg.id || Math.random()} style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                  {msg.role === 'ai' ? (
                    <div style={{
                      width: 24, height: 24,
                      borderRadius: '50%',
                      backgroundColor: colors.primary[600], // Teal-600
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, marginTop: 4
                    }}>
                      <BotIcon size={14} style={{ color: 'white' }} />
                    </div>
                  ) : (
                    <div style={{
                      width: 24, height: 24,
                      borderRadius: '50%',
                      backgroundColor: colors.neutral[200], // Stone-200
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      flexShrink: 0, marginTop: 4
                    }}>
                      <Text variant="caption" style={{ fontWeight: 700 }}>AL</Text>
                    </div>
                  )}

                  <div style={{ flex: 1 }}>
                    <MarkdownContent
                      content={msg.content || (msg.role === 'ai' && isLoading ? 'Thinking...' : '')}
                      citations={msg.citations}
                      documents={documents}
                      onCitationClick={() => { }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Collapse>
        </Surface>

        {/* 3. Input Pill (Bottom) */}
        <Surface
          ref={inputAreaRef}
          elevation={4}
          style={{
            pointerEvents: 'auto',
            padding: 6,
            display: 'flex',
            flexDirection: 'column',
            width: '100%',
            borderRadius: contextNodes.length > 0 ? '24px' : '999px',
            backgroundColor: '#fff',
            borderWidth: '2px',
            borderStyle: isDragOver ? 'dashed' : 'solid',
            borderColor: isDragOver ? colors.primary[600] : 'rgba(0,0,0,0.08)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: isDragOver
              ? '0 8px 32px rgba(13, 148, 136, 0.15)' // Teal shadow
              : '0 4px 20px rgba(0,0,0,0.06)',
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {/* Context Nodes (Now Inside Input Container) */}
          {contextNodes.length > 0 && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', paddingLeft: 16, paddingRight: 16, paddingTop: 12, paddingBottom: 4, width: '100%' }}>
              {contextNodes.map(node => (
                <Chip
                  key={node.id}
                  label={node.title}
                  onDelete={() => removeContextNode(node.id)}
                  size="sm"
                  style={{
                    height: 28,
                    backgroundColor: colors.neutral[100], // Stone-100
                    borderColor: 'rgba(0,0,0,0.05)',
                    color: colors.neutral[700], // Stone-700
                  }}
                />
              ))}
            </div>
          )}

          {/* Input Row */}
          <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            <div style={{
              marginLeft: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: colors.primary[500]
            }}>
              <FlashIcon size={20} />
            </div>

            <TextField
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={contextNodes.length > 0 ? "Ask about these documents..." : "Drop to analyze..."}
              disabled={isLoading}
              onKeyDown={handleKeyDown}
              style={{
                flex: 1,
                marginLeft: 16,
                color: '#4B5563',
                fontWeight: 500,
                border: 'none',
                outline: 'none',
                background: 'transparent'
              }}
            />

            <IconButton
              type="button"
              variant="default"
              style={{
                width: 40, height: 40,
                borderRadius: '50%',
                boxShadow: '0 2px 8px rgba(13, 148, 136, 0.4)' // Teal shadow
              }}
              onClick={handleSend}
              disabled={!input.trim() && contextNodes.length === 0}
            >
              {isLoading ? <Spinner size="sm" color="inherit" /> : <AddIcon size={24} />}
            </IconButton>
          </div>
        </Surface>

      </div>

      {/* Hidden Dialogs/Menus */}
      <Menu
        open={Boolean(sessionMenuAnchor)}
        onClose={handleSessionMenuClose}
        anchorPosition={sessionMenuAnchor ? { top: sessionMenuAnchor.getBoundingClientRect().bottom + window.scrollY, left: sessionMenuAnchor.getBoundingClientRect().left + window.scrollX } : undefined}
      >
        <MenuItem onClick={handleStartEditSession}>Rename</MenuItem>
        <MenuItem onClick={handleDeleteSessionConfirm} danger style={{ color: '#EF4444' }}>Delete</MenuItem>
      </Menu>

      <Modal open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <Modal.Header>Delete Conversation?</Modal.Header>
        <Modal.Footer>
          <Button variant="ghost" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button variant="danger" onClick={handleDeleteSession}>Delete</Button>
        </Modal.Footer>
      </Modal>

    </div >
  );
}
