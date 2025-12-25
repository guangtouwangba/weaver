import { useCallback, useRef, useEffect } from 'react';
import { useStudio, GenerationType } from '@/contexts/StudioContext';
import { 
  CanvasNode, 
  CanvasEdge, 
  outputsApi, 
  SummaryData, 
  MindmapData, 
  MindmapNode, 
  MindmapEdge,
  getWebSocketUrl 
} from '@/lib/api';

// Helper for polling (still used for non-streaming types)
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

interface UseCanvasActionsProps {
  onOpenImport?: () => void;
}

export function useCanvasActions({ onOpenImport }: UseCanvasActionsProps = {}) {
  const { 
    addNodeToCanvas, 
    documents, 
    projectId, 
    selectedDocumentIds,
    setCanvasNodes,
    setCanvasEdges,
    canvasViewport,
    // Global state setters (legacy)
    setIsGenerating,
    setGenerationError,
    setSummaryResult,
    setShowSummaryOverlay,
    setMindmapResult,
    setShowMindmapOverlay,
    // Concurrent generation
    startGeneration,
    updateGenerationTask,
    completeGeneration,
    failGeneration,
  } = useStudio();

  // WebSocket ref for streaming
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    };
  }, []);

  const handleAddNode = useCallback((
    type: 'default' | 'sticky' | 'source' | 'insight', 
    position: { x: number, y: number },
    content: string = 'New Node'
  ) => {
    const node: Omit<CanvasNode, 'id'> = {
      type: type === 'sticky' ? 'sticky' : 'default',
      title: type === 'sticky' ? 'Sticky Note' : 'New Node',
      content: content,
      x: position.x,
      y: position.y,
      width: type === 'sticky' ? 200 : 280,
      height: type === 'sticky' ? 200 : 160,
      color: type === 'sticky' ? '#fef3c7' : 'white',
      viewType: 'free',
    };
    
    addNodeToCanvas(node);
  }, [addNodeToCanvas]);

  /**
   * Generate mindmap using WebSocket streaming for real-time node visualization
   */
  const handleGenerateMindmapStreaming = useCallback(async (
    targetDocumentIds: string[],
    title: string,
    docTitle: string
  ) => {
    if (!projectId) return;

    // Start generation via API
    const { task_id, output_id } = await outputsApi.generate(
      projectId,
      'mindmap',
      targetDocumentIds,
      title
    );

    console.log(`[Mindmap] Started streaming generation: task=${task_id}, output=${output_id}`);

    // Initialize empty mindmap data and show overlay immediately
    const streamingData: MindmapData = { nodes: [], edges: [] };
    
    setMindmapResult({
      data: { ...streamingData },
      title: docTitle
    });
    setShowMindmapOverlay(true);

    // Connect to WebSocket for real-time updates
    return new Promise<void>((resolve, reject) => {
      const wsUrl = `${getWebSocketUrl()}/ws/projects/${projectId}/outputs?task_id=${task_id}`;
      console.log('[Mindmap WS] Connecting to:', wsUrl);

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('[Mindmap WS] Connected');
          
          // Start ping interval
          pingIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
            }
          }, 30000);
        };

        ws.onmessage = (event) => {
          if (event.data === 'pong') return;

          try {
            const data = JSON.parse(event.data);
            console.log('[Mindmap WS] Event:', data.type, data);

            switch (data.type) {
              case 'node_added':
                if (data.nodeData) {
                  const node = data.nodeData as MindmapNode;
                  streamingData.nodes.push(node);
                  
                  // Update result with new node - create new object for React to detect change
                  setMindmapResult({
                    data: { 
                      nodes: [...streamingData.nodes], 
                      edges: [...streamingData.edges] 
                    },
                    title: docTitle
                  });
                }
                break;

              case 'edge_added':
                if (data.edgeData) {
                  const edge = data.edgeData as MindmapEdge;
                  streamingData.edges.push(edge);
                  
                  // Update result with new edge
                  setMindmapResult({
                    data: { 
                      nodes: [...streamingData.nodes], 
                      edges: [...streamingData.edges] 
                    },
                    title: docTitle
                  });
                }
                break;

              case 'generation_progress':
                // Could show progress indicator here
                console.log(`[Mindmap] Progress: ${(data.progress * 100).toFixed(0)}%`);
                break;

              case 'level_complete':
                console.log(`[Mindmap] Level ${data.currentLevel}/${data.totalLevels} complete`);
                break;

              case 'generation_complete':
                console.log('[Mindmap] Generation complete:', data.message);
                setIsGenerating(false);
                
                // Clean up WebSocket
                if (pingIntervalRef.current) {
                  clearInterval(pingIntervalRef.current);
                  pingIntervalRef.current = null;
                }
                ws.close();
                wsRef.current = null;
                
                resolve();
                break;

              case 'generation_error':
                console.error('[Mindmap] Generation error:', data.errorMessage);
                setGenerationError(data.errorMessage || 'Generation failed');
                setIsGenerating(false);
                
                // Clean up WebSocket
                if (pingIntervalRef.current) {
                  clearInterval(pingIntervalRef.current);
                  pingIntervalRef.current = null;
                }
                ws.close();
                wsRef.current = null;
                
                reject(new Error(data.errorMessage || 'Generation failed'));
                break;
            }
          } catch (e) {
            console.error('[Mindmap WS] Failed to parse message:', e);
          }
        };

        ws.onerror = (error) => {
          console.error('[Mindmap WS] Error:', error);
          setGenerationError('WebSocket connection error');
          setIsGenerating(false);
          reject(new Error('WebSocket connection error'));
        };

        ws.onclose = (event) => {
          console.log('[Mindmap WS] Disconnected:', event.code, event.reason);
          
          if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current);
            pingIntervalRef.current = null;
          }
          wsRef.current = null;
          
          // If closed unexpectedly before completion, fall back to polling
          if (event.code !== 1000 && streamingData.nodes.length === 0) {
            console.log('[Mindmap WS] Falling back to polling...');
            handleFallbackPolling(output_id, 'mindmap', docTitle).then(resolve).catch(reject);
          }
        };

      } catch (error) {
        console.error('[Mindmap WS] Failed to create WebSocket:', error);
        // Fall back to polling
        handleFallbackPolling(output_id, 'mindmap', docTitle).then(resolve).catch(reject);
      }
    });
  }, [projectId, setMindmapResult, setShowMindmapOverlay, setIsGenerating, setGenerationError]);

  /**
   * Fallback polling for when WebSocket fails or for non-streaming types
   */
  const handleFallbackPolling = useCallback(async (
    outputId: string,
    type: string,
    docTitle: string
  ) => {
    if (!projectId) return;

    let attempts = 0;
    const maxAttempts = 300; // 5 minutes timeout for fallback
    
    while (attempts < maxAttempts) {
      await sleep(1000);
      const output = await outputsApi.get(projectId, outputId);
      
      if (output.status === 'complete') {
        console.log(`${type} generation complete (polling):`, output);
        
        if (type === 'mindmap' && output.data) {
          const mindmapData = output.data as MindmapData;
          setMindmapResult({
            data: mindmapData,
            title: output.title || docTitle
          });
          setShowMindmapOverlay(true);
        } else if (type === 'summary' && output.data) {
          const summaryData = output.data as SummaryData;
          setSummaryResult({
            data: summaryData,
            title: output.title || docTitle
          });
          setShowSummaryOverlay(true);
        } else if (type === 'flashcards' && output.data) {
          const flashcardData = output.data as { cards: unknown[] };
          console.log('Flashcards generated:', flashcardData.cards);
          alert(`Generated ${flashcardData.cards.length} flashcards! View them in the console.`);
        }
        
        setIsGenerating(false);
        return;
      } else if (output.status === 'error') {
        const errMsg = output.error_message || 'Generation failed';
        console.error(`${type} generation failed:`, errMsg);
        setGenerationError(errMsg);
        setIsGenerating(false);
        throw new Error(errMsg);
      }
      
      attempts++;
    }

    setGenerationError('Generation timed out');
    setIsGenerating(false);
    throw new Error('Generation timed out');
  }, [projectId, setMindmapResult, setShowMindmapOverlay, setSummaryResult, setShowSummaryOverlay, setIsGenerating, setGenerationError]);

  const handleGenerateContent = useCallback(async (
    type: 'mindmap' | 'flashcards' | 'summary' | 'podcast' | 'quiz' | 'timeline' | 'compare'
  ) => {
    if (!documents.length) {
      console.warn('No documents to generate from');
      return;
    }

    if (!projectId) {
      console.error('No project ID');
      return;
    }

    // Start Global Loading State
    setIsGenerating(true);
    setGenerationError(null);
    setSummaryResult(null);
    setShowSummaryOverlay(false);
    setMindmapResult(null);
    setShowMindmapOverlay(false);

    try {
      const targetDocumentIds = selectedDocumentIds.size > 0 
        ? Array.from(selectedDocumentIds) 
        : documents.map(d => d.id);

      const firstDocId = targetDocumentIds[0];
      const firstDoc = documents.find(d => d.id === firstDocId);
      const docTitle = firstDoc?.filename || 'Document';
      const title = `Generated ${type}`;

      console.log(`Starting ${type} generation...`);

      // Use streaming for mindmap, polling for others
      if (type === 'mindmap') {
        await handleGenerateMindmapStreaming(targetDocumentIds, title, docTitle);
      } else {
        // Start generation and poll for completion
        const { output_id } = await outputsApi.generate(
          projectId,
          type as 'summary' | 'flashcards',
          targetDocumentIds,
          title
        );

        await handleFallbackPolling(output_id, type, docTitle);
      }
      
    } catch (error) {
      console.error(`Failed to generate ${type}:`, error);
      if (!String(error).includes('timed out') && !String(error).includes('failed')) {
        setGenerationError(error instanceof Error ? error.message : 'Unknown error');
      }
      setIsGenerating(false);
    }
  }, [
    documents, 
    selectedDocumentIds, 
    projectId, 
    setIsGenerating,
    setGenerationError,
    setSummaryResult,
    setShowSummaryOverlay,
    setMindmapResult,
    setShowMindmapOverlay,
    handleGenerateMindmapStreaming,
    handleFallbackPolling
  ]);

  const handleImportSource = useCallback(() => {
    if (onOpenImport) {
      onOpenImport();
    } else {
      console.warn('Import dialog handler not provided');
    }
  }, [onOpenImport]);

  /**
   * Get the current viewport center position for placing generated content
   */
  const getViewportCenterPosition = useCallback(() => {
    // Calculate center of visible canvas area
    // canvasViewport contains { x, y, scale } where x,y is the pan offset
    // We want to find the center of what's currently visible
    const viewportWidth = typeof window !== 'undefined' ? window.innerWidth * 0.6 : 800; // Approximate canvas width
    const viewportHeight = typeof window !== 'undefined' ? window.innerHeight * 0.7 : 600;
    
    const centerX = (-canvasViewport.x + viewportWidth / 2) / canvasViewport.scale;
    const centerY = (-canvasViewport.y + viewportHeight / 2) / canvasViewport.scale;
    
    return { x: centerX, y: centerY };
  }, [canvasViewport]);

  /**
   * Concurrent (non-blocking) version of content generation.
   * Starts generation in background and updates task state.
   * Does NOT block the UI or wait for completion.
   */
  const handleGenerateContentConcurrent = useCallback((
    type: GenerationType,
    position: { x: number; y: number }
  ) => {
    if (!documents.length) {
      console.warn('No documents to generate from');
      return;
    }

    if (!projectId) {
      console.error('No project ID');
      return;
    }

    // Start a new generation task (non-blocking)
    const taskId = startGeneration(type, position);
    
    const targetDocumentIds = selectedDocumentIds.size > 0 
      ? Array.from(selectedDocumentIds) 
      : documents.map(d => d.id);

    const firstDocId = targetDocumentIds[0];
    const firstDoc = documents.find(d => d.id === firstDocId);
    const docTitle = firstDoc?.filename || 'Document';
    const title = `Generated ${type}`;

    console.log(`[Concurrent] Starting ${type} generation, task=${taskId}...`);

    // Start the generation process asynchronously (fire and forget)
    (async () => {
      try {
        // Start generation via API
        const { task_id, output_id } = await outputsApi.generate(
          projectId,
          type as 'summary' | 'mindmap' | 'flashcards',
          targetDocumentIds,
          title
        );

        // Update task with backend IDs
        updateGenerationTask(taskId, { 
          taskId: task_id, 
          outputId: output_id,
          status: 'generating' 
        });

        // For mindmap, use WebSocket streaming
        if (type === 'mindmap') {
          await handleMindmapStreamingConcurrent(taskId, task_id, output_id, docTitle);
        } else {
          // For other types, poll for completion
          await handlePollingConcurrent(taskId, output_id, type, docTitle);
        }
      } catch (error) {
        console.error(`[Concurrent] Failed to generate ${type}:`, error);
        failGeneration(taskId, error instanceof Error ? error.message : 'Unknown error');
      }
    })();

    return taskId;
  }, [documents, selectedDocumentIds, projectId, startGeneration, updateGenerationTask, failGeneration]);

  /**
   * WebSocket streaming for mindmap generation (concurrent version)
   */
  const handleMindmapStreamingConcurrent = useCallback(async (
    localTaskId: string,
    backendTaskId: string,
    outputId: string,
    docTitle: string
  ) => {
    if (!projectId) return;

    const streamingData: MindmapData = { nodes: [], edges: [] };

    // Also show in legacy overlay for backward compatibility
    setMindmapResult({
      data: { ...streamingData },
      title: docTitle
    });
    setShowMindmapOverlay(true);

    return new Promise<void>((resolve, reject) => {
      const wsUrl = `${getWebSocketUrl()}/ws/projects/${projectId}/outputs?task_id=${backendTaskId}`;
      console.log('[Mindmap WS Concurrent] Connecting to:', wsUrl);

      try {
        const ws = new WebSocket(wsUrl);
        
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);

        ws.onopen = () => {
          console.log('[Mindmap WS Concurrent] Connected');
        };

        ws.onmessage = (event) => {
          if (event.data === 'pong') return;

          try {
            const data = JSON.parse(event.data);

            switch (data.type) {
              case 'node_added':
                if (data.nodeData) {
                  streamingData.nodes.push(data.nodeData as MindmapNode);
                  setMindmapResult({
                    data: { 
                      nodes: [...streamingData.nodes], 
                      edges: [...streamingData.edges] 
                    },
                    title: docTitle
                  });
                }
                break;

              case 'edge_added':
                if (data.edgeData) {
                  streamingData.edges.push(data.edgeData as MindmapEdge);
                  setMindmapResult({
                    data: { 
                      nodes: [...streamingData.nodes], 
                      edges: [...streamingData.edges] 
                    },
                    title: docTitle
                  });
                }
                break;

              case 'generation_complete':
                console.log('[Mindmap WS Concurrent] Complete');
                completeGeneration(localTaskId, streamingData, docTitle);
                clearInterval(pingInterval);
                ws.close();
                resolve();
                break;

              case 'generation_error':
                console.error('[Mindmap WS Concurrent] Error:', data.errorMessage);
                failGeneration(localTaskId, data.errorMessage || 'Generation failed');
                clearInterval(pingInterval);
                ws.close();
                reject(new Error(data.errorMessage));
                break;
            }
          } catch (e) {
            console.error('[Mindmap WS Concurrent] Parse error:', e);
          }
        };

        ws.onerror = () => {
          clearInterval(pingInterval);
          // Fall back to polling on WebSocket error
          handlePollingConcurrent(localTaskId, outputId, 'mindmap', docTitle)
            .then(resolve)
            .catch(reject);
        };

        ws.onclose = (event) => {
          clearInterval(pingInterval);
          if (event.code !== 1000 && streamingData.nodes.length === 0) {
            handlePollingConcurrent(localTaskId, outputId, 'mindmap', docTitle)
              .then(resolve)
              .catch(reject);
          }
        };

      } catch (error) {
        handlePollingConcurrent(localTaskId, outputId, 'mindmap', docTitle)
          .then(resolve)
          .catch(reject);
      }
    });
  }, [projectId, setMindmapResult, setShowMindmapOverlay, completeGeneration, failGeneration]);

  /**
   * Polling for concurrent generation completion
   */
  const handlePollingConcurrent = useCallback(async (
    localTaskId: string,
    outputId: string,
    type: string,
    docTitle: string
  ) => {
    if (!projectId) return;

    let attempts = 0;
    const maxAttempts = 300; // 5 minutes
    
    while (attempts < maxAttempts) {
      await sleep(1000);
      const output = await outputsApi.get(projectId, outputId);
      
      if (output.status === 'complete') {
        console.log(`[Concurrent] ${type} complete`);
        
        if (type === 'mindmap' && output.data) {
          setMindmapResult({
            data: output.data as MindmapData,
            title: output.title || docTitle
          });
          setShowMindmapOverlay(true);
        } else if (type === 'summary' && output.data) {
          setSummaryResult({
            data: output.data as SummaryData,
            title: output.title || docTitle
          });
          setShowSummaryOverlay(true);
        }
        
        completeGeneration(localTaskId, output.data, output.title || docTitle);
        return;
      } else if (output.status === 'error') {
        const errMsg = output.error_message || 'Generation failed';
        failGeneration(localTaskId, errMsg);
        throw new Error(errMsg);
      }
      
      attempts++;
    }

    failGeneration(localTaskId, 'Generation timed out');
    throw new Error('Generation timed out');
  }, [projectId, setMindmapResult, setShowMindmapOverlay, setSummaryResult, setShowSummaryOverlay, completeGeneration, failGeneration]);

  return {
    handleAddNode,
    handleGenerateContent, // Legacy blocking version
    handleGenerateContentConcurrent, // New concurrent version
    getViewportCenterPosition,
    handleImportSource,
  };
}
