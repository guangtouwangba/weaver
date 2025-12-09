'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef } from 'react';
import { ProjectDocument, CanvasNode, CanvasEdge, CanvasSection, CanvasViewState, documentsApi, canvasApi, chatApi, Citation } from '@/lib/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  content: string;
  sources?: Array<{
    document_id: string;
    page_number: number;
    snippet: string;
    similarity: number;
  }>;
  citations?: Citation[];  // Mega-Prompt mode citations with quote localization
  timestamp: Date;
  // Optional: original user query that triggered this AI response
  query?: string;
}

interface StudioContextType {
  // Project
  projectId: string;
  
  // Documents
  documents: ProjectDocument[];
  setDocuments: (docs: ProjectDocument[]) => void;
  activeDocumentId: string | null;
  setActiveDocumentId: (id: string | null) => void;
  
  // Canvas
  canvasNodes: CanvasNode[];
  setCanvasNodes: (nodes: CanvasNode[] | ((prev: CanvasNode[]) => CanvasNode[])) => void;
  canvasEdges: CanvasEdge[];
  setCanvasEdges: (edges: CanvasEdge[] | ((prev: CanvasEdge[]) => CanvasEdge[])) => void;
  canvasSections: CanvasSection[];
  setCanvasSections: (sections: CanvasSection[] | ((prev: CanvasSection[]) => CanvasSection[])) => void;
  canvasViewport: { x: number; y: number; scale: number };
  setCanvasViewport: (viewport: { x: number; y: number; scale: number }) => void;
  
  // View system
  currentView: 'free' | 'thinking';
  setCurrentView: (view: 'free' | 'thinking') => void;
  viewStates: {
    free: CanvasViewState;
    thinking: CanvasViewState;
  };
  setViewStates: (viewStates: { free: CanvasViewState; thinking: CanvasViewState }) => void;
  switchView: (view: 'free' | 'thinking') => void;
  
  // Chat
  chatMessages: ChatMessage[];
  setChatMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
  
  // Actions
  addNodeToCanvas: (node: Omit<CanvasNode, 'id'>) => void;
  addSection: (section: CanvasSection) => void;
  promoteNode: (nodeId: string) => void;
  deleteSection: (sectionId: string) => void;
  saveCanvas: () => Promise<void>;
  clearCanvas: (viewType?: 'free' | 'thinking') => Promise<void>;
  
  // Navigation
  navigateToSource: (documentId: string, pageNumber: number, searchText?: string) => void;
  sourceNavigation: {
    documentId: string;
    pageNumber: number;
    searchText?: string;
  } | null;
  
  // Drag Preview
  dragPreview: { x: number; y: number; content: string } | null;
  setDragPreview: (preview: { x: number; y: number; content: string } | null) => void;
  dragContentRef: React.MutableRefObject<string | null>;
  
  // Auto Thinking Path
  autoThinkingPathEnabled: boolean;
  setAutoThinkingPathEnabled: (enabled: boolean) => void;
  
  // Message <-> Node Navigation
  navigateToMessage: (messageId: string) => void;
  highlightedMessageId: string | null;
  navigateToNode: (nodeId: string) => void;
  highlightedNodeId: string | null;
}

const StudioContext = createContext<StudioContextType | undefined>(undefined);

