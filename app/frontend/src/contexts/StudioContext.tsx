'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect, useRef } from 'react';
import { ProjectDocument, CanvasNode, CanvasEdge, CanvasSection, CanvasViewState, ChatSession, documentsApi, canvasApi, chatApi, outputsApi, projectsApi, Citation, SummaryData, MindmapData, OutputResponse } from '@/lib/api';

// === Generation Task Types for Concurrent Outputs ===
export type GenerationType = 'summary' | 'mindmap' | 'podcast' | 'quiz' | 'timeline' | 'compare' | 'flashcards';

export interface GenerationTask {
  id: string;
  type: GenerationType;
  status: 'pending' | 'generating' | 'complete' | 'error';
  position: { x: number; y: number }; // Canvas position where output will appear
  result?: SummaryData | MindmapData | unknown; // Result data when complete
  title?: string;
  error?: string;
  taskId?: string; // Backend task ID
  outputId?: string; // Backend output ID
  createdAt: Date;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  content: string;
  session_id?: string;  // Session this message belongs to
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
  // Optional: context nodes referenced by this message (for user messages)
  contextNodes?: Array<{
    id: string;
    title: string;
    content: string;
  }>;
}

interface StudioContextType {
  // Project
  projectId: string;
  projectTitle: string | null;

  // Documents
  documents: ProjectDocument[];
  setDocuments: (docs: ProjectDocument[]) => void;
  activeDocumentId: string | null;
  setActiveDocumentId: (id: string | null) => void;
  selectedDocumentIds: Set<string>;
  setSelectedDocumentIds: (ids: Set<string> | ((prev: Set<string>) => Set<string>)) => void;
  toggleDocumentSelection: (id: string, multiSelect?: boolean) => void;

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

  // Chat Sessions
  chatSessions: ChatSession[];
  setChatSessions: (sessions: ChatSession[] | ((prev: ChatSession[]) => ChatSession[])) => void;
  activeSessionId: string | null;
  setActiveSessionId: (id: string | null) => void;
  sessionsLoading: boolean;

  // Chat Messages (for current session)
  chatMessages: ChatMessage[];
  setChatMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;

  // Session Actions
  createChatSession: (title?: string, isShared?: boolean) => Promise<ChatSession>;
  switchChatSession: (sessionId: string) => Promise<void>;
  updateChatSessionTitle: (sessionId: string, title: string) => Promise<void>;
  deleteChatSession: (sessionId: string) => Promise<void>;

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

  // Cross-boundary drag (for dragging Konva nodes to DOM elements like chat input)
  crossBoundaryDragNode: { id: string; title: string; content: string; sourceMessageId?: string } | null;
  setCrossBoundaryDragNode: (node: { id: string; title: string; content: string; sourceMessageId?: string } | null) => void;

  // Auto Thinking Path
  autoThinkingPathEnabled: boolean;
  setAutoThinkingPathEnabled: (enabled: boolean) => void;

  // Message <-> Node Navigation
  navigateToMessage: (messageId: string) => void;
  highlightedMessageId: string | null;
  setHighlightedMessageId: (id: string | null) => void;
  navigateToNode: (nodeId: string) => void;
  highlightedNodeId: string | null;

  // === Thinking Graph (Dynamic Mind Map) ===
  activeThinkingId: string | null;  // Currently active thinking node (fork point)
  setActiveThinkingId: (id: string | null) => void;
  thinkingStepCounter: number;
  appendThinkingDraftStep: (userMessage: ChatMessage) => string;  // Returns draft node ID
  finalizeThinkingStep: (messageId: string, backendData: {
    thinkingFields?: CanvasNode['thinkingFields'];
    relatedConcepts?: string[];
    suggestedBranches?: CanvasNode['suggestedBranches'];
    topicId?: string;
  }) => void;
  startNewTopic: () => void;  // Clear activeThinkingId to start a new topic

