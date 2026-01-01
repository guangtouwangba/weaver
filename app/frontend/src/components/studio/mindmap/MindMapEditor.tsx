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
  Box,
  Typography,
  IconButton,
  ButtonGroup,
  Button,
  Tooltip,
  Menu,
  MenuItem,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Divider,
  CircularProgress,
} from '@mui/material';
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
// Utility Hooks
// ============================================================================

function useThrottledCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const lastRun = useRef(Date.now());
  const rafId = useRef<number | null>(null);

  return useCallback(
    ((...args) => {
      const now = Date.now();
      if (now - lastRun.current >= delay) {
        lastRun.current = now;
        callback(...args);
      } else if (!rafId.current) {
        rafId.current = requestAnimationFrame(() => {
          rafId.current = null;
          lastRun.current = Date.now();
          callback(...args);
        });
      }
    }) as T,
    [callback, delay]
  );
}

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
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        p: 1.5,
        borderBottom: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
        flexWrap: 'wrap',
      }}
    >
      {/* Layout Selection */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
          Layout:
        </Typography>
        <ButtonGroup size="small" variant="outlined">
          {layoutOptions.map((opt) => (
            <Tooltip key={opt.value} title={opt.label}>
              <Button
                onClick={() => onLayoutChange(opt.value)}
                variant={layoutType === opt.value ? 'contained' : 'outlined'}
                sx={{ minWidth: 40 }}
              >
                {opt.icon}
              </Button>
            </Tooltip>
          ))}
        </ButtonGroup>
      </Box>

      <Divider orientation="vertical" flexItem />

      {/* Zoom Controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Tooltip title="Zoom Out">
          <IconButton size="small" onClick={onZoomOut}>
            <ZoomOutIcon size={18} />
          </IconButton>
        </Tooltip>
        <Chip
          label={`${Math.round(scale * 100)}%`}
          size="small"
          variant="outlined"
          sx={{ minWidth: 60 }}
        />
        <Tooltip title="Zoom In">
          <IconButton size="small" onClick={onZoomIn}>
            <ZoomInIcon size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Reset View">
          <IconButton size="small" onClick={onResetView}>
            <RefreshIcon size={18} />
          </IconButton>
        </Tooltip>
      </Box>

      <Divider orientation="vertical" flexItem />

      {/* Node Editing */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Tooltip title="Add Node">
          <IconButton size="small" onClick={onAddNode} disabled={!hasSelection}>
            <AddIcon size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Edit Node">
          <IconButton size="small" onClick={onEditNode} disabled={!hasSelection}>
            <EditIcon size={18} />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete Node">
          <IconButton size="small" onClick={onDeleteNode} disabled={!hasSelection}>
            <DeleteIcon size={18} />
          </IconButton>
        </Tooltip>
      </Box>

      <Divider orientation="vertical" flexItem />

      {/* Export */}
      <Tooltip title="Download">
        <IconButton size="small" onClick={(e) => setExportAnchor(e.currentTarget)}>
          <DownloadIcon size={18} />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={exportAnchor}
        open={Boolean(exportAnchor)}
        onClose={() => setExportAnchor(null)}
      >
        <MenuItem onClick={() => { onExport('png'); setExportAnchor(null); }}>
          Export as PNG
        </MenuItem>
        <MenuItem onClick={() => { onExport('json'); setExportAnchor(null); }}>
          Export as JSON
        </MenuItem>
      </Menu>

      {/* Spacer */}
      <Box sx={{ flexGrow: 1 }} />

      {/* Node Count & Warning */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {nodeCount >= PERFORMANCE_WARNING_THRESHOLD && (
          <Tooltip title="Large mindmap may affect performance">
            <Chip
              icon={<WarningIcon size={14} />}
              label={`${nodeCount} nodes`}
              size="small"
              color="warning"
              variant="outlined"
            />
          </Tooltip>
        )}
        {nodeCount < PERFORMANCE_WARNING_THRESHOLD && (
          <Typography variant="caption" color="text.secondary">
            {nodeCount} nodes
          </Typography>
        )}
      </Box>
    </Box>
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

  useEffect(() => {
    setLabel(initialLabel);
    setContent(initialContent);
  }, [initialLabel, initialContent, open]);

  const handleSave = () => {
    if (label.trim()) {
      onSave(label.trim(), content.trim());
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{mode === 'add' ? 'Add New Node' : 'Edit Node'}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="Label"
          fullWidth
          variant="outlined"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          sx={{ mb: 2 }}
        />
        <TextField
          margin="dense"
          label="Content (optional)"
          fullWidth
          variant="outlined"
          multiline
          rows={3}
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained" disabled={!label.trim()}>
          {mode === 'add' ? 'Add' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
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
  onSave,
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
    reset: resetData
  } = useHistory<MindmapData>(
    {
      ...initialData,
      nodes: deduplicateNodes(initialData.nodes)
    }
  );

  // Sync with external data updates (e.g. streaming) and deduplicate
  useEffect(() => {
    setData((prev) => {
      // Quick check if data actually changed (by length) to avoid unnecessary updates
      if (prev.nodes.length === initialData.nodes.length) {
        return prev;
      }

      const existingNodesMap = new Map(prev.nodes.map(n => [n.id, n]));
      const uniqueNewNodes = deduplicateNodes(initialData.nodes);

      const mergedNodes = uniqueNewNodes.map(newNode => {
        const existingNode = existingNodesMap.get(newNode.id);
        if (existingNode) {
          // Preserve existing position
          return {
            ...newNode,
            x: existingNode.x,
            y: existingNode.y,
          };
        }
        return newNode;
      });

      return {
        ...initialData,
        nodes: mergedNodes
      };
    });
  }, [initialData, setData]); // Added setData to deps

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
      const { width, height } = entries[0].contentRect;
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
      setIsCalculatingLayout(false);
      return;
    }

    // Defer layout calculation to not block UI
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
  }, [debouncedContainerSize.width, debouncedContainerSize.height, data.nodes.length, layoutType]);

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
  }, [data, debouncedContainerSize]);

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

  // Add node
  const handleAddNode = useCallback(() => {
    if (!selectedNodeId) return;
    setEditingNode(null);
    setEditMode('add');
    setEditDialogOpen(true);
  }, [selectedNodeId]);

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
      if (editMode === 'add' && selectedNodeId) {
        // Create new node
        const parentNode = data.nodes.find((n) => n.id === selectedNodeId);
        if (!parentNode) return;

        const newId = `node-${Date.now()}`;
        const newNode: MindmapNode = {
          id: newId,
          label,
          content,
          depth: parentNode.depth + 1,
          parentId: selectedNodeId,
          x: parentNode.x + 250,
          y: parentNode.y,
          width: 200,
          height: 80,
          color: parentNode.color,
          status: 'complete',
        };

        const newEdge: MindmapEdge = {
          id: `edge-${Date.now()}`,
          source: selectedNodeId,
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
    },
    [editMode, selectedNodeId, editingNode, data]
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
          const id = Array.from(selectedNodeIds)[0];
          const node = data.nodes.find(n => n.id === id);
          if (node && node.parentId) { // Can't add sibling to root
            // We reuse handleAddNode logic but hacked:
            // handleAddNode adds to *selectedNodeId*.
            // For sibling, we want to add to *node.parentId*.
            // So we would need to selects Parent -> Add -> Select new.
            // But switching selection is jarring.
            // Better: Invoke a new handleAddSibling? 
            // For MVP, letting Enter do nothing or just focus edit?
            // Users expect Enter to add sibling.
            // I'll leave Enter empty or implement specific logic later.
            // Let's implement basic Add Sibling logic here if simple.
            // It requires opening dialog. Dialog uses `selectedNodeId` as parent.
            // So I can't reuse `handleAddNode` easily without state dance.
            // I'll skip Enter for now or just map it to Edit?
            // XMind: Space is Edit.
            handleNodeDoubleClick(id); // Enter to Edit is also common alternative configuration.
          }
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
    data.nodes,
    handleNodeDoubleClick
  ]);

  const selectedNode = useMemo(
    () => data.nodes.find((n) => n.id === selectedNodeId),
    [data.nodes, selectedNodeId]
  );

  return (
    <Box
      sx={{
        position: 'fixed',
        inset: 0,
        bgcolor: 'background.default',
        zIndex: 1300,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" fontWeight={600}>
            {title}
          </Typography>
          {hasChanges && (
            <Chip label="Unsaved changes" size="small" color="warning" variant="outlined" />
          )}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Drag to pan, scroll to zoom">
            <Chip
              icon={<OpenWithIcon size={14} />}
              label="Pan & Zoom"
              size="small"
              variant="outlined"
            />
          </Tooltip>
          <IconButton onClick={onClose}>
            <CloseIcon size="md" />
          </IconButton>
        </Box>
      </Box>

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
      <Box
        ref={containerRef}
        sx={{
          flexGrow: 1,
          bgcolor: '#F8FAFC',
          overflow: 'hidden',
          position: 'relative',
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
            {!isCalculatingLayout && data.edges.map((edge) => {
              const source = data.nodes.find((n) => n.id === edge.source);
              const target = data.nodes.find((n) => n.id === edge.target);
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
            {!isCalculatingLayout && data.nodes.map((node) => (
              <RichMindMapNode
                key={node.id}
                node={node}
                isSelected={selectedNodeIds.has(node.id)}
                lodLevel={lodLevel}
                shouldAnimate={shouldAnimate}
                onClick={handleNodeSelect}
                onDoubleClick={handleNodeDoubleClick}
                onDragEnd={handleNodeDragEnd}
              />
            ))}
          </Layer>
        </Stage>

        {/* Loading Overlay */}
        {isCalculatingLayout && (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: 'rgba(248, 250, 252, 0.95)',
              backdropFilter: 'blur(4px)',
              zIndex: 10,
              gap: 2,
            }}
          >
            <CircularProgress size={48} sx={{ color: '#3B82F6' }} />
            <Typography variant="body1" color="text.secondary" fontWeight={500}>
              Calculating layout for {data.nodes.length} nodes...
            </Typography>
            <Typography variant="caption" color="text.disabled">
              This may take a moment for large mindmaps
            </Typography>
          </Box>
        )}

        {/* Help text */}
        {!isCalculatingLayout && (
          <Box
            sx={{
              position: 'absolute',
              bottom: 16,
              left: 16,
              bgcolor: 'rgba(255,255,255,0.9)',
              backdropFilter: 'blur(4px)',
              px: 2,
              py: 1,
              borderRadius: 2,
              boxShadow: 1,
            }}
          >
            <Typography variant="caption" color="text.secondary">
              Drag canvas to pan • Scroll to zoom • Click node to select • Double-click to edit
            </Typography>
          </Box>
        )}
      </Box>

      {/* Edit Dialog */}
      <NodeEditDialog
        open={editDialogOpen}
        mode={editMode}
        initialLabel={editingNode?.label}
        initialContent={editingNode?.content}
        onClose={() => setEditDialogOpen(false)}
        onSave={handleSaveNode}
      />
    </Box>
  );
};

export default MindMapEditor;

