/**
 * MindMapEditor - Interactive Mind Map Editor
 * 
 * Features:
 * - Draggable nodes
 * - Pan and zoom canvas
 * - Layout selection (radial, tree, balanced)
 * - Node editing (add, delete, edit)
 * - Export (PNG, JSON)
 * - Performance optimizations
 */

import React, { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import { Stage, Layer, Rect } from 'react-konva';
import Konva from 'konva';
import {
  IconButton,
  Button,
  Tooltip,
  Modal,
  Chip,
  Spinner,
  Surface,
  Text,
} from '@/components/ui/primitives';
import {
  Menu,
  MenuItem,
  TextField,
} from '@/components/ui/composites';
import { colors } from '@/components/ui/tokens';
import {
  CloseIcon,
  ZoomInIcon,
  ZoomOutIcon,
  AddIcon,
  DeleteIcon,
  EditIcon,
  RefreshIcon,
  LayersIcon,
  WarningIcon,
  OpenWithIcon,
  DownloadIcon,
  AccountTreeIcon,
  CircleIcon,
} from '@/components/ui/icons';
import { MindmapData, MindmapNode, MindmapEdge } from '@/lib/api';
import { RichMindMapNode } from './RichMindMapNode';
import { CurvedMindMapEdge } from './CurvedMindMapEdge';
import { SourceContextPanel } from './SourceContextPanel';
import { applyLayout, resolveOverlaps, LayoutType } from './layoutAlgorithms';
import { useHistory } from '@/hooks/useHistory';

// ============================================================================
// Types
// ============================================================================

interface MindMapEditorProps {
  initialData: MindmapData;
  title: string;
  onClose: () => void;
  onSave?: (data: MindmapData) => void;
  /** Callback when user wants to open a source reference (e.g., PDF preview) */
  onOpenSourceRef?: (sourceId: string, sourceType: string, location?: string, quote?: string) => void;
}

interface ViewportState {
  x: number;
  y: number;
  scale: number;
}

// ============================================================================
// Constants
// ============================================================================

const MIN_SCALE = 0.1;
const MAX_SCALE = 3;
const SCALE_STEP = 0.1;
const PERFORMANCE_WARNING_THRESHOLD = 200;
const ANIMATION_THRESHOLD = 50; // Disable animations for large datasets
const RESIZE_DEBOUNCE_MS = 200;
const LOD_THRESHOLDS = {
  HIDE_CONTENT: 0.7,
  LABELS_ONLY: 0.5,
  SIMPLE_SHAPES: 0.3,
};

// ============================================================================
// Toolbar Component
// ============================================================================

interface ToolbarProps {
  layoutType: LayoutType;
  onLayoutChange: (layout: LayoutType) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  onAddNode: () => void;
  onDeleteNode: () => void;
  onEditNode: () => void;
  onExport: (format: 'png' | 'json') => void;
  hasSelection: boolean;
  nodeCount: number;
  scale: number;
}

const Toolbar: React.FC<ToolbarProps> = ({
  layoutType,
  onLayoutChange,
  onZoomIn,
  onZoomOut,
  onResetView,
  onAddNode,
  onDeleteNode,
  onEditNode,
  onExport,
  hasSelection,
  nodeCount,
  scale,
}) => {
  const [exportAnchor, setExportAnchor] = useState<null | HTMLElement>(null);

  const layoutOptions: { value: LayoutType; label: string; icon: React.ReactNode }[] = [
    { value: 'balanced', label: 'Balanced', icon: <AccountTreeIcon size="sm" /> },
    { value: 'radial', label: 'Radial', icon: <CircleIcon size="sm" /> },
    { value: 'tree', label: 'Tree', icon: <LayersIcon size="sm" /> },
  ];

  return (
    <Surface
      elevation={1}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        padding: 12,
        borderBottom: `1px solid ${colors.border.default}`,
        backgroundColor: colors.background.default,
        flexWrap: 'wrap',
      }}
    >
      {/* Layout Selection */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Text variant="caption" style={{ marginRight: 4, color: colors.text.secondary }}>
          Layout:
        </Text>
        <div style={{ display: 'flex', gap: 4 }}>
          {layoutOptions.map((opt) => (
            <Tooltip key={opt.value} title={opt.label}>
              <Button
                onClick={() => onLayoutChange(opt.value)}
                variant={layoutType === opt.value ? 'primary' : 'outline'}
                size="sm"
                style={{ minWidth: 40, padding: 0 }}
              >
                {opt.icon}
              </Button>
            </Tooltip>
          ))}
        </div>
      </div>

      <div style={{ width: 1, backgroundColor: colors.border.default, height: 24 }} />

      {/* Zoom Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <Tooltip title="Zoom Out">
          <IconButton size="sm" onClick={onZoomOut}>
            <ZoomOutIcon size={18} />
          </IconButton>
        </Tooltip>
        <Chip
          label={`${Math.round(scale * 100)}%`}
          size="sm"
          variant="outlined"
          style={{ minWidth: 60, justifyContent: 'center' }}
        />
        <Tooltip title="Zoom In">
          <IconButton size="sm" onClick={onZoomIn}>
            <ZoomInIcon size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Reset View">
          <IconButton size="sm" onClick={onResetView}>
            <RefreshIcon size={18} />
          </IconButton>
        </Tooltip>
      </div>

      <div style={{ width: 1, backgroundColor: colors.border.default, height: 24 }} />

      {/* Node Editing */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <Tooltip title="Add Node">
          <IconButton size="sm" onClick={onAddNode} disabled={!hasSelection}>
            <AddIcon size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Edit Node">
          <IconButton size="sm" onClick={onEditNode} disabled={!hasSelection}>
            <EditIcon size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete Node">
          <IconButton size="sm" onClick={onDeleteNode} disabled={!hasSelection}>
            <DeleteIcon size={18} />
          </IconButton>
        </Tooltip>
      </div>

      <div style={{ width: 1, backgroundColor: colors.border.default, height: 24 }} />

      {/* Export */}
      <Tooltip title="Download">
        <IconButton size="sm" onClick={(e) => setExportAnchor(e.currentTarget)}>
          <DownloadIcon size={18} />
        </IconButton>
      </Tooltip>
      <Menu
        open={Boolean(exportAnchor)}
        onClose={() => setExportAnchor(null)}
        anchorPosition={exportAnchor ? {
          top: exportAnchor.getBoundingClientRect().bottom + 8,
          left: exportAnchor.getBoundingClientRect().left
        } : undefined}
      >
        <MenuItem onClick={() => { onExport('png'); setExportAnchor(null); }}>
          Export as PNG
        </MenuItem>
        <MenuItem onClick={() => { onExport('json'); setExportAnchor(null); }}>
          Export as JSON
        </MenuItem>
      </Menu>

      {/* Spacer */}
      <div style={{ flexGrow: 1 }} />

      {/* Node Count & Warning */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {nodeCount >= PERFORMANCE_WARNING_THRESHOLD && (
          <Tooltip title="Large mindmap may affect performance">
            <Chip
              icon={<WarningIcon size={14} />}
              label={`${nodeCount} nodes`}
              size="sm"
              style={{ color: colors.warning[700], borderColor: colors.warning[200], backgroundColor: colors.warning[50] }}
              variant="outlined"
            />
          </Tooltip>
        )}
        {nodeCount < PERFORMANCE_WARNING_THRESHOLD && (
          <Text variant="caption" style={{ color: colors.text.secondary }}>
            {nodeCount} nodes
          </Text>
        )}
      </div>
    </Surface>
  );
};

// ============================================================================
// Node Edit Dialog
// ============================================================================

interface NodeEditDialogProps {
  open: boolean;
  mode: 'add' | 'edit';
  initialLabel?: string;
  initialContent?: string;
  onClose: () => void;
  onSave: (label: string, content: string) => void;
}

const NodeEditDialog: React.FC<NodeEditDialogProps> = ({
  open,
  mode,
  initialLabel = '',
  initialContent = '',
  onClose,
  onSave,
}) => {
  const [label, setLabel] = useState(initialLabel);
  const [content, setContent] = useState(initialContent);
  const [prevOpen, setPrevOpen] = useState(open);

  // Sync state with props when dialog opens or initial values change
  if (open !== prevOpen && open) {
    setLabel(initialLabel);
    setContent(initialContent);
    setPrevOpen(open);
  } else if (open !== prevOpen) {
    setPrevOpen(open);
  }

  // Also sync if initial values change while open
  // This is a derived state pattern
  const [prevInitialLabel, setPrevInitialLabel] = useState(initialLabel);
  const [prevInitialContent, setPrevInitialContent] = useState(initialContent);

  if (open && (initialLabel !== prevInitialLabel || initialContent !== prevInitialContent)) {
    setLabel(initialLabel);
    setContent(initialContent);
    setPrevInitialLabel(initialLabel);
    setPrevInitialContent(initialContent);
  }

  const handleSave = () => {
    if (label.trim()) {
      onSave(label.trim(), content.trim());
      onClose();
    }
  };

  return (
    <Modal open={open} onClose={onClose} size="md">
      <Modal.Header>{mode === 'add' ? 'Add New Node' : 'Edit Node'}</Modal.Header>
      <Modal.Content>
        <TextField
          autoFocus
          label="Label"
          fullWidth
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          inputStyle={{ marginBottom: 16 }}
        />
        <TextField
          label="Content (optional)"
          fullWidth
          multiline
          rows={3}
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      </Modal.Content>
      <Modal.Footer>
        <Button variant="ghost" onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="primary" disabled={!label.trim()}>
          {mode === 'add' ? 'Add' : 'Save'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

// Helper to deduplicate nodes by ID
const deduplicateNodes = (nodes: MindmapNode[]): MindmapNode[] => {
  const seen = new Set<string>();
  return nodes.filter(node => {
    if (seen.has(node.id)) return false;
    seen.add(node.id);
    return true;
  });
};

// ============================================================================
// Main Editor Component
// ============================================================================

export const MindMapEditor: React.FC<MindMapEditorProps> = ({
  initialData,
  title,
  onClose,
  onOpenSourceRef,
}) => {
  // State
  // Initialize with deduplicated nodes to prevent unique key errors
  const {
    state: data,
    set: setData,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useHistory<MindmapData>(
    {
      ...initialData,
      nodes: deduplicateNodes(initialData.nodes)
    }
  );

  // Sync with external data updates (e.g. streaming) and deduplicate
  // Use ref to track previous initialData to avoid unnecessary updates
  const prevInitialDataRef = useRef(initialData);
  useEffect(() => {
    // Deep comparison: check if nodes actually changed
    const prevNodes = prevInitialDataRef.current.nodes;
    const currentNodes = initialData.nodes;
    
    // Quick check: if lengths are the same and all node IDs match, skip update
    if (prevNodes.length === currentNodes.length) {
      const prevNodeIds = new Set(prevNodes.map(n => n.id));
      const currentNodeIds = new Set(currentNodes.map(n => n.id));
      const idsMatch = prevNodeIds.size === currentNodeIds.size && 
        Array.from(prevNodeIds).every(id => currentNodeIds.has(id));
      
      if (idsMatch) {
        // Check if any node content actually changed
        const hasChanges = currentNodes.some(newNode => {
          const oldNode = prevNodes.find(n => n.id === newNode.id);
          if (!oldNode) return true;
          return oldNode.label !== newNode.label || 
                 oldNode.content !== newNode.content ||
                 oldNode.status !== newNode.status;
        });
        
        if (!hasChanges) {
          prevInitialDataRef.current = initialData;
          return; // No changes, skip update
        }
      }
    }

    setData((prev) => {
      const existingNodesMap = new Map(prev.nodes.map(n => [n.id, n]));
      const uniqueNewNodes = deduplicateNodes(initialData.nodes);

      const mergedNodes = uniqueNewNodes.map(newNode => {
        const existingNode = existingNodesMap.get(newNode.id);
        if (existingNode) {
          // Preserve existing position and collapsed state
          return {
            ...newNode,
            x: existingNode.x,
            y: existingNode.y,
            collapsed: existingNode.collapsed,
          };
        }
        return newNode;
      });

      prevInitialDataRef.current = initialData;
      return {
        ...initialData,
        nodes: mergedNodes
      };
    });
  }, [initialData, setData]);

  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());
  // Helper for single selection compatibility if needed
  const selectedNodeId = selectedNodeIds.size === 1 ? Array.from(selectedNodeIds)[0] : null;
  const [layoutType, setLayoutType] = useState<LayoutType>('balanced');
  const [viewport, setViewport] = useState<ViewportState>({ x: 0, y: 0, scale: 1 });
  const [isDragging, setIsDragging] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [isCalculatingLayout, setIsCalculatingLayout] = useState(true);


  // Dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState<'add' | 'edit'>('add');
  const [editingNode, setEditingNode] = useState<MindmapNode | null>(null);
  const [pendingParentId, setPendingParentId] = useState<string | null>(null);
  
  // Drilldown state for source context panel
  const [drilldownNodeId, setDrilldownNodeId] = useState<string | null>(null);
  const [showSourcePanel, setShowSourcePanel] = useState(false);

  // Refs
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 1200, height: 800 });
  const [debouncedContainerSize, setDebouncedContainerSize] = useState({ width: 1200, height: 800 });
  const initialLayoutDone = useRef(false);

  // Get LOD level based on scale
  const lodLevel = useMemo(() => {
    if (viewport.scale < LOD_THRESHOLDS.SIMPLE_SHAPES) return 'simple';
    if (viewport.scale < LOD_THRESHOLDS.LABELS_ONLY) return 'labels';
    return 'full';
  }, [viewport.scale]);

  // Determine if animations should be enabled (disabled for large datasets)
  const shouldAnimate = useMemo(() => {
    return data.nodes.length < ANIMATION_THRESHOLD;
  }, [data.nodes.length]);

  // Resize observer
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      const width = Math.max(1, entries[0].contentRect.width);
      const height = Math.max(1, entries[0].contentRect.height);
      setContainerSize({ width, height });
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Debounce container size changes to prevent multiple layout recalculations
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedContainerSize(containerSize);
    }, RESIZE_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [containerSize]);

  // Apply layout when container resizes or data changes (e.g. new nodes from streaming)
  useEffect(() => {
    // Check if we need layout (unpositioned nodes or explicit layout request)
    // We strictly check for nodes that don't have x/y coordinates
    const needsLayout = data.nodes.some(n => typeof n.x !== 'number' || typeof n.y !== 'number');

    // If all nodes are positioned and we've done initial layout, skip
    // Unless this is a resize event (handled by dependency change)
    if (!needsLayout && initialLayoutDone.current) {
      // Use setTimeout to avoid synchronous state update warning during render
      setTimeout(() => setIsCalculatingLayout(false), 0);
      return;
    }

    // Defer layout calculation to not block UI
    setTimeout(() => {
        setIsCalculatingLayout(true);
        const timeoutId = setTimeout(() => {
        const result = applyLayout(
            data,
            layoutType,
            debouncedContainerSize.width || 1200,
            debouncedContainerSize.height || 800
        );

        setData(prev => ({ ...prev, nodes: result.nodes }));
        initialLayoutDone.current = true;
        setIsCalculatingLayout(false);
        }, 0);
        return () => clearTimeout(timeoutId);
    }, 0);
  }, [debouncedContainerSize.width, debouncedContainerSize.height, data.nodes.length, layoutType, data, setData]);

  // Node position update
  const handleNodeDragEnd = useCallback(
    (nodeId: string, x: number, y: number) => {
      setData((prev) => {
        const oldNode = prev.nodes.find((n) => n.id === nodeId);
        // If node not found or position didn't effectively change (optimization), return prev
        if (!oldNode) return prev;

        // Bulk Move Logic
        if (selectedNodeIds.has(nodeId) && selectedNodeIds.size > 1) {
          const dx = x - oldNode.x;
          const dy = y - oldNode.y;

          if (Math.abs(dx) < 1 && Math.abs(dy) < 1) return prev;

          const newNodes = prev.nodes.map((n) => {
            if (selectedNodeIds.has(n.id)) {
              return { ...n, x: n.x + dx, y: n.y + dy };
            }
            return n;
          });

          return { ...prev, nodes: newNodes };
        }

        // Single Move Logic
        const nodesWithMove = prev.nodes.map((n) =>
          n.id === nodeId ? { ...n, x, y } : n
        );

        // Resolve overlaps
        const resolvedNodes = resolveOverlaps(nodesWithMove, nodeId);

        return {
          ...prev,
          nodes: resolvedNodes,
        };
      });
      setHasChanges(true);
    },
    [setData, selectedNodeIds]
  );


  // Zoom handlers
  const handleZoomIn = useCallback(() => {
    setViewport((v) => ({
      ...v,
      scale: Math.min(v.scale + SCALE_STEP, MAX_SCALE),
    }));
  }, []);

  const handleZoomOut = useCallback(() => {
    setViewport((v) => ({
      ...v,
      scale: Math.max(v.scale - SCALE_STEP, MIN_SCALE),
    }));
  }, []);

  const handleResetView = useCallback(() => {
    setViewport({ x: 0, y: 0, scale: 1 });
  }, []);

  // Wheel zoom
  const handleWheel = useCallback((e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;

    const oldScale = viewport.scale;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;

    const mousePointTo = {
      x: (pointer.x - viewport.x) / oldScale,
      y: (pointer.y - viewport.y) / oldScale,
    };

    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const newScale = Math.max(
      MIN_SCALE,
      Math.min(MAX_SCALE, oldScale + direction * SCALE_STEP * 0.5)
    );

    setViewport({
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y - mousePointTo.y * newScale,
      scale: newScale,
    });
  }, [viewport]);

  // Pan handlers
  const handleDragStart = useCallback(() => setIsDragging(true), []);
  const handleDragEnd = useCallback((e: Konva.KonvaEventObject<DragEvent>) => {
    setIsDragging(false);
    // Only update viewport if the stage itself was dragged
    if (e.target === stageRef.current) {
      setViewport((v) => ({
        ...v,
        x: e.target.x(),
        y: e.target.y(),
      }));
    }
  }, []);

  // Layout change - async to not block UI
  const handleLayoutChange = useCallback((newLayout: LayoutType) => {
    setLayoutType(newLayout);
    setIsCalculatingLayout(true);

    // Defer layout calculation
    setTimeout(() => {
      const result = applyLayout(data, newLayout, debouncedContainerSize.width, debouncedContainerSize.height);
      setData(prev => ({ ...prev, nodes: result.nodes }));
      setHasChanges(true);
      setIsCalculatingLayout(false);
    }, 0);
  }, [data, debouncedContainerSize, setData]);

  // Node selection
  const handleNodeSelect = useCallback((nodeId: string, e?: Konva.KonvaEventObject<MouseEvent>) => {
    const isMultiSelect = e?.evt.shiftKey || e?.evt.metaKey || e?.evt.ctrlKey;

    setSelectedNodeIds(prev => {
      // If clicking inside a set without modifiers, keeping it selected
      // But if we have multiple and click one without modifier, we select just that one
      if (isMultiSelect) {
        const newSet = new Set(prev);
        if (newSet.has(nodeId)) {
          newSet.delete(nodeId);
        } else {
          newSet.add(nodeId);
        }
        return newSet;
      } else {
        // Single select
        return new Set([nodeId]);
      }
    });
  }, []);

  // Node double-click (edit)
  const handleNodeDoubleClick = useCallback((nodeId: string) => {
    const node = data.nodes.find((n) => n.id === nodeId);
    if (node) {
      setEditingNode(node);
      setEditMode('edit');
      setEditDialogOpen(true);
    }
  }, [data.nodes]);

  // Node drilldown (show source context panel)
  const handleNodeDrilldown = useCallback((nodeId: string) => {
    const node = data.nodes.find((n) => n.id === nodeId);
    if (node && node.sourceRefs && node.sourceRefs.length > 0) {
      setDrilldownNodeId(nodeId);
      setShowSourcePanel(true);
    }
  }, [data.nodes]);

  // Close source panel
  const handleCloseSourcePanel = useCallback(() => {
    setShowSourcePanel(false);
    setDrilldownNodeId(null);
  }, []);
  
  // Get the node being drilled down into
  const drilldownNode = useMemo(
    () => data.nodes.find((n) => n.id === drilldownNodeId),
    [data.nodes, drilldownNodeId]
  );

  // Add node (child)
  const handleAddNode = useCallback(() => {
    if (!selectedNodeId) return;
    setPendingParentId(selectedNodeId);
    setEditingNode(null);
    setEditMode('add');
    setEditDialogOpen(true);
  }, [selectedNodeId]);

  // Add sibling
  const handleAddSibling = useCallback(() => {
    if (!selectedNodeId) return;
    const node = data.nodes.find(n => n.id === selectedNodeId);
    if (node && node.parentId) {
      setPendingParentId(node.parentId);
      setEditingNode(null);
      setEditMode('add');
      setEditDialogOpen(true);
    }
  }, [selectedNodeId, data.nodes]);

  // Delete node
  const handleDeleteNode = useCallback(() => {
    if (selectedNodeIds.size === 0) return;

    // Find all descendants to delete
    const toDelete = new Set<string>();
    const findDescendants = (nodeId: string) => {
      toDelete.add(nodeId);
      data.nodes
        .filter((n) => n.parentId === nodeId)
        .forEach((child) => findDescendants(child.id));
    };

    selectedNodeIds.forEach(id => {
      findDescendants(id);
    });

    setData({
      nodes: data.nodes.filter((n) => !toDelete.has(n.id)),
      edges: data.edges.filter(
        (e) => !toDelete.has(e.source) && !toDelete.has(e.target)
      ),
      rootId: data.rootId,
    });
    setSelectedNodeIds(new Set());
    setHasChanges(true);
  }, [selectedNodeIds, data, setData]);

  // Edit node
  const handleEditNode = useCallback(() => {
    if (!selectedNodeId) return;
    const node = data.nodes.find((n) => n.id === selectedNodeId);
    if (node) {
      setEditingNode(node);
      setEditMode('edit');
      setEditDialogOpen(true);
    }
  }, [selectedNodeId, data.nodes]);

  // Save node from dialog
  const handleSaveNode = useCallback(
    (label: string, content: string) => {
      if (editMode === 'add' && pendingParentId) {
        // Create new node
        const parentNode = data.nodes.find((n) => n.id === pendingParentId);
        if (!parentNode) return;

        const newId = `node-${Date.now()}`;
        const newNode: MindmapNode = {
          id: newId,
          label,
          content,
          depth: parentNode.depth + 1,
          parentId: pendingParentId,
          x: parentNode.x + 250,
          y: parentNode.y,
          width: 200,
          height: 80,
          color: parentNode.color,
          status: 'complete',
        };

        const newEdge: MindmapEdge = {
          id: `edge-${Date.now()}`,
          source: pendingParentId,
          target: newId,
        };

        setData({
          ...data,
          nodes: [...data.nodes, newNode],
          edges: [...data.edges, newEdge],
        });
      } else if (editMode === 'edit' && editingNode) {
        // Update existing node
        setData({
          ...data,
          nodes: data.nodes.map((n) =>
            n.id === editingNode.id ? { ...n, label, content } : n
          ),
        });
      }
      setHasChanges(true);
      setEditDialogOpen(false);
      setPendingParentId(null);
    },
    [editMode, pendingParentId, editingNode, data, setData]
  );

  // Export
  const handleExport = useCallback(
    (format: 'png' | 'json') => {
      if (format === 'png') {
        const stage = stageRef.current;
        if (!stage) return;

        // Temporarily reset viewport for clean export
        const oldPosition = { x: stage.x(), y: stage.y() };
        const oldScale = stage.scaleX();
        stage.position({ x: 0, y: 0 });
        stage.scale({ x: 1, y: 1 });

        const dataUrl = stage.toDataURL({ pixelRatio: 2 });

        // Restore viewport
        stage.position(oldPosition);
        stage.scale({ x: oldScale, y: oldScale });

        const link = document.createElement('a');
        link.download = `${title.replace(/\s+/g, '_')}_mindmap.png`;
        link.href = dataUrl;
        link.click();
      } else {
        const jsonData = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.download = `${title.replace(/\s+/g, '_')}_mindmap.json`;
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
      }
    },
    [data, title]
  );

  // Click on empty canvas to deselect
  const handleStageClick = useCallback((e: Konva.KonvaEventObject<MouseEvent>) => {
    if (e.target === e.currentTarget || e.target.getClassName() === 'Rect') {
      const clickedOnBackground = e.target.attrs?.name === 'background';
      if (clickedOnBackground || e.target === stageRef.current) {
        setSelectedNodeIds(new Set());
      }
    }
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if dialog is open or typing in an input
      if (editDialogOpen) return;
      if (
        document.activeElement instanceof HTMLInputElement ||
        document.activeElement instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Undo/Redo
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          if (canRedo) redo();
        } else {
          if (canUndo) undo();
        }
        return;
      }

      // Delete
      if (e.key === 'Backspace' || e.key === 'Delete') {
        if (selectedNodeIds.size > 0) {
          e.preventDefault();
          handleDeleteNode();
        }
        return;
      }

      // Add Child (Tab)
      if (e.key === 'Tab') {
        e.preventDefault();
        if (selectedNodeIds.size === 1) {
          handleAddNode();
        }
        return;
      }

      // Add Sibling (Enter)
      if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedNodeIds.size === 1) {
          handleAddSibling();
        }
        return;
      }

      // Navigation (Arrows) - Placeholder
      // Implementing spatial navigation is complex. 
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    editDialogOpen,
    canUndo,
    canRedo,
    undo,
    redo,
    selectedNodeIds,
    handleDeleteNode,
    handleAddNode,
    handleAddSibling,
    data.nodes,
    handleNodeDoubleClick
  ]);

  // Calculate which nodes have children and build node map for efficient lookup
  const { nodesWithChildren, nodeMap } = useMemo(() => {
    const childrenMap = new Map<string, boolean>();
    const map = new Map<string, MindmapNode>();
    
    data.nodes.forEach(node => {
      map.set(node.id, node);
      if (node.parentId) {
        childrenMap.set(node.parentId, true);
      }
    });
    
    return { nodesWithChildren: childrenMap, nodeMap: map };
  }, [data.nodes]);

  // Filter visible nodes and edges - optimized with node map
  const { visibleNodes, visibleNodeIds } = useMemo(() => {
    const visible = new Set<string>();
    const visibleList: MindmapNode[] = [];
    const checked = new Set<string>(); // Track nodes we've already checked
    
    // Helper to check if a node is visible (all ancestors must not be collapsed)
    const checkVisibility = (nodeId: string): boolean => {
      // If already checked, return cached result
      if (checked.has(nodeId)) {
        return visible.has(nodeId);
      }
      
      checked.add(nodeId);
      
      const node = nodeMap.get(nodeId);
      if (!node) {
        return false;
      }
      
      // Root nodes (no parent) are always visible
      if (!node.parentId) {
        visible.add(nodeId);
        return true;
      }
      
      // Check if parent is collapsed first (faster check)
      const parent = nodeMap.get(node.parentId);
      if (parent?.collapsed) {
        return false; // Parent is collapsed, so this node is hidden
      }
      
      // Recursively check if parent is visible
      const parentVisible = checkVisibility(node.parentId);
      if (!parentVisible) {
        return false; // Parent is not visible
      }
      
      // Node is visible
      visible.add(nodeId);
      return true;
    };
    
    // Check all nodes
    data.nodes.forEach(node => {
      if (checkVisibility(node.id)) {
        visibleList.push(node);
      }
    });
    
    return { visibleNodes: visibleList, visibleNodeIds: visible };
  }, [data.nodes, nodeMap]);

  const visibleEdges = useMemo(() => {
    return data.edges.filter(edge => 
      visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
    );
  }, [data.edges, visibleNodeIds]);

  // Handle toggle collapse
  const handleToggleCollapse = useCallback((nodeId: string) => {
    setData({
      ...data,
      nodes: data.nodes.map(n => 
        n.id === nodeId ? { ...n, collapsed: !(n.collapsed ?? false) } : n
      ),
    });
    setHasChanges(true);
  }, [data, setData]);

  // Prevent unused variable warning for isDragging if not used yet
  // But we use setIsDragging
  // We can just omit isDragging from the destructuring if we don't use it, or use it for cursor style
  const cursorStyle = isDragging ? 'grabbing' : 'grab';

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: colors.background.default,
        zIndex: 1300,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Surface
        elevation={0}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 16,
          borderBottom: `1px solid ${colors.border.default}`,
          backgroundColor: colors.background.paper,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Text variant="h6" fontWeight={600}>
            {title}
          </Text>
          {hasChanges && (
            <Chip label="Unsaved changes" size="sm" style={{ backgroundColor: colors.warning[50], color: colors.warning[700], borderColor: colors.warning[200] }} variant="outlined" />
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tooltip title="Drag to pan, scroll to zoom">
            <Chip
              icon={<OpenWithIcon size={14} />}
              label="Pan & Zoom"
              size="sm"
              variant="outlined"
            />
          </Tooltip>
          <IconButton onClick={onClose} size="sm">
            <CloseIcon size="md" />
          </IconButton>
        </div>
      </Surface>

      {/* Toolbar */}
      <Toolbar
        layoutType={layoutType}
        onLayoutChange={handleLayoutChange}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onResetView={handleResetView}
        onAddNode={handleAddNode}
        onDeleteNode={handleDeleteNode}
        onEditNode={handleEditNode}
        onExport={handleExport}
        hasSelection={!!selectedNodeId}
        nodeCount={data.nodes.length}
        scale={viewport.scale}
      />

      {/* Canvas */}
      <div
        ref={containerRef}
        style={{
          flexGrow: 1,
          backgroundColor: '#F8FAFC',
          overflow: 'hidden',
          position: 'relative',
          cursor: cursorStyle, // Use isDragging state
        }}
      >
        <Stage
          ref={stageRef}
          width={containerSize.width}
          height={containerSize.height}
          x={viewport.x}
          y={viewport.y}
          scaleX={viewport.scale}
          scaleY={viewport.scale}
          draggable
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onWheel={handleWheel}
          onClick={handleStageClick}
        >
          <Layer>
            {/* Background */}
            <Rect
              name="background"
              x={-5000}
              y={-5000}
              width={10000}
              height={10000}
              fill="#F8FAFC"
            />

            {/* Grid pattern - only render after layout is complete and when zoomed in enough */}
            {!isCalculatingLayout && viewport.scale >= 0.5 && (
              <>
                {Array.from({ length: 50 }).map((_, i) => (
                  <React.Fragment key={`grid-${i}`}>
                    <Rect
                      x={-2500 + i * 100}
                      y={-2500}
                      width={1}
                      height={5000}
                      fill="#E2E8F0"
                      opacity={0.3}
                    />
                    <Rect
                      x={-2500}
                      y={-2500 + i * 100}
                      width={5000}
                      height={1}
                      fill="#E2E8F0"
                      opacity={0.3}
                    />
                  </React.Fragment>
                ))}
              </>
            )}

            {/* Edges - only render after layout is complete */}
            {!isCalculatingLayout && visibleEdges.map((edge) => {
              const source = visibleNodes.find((n) => n.id === edge.source);
              const target = visibleNodes.find((n) => n.id === edge.target);
              if (!source || !target) return null;
              return (
                <CurvedMindMapEdge
                  key={edge.id}
                  edge={edge}
                  sourceNode={source}
                  targetNode={target}
                  showAnchors={viewport.scale >= 0.5}
                  shouldAnimate={shouldAnimate}
                />
              );
            })}

            {/* Nodes - only render after layout is complete */}
            {!isCalculatingLayout && visibleNodes.map((node) => (
              <RichMindMapNode
                key={node.id}
                node={node}
                isSelected={selectedNodeIds.has(node.id)}
                lodLevel={lodLevel}
                shouldAnimate={shouldAnimate}
                onClick={handleNodeSelect}
                onDoubleClick={handleNodeDoubleClick}
                onDragEnd={handleNodeDragEnd}
                onDrilldown={handleNodeDrilldown}
                hasChildren={nodesWithChildren.has(node.id)}
                onToggleCollapse={handleToggleCollapse}
              />
            ))}
          </Layer>
        </Stage>

        {/* Loading Overlay */}
        {isCalculatingLayout && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'rgba(248, 250, 252, 0.95)',
              backdropFilter: 'blur(4px)',
              zIndex: 10,
              gap: 16,
            }}
          >
            <Spinner size="lg" style={{ color: '#3B82F6' }} />
            <Text variant="body" color="secondary" fontWeight={500}>
              Calculating layout for {data.nodes.length} nodes...
            </Text>
            <Text variant="caption" color="disabled">
              This may take a moment for large mindmaps
            </Text>
          </div>
        )}


        {/* Help text */}
        {!isCalculatingLayout && (
          <div
            style={{
              position: 'absolute',
              bottom: 16,
              left: 16,
              backgroundColor: 'rgba(255,255,255,0.9)',
              backdropFilter: 'blur(4px)',
              paddingLeft: 16,
              paddingRight: 16,
              paddingTop: 8,
              paddingBottom: 8,
              borderRadius: 8,
              boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
            }}
          >
            <Text variant="caption" color="secondary">
              Drag canvas to pan • Scroll to zoom • Click node to select • Double-click to edit
            </Text>
          </div>
        )}

        {/* Source Context Panel for drilldown */}
        {drilldownNode && (
          <SourceContextPanel
            node={drilldownNode}
            isOpen={showSourcePanel}
            onClose={handleCloseSourcePanel}
            onOpenSource={onOpenSourceRef}
          />
        )}
      </div>

      {/* Edit Dialog */}
      <NodeEditDialog
        open={editDialogOpen}
        mode={editMode}
        initialLabel={editingNode?.label}
        initialContent={editingNode?.content}
        onClose={() => {
          setEditDialogOpen(false);
          setPendingParentId(null);
        }}
        onSave={handleSaveNode}
      />
    </div>
  );
};

export default MindMapEditor;