  // Inspiration Dock
  isInspirationDockVisible: boolean;
  setInspirationDockVisible: (visible: boolean) => void;

  // === PDF Preview Modal ===
  isPreviewModalOpen: boolean;
  previewDocumentId: string | null;
  openDocumentPreview: (documentId: string) => void;
  closeDocumentPreview: () => void;

  // === Concurrent Generation Tasks ===
  generationTasks: Map<string, GenerationTask>;
  startGeneration: (type: GenerationType, position: { x: number; y: number }) => string; // Returns task ID
  updateGenerationTask: (taskId: string, updates: Partial<GenerationTask>) => void;
  updateGenerationTaskPosition: (taskId: string, position: { x: number; y: number }) => void;
  completeGeneration: (taskId: string, result: unknown, title?: string) => void;
  failGeneration: (taskId: string, error: string) => void;
  removeGenerationTask: (taskId: string) => void;
  getActiveGenerationsOfType: (type: GenerationType) => GenerationTask[];
  hasActiveGenerations: () => boolean;
  saveGenerationOutput: (taskId: string, data: Record<string, unknown>, title?: string) => Promise<void>;

  // Legacy Generation State (for backward compatibility during transition)
  isGenerating: boolean;
  setIsGenerating: (generating: boolean) => void;
  generationError: string | null;
  setGenerationError: (error: string | null) => void;
  summaryResult: { data: SummaryData; title: string } | null;
  setSummaryResult: (result: { data: SummaryData; title: string } | null) => void;
  showSummaryOverlay: boolean;
  setShowSummaryOverlay: (show: boolean) => void;

  mindmapResult: { data: MindmapData; title: string } | null;
  setMindmapResult: (result: { data: MindmapData; title: string } | null) => void;
  showMindmapOverlay: boolean;
  setShowMindmapOverlay: (show: boolean) => void;
}

const StudioContext = createContext<StudioContextType | undefined>(undefined);

