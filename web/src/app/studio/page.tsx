'use client';

import { useState, useRef, useEffect, useCallback, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import GlobalLayout from "@/components/layout/GlobalLayout";
import CurriculumPreviewModal from "@/components/dialogs/CurriculumPreviewModal";
import PodcastView from "./PodcastView";
import WriterView from "./WriterView";
import ProjectInitializer from "@/components/studio/ProjectInitializer";
import { NodeInspector } from "@/components/studio/NodeInspector";
import PDFViewer from "@/components/studio/PDFViewer";
import { 
  Box, 
  Typography, 
  Paper, 
  IconButton, 
  Button,
  TextField,
  Chip,
  Avatar,
  Tooltip,
  Collapse,
  Divider,
  Badge,
  ToggleButton,
  ToggleButtonGroup,
  Slider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  LinearProgress
} from "@mui/material";
import { 
  FileText, 
  Maximize2, 
  Minimize2,
  Sparkles, 
  Link as LinkIcon, 
  BookOpen, 
  Layout, 
  Mic, 
  Plus, 
  Bot,
  Image as ImageIcon,
  FolderOpen,
  ChevronDown,
  ChevronUp,
  Search,
  Settings,
  Video,
  GripHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Filter,
  Zap,
  ArrowRight,
  LayoutGrid,
  List as ListIcon,
  PlayCircle,
  Globe,
  Music,
  Play,
  Pause,
  Volume2,
  SkipBack,
  SkipForward,
  ExternalLink,
  Clock,
  X as CloseIcon,
  MoreVertical,
  BrainCircuit,
  Presentation,
  FileQuestion,
  Wand2,
  Loader2,
  PenTool,
  Network,
  X,
  Sparkles as SparklesIcon,
  AlertCircle,
  Trash2
} from "lucide-react";

// --- Helper Components ---

const VerticalResizeHandle = ({ onMouseDown }: { onMouseDown: (e: React.MouseEvent) => void }) => (
  <Box 
    onMouseDown={onMouseDown}
    sx={{
      width: 4,
      cursor: 'col-resize',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      bgcolor: 'transparent',
      zIndex: 50,
      height: '100%',
      flexShrink: 0,
      transition: 'background-color 0.2s',
      '&:hover': {
        bgcolor: 'primary.main'
      },
      '&:active': {
        bgcolor: 'primary.main'
      }
    }}
  />
);

// --- Mock Data ---
type ResourceType = 'pdf' | 'video' | 'audio' | 'link';

interface Resource {
  id: string;
  type: ResourceType;
  title: string;
  date: string;
  duration?: string;
  pages?: number;
  content?: string;
}

const SAMPLE_RESOURCES: Resource[] = [
  { id: '1', type: 'pdf', title: 'Attention Is All You Need.pdf', date: '10:42 AM', pages: 15 },
  { id: '2', type: 'pdf', title: 'BERT_Pre-training.pdf', date: '2d ago', pages: 24 },
  { id: '3', type: 'pdf', title: 'GPT-3_Language_Models.pdf', date: '1w ago', pages: 75 },
];

const SAMPLE_MEDIA: Resource[] = [
  { id: '4', type: 'video', title: 'Lecture_01_Transformers.mp4', date: 'Yesterday', duration: '1:20:00' },
  { id: '5', type: 'audio', title: 'DeepMind_Podcast_#12.mp3', date: '3d ago', duration: '45:12' },
  { id: '6', type: 'link', title: 'HuggingFace Blog', date: '5d ago' },
];

// --- Tab System Types ---
type TabType = 'canvas' | 'podcast' | 'flashcards' | 'ppt' | 'writer';
interface Tab {
  id: string;
  type: TabType;
  title: string;
  status: 'ready' | 'generating';
  progress?: number; // 0-100
}

export default function StudioPage() {
  return (
    <Suspense fallback={
      <GlobalLayout>
        <Box sx={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center' }}>
          <CircularProgress />
        </Box>
      </GlobalLayout>
    }>
      <StudioPageContent />
    </Suspense>
  );
}

function StudioPageContent() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get('projectId') || 'default';
  const [isInitializing, setIsInitializing] = useState(false);
  const [isCurriculumModalOpen, setIsCurriculumModalOpen] = useState(false);

  // Check initialization status on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const needsInit = localStorage.getItem(`project_initializing_${projectId}`);
      if (needsInit === 'true') {
        setIsInitializing(true);
      }
    }
  }, [projectId]);

  // --- Chat & RAG State ---
  interface ChatMessage {
    id: string;
    role: 'user' | 'ai';
    content: string;
    type: 'text' | 'rag_result';
    sources?: { 
      title: string; 
      id: string; 
      snippet?: string;
      page_number?: number;
      similarity?: number;
    }[];
    timestamp: Date;
    // For AI messages, keep track of originating user query (for drag-to-canvas)
    query?: string;
  }

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'ai',
      content: 'Hello! I\'m your research assistant. Ask me anything about your documents, and I can help you add key insights to your canvas.',
      type: 'text',
      timestamp: new Date()
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const chatMessageRefs = useRef<Record<string, HTMLDivElement | null>>({});
  // Drag preview state for AI → Canvas
  const [dragPreview, setDragPreview] = useState<{ x: number; y: number; content: string } | null>(null);
  const dragContentRef = useRef<string | null>(null);

  // --- Selection State (moved before useEffect) ---
  const [activeResource, setActiveResource] = useState<Resource>(SAMPLE_RESOURCES[0]);
  const [sourceNavigation, setSourceNavigation] = useState<{
    resourceId: string;
    pageNumber?: number;
    searchText?: string;
  } | null>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isTyping]);

  // Handle source navigation - scroll to highlighted text
  useEffect(() => {
    if (sourceNavigation && sourceNavigation.resourceId === activeResource.id) {
      setTimeout(() => {
        const highlighted = document.querySelector('.highlighted-text');
        if (highlighted) {
          highlighted.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 200);
    }
  }, [sourceNavigation, activeResource]);

  // Toggle sources expansion
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

  // Navigate to source in PDF viewer (enhanced for bidirectional navigation)
  const navigateToSource = (sourceId: string, pageNumber?: number, searchText?: string) => {
    // Find the resource by ID
    const resource = [...SAMPLE_RESOURCES, ...SAMPLE_MEDIA].find(r => r.id === sourceId);
    if (resource) {
      setActiveResource(resource);
      setSourceNavigation({ resourceId: sourceId, pageNumber, searchText });
      // Scroll to PDF viewer if needed
      setTimeout(() => {
        const pdfViewer = document.querySelector('[data-pdf-viewer]');
        if (pdfViewer) {
          pdfViewer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  };

  // --- Canvas State (moved before callbacks that use it) ---
  interface CanvasNode {
    id: string;
    type: 'card' | 'group' | 'source' | 'concept' | 'application' | 'critique' | 'ai_insight';
    title: string;
    content?: string;
    x: number;
    y: number;
    color?: string;
    tags?: string[];
    timestamp?: string;
    // Source metadata (PDF or Chat)
    sourceId?: string;
    sourcePage?: number;   // PDF page number
    sourceText?: string;   // Highlighted text in source
    sourceType?: 'pdf' | 'chat';
    sourceMessageId?: string; // Chat message id
    sourceQuery?: string;     // Original user query
    connections?: string[];   // Array of target node IDs
    isSimplified?: boolean;   // Flag to track if node has been simplified
  }

  // Generate many nodes for performance testing
  const generateInitialNodes = (): CanvasNode[] => {
    const nodes: CanvasNode[] = [];
    
    // Core source nodes
    nodes.push({ id: 'c1', type: 'card', title: 'SOURCE PDF', content: 'Attention Is All You Need', x: 200, y: 300, color: 'white', connections: ['c2', 'c3', 'c4'] });
    nodes.push({ id: 'c2', type: 'card', title: 'SOURCE PDF', content: 'BERT: Pre-training of Deep Bidirectional Transformers', x: 800, y: 300, color: 'white', connections: ['c5', 'c6'] });
    nodes.push({ id: 'c3', type: 'card', title: 'SOURCE PDF', content: 'GPT-3: Language Models are Few-Shot Learners', x: 1400, y: 300, color: 'white', connections: ['c7', 'c8'] });
    
    // Transformer concepts
    nodes.push({ id: 'c4', type: 'card', title: 'Self-Attention', content: 'The core mechanism that allows the model to weigh the importance of different words in a sequence.', x: 200, y: 600, color: 'blue', tags: ['#transformer', '#nlp'], connections: ['c9', 'c10'] });
    nodes.push({ id: 'c5', type: 'card', title: 'Multi-Head Attention', content: 'Allows the model to jointly attend to information from different representation subspaces at different positions.', x: 500, y: 600, color: 'blue', tags: ['#attention', '#transformer'], connections: ['c11'] });
    nodes.push({ id: 'c6', type: 'card', title: 'Positional Encoding', content: 'Injects information about the relative or absolute position of tokens in the sequence.', x: 800, y: 600, color: 'blue', tags: ['#transformer'], connections: ['c12'] });
    
    // BERT concepts
    nodes.push({ id: 'c7', type: 'card', title: 'Bidirectional Context', content: 'BERT uses bidirectional context to understand the full meaning of words by looking at both left and right context.', x: 1100, y: 600, color: 'green', tags: ['#bert', '#nlp'], connections: ['c13', 'c14'] });
    nodes.push({ id: 'c8', type: 'card', title: 'Masked Language Model', content: 'BERT is pre-trained using a masked language modeling objective where random tokens are masked and predicted.', x: 1400, y: 600, color: 'green', tags: ['#bert', '#pretraining'], connections: ['c15'] });
    
    // GPT concepts
    nodes.push({ id: 'c9', type: 'card', title: 'Autoregressive Generation', content: 'GPT models generate text one token at a time, using previously generated tokens as context.', x: 200, y: 900, color: 'purple', tags: ['#gpt', '#generation'], connections: ['c16'] });
    nodes.push({ id: 'c10', type: 'card', title: 'Few-Shot Learning', content: 'GPT-3 demonstrates the ability to perform tasks with just a few examples without fine-tuning.', x: 500, y: 900, color: 'purple', tags: ['#gpt', '#few-shot'], connections: ['c17'] });
    
    // Architecture details
    nodes.push({ id: 'c11', type: 'card', title: 'Encoder-Decoder', content: 'The Transformer uses an encoder-decoder architecture for sequence-to-sequence tasks.', x: 800, y: 900, color: 'orange', tags: ['#architecture'], connections: ['c18'] });
    nodes.push({ id: 'c12', type: 'card', title: 'Layer Normalization', content: 'Normalizes the inputs across the features to stabilize training and improve convergence.', x: 1100, y: 900, color: 'orange', tags: ['#normalization'], connections: ['c19'] });
    nodes.push({ id: 'c13', type: 'card', title: 'Next Sentence Prediction', content: 'BERT uses NSP task to understand relationships between sentences.', x: 1400, y: 900, color: 'green', tags: ['#bert'], connections: ['c20'] });
    
    // Applications
    nodes.push({ id: 'c14', type: 'card', title: 'Question Answering', content: 'BERT achieves state-of-the-art results on various QA benchmarks.', x: 200, y: 1200, color: 'pink', tags: ['#application', '#qa'] });
    nodes.push({ id: 'c15', type: 'card', title: 'Text Classification', content: 'Transformers excel at text classification tasks with fine-tuning.', x: 500, y: 1200, color: 'pink', tags: ['#application', '#classification'] });
    nodes.push({ id: 'c16', type: 'card', title: 'Text Generation', content: 'GPT models can generate coherent and contextually relevant text.', x: 800, y: 1200, color: 'pink', tags: ['#application', '#generation'] });
    nodes.push({ id: 'c17', type: 'card', title: 'Code Generation', content: 'Large language models can generate code from natural language descriptions.', x: 1100, y: 1200, color: 'pink', tags: ['#application', '#code'] });
    nodes.push({ id: 'c18', type: 'card', title: 'Machine Translation', content: 'Transformer architecture revolutionized neural machine translation.', x: 1400, y: 1200, color: 'pink', tags: ['#application', '#translation'] });
    
    // Technical details
    nodes.push({ id: 'c19', type: 'card', title: 'Residual Connections', content: 'Skip connections help with gradient flow and enable training of deeper networks.', x: 200, y: 1500, color: 'cyan', tags: ['#technical', '#training'] });
    nodes.push({ id: 'c20', type: 'card', title: 'Feed-Forward Networks', content: 'Each transformer layer contains a position-wise feed-forward network.', x: 500, y: 1500, color: 'cyan', tags: ['#technical', '#architecture'] });
    
    // Additional nodes for more complexity
    nodes.push({ id: 'c21', type: 'card', title: 'Scaled Dot-Product', content: 'Attention scores are scaled by the square root of the dimension to prevent softmax saturation.', x: 800, y: 1500, color: 'blue', tags: ['#attention', '#technical'] });
    nodes.push({ id: 'c22', type: 'card', title: 'Token Embeddings', content: 'Words are converted to dense vector representations before processing.', x: 1100, y: 1500, color: 'blue', tags: ['#embedding', '#technical'] });
    nodes.push({ id: 'c23', type: 'card', title: 'Subword Tokenization', content: 'BPE and WordPiece tokenization break words into smaller subword units.', x: 1400, y: 1500, color: 'blue', tags: ['#tokenization'] });
    
    // More application nodes
    nodes.push({ id: 'c24', type: 'card', title: 'Sentiment Analysis', content: 'Transformers can accurately determine the sentiment of text.', x: 200, y: 1800, color: 'pink', tags: ['#application'] });
    nodes.push({ id: 'c25', type: 'card', title: 'Named Entity Recognition', content: 'BERT-based models excel at identifying entities in text.', x: 500, y: 1800, color: 'pink', tags: ['#application', '#ner'] });
    nodes.push({ id: 'c26', type: 'card', title: 'Summarization', content: 'Transformer models can generate concise summaries of long documents.', x: 800, y: 1800, color: 'pink', tags: ['#application', '#summarization'] });
    nodes.push({ id: 'c27', type: 'card', title: 'Dialogue Systems', content: 'GPT models power conversational AI systems and chatbots.', x: 1100, y: 1800, color: 'pink', tags: ['#application', '#dialogue'] });
    nodes.push({ id: 'c28', type: 'card', title: 'Information Extraction', content: 'Transformers can extract structured information from unstructured text.', x: 1400, y: 1800, color: 'pink', tags: ['#application', '#ie'] });
    
    // Performance and optimization
    nodes.push({ id: 'c29', type: 'card', title: 'Model Parallelism', content: 'Large models are distributed across multiple GPUs for training and inference.', x: 200, y: 2100, color: 'yellow', tags: ['#optimization', '#training'] });
    nodes.push({ id: 'c30', type: 'card', title: 'Quantization', content: 'Model weights can be quantized to reduce memory and speed up inference.', x: 500, y: 2100, color: 'yellow', tags: ['#optimization', '#inference'] });
    nodes.push({ id: 'c31', type: 'card', title: 'Knowledge Distillation', content: 'Smaller models can learn from larger teacher models to maintain performance.', x: 800, y: 2100, color: 'yellow', tags: ['#optimization', '#efficiency'] });
    nodes.push({ id: 'c32', type: 'card', title: 'Pruning', content: 'Unimportant weights can be removed to reduce model size.', x: 1100, y: 2100, color: 'yellow', tags: ['#optimization'] });
    nodes.push({ id: 'c33', type: 'card', title: 'Gradient Checkpointing', content: 'Trades computation for memory to enable training of larger models.', x: 1400, y: 2100, color: 'yellow', tags: ['#optimization', '#memory'] });
    
    return nodes;
  };

  const [canvasNodes, setCanvasNodes] = useState<CanvasNode[]>(generateInitialNodes());

  // Scroll chat to specific message (for chat-linked nodes)
  const scrollToChatMessage = useCallback((messageId: string) => {
    const target = chatMessageRefs.current[messageId];
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, []);

  // Navigate from node to its source (PDF or Chat)
  const handleNodeToSource = useCallback((node: CanvasNode) => {
    // Chat source: scroll Assistant column to corresponding message
    if (node.sourceType === 'chat' && node.sourceMessageId) {
      scrollToChatMessage(node.sourceMessageId);
      return;
    }

    // PDF source: existing behavior
    if (node.sourceId) {
      navigateToSource(node.sourceId, node.sourcePage, node.sourceText);
    }
  }, [navigateToSource, scrollToChatMessage]);

  // Navigate from PDF back to node
  const handleSourceToNode = useCallback((nodeId: string) => {
    const node = canvasNodes.find(n => n.id === nodeId);
    if (!node || !canvasRef.current) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    setViewport(prev => ({
      ...prev,
      x: centerX - node.x * prev.scale,
      y: centerY - node.y * prev.scale,
    }));
    
    setSelectedNodeId(nodeId);
  }, [canvasNodes]);

  // --- AI Feature Handlers ---
  // --- Layout State ---
  const [leftVisible, setLeftVisible] = useState(true);
  const [centerVisible, setCenterVisible] = useState(true);
  
  // --- Resizing State ---
  const [leftWidth, setLeftWidth] = useState(380);
  const [centerWidth, setCenterWidth] = useState(420); 
  const [resizingCol, setResizingCol] = useState<'left' | 'center' | null>(null);

  // --- Feature State ---
  const [isReaderExpanded, setIsReaderExpanded] = useState(false);
  const [splitRatio, setSplitRatio] = useState(0.4); 
  const [quietMode, setQuietMode] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid');
  const [papersExpanded, setPapersExpanded] = useState(true);
  const [mediaExpanded, setMediaExpanded] = useState(true);

  // --- Canvas View Mode State ---
  type CanvasViewMode = 'canvas' | 'hierarchical' | 'minimap' | 'list' | 'cluster';
  const [canvasViewMode, setCanvasViewMode] = useState<CanvasViewMode>('canvas');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // --- Node Grouping State ---
  interface CanvasGroup {
    id: string;
    title: string;
    color: string;
    nodeIds: string[];
    collapsed: boolean;
    position: { x: number; y: number };
    bounds: { width: number; height: number };
  }
  const [nodeGroups, setNodeGroups] = useState<CanvasGroup[]>([]);

  // --- Infinite Canvas State ---
  const [viewport, setViewport] = useState({ x: 0, y: 0, scale: 1 });
  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [isShiftPressed, setIsShiftPressed] = useState(false);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [connectingNodeId, setConnectingNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null); // Format: "sourceId-targetId"
  const [tempLineEnd, setTempLineEnd] = useState<{ x: number, y: number } | null>(null);
  const lastMousePos = useRef({ x: 0, y: 0 });
  const mousePos = useRef({ x: 0, y: 0 }); // Current mouse pos in screen space
  const dragStartPos = useRef<{ x: number, y: number } | null>(null); // For threshold check
  const viewportRef = useRef(viewport); // Ref to access latest viewport in event handlers
  const selectedNodeIdRef = useRef(selectedNodeId); // Ref for keyboard handler
  const selectedConnectionIdRef = useRef(selectedConnectionId); // Ref for keyboard handler
  const canvasRef = useRef<HTMLDivElement>(null);
  
  // Unified RAF Manager for performance optimization
  const rafManager = useRef({
    rafId: null as number | null,
    pendingPan: null as { dx: number; dy: number } | null,
    pendingNodeDrag: null as { nodeId: string; dx: number; dy: number } | null,
    pendingTempLine: null as { x: number; y: number } | null,
  });

  // Unified RAF update handler - applies all pending updates in a single frame
  // Using useRef to store the function to avoid stale closure issues with useCallback
  const applyRafUpdatesRef = useRef<() => void>();
  
  applyRafUpdatesRef.current = () => {
    const manager = rafManager.current;
    
    if (manager.pendingPan) {
      const { dx, dy } = manager.pendingPan;
      // Batch update viewport - only update if change is significant
      if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
        setViewport(prev => ({ 
          x: prev.x + dx, 
          y: prev.y + dy, 
          scale: prev.scale 
        }));
      }
      manager.pendingPan = null;
    }
    
    if (manager.pendingNodeDrag) {
      const { nodeId, dx, dy } = manager.pendingNodeDrag;
      // Batch update node position - only update if change is significant
      if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
        setCanvasNodes(prev => prev.map(node => 
          node.id === nodeId ? { ...node, x: node.x + dx, y: node.y + dy } : node
        ));
      }
      manager.pendingNodeDrag = null;
    }
    
    if (manager.pendingTempLine) {
      setTempLineEnd(manager.pendingTempLine);
      manager.pendingTempLine = null;
    }
    
    manager.rafId = null;
  };

  // Keep refs in sync with state
  useEffect(() => {
    viewportRef.current = viewport;
  }, [viewport]);
  
  useEffect(() => {
    selectedNodeIdRef.current = selectedNodeId;
  }, [selectedNodeId]);
  
  useEffect(() => {
    selectedConnectionIdRef.current = selectedConnectionId;
  }, [selectedConnectionId]);

  // --- Interaction State ---
  const [contextMenu, setContextMenu] = useState<{ mouseX: number; mouseY: number } | null>(null);
  const [selectedText, setSelectedText] = useState<string | null>(null);
  const [isDraggingFromPdf, setIsDraggingFromPdf] = useState(false);

  // --- Tab System State ---
  const [tabs, setTabs] = useState<Tab[]>([
    { id: 't1', type: 'canvas', title: 'Main Canvas', status: 'ready' }
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('t1');
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  // --- Canvas Copilot State ---
  const [isCanvasAiOpen, setIsCanvasAiOpen] = useState(false);
  const [canvasAiQuery, setCanvasAiQuery] = useState('');

  // --- Performance Optimization State ---
  const [isLayoutFrozen, setIsLayoutFrozen] = useState(false);
  const nodePoolRef = useRef<Map<string, HTMLElement>>(new Map()); // Node pool for DOM reuse
  const intersectionObserverRef = useRef<IntersectionObserver | null>(null);
  const [showAllConnections, setShowAllConnections] = useState(true); // Toggle for showing all connections
  const [connectionImportanceThreshold, setConnectionImportanceThreshold] = useState(1); // Minimum importance to show

  // --- Learning Path State ---
  interface LearningPath {
    id: string;
    name: string;
    nodeIds: string[]; // Ordered sequence of nodes
    currentStep: number;
  }
  const [learningPaths, setLearningPaths] = useState<LearningPath[]>([]);
  const [activeLearningPath, setActiveLearningPath] = useState<string | null>(null);
  const [unlockedNodes, setUnlockedNodes] = useState<Set<string>>(new Set()); // Nodes that are unlocked
  const [progressiveMode, setProgressiveMode] = useState(false); // Enable progressive disclosure
  const [isTourActive, setIsTourActive] = useState(false);
  const tourIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [focusMode, setFocusMode] = useState(false);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);
  
  // --- Layer System State ---
  const [visibleLayers, setVisibleLayers] = useState<Set<'source' | 'concept' | 'application'>>(new Set(['source', 'concept', 'application']));
  const [layerOpacity, setLayerOpacity] = useState<Record<'source' | 'concept' | 'application', number>>({
    source: 1,
    concept: 1,
    application: 1,
  });

  // --- Refs ---
  const [isVerticalDragging, setIsVerticalDragging] = useState(false);
  const leftColumnRef = useRef<HTMLDivElement>(null);

  // --- Tab Handlers ---
  const handleTabClose = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    const newTabs = tabs.filter(t => t.id !== tabId);
    if (newTabs.length === 0) {
      // Ensure at least one tab? Or show empty state. Let's keep one canvas.
      setTabs([{ id: 'new-canvas', type: 'canvas', title: 'Canvas', status: 'ready' }]);
      setActiveTabId('new-canvas');
    } else {
      setTabs(newTabs);
      if (activeTabId === tabId) {
        setActiveTabId(newTabs[newTabs.length - 1].id);
      }
    }
  };

  const handleAddTab = (type: TabType) => {
    setMenuAnchor(null);
    const newId = `t-${Date.now()}`;
    
    let title = 'New Tab';
    let isGen = false;

    switch (type) {
      case 'canvas': title = 'New Canvas'; break;
      case 'podcast': title = 'Podcast'; isGen = true; break;
      case 'flashcards': title = 'Flashcards'; isGen = true; break;
      case 'ppt': title = 'Slides'; isGen = true; break;
      case 'writer': title = 'Writer'; break;
    }

    const newTab: Tab = { 
      id: newId, 
      type, 
      title, 
      status: isGen ? 'generating' : 'ready',
      progress: 0
    };

    setTabs([...tabs, newTab]);
    setActiveTabId(newId);

    // Simulate Generation
    if (isGen) {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress >= 100) {
          clearInterval(interval);
          setTabs(prev => prev.map(t => t.id === newId ? { ...t, status: 'ready' } : t));
        } else {
          setTabs(prev => prev.map(t => t.id === newId ? { ...t, progress } : t));
        }
      }, 800);
    }
  };

  // --- Global Keyboard Shortcuts ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !e.repeat && (e.target as HTMLElement).tagName !== 'INPUT' && (e.target as HTMLElement).tagName !== 'TEXTAREA') {
        e.preventDefault(); 
        setIsSpacePressed(true);
      }
      if (e.key === 'Shift') {
        setIsShiftPressed(true);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
        e.preventDefault();
        setLeftVisible(prev => !prev);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '.') {
        e.preventDefault();
        setCenterVisible(prev => !prev);
      }
      
      // Delete selected node or connection
      if ((e.key === 'Delete' || e.key === 'Backspace') && 
          (e.target as HTMLElement).tagName !== 'INPUT' && 
          (e.target as HTMLElement).tagName !== 'TEXTAREA') {
        e.preventDefault();
        
        const currentSelectedConnectionId = selectedConnectionIdRef.current;
        const currentSelectedNodeId = selectedNodeIdRef.current;
        
        if (currentSelectedConnectionId) {
          // Delete connection - split only on last '-' since node ids can contain '-'
          const lastDashIndex = currentSelectedConnectionId.lastIndexOf('-');
          const sourceId = currentSelectedConnectionId.substring(0, lastDashIndex);
          const targetId = currentSelectedConnectionId.substring(lastDashIndex + 1);
          setCanvasNodes(prev => prev.map(node => {
            if (node.id === sourceId && node.connections) {
              return { ...node, connections: node.connections.filter(id => id !== targetId) };
            }
            return node;
          }));
          setSelectedConnectionId(null);
        } else if (currentSelectedNodeId) {
          // Delete node and all its connections (both incoming and outgoing)
          setCanvasNodes(prev => {
            // Remove the node
            const filtered = prev.filter(node => node.id !== currentSelectedNodeId);
            // Remove any connections pointing to this node
            return filtered.map(node => ({
              ...node,
              connections: node.connections?.filter(id => id !== currentSelectedNodeId)
            }));
          });
          setSelectedNodeId(null);
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
        setIsPanning(false);
      }
      if (e.key === 'Shift') {
        setIsShiftPressed(false);
        setConnectingNodeId(null); // Cancel connection if Shift released? Maybe keep it. Let's keep it for now.
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // --- Canvas Wheel Handler (Non-passive for preventDefault) with throttling ---
  useEffect(() => {
    const canvasElement = canvasRef.current;
    if (!canvasElement) return;

    let rafId: number | null = null;
    let pendingUpdate: { x?: number; y?: number; scale?: number } | null = null;

    const applyViewportUpdate = () => {
      const update = pendingUpdate;
      if (update) {
        setViewport(prev => {
          const newViewport = { ...prev };
          if (update.x !== undefined) newViewport.x = update.x;
          if (update.y !== undefined) newViewport.y = update.y;
          if (update.scale !== undefined) newViewport.scale = update.scale;
          return newViewport;
        });
        pendingUpdate = null;
      }
      rafId = null;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      
      const currentViewport = viewportRef.current;
      
      // Zoom with Ctrl/Cmd + Wheel
      if (e.metaKey || e.ctrlKey) {
        const zoomSensitivity = 0.001;
        const delta = -e.deltaY * zoomSensitivity;
        const newScale = Math.min(Math.max(0.1, currentViewport.scale * (1 + delta)), 5);
        
        const rect = canvasElement.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const canvasX = (mouseX - currentViewport.x) / currentViewport.scale;
        const canvasY = (mouseY - currentViewport.y) / currentViewport.scale;
        const newX = mouseX - canvasX * newScale;
        const newY = mouseY - canvasY * newScale;

        pendingUpdate = { x: newX, y: newY, scale: newScale };
      } else {
        // Pan with Wheel
        pendingUpdate = {
          x: currentViewport.x - e.deltaX,
          y: currentViewport.y - e.deltaY,
        };
      }

      // Throttle updates using requestAnimationFrame
      if (rafId === null) {
        rafId = requestAnimationFrame(applyViewportUpdate);
      }
    };

    // Add non-passive event listener
    canvasElement.addEventListener('wheel', handleWheel, { passive: false });
    
    return () => {
      canvasElement.removeEventListener('wheel', handleWheel);
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
    };
  }, []); // Empty dependency array - uses ref for latest viewport

  // --- Resize Logic ---
  const handleVerticalMouseDown = useCallback((e: React.MouseEvent) => {
    if (isReaderExpanded) return;
    e.preventDefault();
    setIsVerticalDragging(true);
  }, [isReaderExpanded]);

  const handleHorizontalMouseDown = (col: 'left' | 'center') => (e: React.MouseEvent) => {
    e.preventDefault();
    setResizingCol(col);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isVerticalDragging && leftColumnRef.current) {
      const rect = leftColumnRef.current.getBoundingClientRect();
      const relativeY = e.clientY - rect.top;
        const newRatio = Math.min(Math.max(relativeY / rect.height, 0.2), 0.8);
      setSplitRatio(newRatio);
        return;
      }
      if (resizingCol) {
        const minWidth = 280;
        const maxWidth = 800;
        if (resizingCol === 'left') {
          const newWidth = Math.max(minWidth, Math.min(e.clientX, maxWidth));
          setLeftWidth(newWidth);
        } else if (resizingCol === 'center') {
          const currentLeftWidth = leftVisible ? leftWidth : 49;
          const newWidth = Math.max(minWidth, Math.min(e.clientX - currentLeftWidth, maxWidth));
          setCenterWidth(newWidth);
        }
      }
    };
    const handleMouseUp = () => {
      setIsVerticalDragging(false);
      setResizingCol(null);
    };
    if (isVerticalDragging || resizingCol) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = isVerticalDragging ? 'row-resize' : 'col-resize';
      document.body.style.userSelect = 'none';
    } else {
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    };
  }, [isVerticalDragging, resizingCol, leftWidth, leftVisible]);

  const handleContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    setContextMenu(
      contextMenu === null
        ? {
            mouseX: event.clientX + 2,
            mouseY: event.clientY - 6,
          }
        : null,
    );
  };

  const handleCloseContextMenu = () => {
    setContextMenu(null);
  };

  // --- AI Feature Handlers ---
  const [isAiProcessing, setIsAiProcessing] = useState(false);

  const handleSimplifyNode = useCallback(async (nodeId: string) => {
    const node = canvasNodes.find(n => n.id === nodeId);
    if (!node || node.isSimplified || isAiProcessing) return;

    setIsAiProcessing(true);
    try {
      const result = await canvasApi.simplifyNode(projectId, nodeId);
      setCanvasNodes(prev => prev.map(n => 
        n.id === nodeId 
          ? { ...n, content: result.simplified_content, isSimplified: true }
          : n
      ));
    } catch (error) {
      console.error('Failed to simplify node:', error);
      // TODO: Show error toast
    } finally {
      setIsAiProcessing(false);
    }
  }, [canvasNodes, projectId, isAiProcessing]);

  const handleCritiqueNode = useCallback(async (nodeId: string) => {
    const node = canvasNodes.find(n => n.id === nodeId);
    if (!node || isAiProcessing) return;

    setIsAiProcessing(true);
    try {
      const result = await canvasApi.critiqueNode(projectId, nodeId);
      const critiqueNode = result.critique_node;
      
      // Create new critique node
      const newCritiqueNode: CanvasNode = {
        id: critiqueNode.id || `${nodeId}_critique_${Date.now()}`,
        type: 'critique',
        title: critiqueNode.title,
        content: critiqueNode.content,
        x: critiqueNode.x,
        y: critiqueNode.y,
        color: 'red',
        connections: [nodeId], // Connect to original node
      };

      // Add critique node and connect original to it
      setCanvasNodes(prev => {
        const updated = [...prev, newCritiqueNode];
        return updated.map(n => 
          n.id === nodeId && n.connections
            ? { ...n, connections: [...n.connections, newCritiqueNode.id] }
            : n
        );
      });
    } catch (error) {
      console.error('Failed to create critique node:', error);
      // TODO: Show error toast
    } finally {
      setIsAiProcessing(false);
    }
  }, [canvasNodes, projectId, isAiProcessing]);

  const handleFuseNodes = useCallback(async (nodeId1: string, nodeId2: string) => {
    if (isAiProcessing) return;

    setIsAiProcessing(true);
    try {
      // MOCK: Simulate API call for prototype
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate network delay
      
      const node1 = canvasNodes.find(n => n.id === nodeId1);
      const node2 = canvasNodes.find(n => n.id === nodeId2);
      
      if (!node1 || !node2) {
        throw new Error('Nodes not found');
      }
      
      // Mock fusion result
      const fusionNode = {
        id: `fusion_${nodeId1}_${nodeId2}_${Date.now()}`,
        title: `Connection: ${node1.title} & ${node2.title}`,
        content: `This fusion explores the relationship between "${node1.title}" and "${node2.title}". \n\nKey insights:\n• Both concepts share common themes\n• They complement each other in the research context\n• Understanding one helps illuminate the other`,
        x: (node1.x + node2.x) / 2,
        y: (node1.y + node2.y) / 2,
        connections: [nodeId1, nodeId2],
      };
      
      // Create new fusion node
      const newFusionNode: CanvasNode = {
        id: fusionNode.id,
        type: 'card',
        title: fusionNode.title,
        content: fusionNode.content,
        x: fusionNode.x,
        y: fusionNode.y,
        color: 'purple',
        connections: fusionNode.connections,
      };

      // Add fusion node and connect both nodes to it
      setCanvasNodes(prev => {
        const updated = [...prev, newFusionNode];
        return updated.map(n => {
          if (n.id === nodeId1) {
            const existing = n.connections || [];
            return { ...n, connections: [...existing, newFusionNode.id] };
          }
          if (n.id === nodeId2) {
            const existing = n.connections || [];
            return { ...n, connections: [...existing, newFusionNode.id] };
          }
          return n;
        });
      });

      // Clear selection after fusion
      setSelectedNodeIds(new Set());
      setSelectedNodeId(null);
    } catch (error) {
      console.error('Failed to fuse nodes:', error);
      // TODO: Show error toast
    } finally {
      setIsAiProcessing(false);
    }
  }, [canvasNodes, isAiProcessing]);

  const handleDeleteSelectedNodes = useCallback(() => {
    if (selectedNodeIds.size > 0) {
      setCanvasNodes(prev => {
        const idsToDelete = Array.from(selectedNodeIds);
        const filtered = prev.filter(n => !idsToDelete.includes(n.id));
        return filtered.map(n => ({
          ...n,
          connections: n.connections?.filter(id => !idsToDelete.includes(id))
        }));
      });
      setSelectedNodeIds(new Set());
      setSelectedNodeId(null);
    } else if (selectedNodeId) {
      setCanvasNodes(prev => {
        const filtered = prev.filter(n => n.id !== selectedNodeId);
        return filtered.map(n => ({
          ...n,
          connections: n.connections?.filter(id => id !== selectedNodeId)
        }));
      });
      setSelectedNodeId(null);
    }
  }, [selectedNodeIds, selectedNodeId]);

  const handleCreateCard = (
    text?: string,
    metadata?: { 
      timestamp?: string; 
      sourceId?: string; 
      sourcePage?: number;
      sourceText?: string;
      sourceType?: 'pdf' | 'chat';
      sourceMessageId?: string;
      sourceQuery?: string;
    }, 
    position?: { x: number, y: number }
  ) => {
    const contentToUse = text || "The output is computed as a weighted sum of the values."; // Fallback for demo
    const newId = `c-${Date.now()}`;
    
    // Calculate center of viewport if no position provided
    const centerX = position ? position.x : (-viewport.x + (canvasRef.current?.clientWidth || 800) / 2) / viewport.scale;
    const centerY = position ? position.y : (-viewport.y + (canvasRef.current?.clientHeight || 600) / 2) / viewport.scale;

    const isChatInsight = metadata?.sourceType === 'chat';

    const newNode: CanvasNode = {
      id: newId,
      type: isChatInsight ? 'ai_insight' : 'card',
      title: isChatInsight
        ? (metadata?.sourceQuery || 'AI Insight')
        : (metadata?.timestamp ? `Timestamp ${metadata.timestamp}` : 'New Concept'),
      content: contentToUse,
      x: centerX - 140, // Center the card (width 280)
      y: centerY - 100,
      color: isChatInsight ? 'pink' : 'white',
      timestamp: metadata?.timestamp,
      sourceId: metadata?.sourceId,
      sourcePage: metadata?.sourcePage,
      sourceText: metadata?.sourceText,
      sourceType: metadata?.sourceType,
      sourceMessageId: metadata?.sourceMessageId,
      sourceQuery: metadata?.sourceQuery,
    };

    setCanvasNodes(prev => [...prev, newNode]);
    
    // Ensure we are on a canvas tab
    const currentTab = tabs.find(t => t.id === activeTabId);
    if (currentTab?.type !== 'canvas') {
      // Find first canvas tab or create one
      const canvasTab = tabs.find(t => t.type === 'canvas');
      if (canvasTab) {
        setActiveTabId(canvasTab.id);
      } else {
        handleAddTab('canvas');
      }
    }

    setContextMenu(null);
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: chatInput,
      type: 'text',
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsTyping(true);

    // Simulate RAG Processing
    setTimeout(() => {
      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'ai',
        content: `Based on your query "${userMsg.content}", I found relevant information in the "Attention Is All You Need" paper. The Transformer model relies entirely on self-attention to compute representations of its input and output without using sequence-aligned RNNs or convolution.`,
        type: 'rag_result',
        sources: [
          { 
            title: 'Attention Is All You Need.pdf', 
            id: '1',
            snippet: 'The Transformer model relies entirely on self-attention to compute representations of its input and output without using sequence-aligned RNNs or convolution.',
            page_number: 2,
            similarity: 0.85
          },
          { 
            title: 'BERT_Pre-training.pdf', 
            id: '2',
            snippet: 'BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.',
            page_number: 3,
            similarity: 0.72
          }
        ],
        timestamp: new Date(),
        query: userMsg.content,
      };
      setChatMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);
    }, 1500);
  };

  const handleAddRagToCanvas = (message: ChatMessage) => {
    if (!canvasRef.current) return;
    
    // Calculate position: Center of current viewport
    const centerX = (-viewport.x + (canvasRef.current.clientWidth || 800) / 2) / viewport.scale;
    const centerY = (-viewport.y + (canvasRef.current.clientHeight || 600) / 2) / viewport.scale;

    const newNode: CanvasNode = {
      id: `rag-${Date.now()}`,
      type: 'card',
      title: 'AI Insight',
      content: message.content,
      x: centerX - 140, // Center the card
      y: centerY - 100,
      color: 'white',
      tags: ['#ai-generated'],
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
    };

    setCanvasNodes(prev => [...prev, newNode]);
    
    // Also add citation nodes if available (optional cluster effect)
    if (message.sources) {
        message.sources.forEach((source, index) => {
            const sourceNodeId = `source-${Date.now()}-${index}`;
            const sourceNode: CanvasNode = {
                id: sourceNodeId,
                type: 'card',
                title: 'Source',
                content: source.title,
                x: centerX - 140 + (index + 1) * 40,
                y: centerY + 150, // Place below the main insight
                color: 'blue',
                connections: [newNode.id] // Connect to the insight
            };
            setCanvasNodes(prev => [...prev, sourceNode]);
        });
    }

    // Ensure we are on a canvas tab
    const currentTab = tabs.find(t => t.id === activeTabId);
    if (currentTab?.type !== 'canvas') {
      const canvasTab = tabs.find(t => t.type === 'canvas');
      if (canvasTab) {
        setActiveTabId(canvasTab.id);
      } else {
        handleAddTab('canvas');
      }
    }
  };

  // Auto-layout function using force-directed layout
  const handleAutoLayout = useCallback(() => {
    const nodes = [...canvasNodes];
    if (nodes.length === 0) return;

    // Simple force-directed layout parameters
    const iterations = 100;
    const k = Math.sqrt((2000 * 2000) / nodes.length); // Optimal distance between nodes
    const repulsionStrength = k * k;
    const attractionStrength = 0.01;
    const damping = 0.9;
    
    // Initialize velocities
    const velocities = nodes.map(() => ({ x: 0, y: 0 }));

    // Run force-directed layout iterations
    for (let iter = 0; iter < iterations; iter++) {
      const forces = nodes.map(() => ({ x: 0, y: 0 }));

      // Calculate repulsion forces (all nodes repel each other)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = repulsionStrength / (distance * distance);
          const fx = (dx / distance) * force;
          const fy = (dy / distance) * force;
          
          forces[i].x += fx;
          forces[i].y += fy;
          forces[j].x -= fx;
          forces[j].y -= fy;
        }
      }

      // Calculate attraction forces (connected nodes attract)
      for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].connections) {
          for (const targetId of nodes[i].connections) {
            const targetIndex = nodes.findIndex(n => n.id === targetId);
            if (targetIndex === -1) continue;
            
            const dx = nodes[targetIndex].x - nodes[i].x;
            const dy = nodes[targetIndex].y - nodes[i].y;
            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = (distance - k) * attractionStrength;
            const fx = (dx / distance) * force;
            const fy = (dy / distance) * force;
            
            forces[i].x += fx;
            forces[i].y += fy;
            forces[targetIndex].x -= fx;
            forces[targetIndex].y -= fy;
          }
        }
      }

      // Apply forces with damping
      for (let i = 0; i < nodes.length; i++) {
        velocities[i].x = (velocities[i].x + forces[i].x) * damping;
        velocities[i].y = (velocities[i].y + forces[i].y) * damping;
        nodes[i].x += velocities[i].x;
        nodes[i].y += velocities[i].y;
      }
    }

    // Center the layout
    const minX = Math.min(...nodes.map(n => n.x));
    const minY = Math.min(...nodes.map(n => n.y));
    const centerX = minX + (Math.max(...nodes.map(n => n.x)) - minX) / 2;
    const centerY = minY + (Math.max(...nodes.map(n => n.y)) - minY) / 2;
    
    const offsetX = -centerX + (canvasRef.current?.clientWidth || 800) / 2;
    const offsetY = -centerY + (canvasRef.current?.clientHeight || 600) / 2;
    
    nodes.forEach(node => {
      node.x += offsetX;
      node.y += offsetY;
    });

    setCanvasNodes(nodes);
    // Auto-freeze layout after completion
    setIsLayoutFrozen(true);
  }, [canvasNodes]);

  // Toggle layout freeze
  const handleToggleLayoutFreeze = useCallback(() => {
    setIsLayoutFrozen(prev => !prev);
  }, []);

  // Community detection and clustering
  // Predefined color palette for communities
  const communityColors = [
    '#3B82F6', // blue
    '#10B981', // green
    '#F59E0B', // amber
    '#EF4444', // red
    '#8B5CF6', // purple
    '#EC4899', // pink
    '#06B6D4', // cyan
    '#F97316', // orange
    '#84CC16', // lime
    '#6366F1', // indigo
  ];

  const handleDetectCommunities = useCallback(() => {
    const nodes = [...canvasNodes];
    
    // Build adjacency map for efficient lookup
    const adjacencyMap = new Map<string, Set<string>>();
    nodes.forEach(node => {
      adjacencyMap.set(node.id, new Set());
    });
    
    // Build bidirectional connections
    nodes.forEach(node => {
      if (node.connections) {
        node.connections.forEach(targetId => {
          adjacencyMap.get(node.id)?.add(targetId);
          // Make bidirectional
          if (adjacencyMap.has(targetId)) {
            adjacencyMap.get(targetId)?.add(node.id);
          }
        });
      }
    });

    // Community detection using connected components
    const visited = new Set<string>();
    const communities: string[][] = [];
    
    const dfs = (nodeId: string, community: string[]) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);
      community.push(nodeId);
      
      const neighbors = adjacencyMap.get(nodeId) || new Set();
      neighbors.forEach(neighborId => {
        if (!visited.has(neighborId)) {
          dfs(neighborId, community);
        }
      });
    };

    // Find all connected components
    nodes.forEach(node => {
      if (!visited.has(node.id)) {
        const community: string[] = [];
        dfs(node.id, community);
        if (community.length > 0) {
          communities.push(community);
        }
      }
    });

    // Sort communities by size (largest first)
    communities.sort((a, b) => b.length - a.length);

    // Assign colors to communities
    const nodeCommunityMap = new Map<string, number>();
    communities.forEach((community, index) => {
      community.forEach(nodeId => {
        nodeCommunityMap.set(nodeId, index);
      });
    });

    // Update nodes with community colors
    nodes.forEach(node => {
      const communityIndex = nodeCommunityMap.get(node.id);
      if (communityIndex !== undefined) {
        node.color = communityColors[communityIndex % communityColors.length];
      } else {
        // Isolated nodes get a default color
        node.color = '#94A3B8'; // gray
      }
    });

    setCanvasNodes(nodes);
  }, [canvasNodes]);

  // Advanced clustering: Group nodes by semantic similarity (tags, content)
  const handleSemanticClustering = useCallback(() => {
    const nodes = [...canvasNodes];
    
    // Build tag-based clusters
    const tagClusters = new Map<string, string[]>();
    nodes.forEach(node => {
      if (node.tags && node.tags.length > 0) {
        node.tags.forEach(tag => {
          if (!tagClusters.has(tag)) {
            tagClusters.set(tag, []);
          }
          tagClusters.get(tag)?.push(node.id);
        });
      }
    });

    // Find dominant tag for each node
    const nodeToCluster = new Map<string, { tag: string; count: number }>();
    nodes.forEach(node => {
      if (node.tags && node.tags.length > 0) {
        // Count tag occurrences
        const tagCounts = new Map<string, number>();
        node.tags.forEach(tag => {
          tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
        });
        
        // Find most common tag
        let maxTag = '';
        let maxCount = 0;
        tagCounts.forEach((count, tag) => {
          if (count > maxCount) {
            maxCount = count;
            maxTag = tag;
          }
        });
        
        if (maxTag) {
          nodeToCluster.set(node.id, { tag: maxTag, count: maxCount });
        }
      }
    });

    // Assign colors based on dominant tags
    const tagToColorIndex = new Map<string, number>();
    let colorIndex = 0;
    
    nodes.forEach(node => {
      const clusterInfo = nodeToCluster.get(node.id);
      if (clusterInfo) {
        if (!tagToColorIndex.has(clusterInfo.tag)) {
          tagToColorIndex.set(clusterInfo.tag, colorIndex++);
        }
        const colorIdx = tagToColorIndex.get(clusterInfo.tag) || 0;
        node.color = communityColors[colorIdx % communityColors.length];
      } else {
        // Nodes without tags get default color
        node.color = '#94A3B8'; // gray
      }
    });

    setCanvasNodes(nodes);
  }, [canvasNodes]);

  // Clear community colors
  const handleClearClustering = useCallback(() => {
    const nodes = [...canvasNodes];
    nodes.forEach(node => {
      node.color = undefined; // Reset to default
    });
    setCanvasNodes(nodes);
  }, [canvasNodes]);

  // LOD (Level of Detail) rendering based on zoom level
  type LODLevel = 'dot' | 'minimal' | 'compact' | 'full';
  const getNodeLOD = useCallback((scale: number): LODLevel => {
    if (scale < 0.3) return 'dot';
    if (scale < 0.6) return 'minimal';
    if (scale < 1.0) return 'compact';
    return 'full';
  }, []);

  // Connection LOD: simplify connections at low zoom
  const getConnectionLOD = useCallback((scale: number): 'simplified' | 'full' => {
    return scale < 0.5 ? 'simplified' : 'full';
  }, []);

  // Text LOD: adjust font size based on zoom
  const getTextLOD = useCallback((scale: number): { fontSize: number; showContent: boolean } => {
    if (scale < 0.3) return { fontSize: 8, showContent: false };
    if (scale < 0.6) return { fontSize: 10, showContent: false };
    if (scale < 1.0) return { fontSize: 12, showContent: true };
    return { fontSize: 14, showContent: true };
  }, []);

  // Enhanced clustering: Group nodes by community with connection density analysis
  const handleGroupByCommunity = useCallback(() => {
    const nodes = [...canvasNodes];
    
    // Build adjacency map with connection weights
    const adjacencyMap = new Map<string, Map<string, number>>();
    nodes.forEach(node => {
      adjacencyMap.set(node.id, new Map());
    });
    
    // Calculate connection weights (bidirectional)
    nodes.forEach(node => {
      if (node.connections) {
        node.connections.forEach(targetId => {
          const currentWeight = adjacencyMap.get(node.id)?.get(targetId) || 0;
          adjacencyMap.get(node.id)?.set(targetId, currentWeight + 1);
          if (adjacencyMap.has(targetId)) {
            const targetWeight = adjacencyMap.get(targetId)?.get(node.id) || 0;
            adjacencyMap.get(targetId)?.set(node.id, targetWeight + 1);
          }
        });
      }
    });

    // Enhanced community detection using connection density
    const visited = new Set<string>();
    const communities: string[][] = [];
    
    // Calculate node connection density
    const nodeDensity = new Map<string, number>();
    nodes.forEach(node => {
      const connections = adjacencyMap.get(node.id) || new Map();
      nodeDensity.set(node.id, connections.size);
    });
    
    // Find communities using DFS with minimum connection threshold
    const minConnections = 2; // Minimum connections to form a community
    const dfs = (nodeId: string, community: string[]) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);
      community.push(nodeId);
      
      const neighbors = adjacencyMap.get(nodeId) || new Map();
      // Sort neighbors by connection weight
      const sortedNeighbors = Array.from(neighbors.entries())
        .sort((a, b) => b[1] - a[1])
        .map(([id]) => id);
      
      sortedNeighbors.forEach(neighborId => {
        if (!visited.has(neighborId)) {
          const weight = neighbors.get(neighborId) || 0;
          if (weight >= 1) { // Only follow strong connections
            dfs(neighborId, community);
          }
        }
      });
    };

    // Start from high-density nodes first
    const sortedNodes = [...nodes].sort((a, b) => {
      const densityA = nodeDensity.get(a.id) || 0;
      const densityB = nodeDensity.get(b.id) || 0;
      return densityB - densityA;
    });

    sortedNodes.forEach(node => {
      if (!visited.has(node.id)) {
        const community: string[] = [];
        dfs(node.id, community);
        if (community.length >= minConnections) { // Only group communities with 2+ nodes
          communities.push(community);
        }
      }
    });

    // Create groups
    const groups: CanvasGroup[] = communities.map((community, index) => {
      const communityNodes = nodes.filter(n => community.includes(n.id));
      const minX = Math.min(...communityNodes.map(n => n.x));
      const minY = Math.min(...communityNodes.map(n => n.y));
      const maxX = Math.max(...communityNodes.map(n => n.x + 280));
      const maxY = Math.max(...communityNodes.map(n => n.y + 200));
      
      return {
        id: `group-${index}`,
        title: `Community ${index + 1} (${community.length} nodes)`,
        color: communityColors[index % communityColors.length],
        nodeIds: community,
        collapsed: false,
        position: { x: minX, y: minY },
        bounds: { width: maxX - minX, height: maxY - minY },
      };
    });

    setNodeGroups(groups);
  }, [canvasNodes]);

  // Toggle group collapse
  const handleToggleGroup = useCallback((groupId: string) => {
    setNodeGroups(prev => prev.map(group => 
      group.id === groupId ? { ...group, collapsed: !group.collapsed } : group
    ));
  }, []);

  // Collapse/Expand all groups
  const handleCollapseAll = useCallback(() => {
    setNodeGroups(prev => prev.map(group => ({ ...group, collapsed: true })));
  }, []);

  const handleExpandAll = useCallback(() => {
    setNodeGroups(prev => prev.map(group => ({ ...group, collapsed: false })));
  }, []);

  // Filter nodes based on search and tags
  const filteredNodes = useMemo(() => {
    let filtered = [...canvasNodes];
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(node => 
        node.title.toLowerCase().includes(query) ||
        node.content?.toLowerCase().includes(query) ||
        node.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }
    
    // Tag filter
    if (selectedTags.length > 0) {
      filtered = filtered.filter(node => 
        node.tags?.some(tag => selectedTags.includes(tag))
      );
    }
    
    return filtered;
  }, [canvasNodes, searchQuery, selectedTags]);

  // Get visible nodes considering groups, progressive disclosure, and layers
  const getVisibleNodes = useCallback(() => {
    let nodes = filteredNodes;
    
    // Apply layer filter
    nodes = nodes.filter(node => {
      if (node.type === 'group') return true;
      const nodeLayer: 'source' | 'concept' | 'application' = 
        node.type === 'source' || node.title === 'SOURCE PDF' ? 'source' :
        node.type === 'concept' ? 'concept' :
        node.type === 'application' ? 'application' : 'concept';
      return visibleLayers.has(nodeLayer);
    });
    
    // Apply progressive disclosure: filter out locked nodes
    if (progressiveMode) {
      nodes = nodes.filter(node => {
        // Source nodes are always unlocked
        if (node.type === 'group' || node.title === 'SOURCE PDF') return true;
        return unlockedNodes.has(node.id);
      });
    }
    
    if (nodeGroups.length === 0) return nodes;
    
    const visibleNodeIds = new Set<string>();
    nodeGroups.forEach(group => {
      if (!group.collapsed) {
        group.nodeIds.forEach(id => visibleNodeIds.add(id));
      }
    });
    
    // Also include nodes not in any group
    nodes.forEach(node => {
      const inGroup = nodeGroups.some(g => g.nodeIds.includes(node.id));
      if (!inGroup) {
        visibleNodeIds.add(node.id);
      }
    });
    
    return nodes.filter(node => visibleNodeIds.has(node.id));
  }, [filteredNodes, nodeGroups, progressiveMode, unlockedNodes, visibleLayers]);
  
  // Toggle layer visibility
  const handleToggleLayer = useCallback((layer: 'source' | 'concept' | 'application') => {
    setVisibleLayers(prev => {
      const next = new Set(prev);
      if (next.has(layer)) {
        next.delete(layer);
      } else {
        next.add(layer);
      }
      return next;
    });
  }, []);
  
  // Set layer opacity
  const handleSetLayerOpacity = useCallback((layer: 'source' | 'concept' | 'application', opacity: number) => {
    setLayerOpacity(prev => ({ ...prev, [layer]: opacity }));
  }, []);

  // Create learning path from node connections
  const handleCreateLearningPath = useCallback(() => {
    // Auto-generate learning path based on node connections
    const nodes = [...canvasNodes];
    if (nodes.length === 0) return;
    
    // Find source nodes (starting points)
    const sourceNodes = nodes.filter(n => n.title === 'SOURCE PDF' || n.type === 'group');
    if (sourceNodes.length === 0) {
      // Use first node as starting point
      const path: string[] = [nodes[0].id];
      const visited = new Set<string>([nodes[0].id]);
      
      // Follow connections to build path
      let current = nodes[0];
      while (current.connections && current.connections.length > 0) {
        const nextId = current.connections.find(id => !visited.has(id));
        if (!nextId) break;
        path.push(nextId);
        visited.add(nextId);
        current = nodes.find(n => n.id === nextId) || current;
      }
      
      const learningPath: LearningPath = {
        id: `path-${Date.now()}`,
        name: 'Auto Learning Path',
        nodeIds: path,
        currentStep: 0,
      };
      
      setLearningPaths([learningPath]);
      setActiveLearningPath(learningPath.id);
      
      // Unlock first node
      setUnlockedNodes(new Set([path[0]]));
      setProgressiveMode(true);
    }
  }, [canvasNodes]);

  // Unlock next node in learning path
  const handleUnlockNext = useCallback(() => {
    if (!activeLearningPath) return;
    
    const path = learningPaths.find(p => p.id === activeLearningPath);
    if (!path) return;
    
    if (path.currentStep < path.nodeIds.length - 1) {
      const nextStep = path.currentStep + 1;
      const nextNodeId = path.nodeIds[nextStep];
      
      setLearningPaths(prev => prev.map(p => 
        p.id === activeLearningPath ? { ...p, currentStep: nextStep } : p
      ));
      
      setUnlockedNodes(prev => new Set([...prev, nextNodeId]));
      
      // Auto-navigate to next node
      const nextNode = canvasNodes.find(n => n.id === nextNodeId);
      if (nextNode && canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        setViewport(prev => ({
          ...prev,
          x: centerX - nextNode.x * prev.scale,
          y: centerY - nextNode.y * prev.scale,
        }));
      }
    }
  }, [activeLearningPath, learningPaths, canvasNodes]);

  // Toggle progressive mode
  const handleToggleProgressiveMode = useCallback(() => {
    setProgressiveMode(prev => {
      if (!prev) {
        // Enable: unlock source nodes
        const sourceNodes = canvasNodes
          .filter(n => n.title === 'SOURCE PDF' || n.type === 'group')
          .map(n => n.id);
        setUnlockedNodes(new Set(sourceNodes));
      } else {
        // Disable: unlock all nodes
        setUnlockedNodes(new Set(canvasNodes.map(n => n.id)));
      }
      return !prev;
    });
  }, [canvasNodes]);

  // Start Tour: Auto-navigate through learning path
  const handleStartTour = useCallback(() => {
    if (!activeLearningPath) {
      // Create a tour path if none exists
      handleCreateLearningPath();
      return;
    }
    
    const path = learningPaths.find(p => p.id === activeLearningPath);
    if (!path || path.nodeIds.length === 0) return;
    
    setIsTourActive(true);
    let currentIndex = 0;
    
    const navigateToNode = (nodeId: string) => {
      const node = canvasNodes.find(n => n.id === nodeId);
      if (!node || !canvasRef.current) return;
      
      const rect = canvasRef.current.getBoundingClientRect();
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      // Smooth animation to node
      setViewport(prev => ({
        ...prev,
        x: centerX - node.x * prev.scale,
        y: centerY - node.y * prev.scale,
      }));
      
      // Select the node
      setSelectedNodeId(nodeId);
      
      // Unlock the node
      setUnlockedNodes(prev => new Set([...prev, nodeId]));
      
      // Update learning path step
      setLearningPaths(prev => prev.map(p => 
        p.id === activeLearningPath ? { ...p, currentStep: currentIndex } : p
      ));
    };
    
    // Navigate to first node
    navigateToNode(path.nodeIds[0]);
    
    // Auto-advance through nodes
    tourIntervalRef.current = setInterval(() => {
      currentIndex++;
      if (currentIndex >= path.nodeIds.length) {
        // Tour complete
        if (tourIntervalRef.current) {
          clearInterval(tourIntervalRef.current);
          tourIntervalRef.current = null;
        }
        setIsTourActive(false);
        return;
      }
      
      navigateToNode(path.nodeIds[currentIndex]);
    }, 3000); // 3 seconds per node
  }, [activeLearningPath, learningPaths, canvasNodes]);

  // Stop Tour
  const handleStopTour = useCallback(() => {
    if (tourIntervalRef.current) {
      clearInterval(tourIntervalRef.current);
      tourIntervalRef.current = null;
    }
    setIsTourActive(false);
  }, []);

  // Cleanup tour on unmount
  useEffect(() => {
    return () => {
      if (tourIntervalRef.current) {
        clearInterval(tourIntervalRef.current);
      }
    };
  }, []);

  // Focus Mode: Highlight selected node and its neighbors
  const handleEnterFocusMode = useCallback((nodeId: string) => {
    setFocusMode(true);
    setFocusNodeId(nodeId);
    setSelectedNodeId(nodeId);
    
    // Navigate to node
    const node = canvasNodes.find(n => n.id === nodeId);
    if (node && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      setViewport(prev => ({
        ...prev,
        x: centerX - node.x * prev.scale,
        y: centerY - node.y * prev.scale,
        scale: Math.max(prev.scale, 1.2), // Zoom in when focusing
      }));
    }
  }, [canvasNodes]);

  const handleExitFocusMode = useCallback(() => {
    setFocusMode(false);
    setFocusNodeId(null);
  }, []);

  // Get focus mode neighbors
  const focusNeighbors = useMemo(() => {
    if (!focusNodeId) return new Set<string>();
    const node = canvasNodes.find(n => n.id === focusNodeId);
    if (!node) return new Set<string>();
    
    const neighbors = new Set<string>([focusNodeId]);
    if (node.connections) {
      node.connections.forEach(id => neighbors.add(id));
    }
    // Also add reverse connections
    canvasNodes.forEach(n => {
      if (n.connections?.includes(focusNodeId)) {
        neighbors.add(n.id);
      }
    });
    return neighbors;
  }, [focusNodeId, canvasNodes]);

  // Render node with LOD support
  const renderNodeWithLOD = useCallback((node: CanvasNode, lod: LODLevel) => {
    const isSelected = selectedNodeId === node.id;
    const isHovered = hoveredNodeId === node.id;
    
    if (lod === 'dot') {
      // Minimal: just a colored dot
      return (
        <Box
          key={node.id}
          onClick={() => setSelectedNodeId(node.id)}
          onMouseEnter={() => setHoveredNodeId(node.id)}
          onMouseLeave={() => setHoveredNodeId(null)}
          sx={{
            position: 'absolute',
            top: node.y,
            left: node.x,
            width: 12,
            height: 12,
            borderRadius: '50%',
            bgcolor: node.color || '#94A3B8',
            border: isSelected ? '2px solid' : 'none',
            borderColor: 'primary.main',
            cursor: 'pointer',
            zIndex: isSelected ? 10 : 1,
          }}
        />
      );
    }
    
    if (lod === 'minimal') {
      // Minimal: title only
      return (
        <Paper
          key={node.id}
          elevation={isHovered ? 4 : 1}
          onClick={() => setSelectedNodeId(node.id)}
          onMouseEnter={() => setHoveredNodeId(node.id)}
          onMouseLeave={() => setHoveredNodeId(null)}
          sx={{
            position: 'absolute',
            top: node.y,
            left: node.x,
            width: 200,
            p: 1.5,
            borderRadius: 2,
            border: '1px solid',
            borderColor: isSelected ? 'primary.main' : 'divider',
            bgcolor: 'white',
            cursor: 'pointer',
            zIndex: isSelected ? 10 : 1,
          }}
        >
          <Typography variant="caption" fontWeight="bold" noWrap>
            {node.title}
          </Typography>
        </Paper>
      );
    }
    
    if (lod === 'compact') {
      // Compact: title + short content
      return (
        <Paper
          key={node.id}
          elevation={isHovered ? 4 : 1}
          onClick={() => setSelectedNodeId(node.id)}
          onMouseEnter={() => setHoveredNodeId(node.id)}
          onMouseLeave={() => setHoveredNodeId(null)}
          sx={{
            position: 'absolute',
            top: node.y,
            left: node.x,
            width: 240,
            p: 2,
            borderRadius: 3,
            border: '1px solid',
            borderColor: isSelected ? 'primary.main' : 'divider',
            bgcolor: 'white',
            cursor: 'pointer',
            zIndex: isSelected ? 10 : 1,
          }}
        >
          <Typography variant="subtitle2" fontWeight="bold" gutterBottom noWrap>
            {node.title}
          </Typography>
          {node.content && (
            <Typography variant="caption" color="text.secondary" sx={{ 
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {node.content}
            </Typography>
          )}
        </Paper>
      );
    }
    
    // Full: complete node rendering (existing code)
    return null; // Will use existing full rendering
  }, [selectedNodeId, hoveredNodeId]);

  // --- Render Helpers ---
  const renderResource = (res: Resource) => {
    const isActive = activeResource.id === res.id;
    if (viewMode === 'list') {
  return (
        <Box 
          key={res.id} onClick={() => setActiveResource(res)}
          sx={{ 
            display: 'flex', gap: 1.5, p: 1.5, mb: 1, borderRadius: 2, 
            bgcolor: isActive ? '#EFF6FF' : 'transparent', 
            border: isActive ? '1px solid' : '1px solid', borderColor: isActive ? '#BFDBFE' : 'transparent',
            '&:hover': { bgcolor: isActive ? '#EFF6FF' : 'action.hover' }, cursor: 'pointer', transition: 'all 0.2s'
          }}
        >
          {res.type === 'pdf' && <FileText size={16} className={isActive ? "text-blue-600 mt-0.5" : "text-gray-400 mt-0.5"} />}
          {res.type === 'video' && <Video size={16} className="text-gray-400 mt-0.5" />}
          {res.type === 'audio' && <Music size={16} className="text-gray-400 mt-0.5" />}
          {res.type === 'link' && <LinkIcon size={16} className="text-gray-400 mt-0.5" />}
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="body2" fontWeight={isActive ? "500" : "400"} color={isActive ? "primary.main" : "text.primary"} noWrap>{res.title}</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">{res.date}</Typography>
              {(res.duration || res.pages) && <Typography variant="caption" color="text.disabled">•</Typography>}
              {res.duration && <Typography variant="caption" sx={{ color: 'text.secondary', bgcolor: 'action.hover', px: 0.5, borderRadius: 0.5 }}>{res.duration}</Typography>}
              {res.pages && <Typography variant="caption" color="text.secondary">{res.pages}p</Typography>}
              </Box>
              </Box>
            </Box>
      );
    }
    // Grid Mode
    return (
      <Box key={res.id} sx={{ position: 'relative', group: 'card' }} onClick={() => setActiveResource(res)}>
        <Paper
          elevation={0}
                sx={{ 
            p: 0, overflow: 'hidden', borderRadius: 2, border: isActive ? '2px solid' : '1px solid', borderColor: isActive ? 'primary.main' : 'divider',
            cursor: 'pointer', transition: 'all 0.2s', '&:hover': { borderColor: isActive ? 'primary.main' : 'grey.400', transform: 'translateY(-2px)' }, display: 'flex', flexDirection: 'column'
          }}
        >
          <Box sx={{ height: 100, bgcolor: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', borderBottom: '1px solid', borderColor: 'divider' }}>
            {res.type === 'pdf' && (
              <Box sx={{ width: 50, height: 70, bgcolor: 'white', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', p: 0.5, gap: 0.5 }}>
                <Box sx={{ width: '80%', height: 4, bgcolor: '#E5E7EB', borderRadius: 1 }} /><Box sx={{ width: '100%', height: 2, bgcolor: '#F3F4F6' }} /><Box sx={{ width: '100%', height: 2, bgcolor: '#F3F4F6' }} /><Box sx={{ width: '60%', height: 2, bgcolor: '#F3F4F6' }} />
                <Box sx={{ position: 'absolute', top: 0, right: 0, borderStyle: 'solid', borderWidth: '0 8px 8px 0', borderColor: 'transparent #F3F4F6 transparent transparent' }} />
              </Box>
            )}
            {res.type === 'video' && (
              <Box sx={{ width: '100%', height: '100%', bgcolor: '#1F2937', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <PlayCircle size={32} className="text-white opacity-80" />
                <Box sx={{ position: 'absolute', bottom: 4, right: 4, bgcolor: 'rgba(0,0,0,0.7)', color: '#fff', px: 0.5, borderRadius: 0.5, fontSize: 10, fontWeight: 600 }}>{res.duration}</Box>
              </Box>
            )}
             {res.type === 'audio' && (
              <Box sx={{ width: '100%', height: '100%', bgcolor: '#1F2937', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Music size={32} className="text-purple-400 opacity-80" />
                <Box sx={{ position: 'absolute', bottom: 4, right: 4, bgcolor: 'rgba(0,0,0,0.7)', color: '#fff', px: 0.5, borderRadius: 0.5, fontSize: 10, fontWeight: 600 }}>{res.duration}</Box>
              </Box>
            )}
             {res.type === 'link' && <Box sx={{ width: '100%', height: '100%', bgcolor: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Globe size={32} className="text-blue-300" /></Box>}
            {isActive && <Box sx={{ position: 'absolute', top: 8, right: 8, width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.main', border: '2px solid white' }} />}
              </Box>
          <Box sx={{ p: 1.5 }}>
            <Typography variant="caption" fontWeight="600" sx={{ display: 'block', lineHeight: 1.2, mb: 0.5 }} noWrap title={res.title}>{res.title}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
               {res.type === 'pdf' && <FileText size={12} className="text-gray-400" />}{res.type === 'video' && <Video size={12} className="text-gray-400" />}{res.type === 'audio' && <Music size={12} className="text-gray-400" />}{res.type === 'link' && <LinkIcon size={12} className="text-gray-400" />}
               <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>{res.date}</Typography>
            </Box>
                </Box>
              </Paper>
            </Box>
    );
  };

  // --- Render Content Viewer (Bottom Panel) ---
  const renderContentViewer = () => {
    const { type, title, duration } = activeResource;
    return (
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Box onMouseDown={handleVerticalMouseDown} sx={{ height: 48, borderTop: isReaderExpanded ? 'none' : '1px solid', borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', bgcolor: 'background.default', cursor: isReaderExpanded ? 'default' : 'row-resize', userSelect: 'none', position: 'relative', flexShrink: 0 }}>
          {!isReaderExpanded && <Box sx={{ position: 'absolute', top: -1, left: '50%', transform: 'translateX(-50%)', width: 40, height: 3, bgcolor: 'transparent', cursor: 'row-resize' }} />}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, overflow: 'hidden' }}>
            <Typography variant="caption" sx={{ color: type === 'pdf' ? 'error.main' : type === 'video' ? 'primary.main' : type === 'audio' ? 'purple.main' : 'blue.main', fontWeight: 'bold', bgcolor: type === 'pdf' ? 'error.lighter' : type === 'video' ? 'grey.200' : type === 'audio' ? 'purple.50' : 'blue.50', px: 0.5, borderRadius: 0.5, textTransform: 'uppercase' }}>{type}</Typography>
            <Typography variant="subtitle2" fontWeight="600" noWrap>{title}</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexShrink: 0 }}>
            {type === 'pdf' && <Typography variant="caption" color="text.secondary">Pg 3 / 15</Typography>}
            {(type === 'video' || type === 'audio') && duration && <Typography variant="caption" color="text.secondary">{duration}</Typography>}
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); setIsReaderExpanded(!isReaderExpanded); }}>{isReaderExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}</IconButton>
          </Box>
        </Box>

        {type === 'pdf' && (
          <Box 
            data-pdf-viewer
            sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}
            onClick={handleCloseContextMenu}
          >
            <PDFViewer
              documentId={activeResource.id}
              content={
                <Box sx={{ p: 4 }}>
                  <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>3.2 Attention</Typography>
                  <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: 'text.secondary' }}>An attention function can be described as mapping a query and a set of key-value pairs to an output.</Typography>
                  
                  {/* Highlighted Text Area simulating user selection */}
                  <Box 
                    component="span"
                    onContextMenu={handleContextMenu}
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData("text/plain", "The output is computed as a weighted sum of the values.");
                      e.dataTransfer.effectAllowed = "copy";
                      setIsDraggingFromPdf(true);
                    }}
                    onDragEnd={() => {
                      setIsDraggingFromPdf(false);
                    }}
                    sx={{ 
                      bgcolor: sourceNavigation?.searchText?.includes('output is computed') ? '#FFEB3B' : '#FFF9C4', 
                      p: 0.5, 
                      borderRadius: 1, 
                      mx: -0.5,
                      cursor: 'text',
                      display: 'inline',
                      border: '1px solid transparent',
                      '&:hover': { border: '1px dashed', borderColor: 'orange.300', cursor: 'grab' } 
                    }}
                  >
                    <Typography component="span" variant="body1" sx={{ lineHeight: 1.8, fontWeight: 500 }}>The output is computed as a weighted sum of the values.</Typography>
                  </Box>
                  
                  {/* Additional content that can be highlighted based on source navigation */}
                  {sourceNavigation && sourceNavigation.resourceId === activeResource.id && sourceNavigation.searchText && (
                    <Typography 
                      variant="body1" 
                      paragraph 
                      sx={{ 
                        lineHeight: 1.8, 
                        color: 'text.secondary',
                        mt: 2,
                        '& .highlighted-text': {
                          bgcolor: '#FFEB3B',
                          borderRadius: '2px',
                          padding: '1px 2px',
                          fontWeight: 500,
                        }
                      }}
                    >
                      {sourceNavigation.searchText.toLowerCase().includes('bert') && activeResource.title.includes('BERT') && (
                        <>
                          BERT is designed to{' '}
                          <Box component="span" className="highlighted-text">
                            pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers
                          </Box>
                          . This approach allows the model to understand the full context of a word by looking at both its left and right neighbors simultaneously.
                        </>
                      )}
                      {sourceNavigation.searchText.toLowerCase().includes('transformer') && activeResource.title.includes('Attention') && (
                        <>
                          The{' '}
                          <Box component="span" className="highlighted-text">
                            Transformer model relies entirely on self-attention to compute representations
                          </Box>
                          {' '}of its input and output without using sequence-aligned RNNs or convolution.
                        </>
                      )}
                      {!sourceNavigation.searchText.toLowerCase().includes('bert') && !sourceNavigation.searchText.toLowerCase().includes('transformer') && (
                        <>
                          <Box component="span" className="highlighted-text">
                            {sourceNavigation.searchText}
                          </Box>
                          {' '}This is the relevant content from the document that matches your query.
                        </>
                      )}
                    </Typography>
                  )}

                  <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: 'text.secondary', mt: 2 }}>
                    The two most commonly used attention functions are additive attention, and dot-product (multiplicative) attention. 
                  </Typography>

                  <Paper variant="outlined" sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', my: 4, borderStyle: 'dashed' }}><Box sx={{ textAlign: 'center', color: 'text.disabled' }}><ImageIcon size={32} className="mx-auto mb-2" /><Typography variant="caption">Figure 1: Scaled Dot-Product Attention</Typography></Box></Paper>
                </Box>
              }
              onHighlightCreate={(highlight) => {
                console.log('Highlight created:', highlight);
              }}
              onHighlightUpdate={(highlight) => {
                console.log('Highlight updated:', highlight);
              }}
              onHighlightDelete={(highlightId) => {
                console.log('Highlight deleted:', highlightId);
              }}
            />
          
            {/* Context Menu */}
            <Menu
              open={contextMenu !== null}
              onClose={handleCloseContextMenu}
              anchorReference="anchorPosition"
              anchorPosition={
                contextMenu !== null
                  ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
                  : undefined
              }
              PaperProps={{ sx: { width: 200, borderRadius: 2 } }}
            >
              <MenuItem onClick={() => handleCreateCard()}>
                <ListItemIcon><Layout size={16} /></ListItemIcon>
                <ListItemText primary="Create as Card" secondary="Add to Canvas" secondaryTypographyProps={{ fontSize: 10 }} />
              </MenuItem>
              <MenuItem onClick={handleCloseContextMenu}>
                <ListItemIcon><Bot size={16} /></ListItemIcon>
                <ListItemText primary="Ask AI about this" />
              </MenuItem>
            </Menu>
          </Box>
        )}
        {type === 'video' && (
          <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', position: 'relative', bgcolor: '#000' }}>
             {/* Player Area */}
            <Box sx={{ height: '45%', display: 'flex', flexDirection: 'column', justifyContent: 'center', position: 'relative', borderBottom: '1px solid #333' }}>
            <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Typography variant="body2" sx={{ color: 'grey.500' }}>[ Video Placeholder: {title} ]</Typography></Box>
            <Box sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}><Slider size="small" defaultValue={30} sx={{ color: '#fff', mb: 1 }} /><Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#fff' }}><Box sx={{ display: 'flex', gap: 2 }}><Play size={20} fill="currentColor" /><Volume2 size={20} /></Box><Typography variant="caption">12:30 / {duration}</Typography></Box></Box>
            </Box>

            {/* Transcript Area */}
            <Box sx={{ flexGrow: 1, bgcolor: '#fff', display: 'flex', flexDirection: 'column', height: '55%' }}>
                 <Box sx={{ p: 1.5, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: '#F9FAFB' }}>
                    <Typography variant="subtitle2" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><ListIcon size={14} /> Transcript</Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <Chip label="English" size="small" sx={{ height: 20, fontSize: 10, bgcolor: '#fff', border: '1px solid', borderColor: 'divider' }} />
                    </Box>
                </Box>
                <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
                    {[
                        { time: '00:15', text: "Welcome to the course. Today we discuss Transformers." },
                        { time: '02:30', text: "The attention mechanism is the key component of this architecture." },
                        { time: '12:30', text: "It allows the model to focus on relevant parts of the input sequence.", highlight: true },
                        { time: '15:45', text: "Let's look at the mathematical formulation of Self-Attention." }
                    ].map((item, idx) => (
                         <Box key={idx} sx={{ display: 'flex', gap: 2, mb: 2.5, opacity: item.highlight ? 1 : 0.7, '&:hover': { opacity: 1 } }}>
                            <Typography variant="caption" sx={{ color: 'primary.main', fontFamily: 'monospace', flexShrink: 0, pt: 0.5, cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}>{item.time}</Typography>
                            <Typography 
                                variant="body2" 
                                draggable
                                onDragStart={(e) => {
                                    e.dataTransfer.setData("text/plain", item.text);
                                    e.dataTransfer.setData("application/json", JSON.stringify({ type: 'transcript', text: item.text, timestamp: item.time, sourceId: activeResource.id }));
                                    e.dataTransfer.effectAllowed = "copy";
                                    setIsDraggingFromPdf(true);
                                }}
                                onDragEnd={() => setIsDraggingFromPdf(false)}
                                sx={{ 
                                    cursor: 'grab', 
                                    bgcolor: item.highlight ? '#EFF6FF' : 'transparent',
                                    p: item.highlight ? 1 : 0,
                                    borderRadius: 1,
                                    border: item.highlight ? '1px solid' : '1px solid transparent',
                                    borderColor: item.highlight ? 'primary.light' : 'transparent',
                                    lineHeight: 1.6,
                                    '&:hover': { bgcolor: '#F3F4F6' }
                                }}
                            >
                                {item.text}
                            </Typography>
                         </Box>
                    ))}
                </Box>
            </Box>
          </Box>
        )}
        {type === 'audio' && (
          <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', position: 'relative', bgcolor: '#1F2937' }}>
            {/* Player Area */}
            <Box sx={{ height: '45%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 2, borderBottom: '1px solid #374151' }}>
              <Box sx={{ width: 80, height: 80, borderRadius: 4, bgcolor: 'primary.main', mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 20px 40px rgba(0,0,0,0.3)' }}><Music size={32} color="#fff" /></Box>
              <Typography variant="subtitle1" sx={{ color: '#fff', mb: 0.5, textAlign: 'center' }}>{title}</Typography>
              <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', height: 24, mb: 2 }}>{[...Array(20)].map((_, i) => (<Box key={i} sx={{ width: 3, height: Math.random() * 24 + 6, bgcolor: i === 10 ? '#fff' : 'grey.600', borderRadius: 2 }} />))}</Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, color: '#fff' }}><SkipBack size={20} /><Box sx={{ width: 48, height: 48, borderRadius: '50%', bgcolor: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000' }}><Play size={20} fill="currentColor" className="ml-1" /></Box><SkipForward size={20} /></Box>
            </Box>

             {/* Transcript Area */}
            <Box sx={{ flexGrow: 1, bgcolor: '#fff', display: 'flex', flexDirection: 'column', height: '55%' }}>
                 <Box sx={{ p: 1.5, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: '#F9FAFB' }}>
                    <Typography variant="subtitle2" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><ListIcon size={14} /> Transcript</Typography>
                </Box>
                <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
                   {[
                        { time: '00:05', text: "In this episode, we explore the depths of DeepMind's latest research." },
                        { time: '04:12', text: "Reinforcement learning has shown remarkable results in complex environments." },
                        { time: '15:00', text: "AlphaGo was a turning point for the field of AI.", highlight: true },
                        { time: '22:30', text: "The future of AGI depends on generalizable learning algorithms." }
                    ].map((item, idx) => (
                         <Box key={idx} sx={{ display: 'flex', gap: 2, mb: 2.5, opacity: item.highlight ? 1 : 0.7, '&:hover': { opacity: 1 } }}>
                            <Typography variant="caption" sx={{ color: 'purple.500', fontFamily: 'monospace', flexShrink: 0, pt: 0.5, cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}>{item.time}</Typography>
                            <Typography 
                                variant="body2" 
                                draggable
                                onDragStart={(e) => {
                                    e.dataTransfer.setData("text/plain", item.text);
                                    e.dataTransfer.setData("application/json", JSON.stringify({ type: 'transcript', text: item.text, timestamp: item.time, sourceId: activeResource.id }));
                                    e.dataTransfer.effectAllowed = "copy";
                                    setIsDraggingFromPdf(true);
                                }}
                                onDragEnd={() => setIsDraggingFromPdf(false)}
                                sx={{ 
                                    cursor: 'grab', 
                                    bgcolor: item.highlight ? '#F5F3FF' : 'transparent',
                                    p: item.highlight ? 1 : 0,
                                    borderRadius: 1,
                                    border: item.highlight ? '1px solid' : '1px solid transparent',
                                    borderColor: item.highlight ? 'purple.200' : 'transparent',
                                    lineHeight: 1.6,
                                    '&:hover': { bgcolor: '#FAF5FF' }
                                }}
                            >
                                {item.text}
                            </Typography>
                         </Box>
                    ))}
                </Box>
            </Box>
          </Box>
        )}
        {type === 'link' && (
           <Box sx={{ flexGrow: 1, bgcolor: '#F9FAFB', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4 }}>
             <Box sx={{ textAlign: 'center', mb: 4 }}><Globe size={48} className="text-gray-300 mb-2 mx-auto" /><Typography variant="h6" gutterBottom>External Resource</Typography><Button variant="outlined" startIcon={<ExternalLink size={16} />} href="https://huggingface.co" target="_blank">Open in Browser</Button></Box>
           </Box>
        )}
      </Box>
    );
  };

  // --- Render Tab Content ---
  const renderTabContent = () => {
    const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];
    
    // Loading State
    if (activeTab.status === 'generating') {
      return (
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: '#F9FAFB' }}>
           <Box sx={{ position: 'relative', display: 'inline-flex', mb: 3 }}>
             <CircularProgress size={60} thickness={4} sx={{ color: 'primary.main' }} />
             <Box sx={{ top: 0, left: 0, bottom: 0, right: 0, position: 'absolute', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               {activeTab.type === 'podcast' && <Mic size={24} className="text-primary-main" />}
               {activeTab.type === 'flashcards' && <BrainCircuit size={24} className="text-primary-main" />}
               {activeTab.type === 'ppt' && <Presentation size={24} className="text-primary-main" />}
             </Box>
           </Box>
           <Typography variant="h6" fontWeight="bold" gutterBottom>Generating {activeTab.title}...</Typography>
           <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>AI is analyzing your resources and synthesizing content.</Typography>
           <Box sx={{ width: 300 }}>
             <LinearProgress variant="determinate" value={activeTab.progress || 0} sx={{ borderRadius: 2, height: 6 }} />
                </Box>
              </Box>
      );
    }

    // Ready State
    switch (activeTab.type) {
      case 'podcast': return <PodcastView />;
      case 'writer': return <WriterView />;
      case 'canvas': 
      default:
        // Viewport culling: Calculate visible nodes and connections
        // Use explicit dependencies instead of viewport object to avoid unnecessary recalculations
        const visibleData = useMemo(() => {
          // Get nodes considering filters and groups
          const baseNodes = getVisibleNodes();
          
          if (baseNodes.length === 0) {
            return { visibleNodes: baseNodes, visibleConnections: [] };
          }
          
          // Read ref but don't include it in dependencies (refs don't trigger re-renders)
          const rect = canvasRef.current?.getBoundingClientRect();
          if (!rect) {
            return { visibleNodes: baseNodes, visibleConnections: [] };
          }
          
          // Enhanced virtualization: dynamic padding based on scale and performance
          // Larger padding for smoother scrolling, but adaptive to prevent over-rendering
          const basePadding = 300;
          const scaleFactor = Math.max(0.5, Math.min(2, viewport.scale)); // Clamp scale factor
          const padding = basePadding * (1 / scaleFactor); // More padding when zoomed out
          
          // Calculate viewport bounds in canvas coordinates with buffer zone
          const viewportLeft = (-viewport.x - padding) / viewport.scale;
          const viewportRight = (-viewport.x + rect.width + padding) / viewport.scale;
          const viewportTop = (-viewport.y - padding) / viewport.scale;
          const viewportBottom = (-viewport.y + rect.height + padding) / viewport.scale;
          
          // Filter nodes in viewport
          const visibleNodes = baseNodes.filter(node => {
            const nodeRight = node.x + 280; // Card width
            const nodeBottom = node.y + 200; // Approximate card height
            return node.x < viewportRight && nodeRight > viewportLeft &&
                   node.y < viewportBottom && nodeBottom > viewportTop;
          });
          
          // Filter connections where both nodes are visible
          const visibleConnections: Array<{ source: CanvasNode; target: CanvasNode; connectionId: string }> = [];
          visibleNodes.forEach(node => {
            if (node.connections) {
              node.connections.forEach(targetId => {
                const target = visibleNodes.find(n => n.id === targetId);
                if (target) {
                  visibleConnections.push({
                    source: node,
                    target,
                    connectionId: `${node.id}-${targetId}`
                  });
                }
              });
            }
          });
          
          return { visibleNodes, visibleConnections };
        }, [canvasNodes, viewport.x, viewport.y, viewport.scale, searchQuery, selectedTags, nodeGroups, getVisibleNodes]); // Explicit dependencies
        
        const { visibleNodes, visibleConnections } = visibleData;
        const currentLOD = getNodeLOD(viewport.scale);
        const connectionLOD = getConnectionLOD(viewport.scale);
        const textLOD = getTextLOD(viewport.scale);
        
        // Render different views based on viewMode
        const renderListView = () => (
          <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
              <TextField
                size="small"
                placeholder="Search nodes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                sx={{ flexGrow: 1, maxWidth: 400 }}
                InputProps={{
                  startAdornment: <Search size={16} style={{ marginRight: 8, color: '#9CA3AF' }} />,
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {filteredNodes.length} nodes
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {filteredNodes.map(node => (
                <Paper
                  key={node.id}
                  elevation={selectedNodeId === node.id ? 4 : 1}
                  onClick={() => {
                    setSelectedNodeId(node.id);
                    // Jump to node in canvas
                    const rect = canvasRef.current?.getBoundingClientRect();
                    if (rect) {
                      const centerX = rect.width / 2;
                      const centerY = rect.height / 2;
                      setViewport({
                        x: centerX - node.x * viewport.scale,
                        y: centerY - node.y * viewport.scale,
                        scale: viewport.scale,
                      });
                    }
                  }}
                  sx={{
                    p: 2,
                    cursor: 'pointer',
                    border: selectedNodeId === node.id ? '2px solid' : '1px solid',
                    borderColor: selectedNodeId === node.id ? 'primary.main' : 'divider',
                    bgcolor: selectedNodeId === node.id ? 'primary.50' : 'white',
                    '&:hover': { bgcolor: 'action.hover' },
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                        {node.title}
                      </Typography>
                      {node.content && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          {node.content.substring(0, 150)}...
                        </Typography>
                      )}
                      {node.tags && (
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {node.tags.map(tag => (
                            <Chip key={tag} label={tag} size="small" sx={{ fontSize: 10, height: 20 }} />
                          ))}
                        </Box>
                      )}
                    </Box>
                    {node.color && (
                      <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: node.color, ml: 2, mt: 1 }} />
                    )}
                  </Box>
                </Paper>
              ))}
            </Box>
          </Box>
        );

        const renderHierarchicalView = () => {
          // Group nodes by community or tags
          const groups = nodeGroups.length > 0 ? nodeGroups : [];
          
          if (groups.length === 0) {
            return (
              <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 2 }}>
                <Typography variant="body1" color="text.secondary">
                  No groups found. Click "Group by Community" to create groups.
                </Typography>
                <Button variant="outlined" onClick={handleGroupByCommunity}>
                  Create Groups
                </Button>
              </Box>
            );
          }
          
          return (
            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
              {groups.map(group => (
                <Paper
                  key={group.id}
                  elevation={2}
                  sx={{
                    mb: 2,
                    p: 2,
                    border: '1px solid',
                    borderColor: group.color,
                    bgcolor: `${group.color}10`,
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: group.color }} />
                      <Typography variant="subtitle1" fontWeight="bold">
                        {group.title}
                      </Typography>
                    </Box>
                    <IconButton size="small" onClick={() => handleToggleGroup(group.id)}>
                      {group.collapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
                    </IconButton>
                  </Box>
                  <Collapse in={!group.collapsed}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 1 }}>
                      {group.nodeIds.map(nodeId => {
                        const node = canvasNodes.find(n => n.id === nodeId);
                        if (!node) return null;
                        return (
                          <Paper
                            key={node.id}
                            elevation={0}
                            onClick={() => setSelectedNodeId(node.id)}
                            sx={{
                              p: 1.5,
                              cursor: 'pointer',
                              bgcolor: selectedNodeId === node.id ? 'primary.50' : 'white',
                              border: selectedNodeId === node.id ? '1px solid' : '1px solid',
                              borderColor: selectedNodeId === node.id ? 'primary.main' : 'divider',
                              '&:hover': { bgcolor: 'action.hover' },
                            }}
                          >
                            <Typography variant="body2" fontWeight="500">
                              {node.title}
                            </Typography>
                          </Paper>
                        );
                      })}
                    </Box>
                  </Collapse>
                </Paper>
              ))}
            </Box>
          );
        };
        
        // Main canvas view (default)
        if (canvasViewMode !== 'canvas') {
          return (
            <Box sx={{ position: 'relative', flexGrow: 1, height: '100%', overflow: 'hidden', bgcolor: '#F9FAFB' }}>
              {canvasViewMode === 'list' && renderListView()}
              {canvasViewMode === 'hierarchical' && renderHierarchicalView()}
              {canvasViewMode === 'minimap' && (
                <Box sx={{ p: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Minimap view coming soon...
                  </Typography>
                </Box>
              )}
              {canvasViewMode === 'cluster' && (
                <Box sx={{ p: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Cluster view coming soon...
                  </Typography>
                </Box>
              )}
            </Box>
          );
        }
        
        return (
          <Box sx={{ position: 'relative', flexGrow: 1, height: '100%', overflow: 'hidden' }}>
            {/* Project Initializer Overlay */}
            {isInitializing && (
              <ProjectInitializer 
                projectId={projectId} 
                onComplete={() => setIsInitializing(false)} 
              />
            )}
            
          <Box 
            ref={canvasRef}
            className={isPanning ? 'panning' : ''}
            sx={{ 
                width: '100%',
                height: '100%',
                bgcolor: '#F9FAFB', 
                position: 'relative',
                overflow: 'hidden',
                cursor: isSpacePressed ? (isPanning ? 'grabbing' : 'grab') : 'default',
                touchAction: 'none', // Prevent native browser zooming
                userSelect: 'none',   // Prevent text selection while dragging
                // Performance optimizations
                contain: 'layout style paint', // CSS containment for better performance
                willChange: isPanning || draggingNodeId ? 'contents' : 'auto',
            }}
            onMouseDown={(e) => {
                // Only start panning if:
                // 1. Space is pressed (force pan mode)
                // 2. Middle mouse button
                // 3. Left click on empty background (not on a node - nodes stopPropagation)
                if (isSpacePressed || e.button === 1) {
                   setIsPanning(true);
                   lastMousePos.current = { x: e.clientX, y: e.clientY };
                } else if (e.button === 0) {
                   // Left click on background - deselect, but DON'T pan (let user marquee select in future)
                   setSelectedNodeId(null);
                   setSelectedConnectionId(null);
                   // For now, also allow panning on background drag
                   setIsPanning(true);
                   lastMousePos.current = { x: e.clientX, y: e.clientY };
                }
            }}
            onMouseMove={(e) => {
                mousePos.current = { x: e.clientX, y: e.clientY };
                const manager = rafManager.current;
                
                // Update temp line end position when connecting
                if (connectingNodeId && canvasRef.current) {
                    const rect = canvasRef.current.getBoundingClientRect();
                    const currentViewport = viewportRef.current;
                    const canvasX = (e.clientX - rect.left - currentViewport.x) / currentViewport.scale;
                    const canvasY = (e.clientY - rect.top - currentViewport.y) / currentViewport.scale;
                    mousePos.current = { x: canvasX, y: canvasY };
                    // Store in pending update
                    manager.pendingTempLine = { x: canvasX, y: canvasY };
                } else if (draggingNodeId) {
                    // Calculate total movement since drag start
                    if (dragStartPos.current) {
                        const moveX = Math.abs(e.clientX - dragStartPos.current.x);
                        const moveY = Math.abs(e.clientY - dragStartPos.current.y);
                        if (moveX < 3 && moveY < 3) {
                            lastMousePos.current = { x: e.clientX, y: e.clientY };
                            return;
                        }
                        dragStartPos.current = null; 
                    }

                    // Dragging Node logic (Canvas Space)
                    const currentViewport = viewportRef.current;
                    const dx = (e.clientX - lastMousePos.current.x) / currentViewport.scale;
                    const dy = (e.clientY - lastMousePos.current.y) / currentViewport.scale;
                    
                    // Store in pending update
                    manager.pendingNodeDrag = { nodeId: draggingNodeId, dx, dy };
                    
                    lastMousePos.current = { x: e.clientX, y: e.clientY };
                } else if (isPanning && !draggingNodeId) {
                    // Panning Viewport logic (Screen Space)
                    const dx = e.clientX - lastMousePos.current.x;
                    const dy = e.clientY - lastMousePos.current.y;
                    
                    // Store in pending update
                    manager.pendingPan = { dx, dy };
                    
                    lastMousePos.current = { x: e.clientX, y: e.clientY };
                }
                
                // Schedule RAF update if not already scheduled
                if (manager.rafId === null && applyRafUpdatesRef.current) {
                    manager.rafId = requestAnimationFrame(applyRafUpdatesRef.current);
                }
            }}
            onMouseUp={() => {
                setIsPanning(false);
                setDraggingNodeId(null);
                dragStartPos.current = null;
                // Cancel connection if mouse released on empty space (not on a card)
                setConnectingNodeId(null);
                setTempLineEnd(null);
            }}
            onMouseLeave={() => {
                setIsPanning(false);
                setDraggingNodeId(null);
                setConnectingNodeId(null);
                setTempLineEnd(null);
                dragStartPos.current = null;
            }}
            onClick={(e) => {
              // Clear selection when clicking on empty canvas (not on a node)
              if (e.target === e.currentTarget) {
                setSelectedNodeId(null);
                setSelectedNodeIds(new Set());
              }
            }}
            onDragOver={(e) => {
              e.preventDefault();
              e.dataTransfer.dropEffect = "copy";

              // Update drag preview position while dragging AI response
              if (dragContentRef.current && canvasRef.current) {
                const rect = canvasRef.current.getBoundingClientRect();
                const screenX = e.clientX - rect.left;
                const screenY = e.clientY - rect.top;
                const canvasX = (screenX - viewport.x) / viewport.scale;
                const canvasY = (screenY - viewport.y) / viewport.scale;

                setDragPreview({
                  x: canvasX,
                  y: canvasY,
                  content: dragContentRef.current,
                });
              }
            }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();

              // Calculate drop position in Canvas Coordinates
              const rect = canvasRef.current?.getBoundingClientRect();
              if (rect) {
                  const screenX = e.clientX - rect.left;
                  const screenY = e.clientY - rect.top;
                  const canvasX = (screenX - viewport.x) / viewport.scale;
                  const canvasY = (screenY - viewport.y) / viewport.scale;

                  // Try parsing JSON metadata first
                  const jsonData = e.dataTransfer.getData("application/json");
                  let handled = false;
                  if (jsonData) {
                    try {
                      const data = JSON.parse(jsonData);
                      
                      // From transcript / timeline
                      if (data.type === 'transcript') {
                        handleCreateCard(
                          data.text, 
                          { 
                            timestamp: data.timestamp, 
                            sourceId: data.sourceId, 
                            sourcePage: data.pageNumber, 
                            sourceText: data.text,
                            sourceType: 'pdf',
                          }, 
                          { x: canvasX, y: canvasY }
                        );
                        handled = true;
                      }

                      // From AI Assistant response drag
                      if (!handled && data.type === 'ai_response') {
                        handleCreateCard(
                          data.content,
                          {
                            sourceType: 'chat',
                            sourceMessageId: data.source?.messageId,
                            sourceQuery: data.source?.query,
                            timestamp: data.source?.timestamp,
                          },
                          { x: canvasX, y: canvasY }
                        );
                        handled = true;
                      }
                    } catch(err) { 
                      console.error(err); 
                    }
                  }

                  if (!handled) {
                    const text = e.dataTransfer.getData("text/plain");
                    if (text) {
                      handleCreateCard(text, undefined, { x: canvasX, y: canvasY });
                    }
                  }
              }

              setIsDraggingFromPdf(false);
              setDragPreview(null);
            }}
          >
            {/* Floating Toolbar */}
            {(selectedNodeId || selectedNodeIds.size > 0) && (
              <Box
                sx={{
                  position: 'absolute',
                  top: 20,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  zIndex: 1000,
                  display: 'flex',
                  gap: 1,
                  alignItems: 'center',
                  bgcolor: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(8px)',
                  borderRadius: 2,
                  p: 1,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  border: '1px solid',
                  borderColor: 'divider',
                  transition: 'opacity 0.2s, transform 0.2s',
                }}
              >
                {selectedNodeIds.size === 2 ? (
                  // Smart Fusion button when exactly 2 nodes selected
                  <Button
                    variant="contained"
                    startIcon={<SparklesIcon size={18} />}
                    onClick={() => {
                      const ids = Array.from(selectedNodeIds);
                      if (ids.length === 2) {
                        handleFuseNodes(ids[0], ids[1]);
                      }
                    }}
                    disabled={isAiProcessing}
                    sx={{
                      bgcolor: '#9333EA',
                      color: 'white',
                      '&:hover': { bgcolor: '#7E22CE' },
                      minWidth: 140,
                    }}
                  >
                    {isAiProcessing ? <CircularProgress size={16} /> : 'Smart Fusion'}
                  </Button>
                ) : (
                  // Single node actions
                  <>
                    {(() => {
                      const nodeId = selectedNodeId || Array.from(selectedNodeIds)[0];
                      const node = canvasNodes.find(n => n.id === nodeId);
                      if (!node) return null;
                      
                      return (
                        <>
                          {!node.isSimplified && (
                            <Tooltip title="AI Simplify">
                              <IconButton
                                size="small"
                                onClick={() => handleSimplifyNode(nodeId)}
                                disabled={isAiProcessing}
                                sx={{ color: 'primary.main' }}
                              >
                                {isAiProcessing ? <CircularProgress size={16} /> : <Wand2 size={18} />}
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="AI Critique">
                            <IconButton
                              size="small"
                              onClick={() => handleCritiqueNode(nodeId)}
                              disabled={isAiProcessing}
                              sx={{ color: 'error.main' }}
                            >
                              {isAiProcessing ? <CircularProgress size={16} /> : <AlertCircle size={18} />}
                            </IconButton>
                          </Tooltip>
                        </>
                      );
                    })()}
                  </>
                )}
                {/* Delete button for any selection */}
                <Tooltip title="Delete">
                  <IconButton
                    size="small"
                    onClick={handleDeleteSelectedNodes}
                    sx={{ color: 'error.main' }}
                  >
                    <Trash2 size={18} />
                  </IconButton>
                </Tooltip>
              </Box>
            )}
            
            {/* Infinite Grid Background - Static (no recalc on viewport change) */}
            <Box 
              sx={{ 
                position: 'absolute', 
                inset: 0, 
                opacity: 0.3, 
                backgroundImage: 'radial-gradient(#CBD5E1 1px, transparent 1px)', 
                backgroundSize: '24px 24px',
                pointerEvents: 'none',
                // Use transform for better performance
                transform: `translate3d(${viewport.x % 24}px, ${viewport.y % 24}px, 0) scale(${viewport.scale})`,
                transformOrigin: '0 0',
              }} 
            />
            
            {/* Focus Mode Overlay */}
            {focusMode && (
              <Box
                sx={{
                  position: 'absolute',
                  inset: 0,
                  bgcolor: 'rgba(0, 0, 0, 0.3)',
                  zIndex: 5,
                  pointerEvents: 'none',
                  transition: 'background-color 0.3s',
                }}
              />
            )}
            
            {/* Canvas Content Container - Transformed */}
            <Box 
            sx={{ 
                transform: `translate3d(${viewport.x}px, ${viewport.y}px, 0) scale(${viewport.scale})`,
                transformOrigin: '0 0',
                willChange: isPanning || draggingNodeId ? 'transform' : 'auto',
                position: 'absolute',
                top: 0, 
                left: 0,
                // Performance: Force GPU layer
                backfaceVisibility: 'hidden',
                perspective: 1000,
              }}
            >
              {/* Drag Preview for AI Insights */}
              {dragPreview && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: dragPreview.y - 80,
                    left: dragPreview.x - 140,
                    width: 280,
                    pointerEvents: 'none',
                    opacity: 0.7,
                    zIndex: 20,
                  }}
                >
                  <Paper
                    elevation={6}
                    sx={{
                      borderRadius: 3,
                      border: '1px dashed',
                      borderColor: 'primary.main',
                      bgcolor: 'background.paper',
                      p: 2,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Bot size={14} className="text-blue-600" />
                      <Typography variant="caption" fontWeight="bold" color="primary.main">
                        AI Insight (Preview)
                      </Typography>
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        maxHeight: 72,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {dragPreview.content}
                    </Typography>
                  </Paper>
                </Box>
              )}
                  {/* SVG Connections - Render lines between connected nodes (only visible) */}
              <svg style={{ 
                position: 'absolute', 
                top: 0, 
                left: 0, 
                width: 10000, 
                height: 10000, 
                overflow: 'visible', 
                pointerEvents: 'visiblePainted',
                shapeRendering: 'geometricPrecision',
              }}>
                {/* Background rect to pass through events */}
                <rect width="10000" height="10000" fill="transparent" style={{ pointerEvents: 'none' }} />
                    {/* Existing Connections - only render visible ones */}
                    {visibleConnections.map(({ source: node, target, connectionId }) => {
                        // Start from right edge of source, end at left edge of target
                        const x1 = node.x + 280; // Right edge (card width)
                        const y1 = node.y + 60;  // Vertical center approx
                        const x2 = target.x;     // Left edge
                        const y2 = target.y + 60;
                        
                        const dx = Math.abs(x2 - x1);
                        const controlX = Math.max(dx * 0.4, 50);
                        const isSelected = selectedConnectionId === connectionId;
                        
                        // Hover highlight: check if connection is related to hovered node
                        const isHovered = hoveredNodeId === node.id || hoveredNodeId === target.id;
                        const shouldHighlight = showAllConnections || isHovered || isSelected;
                        let opacity = shouldHighlight ? 1 : (hoveredNodeId ? 0.2 : 1); // Dim non-hovered when hovering
                        
                        // Focus mode: dim connections not in focus
                        if (focusMode) {
                          const isInFocus = focusNeighbors.has(node.id) && focusNeighbors.has(target.id);
                          opacity = isInFocus ? opacity : opacity * 0.2;
                        }
                        
                        // Learning path: check if this connection is the next step
                        const activePath = learningPaths.find(p => p.id === activeLearningPath);
                        const isNextStepConnection = activePath && 
                          activePath.currentStep < activePath.nodeIds.length - 1 &&
                          node.id === activePath.nodeIds[activePath.currentStep] &&
                          target.id === activePath.nodeIds[activePath.currentStep + 1];
                        
                        // Apply connection LOD: simplified mode uses straight line
                        const pathD = connectionLOD === 'simplified' 
                          ? `M ${x1} ${y1} L ${x2} ${y2}`  // Straight line
                          : `M ${x1} ${y1} C ${x1 + controlX} ${y1}, ${x2 - controlX} ${y2}, ${x2} ${y2}`; // Curved

                        return (
                            <g key={connectionId}>
                              {/* Invisible wider path for easier clicking */}
                              <path 
                                d={pathD}
                                stroke="transparent" 
                                strokeWidth="12" 
                                fill="none"
                                style={{ pointerEvents: 'stroke', cursor: 'pointer' }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedConnectionId(connectionId);
                                  setSelectedNodeId(null);
                                }}
                              />
                              {/* Visible path with LOD and hover highlight */}
                              <path 
                                d={pathD}
                                stroke={
                                  isSelected ? "#EF4444" : 
                                  isNextStepConnection ? "#10B981" : // Green for next step
                                  isHovered ? "#3B82F6" :
                                  selectedNodeId === node.id || selectedNodeId === target.id ? "#3B82F6" : 
                                  "#94A3B8"
                                } 
                                strokeWidth={
                                  connectionLOD === 'simplified' ? 1 : 
                                  (isSelected ? 3 : isNextStepConnection ? 3 : isHovered ? 2.5 : 2)
                                }
                                fill="none"
                                style={{ 
                                  pointerEvents: 'none', 
                                  opacity: connectionLOD === 'simplified' ? 0.6 * opacity : opacity,
                                  transition: 'opacity 0.2s, stroke-width 0.2s',
                                  ...(isNextStepConnection && {
                                    strokeDasharray: '8 4',
                                    animation: 'dash 1s linear infinite',
                                  }),
                                }}
                              />
                              {/* Next step label on connection */}
                              {isNextStepConnection && (
                                <text
                                  x={(x1 + x2) / 2}
                                  y={(y1 + y2) / 2 - 10}
                                  textAnchor="middle"
                                  dominantBaseline="middle"
                                  fill="#10B981"
                                  fontSize="12"
                                  fontWeight="bold"
                                  style={{ pointerEvents: 'none' }}
                                >
                                  Next →
                                </text>
                              )}
                              {/* Delete indicator when selected - clickable */}
                              {isSelected && (
                                <g 
                                  style={{ cursor: 'pointer', pointerEvents: 'auto' }}
                                  onMouseDown={(e) => {
                                    e.stopPropagation();
                                  }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    e.preventDefault();
                                    // Delete this connection - split only on last '-'
                                    const lastDashIndex = connectionId.lastIndexOf('-');
                                    const srcId = connectionId.substring(0, lastDashIndex);
                                    const tgtId = connectionId.substring(lastDashIndex + 1);
                                    console.log('Deleting connection from', srcId, 'to', tgtId);
                                    setCanvasNodes(prev => prev.map(n => {
                                      if (n.id === srcId && n.connections) {
                                        return { ...n, connections: n.connections.filter(id => id !== tgtId) };
                                      }
                                      return n;
                                    }));
                                    setSelectedConnectionId(null);
                                  }}
                                >
                                  <circle 
                                    cx={(x1 + x2) / 2} 
                                    cy={(y1 + y2) / 2} 
                                    r="12" 
                                    fill="#EF4444"
                                  />
                                  <text 
                                    x={(x1 + x2) / 2} 
                                    y={(y1 + y2) / 2 + 1} 
                                    textAnchor="middle" 
                                    dominantBaseline="middle" 
                                    fill="white" 
                                    fontSize="14"
                                    fontWeight="bold"
                                  >
                                    ×
                                  </text>
                                </g>
                              )}
                            </g>
                        );
                })}

                {/* Temporary Connection Line (When Dragging) */}
                {connectingNodeId && tempLineEnd && (
                    (() => {
                        const sourceNode = canvasNodes.find(n => n.id === connectingNodeId);
                        if (!sourceNode) return null;

                        const x1 = sourceNode.x + 280; // Right edge
                        const y1 = sourceNode.y + 50;
                        const x2 = tempLineEnd.x;
                        const y2 = tempLineEnd.y;

                        const dx = Math.abs(x2 - x1);
                        const controlX = Math.max(dx * 0.5, 50);

                        return (
                            <path 
                                d={`M ${x1} ${y1} C ${x1 + controlX} ${y1}, ${x2 - controlX} ${y2}, ${x2} ${y2}`}
                                stroke="#3B82F6" 
                                strokeWidth="2" 
                                fill="none" 
                                strokeDasharray="5,5" 
                            />
                        );
                    })()
                )}
              </svg>

              {/* Render groups first (if any) */}
              {nodeGroups.map(group => {
                if (group.collapsed) {
                  // Render collapsed group as a single box
                  return (
                    <Box
                      key={group.id}
                      onClick={() => handleToggleGroup(group.id)}
                      sx={{
                        position: 'absolute',
                        top: group.position.y,
                        left: group.position.x,
                        width: group.bounds.width,
                        height: group.bounds.height,
                        border: `2px dashed ${group.color}`,
                        borderRadius: 2,
                        bgcolor: `${group.color}15`,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1,
                        '&:hover': {
                          bgcolor: `${group.color}25`,
                        },
                      }}
                    >
                      <Typography variant="caption" fontWeight="bold" sx={{ color: group.color }}>
                        {group.title} (Click to expand)
                      </Typography>
                    </Box>
                  );
                }
                return null; // Expanded groups show their nodes
              })}
              
              {/* Render Canvas Nodes - only visible ones */}
              {visibleNodes.map(node => {
                // Check if node is in a collapsed group
                const inCollapsedGroup = nodeGroups.some(g => g.collapsed && g.nodeIds.includes(node.id));
                if (inCollapsedGroup) return null; // Don't render nodes in collapsed groups
                
                // Progressive disclosure: check if node is locked
                const isLocked = progressiveMode && !unlockedNodes.has(node.id) && node.title !== 'SOURCE PDF' && node.type !== 'group';
                
                // Check if node is in active learning path
                const activePath = learningPaths.find(p => p.id === activeLearningPath);
                const isInPath = activePath?.nodeIds.includes(node.id);
                const isCurrentStep = activePath && activePath.nodeIds[activePath.currentStep] === node.id;
                const isNextStep = activePath && activePath.currentStep < activePath.nodeIds.length - 1 && 
                                  activePath.nodeIds[activePath.currentStep + 1] === node.id;
                
                // Focus mode: dim nodes not in focus
                const isInFocus = focusMode ? focusNeighbors.has(node.id) : true;
                const focusOpacity = focusMode && !isInFocus ? 0.2 : 1;
                
                // Use LOD rendering for far nodes, full rendering for close nodes
                const lodNode = currentLOD !== 'full' ? renderNodeWithLOD(node, currentLOD) : null;
                if (lodNode) return lodNode;
                
                return (
                <Paper 
                  key={node.id}
                  elevation={(selectedNodeId === node.id || selectedNodeIds.has(node.id)) ? 8 : 3} 
                  onMouseDown={(e) => {
                      e.stopPropagation(); // CRITICAL: Prevent parent from starting pan
                      
                      // Only start dragging if NOT clicking on the connection handle
                      if (!(e.target as HTMLElement).closest('.connection-handle')) {
                          // Handle multi-select with Shift
                          if (e.shiftKey) {
                            setSelectedNodeIds(prev => {
                              const newSet = new Set(prev);
                              if (newSet.has(node.id)) {
                                newSet.delete(node.id);
                                if (newSet.size === 0) {
                                  setSelectedNodeId(null);
                                } else if (newSet.size === 1) {
                                  setSelectedNodeId(Array.from(newSet)[0]);
                                }
                              } else {
                                newSet.add(node.id);
                                if (newSet.size === 1) {
                                  setSelectedNodeId(node.id);
                                } else {
                                  setSelectedNodeId(null); // Multi-select mode
                                }
                              }
                              return newSet;
                            });
                          } else {
                            // Single select
                            setSelectedNodeId(node.id);
                            setSelectedNodeIds(new Set([node.id]));
                          }
                          
                          setDraggingNodeId(node.id);
                          setSelectedConnectionId(null); // Deselect any connection
                          lastMousePos.current = { x: e.clientX, y: e.clientY };
                          dragStartPos.current = { x: e.clientX, y: e.clientY };
                      }
                  }}
                  onDoubleClick={(e) => {
                      e.stopPropagation();
                      setInspectorOpen(true);
                  }}
                  onMouseUp={(e) => {
                      e.stopPropagation();
                      
                      // Handle connection completion - drop on this card
                      if (connectingNodeId && connectingNodeId !== node.id) {
                          console.log('Completing connection from', connectingNodeId, 'to', node.id);
                          setCanvasNodes(prev => prev.map(n => {
                              if (n.id === connectingNodeId) {
                                  const existingConnections = n.connections || [];
                                  if (existingConnections.includes(node.id)) {
                                      return n;
                                  }
                                  return { ...n, connections: [...existingConnections, node.id] };
                              }
                              return n;
                          }));
                      }
                      
                      // Clean up all states
                      setConnectingNodeId(null);
                      setTempLineEnd(null);
                      setDraggingNodeId(null);
                      dragStartPos.current = null;
                  }}
                  onMouseEnter={() => setHoveredNodeId(node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  sx={{ 
                    position: 'absolute', 
                    top: 0,
                    left: 0,
                    transform: `translate(${node.x}px, ${node.y}px)`,
                    width: 280, 
                    p: node.type === 'card' && node.title === 'SOURCE PDF' ? 2 : 0, 
                    borderRadius: 4, 
                    border: '2px solid', 
                    borderColor: connectingNodeId && connectingNodeId !== node.id 
                        ? '#10B981' // Green highlight when can receive connection
                        : isCurrentStep
                        ? '#10B981' // Green for current step in learning path
                        : isNextStep
                        ? '#F59E0B' // Amber for next step
                        : (selectedNodeId === node.id || selectedNodeIds.has(node.id))
                        ? 'primary.main' // Selected border
                        : node.type === 'critique'
                        ? '#EF4444' // Red for critique nodes
                        : (node.color === 'blue' ? '#3B82F6' : 'transparent'),
                    overflow: 'visible', // Allow handle to overflow
                    cursor: isSpacePressed ? 'grab' : 'grab',
                    transition: 'box-shadow 0.2s ease-out, border-color 0.2s ease-out, opacity 0.2s ease-out',
                    opacity: isLocked ? 0.3 : focusOpacity,
                    filter: isLocked ? 'blur(2px)' : (focusMode && !isInFocus ? 'blur(1px)' : 'none'),
                    willChange: draggingNodeId === node.id ? 'transform' : 'auto',
                    // Glassmorphism effect for selected nodes
                    ...(selectedNodeId === node.id || selectedNodeIds.has(node.id) ? {
                      background: 'rgba(255, 255, 255, 0.95)',
                      backdropFilter: 'blur(12px)',
                      // Halo effect - colorful gradient glow
                      boxShadow: `
                        0 0 0 1px rgba(255, 255, 255, 0.2),
                        0 0 20px rgba(99, 102, 241, 0.4),
                        0 0 40px rgba(168, 85, 247, 0.3),
                        0 0 60px rgba(236, 72, 153, 0.2),
                        0 8px 32px rgba(0, 0, 0, 0.12)
                      `,
                    } : {}),
                    '&:active': { cursor: 'grabbing' },
                    '&:hover': { 
                      boxShadow: (selectedNodeId === node.id || selectedNodeIds.has(node.id)) 
                        ? `
                          0 0 0 1px rgba(255, 255, 255, 0.2),
                          0 0 25px rgba(99, 102, 241, 0.5),
                          0 0 50px rgba(168, 85, 247, 0.4),
                          0 0 75px rgba(236, 72, 153, 0.3),
                          0 12px 40px rgba(0, 0, 0, 0.15)
                        `
                        : '0 8px 16px rgba(0,0,0,0.12)',
                    },
                    // Highlight current step in learning path
                    ...(isCurrentStep && {
                      boxShadow: '0 0 0 4px rgba(16, 185, 129, 0.2)',
                      animation: 'pulse 2s infinite',
                    }),
                  }}
                >
                  {/* Focus Mode Button */}
                  {/* Simplified Badge */}
                  {node.isSimplified && (
                    <Badge
                      badgeContent="简化"
                      color="success"
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        zIndex: 10,
                      }}
                    />
                  )}
                  
                  {(selectedNodeId === node.id || selectedNodeIds.has(node.id)) && !focusMode && (
                    <Box
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEnterFocusMode(node.id);
                      }}
                      sx={{
                        position: 'absolute',
                        left: -10,
                        top: -10,
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        bgcolor: '#10B981',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        zIndex: 20,
                        transition: 'transform 0.2s, background-color 0.2s',
                        '&:hover': {
                          bgcolor: '#059669',
                          transform: 'scale(1.1)'
                        }
                      }}
                      title="Enter Focus Mode"
                    >
                      <Zap size={12} style={{ color: 'white' }} />
                    </Box>
                  )}
                  
                  {/* Exit Focus Mode Button */}
                  {focusMode && focusNodeId === node.id && (
                    <Box
                      onClick={(e) => {
                        e.stopPropagation();
                        handleExitFocusMode();
                      }}
                      sx={{
                        position: 'absolute',
                        left: -10,
                        top: -10,
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        bgcolor: '#EF4444',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        zIndex: 20,
                        transition: 'transform 0.2s, background-color 0.2s',
                        '&:hover': {
                          bgcolor: '#DC2626',
                          transform: 'scale(1.1)'
                        }
                      }}
                      title="Exit Focus Mode"
                    >
                      <X size={12} style={{ color: 'white' }} />
                    </Box>
                  )}
                  
                  {/* Delete Button - Top right corner when selected */}
                  {(selectedNodeId === node.id || selectedNodeIds.has(node.id)) && !focusMode && (
                    <Box
                      onClick={(e) => {
                        e.stopPropagation();
                        // Delete node and all its connections
                        setCanvasNodes(prev => {
                          const filtered = prev.filter(n => n.id !== node.id);
                          return filtered.map(n => ({
                            ...n,
                            connections: n.connections?.filter(id => id !== node.id)
                          }));
                        });
                        setSelectedNodeId(null);
                      }}
                      sx={{
                        position: 'absolute',
                        right: -10,
                        top: -10,
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        bgcolor: '#EF4444',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        zIndex: 20,
                        transition: 'transform 0.2s, background-color 0.2s',
                        '&:hover': {
                          bgcolor: '#DC2626',
                          transform: 'scale(1.1)'
                        }
                      }}
                    >
                      <Typography sx={{ color: 'white', fontSize: 16, fontWeight: 'bold', lineHeight: 1 }}>×</Typography>
                    </Box>
                  )}
                  
                  {/* Connection Handle - Right side */}
                  <Box
                    className="connection-handle"
                    onMouseDown={(e) => {
                        e.stopPropagation();
                        setConnectingNodeId(node.id);
                        mousePos.current = { x: e.clientX, y: e.clientY };
                    }}
                    sx={{
                        position: 'absolute',
                        right: -8,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: 16,
                        height: 16,
                        borderRadius: '50%',
                        bgcolor: '#3B82F6',
                        border: '2px solid white',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        cursor: 'crosshair',
                        opacity: (hoveredNodeId === node.id || connectingNodeId === node.id) ? 1 : 0,
                        transition: 'opacity 0.2s, transform 0.2s',
                        '&:hover': {
                            transform: 'translateY(-50%) scale(1.2)',
                            bgcolor: '#2563EB'
                        },
                        zIndex: 10
                    }}
                  />
                  
                  {/* Left Connection Handle - for receiving */}
                  {connectingNodeId && connectingNodeId !== node.id && (
                    <Box
                      sx={{
                          position: 'absolute',
                          left: -8,
                          top: '50%',
                          transform: 'translateY(-50%)',
                          width: 16,
                          height: 16,
                          borderRadius: '50%',
                          bgcolor: '#10B981',
                          border: '2px solid white',
                          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                          animation: 'pulse 1s infinite',
                          zIndex: 10
                      }}
                    />
                  )}
                  
                  {node.title === 'SOURCE PDF' ? (
                    <Box sx={{ p: 2 }}>
              <Typography variant="caption" color="text.disabled" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>SOURCE PDF</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}><FileText size={18} className="text-red-500" /><Typography variant="subtitle2" fontWeight="600">{node.content}</Typography></Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}><LinkIcon size={14} /><Typography variant="caption">Connected to 3 concepts</Typography></Box>
                    </Box>
                  ) : (
                    <Box sx={{ overflow: 'hidden', borderRadius: 3 }}>
                      <Box sx={{ height: 6, bgcolor: node.color === 'blue' ? '#3B82F6' : 'grey.300' }} />
                      <Box sx={{ p: 2 }}>
                        <Typography 
                          variant="subtitle1" 
                          fontWeight="bold" 
                          gutterBottom
                          sx={{ fontSize: textLOD.fontSize + 2 }}
                        >
                          {node.title}
                        </Typography>
                        {textLOD.showContent && node.content && (
                          <Typography 
                            variant="body2" 
                            color="text.secondary" 
                            sx={{ lineHeight: 1.6, mb: 2, fontSize: textLOD.fontSize }}
                          >
                            {node.content}
                          </Typography>
                        )}
                        
                        {node.timestamp && node.sourceType === 'pdf' && (
                          <Box 
                            sx={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: 1, 
                              mt: 1, 
                              mb: 2, 
                              bgcolor: '#F3F4F6', 
                              p: 1, 
                              borderRadius: 1, 
                              width: 'fit-content', 
                              cursor: 'pointer', 
                              '&:hover': { bgcolor: '#E5E7EB' } 
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleNodeToSource(node);
                            }}
                          >
                            <PlayCircle size={16} className="text-blue-600" />
                            <Typography variant="caption" fontWeight="bold" color="primary.main">
                              {node.timestamp}
                            </Typography>
                          </Box>
                        )}

                        {/* Chat source badge (AI insight) */}
                        {node.sourceType === 'chat' && node.sourceQuery && (
                          <Box
                            sx={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 0.5,
                              px: 1,
                              py: 0.5,
                              mb: 2,
                              bgcolor: '#EEF2FF',
                              borderRadius: 1,
                              cursor: 'pointer',
                              '&:hover': { bgcolor: '#E0E7FF' },
                              maxWidth: '100%',
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleNodeToSource(node);
                            }}
                          >
                            <Bot size={12} className="text-blue-600" />
                            <Typography
                              variant="caption"
                              color="primary.main"
                              sx={{
                                maxWidth: 200,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              Q: {node.sourceQuery}
                            </Typography>
                          </Box>
                        )}

                        {node.tags && (
                          <Box sx={{ display: 'flex', gap: 1, mb: 0 }}>
                            {node.tags.map(tag => (
                              <Chip key={tag} label={tag} size="small" sx={{ borderRadius: 1, bgcolor: 'grey.100', fontSize: 11 }} />
                            ))}
                          </Box>
                        )}
                        
                        {/* Source navigation button */}
                        {node.sourceId && (
                          <Button
                            size="small"
                            startIcon={<FileText size={12} />}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleNodeToSource(node);
                            }}
                            sx={{ 
                              mt: 1, 
                              fontSize: 10, 
                              textTransform: 'none',
                              bgcolor: 'primary.50',
                              color: 'primary.main',
                              '&:hover': { bgcolor: 'primary.100' }
                            }}
                          >
                            View Source {node.sourcePage && `(Page ${node.sourcePage})`}
                          </Button>
                        )}
                      </Box>
                      <Box sx={{ position: 'absolute', bottom: 12, right: 12 }}>
                        <Avatar sx={{ 
                          width: 24, 
                          height: 24, 
                          fontSize: 10, 
                          bgcolor: node.type === 'source' ? 'blue.100' : 
                                   node.type === 'concept' ? 'purple.100' : 
                                   node.type === 'application' ? 'green.100' : 
                                   node.type === 'ai_insight' ? 'grey.900' : 'pink.100',
                          color: node.type === 'source' ? 'blue.500' : 
                                 node.type === 'concept' ? 'purple.500' : 
                                 node.type === 'application' ? 'green.500' : 
                                 node.type === 'ai_insight' ? 'white' : 'pink.500'
                        }}>
                          {node.type === 'source' ? 'S' : node.type === 'concept' ? 'C' : node.type === 'application' ? 'A' : 'AI'}
                        </Avatar>
                      </Box>
                    </Box>
                  )}
            </Paper>
                );
              })}

              {/* SVG Connections - also in transformed space */}
              {/* Removed static SVG example */}
            </Box>
            
            {/* Context Drop Zone - Only visible when dragging */}
            <Box 
              sx={{ 
                position: 'absolute', 
                bottom: 40, 
                left: '50%', 
                transform: isDraggingFromPdf ? 'translateX(-50%) translateY(0)' : 'translateX(-50%) translateY(100px)', 
                opacity: isDraggingFromPdf ? 1 : 0,
                pointerEvents: 'none', // Just visual now, drop handled by container
                width: 400, 
                height: 60, 
                border: '2px dashed', 
                borderColor: !centerVisible ? 'primary.main' : 'divider', 
                borderRadius: 4, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                gap: 1, 
                bgcolor: !centerVisible ? 'rgba(59, 130, 246, 0.05)' : 'rgba(255,255,255,0.6)', 
                backdropFilter: 'blur(4px)', 
                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                zIndex: 20 
              }}
            >
              <Plus size={16} className={!centerVisible ? "text-primary-600" : "text-gray-400"} />
              <Typography variant="body2" color={!centerVisible ? "primary.main" : "text.secondary"}>
                {`Drop ${activeResource.type === 'pdf' ? 'text' : 'transcript'} from ${activeResource.type}`}
              </Typography>
            </Box>
            
            {/* Minimap - Bottom Right */}
            {canvasViewMode === 'canvas' && canvasNodes.length > 0 && (
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 20,
                  right: 20,
                  width: 200,
                  height: 150,
                  bgcolor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 2,
                  p: 1,
                  zIndex: 15,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  backdropFilter: 'blur(8px)',
                }}
              >
                <Typography variant="caption" fontWeight="bold" sx={{ mb: 0.5, display: 'block' }}>
                  Minimap
                </Typography>
                <Box
                  sx={{
                    position: 'relative',
                    width: '100%',
                    height: 'calc(100% - 20px)',
                    bgcolor: '#F9FAFB',
                    borderRadius: 1,
                    overflow: 'hidden',
                    cursor: 'pointer',
                  }}
                  onMouseDown={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const minimapX = (e.clientX - rect.left) / rect.width;
                    const minimapY = (e.clientY - rect.top) / rect.height;
                    
                    // Calculate canvas bounds
                    const canvasRect = canvasRef.current?.getBoundingClientRect();
                    if (!canvasRect) return;
                    
                    const minX = Math.min(...canvasNodes.map(n => n.x));
                    const maxX = Math.max(...canvasNodes.map(n => n.x + 280));
                    const minY = Math.min(...canvasNodes.map(n => n.y));
                    const maxY = Math.max(...canvasNodes.map(n => n.y + 200));
                    
                    const canvasWidth = maxX - minX + 500;
                    const canvasHeight = maxY - minY + 500;
                    
                    // Calculate new viewport position
                    const newX = minX + minimapX * canvasWidth - canvasRect.width / 2 / viewport.scale;
                    const newY = minY + minimapY * canvasHeight - canvasRect.height / 2 / viewport.scale;
                    
                    setViewport(prev => ({
                      ...prev,
                      x: -newX * prev.scale + canvasRect.width / 2,
                      y: -newY * prev.scale + canvasRect.height / 2,
                    }));
                  }}
                >
                  {/* Render nodes as dots in minimap */}
                  {canvasNodes.map(node => {
                    const minX = Math.min(...canvasNodes.map(n => n.x));
                    const maxX = Math.max(...canvasNodes.map(n => n.x + 280));
                    const minY = Math.min(...canvasNodes.map(n => n.y));
                    const maxY = Math.max(...canvasNodes.map(n => n.y + 200));
                    
                    const canvasWidth = maxX - minX + 500;
                    const canvasHeight = maxY - minY + 500;
                    
                    const x = ((node.x - minX) / canvasWidth) * 100;
                    const y = ((node.y - minY) / canvasHeight) * 100;
                    
                    return (
                      <Box
                        key={node.id}
                        sx={{
                          position: 'absolute',
                          left: `${x}%`,
                          top: `${y}%`,
                          width: 3,
                          height: 3,
                          borderRadius: '50%',
                          bgcolor: node.color || '#94A3B8',
                          transform: 'translate(-50%, -50%)',
                        }}
                      />
                    );
                  })}
                  
                  {/* Viewport indicator */}
                  {(() => {
                    const canvasRect = canvasRef.current?.getBoundingClientRect();
                    if (!canvasRect) return null;
                    
                    const minX = Math.min(...canvasNodes.map(n => n.x));
                    const maxX = Math.max(...canvasNodes.map(n => n.x + 280));
                    const minY = Math.min(...canvasNodes.map(n => n.y));
                    const maxY = Math.max(...canvasNodes.map(n => n.y + 200));
                    
                    const canvasWidth = maxX - minX + 500;
                    const canvasHeight = maxY - minY + 500;
                    
                    const viewportLeft = (-viewport.x) / viewport.scale;
                    const viewportTop = (-viewport.y) / viewport.scale;
                    const viewportWidth = canvasRect.width / viewport.scale;
                    const viewportHeight = canvasRect.height / viewport.scale;
                    
                    const x = ((viewportLeft - minX) / canvasWidth) * 100;
                    const y = ((viewportTop - minY) / canvasHeight) * 100;
                    const width = (viewportWidth / canvasWidth) * 100;
                    const height = (viewportHeight / canvasHeight) * 100;
                    
                    return (
                      <Box
                        sx={{
                          position: 'absolute',
                          left: `${x}%`,
                          top: `${y}%`,
                          width: `${width}%`,
                          height: `${height}%`,
                          border: '2px solid',
                          borderColor: 'primary.main',
                          bgcolor: 'rgba(59, 130, 246, 0.1)',
                          pointerEvents: 'none',
                        }}
                      />
                    );
                  })()}
                </Box>
              </Box>
            )}
            
            {/* Canvas Copilot / Magic Tools */}
            <Box sx={{ position: 'absolute', bottom: 40, right: 40, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2, zIndex: 10 }}>
              {isCanvasAiOpen && (
                <Paper elevation={4} sx={{ width: 320, p: 2, borderRadius: 3, border: '1px solid', borderColor: 'divider', bgcolor: 'rgba(255,255,255,0.9)', backdropFilter: 'blur(8px)', animation: 'fadeIn 0.2s ease-out' }}>
                  <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ mb: 1.5, display: 'block', letterSpacing: 0.5 }}>CANVAS COPILOT</Typography>
                  
                  {/* View Mode Switcher */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>VIEW MODE</Typography>
                    <ToggleButtonGroup
                      value={canvasViewMode}
                      exclusive
                      onChange={(e, newMode) => newMode && setCanvasViewMode(newMode)}
                      size="small"
                      sx={{ width: '100%', display: 'flex', flexWrap: 'wrap', gap: 0.5 }}
                    >
                      <ToggleButton value="canvas" sx={{ flex: 1, minWidth: 80 }}>
                        <Layout size={12} style={{ marginRight: 4 }} />
                        Canvas
                      </ToggleButton>
                      <ToggleButton value="list" sx={{ flex: 1, minWidth: 80 }}>
                        <ListIcon size={12} style={{ marginRight: 4 }} />
                        List
                      </ToggleButton>
                      <ToggleButton value="hierarchical" sx={{ flex: 1, minWidth: 80 }}>
                        <Network size={12} style={{ marginRight: 4 }} />
                        Groups
                      </ToggleButton>
                    </ToggleButtonGroup>
                  </Box>
                  
                  {/* Quick Actions */}
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      <Chip 
                      label="Auto Layout" 
                        size="small" 
                      onClick={() => { handleAutoLayout(); setIsCanvasAiOpen(false); }}
                        icon={<Sparkles size={12} />}
                        sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'primary.50', borderColor: 'primary.main', color: 'primary.main' } }} 
                      />
                    <Chip 
                      label={isLayoutFrozen ? "Unfreeze Layout" : "Freeze Layout"} 
                      size="small" 
                      onClick={() => { handleToggleLayoutFreeze(); setIsCanvasAiOpen(false); }}
                      icon={isLayoutFrozen ? <Zap size={12} /> : <Zap size={12} />}
                      sx={{ 
                        bgcolor: isLayoutFrozen ? 'success.50' : 'white', 
                        border: '1px solid', 
                        borderColor: isLayoutFrozen ? 'success.main' : 'divider', 
                        cursor: 'pointer', 
                        color: isLayoutFrozen ? 'success.main' : 'inherit',
                        '&:hover': { bgcolor: isLayoutFrozen ? 'success.100' : 'primary.50', borderColor: isLayoutFrozen ? 'success.main' : 'primary.main' } 
                      }} 
                    />
                    <Chip 
                      label="Detect Communities" 
                      size="small" 
                      onClick={() => { handleDetectCommunities(); setIsCanvasAiOpen(false); }}
                      icon={<Network size={12} />}
                      sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'primary.50', borderColor: 'primary.main', color: 'primary.main' } }} 
                    />
                    <Chip 
                      label="Semantic Clustering" 
                      size="small" 
                      onClick={() => { handleSemanticClustering(); setIsCanvasAiOpen(false); }}
                      icon={<BrainCircuit size={12} />}
                      sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'primary.50', borderColor: 'primary.main', color: 'primary.main' } }} 
                    />
                    <Chip 
                      label="Clear Colors" 
                      size="small" 
                      onClick={() => { handleClearClustering(); setIsCanvasAiOpen(false); }}
                      icon={<X size={12} />}
                      sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'error.50', borderColor: 'error.main', color: 'error.main' } }} 
                    />
                    <Chip 
                      label="Group by Community" 
                      size="small" 
                      onClick={() => { handleGroupByCommunity(); setIsCanvasAiOpen(false); }}
                      icon={<FolderOpen size={12} />}
                      sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'primary.50', borderColor: 'primary.main', color: 'primary.main' } }} 
                    />
                    {nodeGroups.length > 0 && (
                      <>
                        <Chip 
                          label="Collapse All" 
                          size="small" 
                          onClick={() => { handleCollapseAll(); setIsCanvasAiOpen(false); }}
                          icon={<ChevronDown size={12} />}
                          sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'primary.50', borderColor: 'primary.main', color: 'primary.main' } }} 
                        />
                        <Chip 
                          label="Expand All" 
                          size="small" 
                          onClick={() => { handleExpandAll(); setIsCanvasAiOpen(false); }}
                          icon={<ChevronUp size={12} />}
                          sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'primary.50', borderColor: 'primary.main', color: 'primary.main' } }} 
                        />
                      </>
                    )}
                  </Box>

                  {/* Learning Path Section */}
                  <Box sx={{ mb: 2, pt: 1, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>LEARNING</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      <Chip 
                        label={progressiveMode ? "Disable Progressive" : "Enable Progressive"} 
                        size="small" 
                        onClick={() => { handleToggleProgressiveMode(); setIsCanvasAiOpen(false); }}
                        icon={<BrainCircuit size={12} />}
                        sx={{ 
                          bgcolor: progressiveMode ? 'success.50' : 'white', 
                          border: '1px solid', 
                          borderColor: progressiveMode ? 'success.main' : 'divider', 
                          cursor: 'pointer', 
                          color: progressiveMode ? 'success.main' : 'inherit',
                          '&:hover': { bgcolor: progressiveMode ? 'success.100' : 'primary.50', borderColor: progressiveMode ? 'success.main' : 'primary.main' } 
                        }} 
                      />
                      <Chip 
                        label="Create Learning Path" 
                        size="small" 
                        onClick={() => { handleCreateLearningPath(); setIsCanvasAiOpen(false); }}
                        icon={<ArrowRight size={12} />}
                        sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', cursor: 'pointer', '&:hover': { bgcolor: 'primary.50', borderColor: 'primary.main', color: 'primary.main' } }} 
                      />
                      {activeLearningPath && (
                        <>
                          <Chip 
                            label="Next Step" 
                            size="small" 
                            onClick={() => { handleUnlockNext(); setIsCanvasAiOpen(false); }}
                            icon={<ArrowRight size={12} />}
                            sx={{ bgcolor: 'success.50', border: '1px solid', borderColor: 'success.main', cursor: 'pointer', color: 'success.main', '&:hover': { bgcolor: 'success.100' } }} 
                          />
                          {!isTourActive ? (
                            <Chip 
                              label="Start Tour" 
                              size="small" 
                              onClick={() => { handleStartTour(); setIsCanvasAiOpen(false); }}
                              icon={<PlayCircle size={12} />}
                              sx={{ bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.main', cursor: 'pointer', color: 'primary.main', '&:hover': { bgcolor: 'primary.100' } }} 
                            />
                          ) : (
                            <Chip 
                              label="Stop Tour" 
                              size="small" 
                              onClick={() => { handleStopTour(); setIsCanvasAiOpen(false); }}
                              icon={<Pause size={12} />}
                              sx={{ bgcolor: 'error.50', border: '1px solid', borderColor: 'error.main', cursor: 'pointer', color: 'error.main', '&:hover': { bgcolor: 'error.100' } }} 
                            />
                          )}
                        </>
                      )}
                    </Box>
                    {activeLearningPath && (() => {
                      const path = learningPaths.find(p => p.id === activeLearningPath);
                      if (!path) return null;
                      return (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          Step {path.currentStep + 1} of {path.nodeIds.length}: {path.name}
                        </Typography>
                      );
                    })()}
                  </Box>

                  {/* Input Area */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, bgcolor: 'white', border: '1px solid', borderColor: 'primary.main', borderRadius: 2, px: 1.5, py: 0.5, boxShadow: '0 2px 4px rgba(59,130,246,0.1)' }}>
                    <Wand2 size={16} className="text-primary-500" />
                    <TextField 
                      fullWidth 
                      variant="standard" 
                      placeholder="Ask AI to edit canvas..." 
                      value={canvasAiQuery}
                      onChange={(e) => setCanvasAiQuery(e.target.value)}
                      onKeyDown={(e) => { if(e.key === 'Enter') { setIsCanvasAiOpen(false); setCanvasAiQuery(''); } }}
                      autoFocus
                      InputProps={{ disableUnderline: true, style: { fontSize: 14 } }} 
                    />
                    <IconButton size="small" onClick={() => { setIsCanvasAiOpen(false); setCanvasAiQuery(''); }} color="primary"><ArrowRight size={16} /></IconButton>
                  </Box>
            </Paper>
              )}

              <IconButton 
                onClick={() => setIsCanvasAiOpen(!isCanvasAiOpen)}
                sx={{ 
                  bgcolor: isCanvasAiOpen ? '#fff' : '#171717', 
                  color: isCanvasAiOpen ? '#171717' : '#fff', 
                  width: 48, height: 48, 
                  border: isCanvasAiOpen ? '1px solid' : 'none',
                  borderColor: 'divider',
                  boxShadow: isCanvasAiOpen ? '0 4px 12px rgba(0,0,0,0.1)' : '0 4px 12px rgba(0,0,0,0.3)',
                  '&:hover': { bgcolor: isCanvasAiOpen ? '#f5f5f5' : '#000' },
                  transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)'
                }}
              >
                {isCanvasAiOpen ? <CloseIcon size={20} /> : <Sparkles size={20} />}
              </IconButton>
            </Box>
            </Box>
          </Box>
        );
    }
  };

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.paper' }}>
        
        {/* LEFT & CENTER COLUMN (Keep existing code structure) */}
        <Box ref={leftColumnRef} sx={{ width: leftVisible ? leftWidth : 48, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', transition: resizingCol ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)', overflow: 'hidden', position: 'relative', bgcolor: 'background.paper' }}>
           {leftVisible ? (
             <>
              <Box sx={{ height: isReaderExpanded ? 0 : `${splitRatio * 100}%`, display: 'flex', flexDirection: 'column', overflow: 'hidden', transition: isVerticalDragging ? 'none' : 'height 0.3s ease' }}>
                 <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                   <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Box component="span" sx={{ color: 'primary.main' }}><FolderOpen size={18} /></Box><Typography variant="subtitle2" fontWeight="bold">Research_v1</Typography></Box>
                   <Box sx={{ display: 'flex', gap: 0.5 }}><Box sx={{ bgcolor: '#F3F4F6', borderRadius: 1, p: 0.5, display: 'flex' }}><IconButton size="small" onClick={() => setViewMode('list')} sx={{ p: 0.5, bgcolor: viewMode === 'list' ? '#fff' : 'transparent', boxShadow: viewMode === 'list' ? '0 1px 2px rgba(0,0,0,0.1)' : 'none', borderRadius: 1 }}><ListIcon size={14} /></IconButton><IconButton size="small" onClick={() => setViewMode('grid')} sx={{ p: 0.5, bgcolor: viewMode === 'grid' ? '#fff' : 'transparent', boxShadow: viewMode === 'grid' ? '0 1px 2px rgba(0,0,0,0.1)' : 'none', borderRadius: 1 }}><LayoutGrid size={14} /></IconButton></Box><Tooltip title="Collapse Sidebar (Cmd+\)"><IconButton size="small" onClick={() => setLeftVisible(false)}><PanelLeftClose size={16} /></IconButton></Tooltip></Box>
                 </Box>
                 <Box sx={{ px: 2, mb: 2 }}><Button fullWidth variant="contained" startIcon={<Plus size={16} />} sx={{ bgcolor: '#0F172A', color: '#fff', textTransform: 'none', borderRadius: 2, py: 1, '&:hover': { bgcolor: '#1E293B' } }}>Add Resource</Button></Box>
                 <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 2, pb: 2 }}>
                   <Box sx={{ mb: 3 }}>
                     <Box 
                       onClick={() => setPapersExpanded(!papersExpanded)}
                       sx={{ 
                         display: 'flex', 
                         alignItems: 'center', 
                         gap: 1, 
                         mb: 1.5, 
                         color: 'text.secondary',
                         cursor: 'pointer',
                         userSelect: 'none',
                         '&:hover': { color: 'text.primary' }
                       }}
                     >
                       {papersExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
                       <Typography variant="caption" fontWeight="bold">PAPERS ({SAMPLE_RESOURCES.length})</Typography>
                     </Box>
                     <Collapse in={papersExpanded}>
                       <Box sx={{ display: viewMode === 'grid' ? 'grid' : 'block', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 1.5 }}>
                         {SAMPLE_RESOURCES.map(renderResource)}
                       </Box>
                     </Collapse>
                   </Box>
                   <Box>
                     <Box 
                       onClick={() => setMediaExpanded(!mediaExpanded)}
                       sx={{ 
                         display: 'flex', 
                         alignItems: 'center', 
                         gap: 1, 
                         mb: 1.5, 
                         color: 'text.secondary',
                         cursor: 'pointer',
                         userSelect: 'none',
                         '&:hover': { color: 'text.primary' }
                       }}
                     >
                       {mediaExpanded ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
                       <Typography variant="caption" fontWeight="bold">MEDIA & LINKS ({SAMPLE_MEDIA.length})</Typography>
                     </Box>
                     <Collapse in={mediaExpanded}>
                       <Box sx={{ display: viewMode === 'grid' ? 'grid' : 'block', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 1.5 }}>
                         {SAMPLE_MEDIA.map(renderResource)}
                       </Box>
                     </Collapse>
                   </Box>
                </Box>
              </Box>
              {renderContentViewer()}
             </>
           ) : (
             <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
               <Box sx={{ height: 56, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
                 <Tooltip title="Expand Source (Cmd+\)" placement="right">
                   <IconButton onClick={() => setLeftVisible(true)} size="small">
                     <PanelLeftOpen size={20} />
                   </IconButton>
                 </Tooltip>
               </Box>
               <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2, gap: 2 }}>
                 {/* Divider removed as we have borderBottom now, or keep if spacing is needed. Let's keep it for visual separation from header if preferred, but usually border is enough. Let's remove explicit Divider and rely on spacing. Actually, let's keep the logic clean. */}
                 <Tooltip title={activeResource.title} placement="right">
                   <Box 
                     sx={{ 
                       p: 1, 
                       borderRadius: 1, 
                       bgcolor: activeResource.id === activeResource.id ? '#EFF6FF' : 'transparent', 
                       color: activeResource.type === 'pdf' ? 'primary.main' : 
                              activeResource.type === 'video' ? 'primary.main' : 
                              activeResource.type === 'audio' ? 'purple.500' : 'blue.500',
                       cursor: 'pointer',
                       '&:hover': { bgcolor: 'action.hover' }
                     }} 
                     onClick={() => setLeftVisible(true)}
                   >
                     {activeResource.type === 'pdf' && <FileText size={18} />}
                     {activeResource.type === 'video' && <Video size={18} />}
                     {activeResource.type === 'audio' && <Music size={18} />}
                     {activeResource.type === 'link' && <LinkIcon size={18} />}
                   </Box>
                 </Tooltip>
               </Box>
             </Box>
           )}
        </Box>
        {leftVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('left')} />}

        <Box sx={{ width: centerVisible ? centerWidth : 0, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: centerVisible ? '1px solid' : 'none', borderColor: 'divider', transition: resizingCol ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)', bgcolor: '#F9FAFB', overflow: 'hidden', position: 'relative' }}>
            <Box sx={{ height: 56, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', minWidth: 300 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}><Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#10B981' }} /><Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>Assistant</Typography></Box>
            <Box sx={{ display: 'flex', gap: 0.5 }}><Tooltip title={quietMode ? "Show All" : "Quiet Mode"}><IconButton size="small" onClick={() => setQuietMode(!quietMode)} sx={{ bgcolor: quietMode ? 'primary.main' : 'transparent', color: quietMode ? '#fff' : 'text.secondary', '&:hover': { bgcolor: quietMode ? 'primary.dark' : 'action.hover' } }}><Filter size={14} /></IconButton></Tooltip><Tooltip title="Collapse Processor (Cmd+.)"><IconButton size="small" onClick={() => setCenterVisible(false)}><PanelRightClose size={16} /></IconButton></Tooltip></Box>
          </Box>
          
          {/* Chat Messages Area */}
          <Box 
            ref={chatContainerRef}
            sx={{ p: 2, overflowY: 'auto', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 300 }}
          >
            {chatMessages.map((msg) => (
              <Box 
                key={msg.id} 
                ref={(el) => { if (el) chatMessageRefs.current[msg.id] = el; }} 
                sx={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '90%' }}
              >
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 2, 
                    borderRadius: 2, 
                    bgcolor: msg.role === 'user' ? 'primary.main' : 'white', 
                    color: msg.role === 'user' ? 'white' : 'text.primary',
                    border: msg.role === 'ai' ? '1px solid' : 'none',
                    borderColor: 'divider'
                  }}
                >
                  {msg.role === 'ai' && (
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'primary.main' }}>
                        <Bot size={16} />
                        <Typography variant="caption" fontWeight="bold">AI Assistant</Typography>
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
                            // Prefer any selected text; fallback to full message
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
                            // Prevent click from focusing / doing anything; drag only
                            e.stopPropagation();
                          }}
                        >
                          <GripHorizontal size={14} />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  )}
                  
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.content}</Typography>
                  
                  {msg.type === 'rag_result' && msg.sources && (
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
                              onClick={() => navigateToSource(source.id, source.page_number, source.snippet)}
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
                                    mb: source.snippet ? 0.5 : 0,
                                  }}
                                >
                                  {source.title}
                                </Typography>
                                {source.snippet && (
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{
                                      lineHeight: 1.6,
                                      display: 'block',
                                      wordBreak: 'break-word',
                                      fontSize: '0.75rem',
                                      fontStyle: 'italic',
                                      mb: 1,
                                    }}
                                  >
                                    {source.snippet}
                                  </Typography>
                                )}
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1 }}>
                                  {source.page_number && (
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
                                  )}
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
                      
                      <Button 
                        fullWidth 
                        size="small" 
                        variant="outlined" 
                        startIcon={<Layout size={14} />}
                        onClick={() => handleAddRagToCanvas(msg)}
                        sx={{ 
                          mt: 1.5,
                          borderColor: 'primary.main', 
                          color: 'primary.main',
                          '&:hover': { bgcolor: 'primary.50' }
                        }}
                      >
                        Add to Canvas
                      </Button>
                    </Box>
                  )}
                </Paper>
                <Typography 
                  variant="caption" 
                  color="text.disabled" 
                  sx={{ mt: 0.5, display: 'block', textAlign: msg.role === 'user' ? 'right' : 'left', fontSize: 10 }}
                  suppressHydrationWarning
                >
                  {typeof msg.timestamp === 'string' 
                    ? new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
                    : msg.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
                  }
                </Typography>
              </Box>
            ))}
            {isTyping && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2, bgcolor: 'white', borderRadius: 2, width: 'fit-content', border: '1px solid', borderColor: 'divider' }}>
                <CircularProgress size={14} />
                <Typography variant="caption" color="text.secondary">Thinking...</Typography>
              </Box>
            )}
            <div ref={chatEndRef} />
          </Box>

          {/* Chat Input Area */}
          <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#fff', minWidth: 300 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, bgcolor: '#F3F4F6', px: 2, py: 1, borderRadius: 2 }}>
              <TextField 
                fullWidth 
                placeholder="Ask about your documents..." 
                variant="standard" 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                InputProps={{ disableUnderline: true, style: { fontSize: 14 } }} 
              />
              <IconButton size="small" color={chatInput.trim() ? "primary" : "default"} onClick={handleSendMessage} disabled={!chatInput.trim() || isTyping}>
                <ArrowRight size={18} />
              </IconButton>
            </Box>
          </Box>
        </Box>
        {centerVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('center')} />}
        {!centerVisible && <Box sx={{ width: 40, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: '#F9FAFB' }}>
          <Box sx={{ height: 56, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
            <Tooltip title="Expand Processor (Cmd+.)" placement="right">
              <IconButton onClick={() => setCenterVisible(true)} size="small">
                <PanelRightOpen size={20} />
              </IconButton>
            </Tooltip>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2, gap: 2 }}>
            <Tooltip title={quietMode ? "AI Assistant (Focus Mode)" : "AI Assistant (Ready)"} placement="right">
              <Box 
                onClick={() => setCenterVisible(true)}
                sx={{ 
                  p: 1, 
                  borderRadius: 1, 
                  cursor: 'pointer',
                  color: quietMode ? 'text.disabled' : 'primary.main',
                  bgcolor: quietMode ? 'transparent' : 'primary.50',
                  transition: 'all 0.2s',
                  '&:hover': { bgcolor: quietMode ? 'action.hover' : 'primary.100' }
                }}
              >
                <Badge color="secondary" variant="dot" invisible={quietMode}>
                  <Bot size={18} />
                </Badge>
              </Box>
            </Tooltip>
          </Box>
        </Box>}


        {/* ================= RIGHT COLUMN: Output OS (Tabs + Launcher) ================= */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          
          {/* Header (Tab Bar) */}
          <Box sx={{ 
            height: 56, borderBottom: '1px solid', borderColor: 'divider', 
            display: 'flex', alignItems: 'flex-end', px: 2, justifyContent: 'space-between', bgcolor: '#F9FAFB'
          }}>
            {/* Tabs Container */}
            <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', width: '100%', '::-webkit-scrollbar': { display: 'none' } }}>
              {tabs.map(tab => (
                <Box
                  key={tab.id}
                  onClick={() => setActiveTabId(tab.id)}
                  sx={{
                    display: 'flex', alignItems: 'center', gap: 1,
                    px: 2, py: 1.5,
                    bgcolor: activeTabId === tab.id ? '#fff' : 'transparent',
                    borderTopLeftRadius: 8, borderTopRightRadius: 8,
                    border: '1px solid',
                    borderBottom: activeTabId === tab.id ? 'none' : '1px solid',
                    borderColor: 'divider',
                    position: 'relative', top: 1, // overlap bottom border
                    cursor: 'pointer',
                    userSelect: 'none',
                    minWidth: 120,
                    maxWidth: 200,
                    '&:hover': { bgcolor: activeTabId === tab.id ? '#fff' : 'rgba(0,0,0,0.03)' }
                  }}
                >
                  {tab.status === 'generating' ? <Loader2 size={14} className="animate-spin text-blue-600" /> : 
                   tab.type === 'podcast' ? <Mic size={14} className="text-purple-500" /> :
                   tab.type === 'flashcards' ? <BrainCircuit size={14} className="text-orange-500" /> :
                   tab.type === 'ppt' ? <Presentation size={14} className="text-pink-500" /> :
                   tab.type === 'writer' ? <PenTool size={14} className="text-green-600" /> :
                   <Layout size={14} className="text-gray-500" />
                  }
                  <Typography variant="caption" fontWeight={activeTabId === tab.id ? 600 : 400} noWrap sx={{ flex: 1 }}>{tab.title}</Typography>
                  <IconButton size="small" onClick={(e) => handleTabClose(e, tab.id)} sx={{ p: 0.5, opacity: 0.6, '&:hover': { opacity: 1, bgcolor: 'error.lighter', color: 'error.main' } }}>
                    <CloseIcon size={12} />
                  </IconButton>
                </Box>
              ))}
              
              {/* Add Tab Button */}
              <IconButton size="small" onClick={(e) => setMenuAnchor(e.currentTarget)} sx={{ mb: 1, ml: 0.5 }}>
                <Plus size={16} />
              </IconButton>

              {/* Capability Launcher Menu */}
              <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={() => setMenuAnchor(null)}
                PaperProps={{ sx: { width: 220, borderRadius: 3, mt: 1 } }}
              >
                <Typography variant="caption" sx={{ px: 2, py: 1, display: 'block', color: 'text.secondary', fontWeight: 600 }}>CREATE NEW</Typography>
                <MenuItem onClick={() => handleAddTab('canvas')}>
                  <ListItemIcon><Layout size={16} /></ListItemIcon>
                  <ListItemText primary="Canvas" secondary="Whiteboard" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <MenuItem onClick={() => handleAddTab('writer')}>
                  <ListItemIcon><PenTool size={16} className="text-green-600" /></ListItemIcon>
                  <ListItemText primary="Writer" secondary="Drafting & Mixing" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <Divider />
                <Typography variant="caption" sx={{ px: 2, py: 1, display: 'block', color: 'text.secondary', fontWeight: 600 }}>GENERATE WITH AI</Typography>
                <MenuItem onClick={() => { setMenuAnchor(null); setIsCurriculumModalOpen(true); }}>
                  <ListItemIcon><BookOpen size={16} className="text-blue-600" /></ListItemIcon>
                  <ListItemText primary="Curriculum" secondary="Learning Path" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <MenuItem onClick={() => handleAddTab('podcast')}>
                  <ListItemIcon><Mic size={16} className="text-purple-500" /></ListItemIcon>
                  <ListItemText primary="Podcast" secondary="Audio Overview" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <MenuItem onClick={() => handleAddTab('flashcards')}>
                  <ListItemIcon><BrainCircuit size={16} className="text-orange-500" /></ListItemIcon>
                  <ListItemText primary="Flashcards" secondary="Study Aid" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <MenuItem onClick={() => handleAddTab('ppt')}>
                  <ListItemIcon><Presentation size={16} className="text-pink-500" /></ListItemIcon>
                  <ListItemText primary="Slides" secondary="Presentation" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
              </Menu>
            </Box>

            {/* Right Header Actions */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, pl: 2 }}>
              <Typography variant="caption" color="text.disabled" fontWeight="600" sx={{ whiteSpace: 'nowrap' }}>SAVED</Typography>
            </Box>
          </Box>

          {/* Active Tab Content */}
          {renderTabContent()}

          </Box>
      </Box>
      <CurriculumPreviewModal
        open={isCurriculumModalOpen}
        onClose={() => setIsCurriculumModalOpen(false)}
        onConfirm={(steps) => {
          console.log('Curriculum confirmed:', steps);
          setIsCurriculumModalOpen(false);
          // Here we could add a tab for curriculum or navigate to a view
        }}
      />
      <NodeInspector
        node={selectedNodeId ? canvasNodes.find(n => n.id === selectedNodeId) || null : null}
        isOpen={inspectorOpen && selectedNodeId !== null}
        onClose={() => setInspectorOpen(false)}
        onUpdate={(nodeId, updates) => {
          setCanvasNodes(prev => prev.map(n => 
            n.id === nodeId ? { ...n, ...updates } : n
          ));
        }}
      />
    </GlobalLayout>
  );
}