export function StudioProvider({ 
  children, 
  projectId 
}: { 
  children: ReactNode; 
  projectId: string;
}) {
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [canvasNodes, setCanvasNodes] = useState<CanvasNode[]>([]);
  const [canvasEdges, setCanvasEdges] = useState<CanvasEdge[]>([]);
  const [canvasSections, setCanvasSections] = useState<CanvasSection[]>([]);
  const [canvasViewport, setCanvasViewport] = useState({ x: 0, y: 0, scale: 1 });
  const [currentView, setCurrentView] = useState<'free' | 'thinking'>('free');
  const [viewStates, setViewStates] = useState<{
    free: CanvasViewState;
    thinking: CanvasViewState;
  }>({
    free: {
      viewType: 'free',
      viewport: { x: 0, y: 0, scale: 1 },
      selectedNodeIds: [],
      collapsedSectionIds: [],
    },
    thinking: {
      viewType: 'thinking',
      viewport: { x: 0, y: 0, scale: 1 },
      selectedNodeIds: [],
      collapsedSectionIds: [],
    },
  });
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'ai',
      content: "Hello! I'm your research assistant. Upload a document and ask me anything about it.",
      timestamp: new Date(),
    }
  ]);
  
  // Navigation state for source jumping
  const [sourceNavigation, setSourceNavigation] = useState<{
    documentId: string;
    pageNumber: number;
    searchText?: string;
  } | null>(null);
  
  // Drag preview state
  const [dragPreview, setDragPreview] = useState<{ x: number; y: number; content: string } | null>(null);
  const dragContentRef = useRef<string | null>(null);

  // Auto Thinking Path state
  const [autoThinkingPathEnabled, setAutoThinkingPathEnabled] = useState(true);
  
  // Message <-> Node Navigation state
  const [highlightedMessageId, setHighlightedMessageId] = useState<string | null>(null);
  const [highlightedNodeId, setHighlightedNodeId] = useState<string | null>(null);

  const navigateToMessage = useCallback((messageId: string) => {
    setHighlightedMessageId(messageId);
    // Auto-clear highlight after 3 seconds
    setTimeout(() => setHighlightedMessageId(null), 3000);
  }, []);

  // Define switchView BEFORE navigateToNode since navigateToNode depends on it
  const switchView = useCallback((view: 'free' | 'thinking') => {
    // Save current view state before switching
    setViewStates(prev => ({
      ...prev,
      [currentView]: {
        ...prev[currentView],
        viewport: canvasViewport,
      },
    }));
    
    // Switch to new view and restore its viewport
    setCurrentView(view);
    setCanvasViewport(viewStates[view].viewport);
  }, [currentView, canvasViewport, viewStates]);

  const navigateToNode = useCallback((nodeId: string) => {
    setHighlightedNodeId(nodeId);
    // Switch to thinking view if the node is in thinking view
    const node = canvasNodes.find(n => n.id === nodeId);
    if (node?.viewType === 'thinking' && currentView !== 'thinking') {
      switchView('thinking');
    }
    // Auto-clear highlight after 3 seconds
    setTimeout(() => setHighlightedNodeId(null), 3000);
  }, [canvasNodes, currentView, switchView]);

  const addNodeToCanvas = useCallback((node: Omit<CanvasNode, 'id'>) => {
    const newNode: CanvasNode = {
      viewType: currentView,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      ...node,
      id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
    setCanvasNodes(prev => [...prev, newNode]);
  }, [currentView]);

  const addSection = useCallback((section: CanvasSection) => {
    setCanvasSections(prev => [...prev, section]);
  }, []);

  const promoteNode = useCallback((nodeId: string) => {
    const node = canvasNodes.find(n => n.id === nodeId);
    if (!node) return;

    // Create a copy in free canvas view
    const newNode: CanvasNode = {
      ...node,
      id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      viewType: 'free',
      sectionId: undefined, // Remove section when promoting
      promotedFrom: nodeId, // Keep reference to original
      x: node.x + 50, // Slight offset for clarity
      y: node.y + 50,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setCanvasNodes(prev => [...prev, newNode]);
  }, [canvasNodes]);

  const deleteSection = useCallback((sectionId: string) => {
    // Remove section
    setCanvasSections(prev => prev.filter(s => s.id !== sectionId));
    // Remove nodes in section (optional, can keep nodes orphaned)
    setCanvasNodes(prev => prev.filter(n => n.sectionId !== sectionId));
  }, []);

  const saveCanvas = useCallback(async () => {
    // This will be implemented in CanvasPanel
    console.log('Saving canvas...');
  }, []);

  const clearCanvas = useCallback(async (viewType?: 'free' | 'thinking') => {
    // Capture the view type at the moment of calling to handle tab switching edge case
    const targetViewType = viewType;
    
    try {
      await canvasApi.clear(projectId, targetViewType);
      
      // Clear local state based on the captured view type
      if (targetViewType) {
        // Only clear nodes/edges/sections for the specific view type
        setCanvasNodes(prev => prev.filter(n => n.viewType !== targetViewType));
        setCanvasEdges(prev => {
          // Get IDs of nodes being removed
          const nodesToRemove = new Set(
            canvasNodes.filter(n => n.viewType === targetViewType).map(n => n.id)
          );
          // Remove edges connected to removed nodes
          return prev.filter(e => !nodesToRemove.has(e.source) && !nodesToRemove.has(e.target));
        });
        setCanvasSections(prev => prev.filter(s => s.viewType !== targetViewType));
        console.log(`Canvas view '${targetViewType}' cleared successfully`);
      } else {
        // Clear all
        setCanvasNodes([]);
        setCanvasEdges([]);
        setCanvasSections([]);
        console.log('All canvas cleared successfully');
      }
    } catch (error) {
      console.error('Failed to clear canvas:', error);
      throw error;
    }
  }, [projectId, canvasNodes]);

  const navigateToSource = useCallback((documentId: string, pageNumber: number, searchText?: string) => {
    setActiveDocumentId(documentId);
    setSourceNavigation({ documentId, pageNumber, searchText });
  }, []);

  // Load data on mount and when projectId changes
  useEffect(() => {
    if (!projectId) return;

    // Clear previous project data immediately to prevent showing stale data
    setDocuments([]);
    setCanvasNodes([]);
    setCanvasEdges([]);
    setCanvasSections([]);
    setCanvasViewport({ x: 0, y: 0, scale: 1 });
    setCurrentView('free');
    setViewStates({
      free: {
        viewType: 'free',
        viewport: { x: 0, y: 0, scale: 1 },
        selectedNodeIds: [],
        collapsedSectionIds: [],
      },
      thinking: {
        viewType: 'thinking',
        viewport: { x: 0, y: 0, scale: 1 },
        selectedNodeIds: [],
        collapsedSectionIds: [],
      },
    });
    setChatMessages([
      {
        id: 'welcome',
        role: 'ai',
        content: "Hello! I'm your research assistant. Upload a document and ask me anything about it.",
        timestamp: new Date(),
      }
    ]);
    setActiveDocumentId(null);
    setSourceNavigation(null);

    const loadData = async () => {
      try {
        const [docsRes, canvasRes, historyRes] = await Promise.all([
          documentsApi.list(projectId),
          canvasApi.get(projectId).catch(() => null), // Handle 404 for new canvas
          chatApi.getHistory(projectId).catch(() => null),
        ]);

        if (docsRes) {
          setDocuments(docsRes.items);
        }

        if (canvasRes) {
          setCanvasNodes(canvasRes.nodes || []);
          setCanvasEdges(canvasRes.edges || []);
          setCanvasSections(canvasRes.sections || []);
          if (canvasRes.viewport) {
            setCanvasViewport(canvasRes.viewport);
          }
          if (canvasRes.viewStates) {
            setViewStates({
              free: canvasRes.viewStates.free || {
                viewType: 'free',
                viewport: { x: 0, y: 0, scale: 1 },
                selectedNodeIds: [],
                collapsedSectionIds: [],
              },
              thinking: canvasRes.viewStates.thinking || {
                viewType: 'thinking',
                viewport: { x: 0, y: 0, scale: 1 },
                selectedNodeIds: [],
                collapsedSectionIds: [],
              },
            });
          }
        }

        if (historyRes && historyRes.messages.length > 0) {
          setChatMessages(
            historyRes.messages.map((m) => ({
              id: m.id,
              role: m.role,
              content: m.content,
              sources: m.sources,
              timestamp: new Date(m.created_at),
            }))
          );
        }
      } catch (error) {
        console.error('Failed to load project data:', error);
      }
    };

    loadData();
  }, [projectId]);

  const value: StudioContextType = {
    projectId,
    documents,
    setDocuments,
    activeDocumentId,
    setActiveDocumentId,
    canvasNodes,
    setCanvasNodes,
    canvasEdges,
    setCanvasEdges,
    canvasSections,
    setCanvasSections,
    canvasViewport,
    setCanvasViewport,
    currentView,
    setCurrentView,
    viewStates,
    setViewStates,
    switchView,
    chatMessages,
    setChatMessages,
    addNodeToCanvas,
    addSection,
    promoteNode,
    deleteSection,
    saveCanvas,
    clearCanvas,
    navigateToSource,
    sourceNavigation,
    dragPreview,
    setDragPreview,
    dragContentRef,
    autoThinkingPathEnabled,
    setAutoThinkingPathEnabled,
    navigateToMessage,
    highlightedMessageId,
    navigateToNode,
    highlightedNodeId,
  };

  return (
    <StudioContext.Provider value={value}>
      {children}
    </StudioContext.Provider>
  );
}

export function useStudio() {
  const context = useContext(StudioContext);
  if (!context) {
    throw new Error('useStudio must be used within StudioProvider');
  }
  return context;
}

