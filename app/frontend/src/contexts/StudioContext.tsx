'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ProjectDocument, CanvasNode, CanvasEdge } from '@/lib/api';

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

