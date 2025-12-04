'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef } from 'react';
import { ProjectDocument, CanvasNode, CanvasEdge, documentsApi, canvasApi, chatApi } from '@/lib/api';

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
  canvasViewport: { x: number; y: number; scale: number };
  setCanvasViewport: (viewport: { x: number; y: number; scale: number }) => void;
  
  // Chat
  chatMessages: ChatMessage[];
  setChatMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
  
  // Actions
  addNodeToCanvas: (node: Omit<CanvasNode, 'id'>) => void;
  saveCanvas: () => Promise<void>;
  
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
  const [canvasViewport, setCanvasViewport] = useState({ x: 0, y: 0, scale: 1 });
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

  const addNodeToCanvas = useCallback((node: Omit<CanvasNode, 'id'>) => {
    const newNode: CanvasNode = {
      ...node,
      id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
    setCanvasNodes(prev => [...prev, newNode]);
  }, []);

  const saveCanvas = useCallback(async () => {
    // This will be implemented in CanvasPanel
    console.log('Saving canvas...');
  }, []);

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
    setCanvasViewport({ x: 0, y: 0, scale: 1 });
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
          if (canvasRes.viewport) {
            setCanvasViewport(canvasRes.viewport);
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
    canvasViewport,
    setCanvasViewport,
    chatMessages,
    setChatMessages,
    addNodeToCanvas,
    saveCanvas,
    navigateToSource,
    sourceNavigation,
    dragPreview,
    setDragPreview,
    dragContentRef,
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