export function StudioProvider({
  children,
  projectId
}: {
  children: ReactNode;
  projectId: string;
}) {
  const [projectTitle, setProjectTitle] = useState<string | null>(null);
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(new Set());

  const toggleDocumentSelection = useCallback((id: string, multiSelect: boolean = false) => {
    setSelectedDocumentIds(prev => {
      const newSet = new Set(multiSelect ? prev : []);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
    // Also set as active if selecting (optional, but good UX)
    if (!multiSelect) {
      setActiveDocumentId(id);
    }
  }, []);

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
  // Chat Sessions state
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState(false);

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

  // Cross-boundary drag state (for dragging Konva nodes to DOM elements)
  const [crossBoundaryDragNode, setCrossBoundaryDragNode] = useState<{
    id: string;
    title: string;
    content: string;
    sourceMessageId?: string;
  } | null>(null);

  // Auto Thinking Path state
  const [autoThinkingPathEnabled, setAutoThinkingPathEnabled] = useState(true);

  // Message <-> Node Navigation state
  const [highlightedMessageId, setHighlightedMessageId] = useState<string | null>(null);
  const [highlightedNodeId, setHighlightedNodeId] = useState<string | null>(null);

  // === Thinking Graph (Dynamic Mind Map) State ===
  const [activeThinkingId, setActiveThinkingId] = useState<string | null>(null);
  const [thinkingStepCounter, setThinkingStepCounter] = useState(0);

  // Inspiration Dock state
  const [isInspirationDockVisible, setInspirationDockVisible] = useState(true);

  // === PDF Preview Modal State ===
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [previewDocumentId, setPreviewDocumentId] = useState<string | null>(null);

  const openDocumentPreview = useCallback((documentId: string) => {
    setPreviewDocumentId(documentId);
    setIsPreviewModalOpen(true);
  }, []);

  const closeDocumentPreview = useCallback(() => {
    setIsPreviewModalOpen(false);
    setPreviewDocumentId(null);
  }, []);

  // === Concurrent Generation Tasks State ===
  const [generationTasks, setGenerationTasks] = useState<Map<string, GenerationTask>>(new Map());

  // Start a new generation task
  const startGeneration = useCallback((type: GenerationType, position: { x: number; y: number }): string => {
    const taskId = `gen-${type}-${crypto.randomUUID()}`;
    const task: GenerationTask = {
      id: taskId,
      type,
      status: 'pending',
      position,
      createdAt: new Date(),
    };
    setGenerationTasks(prev => {
      const next = new Map(prev);
      next.set(taskId, task);
      return next;
    });
    return taskId;
  }, []);

  // Update an existing generation task
  const updateGenerationTask = useCallback((taskId: string, updates: Partial<GenerationTask>) => {
    setGenerationTasks(prev => {
      const task = prev.get(taskId);
      if (!task) return prev;
      const next = new Map(prev);
      next.set(taskId, { ...task, ...updates });
      return next;
    });
  }, []);

  // Update position of a generation task (for dragging output cards)
  const updateGenerationTaskPosition = useCallback((taskId: string, position: { x: number; y: number }) => {
    const updateStart = performance.now();
    setGenerationTasks(prev => {
      const task = prev.get(taskId);
      if (!task) return prev;
      const next = new Map(prev);
      next.set(taskId, { ...task, position });
      const updateDuration = performance.now() - updateStart;
      if (updateDuration > 5) {
        console.log(`[Perf][Context] State update took ${updateDuration.toFixed(2)}ms`);
      }
      return next;
    });
  }, []);

  // Complete a generation task with result
  const completeGeneration = useCallback((taskId: string, result: unknown, title?: string) => {
    setGenerationTasks(prev => {
      const task = prev.get(taskId);
      if (!task) return prev;
      const next = new Map(prev);
      next.set(taskId, { ...task, status: 'complete', result, title });
      return next;
    });
  }, []);

  // Mark a generation task as failed
  const failGeneration = useCallback((taskId: string, error: string) => {
    setGenerationTasks(prev => {
      const task = prev.get(taskId);
      if (!task) return prev;
      const next = new Map(prev);
      next.set(taskId, { ...task, status: 'error', error });
      return next;
    });
  }, []);

  // Remove a generation task
  const removeGenerationTask = useCallback(async (taskId: string) => {
    // 1. Get task details before removing from state
    const task = generationTasks.get(taskId);

    // 2. Optimistically remove from UI immediately
    setGenerationTasks(prev => {
      const next = new Map(prev);
      next.delete(taskId);
      return next;
    });

    // 3. If it has a backend ID, delete it from the server
    if (task?.outputId && projectId) {
      try {
        console.log(`[StudioContext] Deleting output ${task.outputId} for task ${taskId}`);
        await outputsApi.delete(projectId, task.outputId);
      } catch (error) {
        console.error('[StudioContext] Failed to delete output persistence:', error);
        // We don't rollback state here because the user intent was to remove it from view
        // and we don't want it popping back up.
        // It's better to fail silently on the backend delete than to have a "zombie" card.
      }
    }
  }, [generationTasks, projectId]);

  // Get active (pending or generating) tasks of a specific type
  const getActiveGenerationsOfType = useCallback((type: GenerationType): GenerationTask[] => {
    return Array.from(generationTasks.values()).filter(
      t => t.type === type && (t.status === 'pending' || t.status === 'generating')
    );
  }, [generationTasks]);

  // Check if there are any active generations
  const hasActiveGenerations = useCallback((): boolean => {
    return Array.from(generationTasks.values()).some(
      t => t.status === 'pending' || t.status === 'generating'
    );
  }, [generationTasks]);

  // Save updated output data to the backend and update local state
  const saveGenerationOutput = useCallback(async (
    taskId: string,
    data: Record<string, unknown>,
    title?: string
  ): Promise<void> => {
    const task = generationTasks.get(taskId);
    if (!task || !task.outputId) {
      console.warn('[StudioContext] Cannot save output: Task or outputId not found', taskId);
      return;
    }

    try {
      await outputsApi.update(projectId, task.outputId, { data, title });
      // Update local state
      setGenerationTasks(prev => {
        const t = prev.get(taskId);
        if (!t) return prev;
        const next = new Map(prev);
        next.set(taskId, { ...t, result: data, title: title ?? t.title });
        return next;
      });
      console.log('[StudioContext] Successfully saved output', taskId);
    } catch (error) {
      console.error('[StudioContext] Failed to save output:', error);
      // Could show a toast or error state here in the future
    }
  }, [generationTasks, projectId]);

  // Legacy Generation State (for backward compatibility during transition)
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [summaryResult, setSummaryResult] = useState<{ data: SummaryData; title: string } | null>(null);
  const [showSummaryOverlay, setShowSummaryOverlay] = useState(false);
  const [mindmapResult, setMindmapResult] = useState<{ data: MindmapData; title: string } | null>(null);
  const [showMindmapOverlay, setShowMindmapOverlay] = useState(false);

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

  // === Thinking Graph Methods ===

  /**
   * Create an optimistic "draft" thinking step node when user sends a message.
   * This provides immediate visual feedback before the backend responds.
   * 
   * @param userMessage - The user's chat message
   * @returns The ID of the created draft node
   */
  const appendThinkingDraftStep = useCallback((userMessage: ChatMessage): string => {
    const newStepIndex = thinkingStepCounter + 1;
    setThinkingStepCounter(newStepIndex);

    const draftNodeId = `tp-draft-${crypto.randomUUID()}`;

    // Calculate position based on active thinking node
    let x = 100;
    let y = 300;
    let depth = 0;
    let parentStepId: string | undefined;

    if (activeThinkingId) {
      // Find the active node to position relative to it
      const activeNode = canvasNodes.find(n => n.id === activeThinkingId);
      if (activeNode) {
        parentStepId = activeThinkingId;
        depth = (activeNode.depth || 0) + 1;
        // Position to the right of the active node (horizontal tree layout)
        x = activeNode.x + 400;
        // Offset vertically based on siblings at same depth
        const siblingsAtDepth = canvasNodes.filter(
          n => n.parentStepId === activeThinkingId && n.viewType === 'thinking'
        ).length;
        y = activeNode.y + (siblingsAtDepth * 220);
      }
    } else {
      // No active node - this is a new root topic
      const thinkingNodes = canvasNodes.filter(n => n.viewType === 'thinking');
      if (thinkingNodes.length > 0) {
        // Find the bottom-most node and place below it
        const maxY = Math.max(...thinkingNodes.map(n => n.y));
        y = maxY + 300;
      }
    }

    // Create draft node
    const draftNode: CanvasNode = {
      id: draftNodeId,
      type: 'thinking_step',
      title: `Step ${newStepIndex}`,
      content: userMessage.content.length > 100
        ? userMessage.content.substring(0, 100) + '...'
        : userMessage.content,
      x,
      y,
      width: 320,
      height: 200,
      color: 'purple',  // Draft nodes are purple
      tags: ['#thinking-path', '#draft'],
      viewType: 'thinking',
      messageIds: [userMessage.id],
      analysisStatus: 'pending',
      isDraft: true,
      thinkingStepIndex: newStepIndex,
      depth,
      parentStepId,
      thinkingFields: {
        claim: userMessage.content.length > 100
          ? userMessage.content.substring(0, 100) + '...'
          : userMessage.content,
        reason: '',
        evidence: '',
        uncertainty: '',
        decision: '',
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Add the draft node
    setCanvasNodes(prev => [...prev, draftNode]);

    // Create edge from parent if exists
    if (parentStepId) {
      const edgeId = `edge-${parentStepId}-${draftNodeId}`;
      setCanvasEdges(prev => [...prev, {
        id: edgeId,
        source: parentStepId,
        target: draftNodeId,
      }]);
    }

    // Set this as the new active thinking node
    setActiveThinkingId(draftNodeId);

    return draftNodeId;
  }, [activeThinkingId, canvasNodes, thinkingStepCounter]);

  /**
   * Finalize a draft thinking step with data from the backend.
   * This is called when the backend WebSocket sends the analysis result.
   * 
   * @param messageId - The message ID to match (from the draft node's messageIds)
   * @param backendData - Data from the backend to update the node with
   */
  const finalizeThinkingStep = useCallback((
    messageId: string,
    backendData: {
      thinkingFields?: CanvasNode['thinkingFields'];
      relatedConcepts?: string[];
      suggestedBranches?: CanvasNode['suggestedBranches'];
      topicId?: string;
    }
  ) => {
    setCanvasNodes(prev => prev.map(node => {
      // Find the draft node that matches this message
      if (node.isDraft && node.messageIds?.includes(messageId)) {
        return {
          ...node,
          isDraft: false,
          color: 'blue',  // Finalized nodes are blue
          analysisStatus: 'analyzed' as const,
          thinkingFields: backendData.thinkingFields || node.thinkingFields,
          relatedConcepts: backendData.relatedConcepts,
          suggestedBranches: backendData.suggestedBranches,
          topicId: backendData.topicId,
          tags: node.tags?.filter(t => t !== '#draft') || ['#thinking-path'],
          updatedAt: new Date().toISOString(),
        };
      }
      return node;
    }));
  }, []);

  /**
   * Start a new topic by clearing the activeThinkingId.
   * The next message will create a new root node in the thinking graph.
   */
  const startNewTopic = useCallback(() => {
    setActiveThinkingId(null);
  }, []);

  const addNodeToCanvas = useCallback((node: Omit<CanvasNode, 'id'>) => {
    const newNode: CanvasNode = {
      ...node,
      viewType: currentView,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      id: `node-${crypto.randomUUID()}`,
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
      id: `node-${crypto.randomUUID()}`,
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

  // Session Management Functions
  const createChatSession = useCallback(async (title: string = 'New Conversation', isShared: boolean = true): Promise<ChatSession> => {
    const session = await chatApi.createSession(projectId, title, isShared);
    setChatSessions(prev => [session, ...prev]);
    setActiveSessionId(session.id);
    // Clear messages for new session
    setChatMessages([
      {
        id: 'welcome',
        role: 'ai',
        content: "Hello! I'm your research assistant. Upload a document and ask me anything about it.",
        timestamp: new Date(),
      }
    ]);
    return session;
  }, [projectId]);

  const switchChatSession = useCallback(async (sessionId: string) => {
    if (sessionId === activeSessionId) return;

    setActiveSessionId(sessionId);

    // Load history for the selected session
    try {
      const historyRes = await chatApi.getHistory(projectId, sessionId);
      if (historyRes && historyRes.messages.length > 0) {
        setChatMessages(
          historyRes.messages.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            session_id: m.session_id,
            sources: m.sources,
            timestamp: new Date(m.created_at),
          }))
        );
      } else {
        setChatMessages([
          {
            id: 'welcome',
            role: 'ai',
            content: "Hello! I'm your research assistant. Upload a document and ask me anything about it.",
            timestamp: new Date(),
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to load session history:', error);
    }
  }, [projectId, activeSessionId]);

  const updateChatSessionTitle = useCallback(async (sessionId: string, title: string) => {
    const updatedSession = await chatApi.updateSession(projectId, sessionId, title);
    setChatSessions(prev =>
      prev.map(s => s.id === sessionId ? updatedSession : s)
    );
  }, [projectId]);

  const deleteChatSession = useCallback(async (sessionId: string) => {
    await chatApi.deleteSession(projectId, sessionId);
    setChatSessions(prev => prev.filter(s => s.id !== sessionId));

    // If we deleted the active session, switch to another one
    if (sessionId === activeSessionId) {
      const remainingSessions = chatSessions.filter(s => s.id !== sessionId);
      if (remainingSessions.length > 0) {
        await switchChatSession(remainingSessions[0].id);
      } else {
        // Create a new default session
        await createChatSession('Default Conversation', true);
      }
    }
  }, [projectId, activeSessionId, chatSessions, switchChatSession, createChatSession]);

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
    setChatSessions([]);
    setActiveSessionId(null);
    setChatMessages([
      {
        id: 'welcome',
        role: 'ai',
        content: "Hello! I'm your research assistant. Upload a document and ask me anything about it.",
        timestamp: new Date(),
      }
    ]);
    setActiveDocumentId(null);
    setSelectedDocumentIds(new Set());
    setSourceNavigation(null);
    // Clear generation tasks when switching projects
    setGenerationTasks(new Map());

    const loadData = async () => {
      setSessionsLoading(true);
      try {
        const [docsRes, canvasRes, sessionsRes, outputsRes, projectRes] = await Promise.all([
          documentsApi.list(projectId),
          canvasApi.get(projectId).catch(() => null), // Handle 404 for new canvas
          chatApi.listSessions(projectId).catch(() => null),
          outputsApi.list(projectId).catch(() => null), // Fetch saved outputs
          projectsApi.get(projectId).catch(() => null),
        ]);

        if (projectRes) {
          setProjectTitle(projectRes.name);
        }

        if (docsRes) {
          setDocuments(docsRes.items);
        }

        if (canvasRes) {
          // Deduplicate nodes by ID to prevent React key conflicts
          const nodesMap = new Map<string, CanvasNode>();
          (canvasRes.nodes || []).forEach((node: CanvasNode) => {
            if (!nodesMap.has(node.id)) {
              nodesMap.set(node.id, node);
            } else {
              console.warn(`[StudioContext] Duplicate node ID detected and skipped: ${node.id}`);
            }
          });
          setCanvasNodes(Array.from(nodesMap.values()));
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

        // Restore saved outputs (summary, mindmap) into generationTasks
        if (outputsRes && outputsRes.outputs.length > 0) {
          // Filter for complete outputs only
          const completeOutputs = outputsRes.outputs.filter(
            (o: OutputResponse) => o.status === 'complete'
          );

          // Convert persisted outputs to GenerationTask format
          const restoredTasks = new Map<string, GenerationTask>();

          // Grid layout for multiple outputs: position them in a grid pattern
          const CARD_WIDTH = 380;
          const CARD_HEIGHT = 280;
          const GAP = 40;
          const START_X = 200;
          const START_Y = 200;

          completeOutputs.forEach((output: OutputResponse, index: number) => {
            // Skip outputs without data
            if (!output.data) return;

            // Map output_type to GenerationType
            const type = output.output_type as GenerationType;
            if (type !== 'summary' && type !== 'mindmap') return; // Only support these for now

            // Calculate grid position (2 columns)
            const col = index % 2;
            const row = Math.floor(index / 2);
            const x = START_X + col * (CARD_WIDTH + GAP);
            const y = START_Y + row * (CARD_HEIGHT + GAP);

            const task: GenerationTask = {
              id: output.id,
              type,
              status: 'complete',
              position: { x, y },
              result: output.data,
              title: output.title,
              outputId: output.id,
              createdAt: new Date(output.created_at),
            };

            restoredTasks.set(output.id, task);
          });

          // Set the restored tasks
          if (restoredTasks.size > 0) {
            setGenerationTasks(restoredTasks);
          }

          // Also set legacy states for backward compatibility
          const latestSummary = completeOutputs.find(
            (o: OutputResponse) => o.output_type === 'summary'
          );
          if (latestSummary?.data) {
            setSummaryResult({
              data: latestSummary.data as SummaryData,
              title: latestSummary.title || 'Summary',
            });
            // Keep overlay closed - user clicks to view
            setShowSummaryOverlay(false);
          }

          const latestMindmap = completeOutputs.find(
            (o: OutputResponse) => o.output_type === 'mindmap'
          );
          if (latestMindmap?.data) {
            setMindmapResult({
              data: latestMindmap.data as MindmapData,
              title: latestMindmap.title || 'Mindmap',
            });
            // Keep overlay closed - user clicks to view
            setShowMindmapOverlay(false);
          }
        }

        // Load sessions and set active session
        let currentSessionId: string | null = null;
        if (sessionsRes && sessionsRes.items.length > 0) {
          setChatSessions(sessionsRes.items);
          // Select the first session (most recent by last_message_at)
          currentSessionId = sessionsRes.items[0].id;
          setActiveSessionId(currentSessionId);
        } else {
          // Create a default session if none exist
          try {
            const defaultSession = await chatApi.getOrCreateDefaultSession(projectId);
            setChatSessions([defaultSession]);
            currentSessionId = defaultSession.id;
            setActiveSessionId(currentSessionId);
          } catch (error) {
            console.error('Failed to create default session:', error);
          }
        }

        // Load chat history for the active session
        if (currentSessionId) {
          try {
            const historyRes = await chatApi.getHistory(projectId, currentSessionId);
            if (historyRes && historyRes.messages.length > 0) {
              setChatMessages(
                historyRes.messages.map((m) => ({
                  id: m.id,
                  role: m.role,
                  content: m.content,
                  session_id: m.session_id,
                  sources: m.sources,
                  timestamp: new Date(m.created_at),
                }))
              );
            }
          } catch (error) {
            console.error('Failed to load chat history:', error);
          }
        }
      } catch (error) {
        console.error('Failed to load project data:', error);
      } finally {
        setSessionsLoading(false);
      }
    };

    loadData();
  }, [projectId]);



  const value: StudioContextType = {
    projectId,
    projectTitle,
    documents,
    setDocuments,
    activeDocumentId,
    setActiveDocumentId,
    selectedDocumentIds,
    setSelectedDocumentIds,
    toggleDocumentSelection,
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
    // Chat Sessions
    chatSessions,
    setChatSessions,
    activeSessionId,
    setActiveSessionId,
    sessionsLoading,
    // Chat Messages
    chatMessages,
    setChatMessages,
    // Session Actions
    createChatSession,
    switchChatSession,
    updateChatSessionTitle,
    deleteChatSession,
    // Canvas Actions
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
    crossBoundaryDragNode,
    setCrossBoundaryDragNode,
    autoThinkingPathEnabled,
    setAutoThinkingPathEnabled,
    navigateToMessage,
    highlightedMessageId,
    setHighlightedMessageId,
    navigateToNode,
    highlightedNodeId,
    // Thinking Graph
    activeThinkingId,
    setActiveThinkingId,
    thinkingStepCounter,
    appendThinkingDraftStep,
    finalizeThinkingStep,
    startNewTopic,
    // Inspiration Dock
    isInspirationDockVisible,
    setInspirationDockVisible,
    // Concurrent Generation Tasks
    generationTasks,
    startGeneration,
    updateGenerationTask,
    updateGenerationTaskPosition,
    completeGeneration,
    failGeneration,
    removeGenerationTask,
    getActiveGenerationsOfType,
    hasActiveGenerations,
    saveGenerationOutput,
    // Legacy Generation State (backward compatibility)
    isGenerating,
    setIsGenerating,
    generationError,
    setGenerationError,
    summaryResult,
    setSummaryResult,
    showSummaryOverlay,
    setShowSummaryOverlay,
    mindmapResult,
    setMindmapResult,
    showMindmapOverlay,
    setShowMindmapOverlay,

    // PDF Preview
    isPreviewModalOpen,
    previewDocumentId,
    openDocumentPreview,
    closeDocumentPreview,
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

