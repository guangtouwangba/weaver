'use client';

import { useState, useRef, useEffect, useCallback } from "react";
import GlobalLayout from "@/components/layout/GlobalLayout";
import { 
  Box, 
  Typography, 
  Paper, 
  IconButton, 
  Button,
  TextField,
  Chip,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import { 
  FileText, 
  Maximize2, 
  Minimize2,
  Link as LinkIcon, 
  Layout, 
  Plus, 
  Bot,
  FolderOpen,
  ChevronDown,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  LayoutGrid,
  List as ListIcon,
  Upload,
  Send
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
      '&:hover': { bgcolor: 'primary.main' },
      '&:active': { bgcolor: 'primary.main' }
    }}
  />
);

// --- Mock Data (PDF Only) ---

interface Resource {
  id: string;
  title: string;
  date: string;
  pages?: number;
}

const SAMPLE_RESOURCES: Resource[] = [
  { id: '1', title: 'Attention Is All You Need.pdf', date: '10:42 AM', pages: 15 },
  { id: '2', title: 'BERT_Pre-training.pdf', date: '2d ago', pages: 24 },
  { id: '3', title: 'GPT-3_Language_Models.pdf', date: '1w ago', pages: 75 },
];

// --- Canvas Node Type ---
interface CanvasNode {
  id: string;
  type: 'card' | 'group';
  title: string;
  content?: string;
  x: number;
  y: number;
  color?: string;
  tags?: string[];
  sourceId?: string;
  connections?: string[];
}

export default function StudioPage() {
  // --- Layout State ---
  const [leftVisible, setLeftVisible] = useState(true);
  const [centerVisible, setCenterVisible] = useState(true);
  const [leftWidth, setLeftWidth] = useState(380);
  const [centerWidth, setCenterWidth] = useState(380); 
  const [resizingCol, setResizingCol] = useState<'left' | 'center' | null>(null);

  // --- Feature State ---
  const [isReaderExpanded, setIsReaderExpanded] = useState(false);
  const [splitRatio, setSplitRatio] = useState(0.4); 
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid');
  const [activeResource, setActiveResource] = useState<Resource>(SAMPLE_RESOURCES[0]);

  // --- Canvas State ---
  const [canvasNodes, setCanvasNodes] = useState<CanvasNode[]>([
    { id: 'c1', type: 'card', title: 'SOURCE PDF', content: 'Attention Is All You Need', x: 100, y: 200, color: 'white', connections: ['c2'] },
    { id: 'c2', type: 'card', title: 'Self-Attention', content: 'The core mechanism that allows the model to weigh the importance of different words in a sequence.', x: 500, y: 150, color: 'blue', tags: ['#transformer', '#nlp'] }
  ]);

  // --- Infinite Canvas State ---
  const [viewport, setViewport] = useState({ x: 0, y: 0, scale: 1 });
  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [connectingNodeId, setConnectingNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null);
  const [tempLineEnd, setTempLineEnd] = useState<{ x: number, y: number } | null>(null);
  
  const lastMousePos = useRef({ x: 0, y: 0 });
  const mousePos = useRef({ x: 0, y: 0 });
  const dragStartPos = useRef<{ x: number, y: number } | null>(null);
  const viewportRef = useRef(viewport);
  const selectedNodeIdRef = useRef(selectedNodeId);
  const selectedConnectionIdRef = useRef(selectedConnectionId);
  const canvasRef = useRef<HTMLDivElement>(null);
  const leftColumnRef = useRef<HTMLDivElement>(null);

  // --- Interaction State ---
  const [contextMenu, setContextMenu] = useState<{ mouseX: number; mouseY: number } | null>(null);
  const [isDraggingFromPdf, setIsDraggingFromPdf] = useState(false);
  const [isVerticalDragging, setIsVerticalDragging] = useState(false);
  const [chatInput, setChatInput] = useState('');

  // Keep refs in sync
  useEffect(() => { viewportRef.current = viewport; }, [viewport]);
  useEffect(() => { selectedNodeIdRef.current = selectedNodeId; }, [selectedNodeId]);
  useEffect(() => { selectedConnectionIdRef.current = selectedConnectionId; }, [selectedConnectionId]);

  // --- Keyboard Shortcuts ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
      
      if (e.code === 'Space' && !e.repeat && !isInput) {
        e.preventDefault(); 
        setIsSpacePressed(true);
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
      if ((e.key === 'Delete' || e.key === 'Backspace') && !isInput) {
        e.preventDefault();
        if (selectedConnectionIdRef.current) {
          const lastDash = selectedConnectionIdRef.current.lastIndexOf('-');
          const sourceId = selectedConnectionIdRef.current.substring(0, lastDash);
          const targetId = selectedConnectionIdRef.current.substring(lastDash + 1);
          setCanvasNodes(prev => prev.map(node => 
            node.id === sourceId && node.connections 
              ? { ...node, connections: node.connections.filter(id => id !== targetId) }
              : node
          ));
          setSelectedConnectionId(null);
        } else if (selectedNodeIdRef.current) {
          setCanvasNodes(prev => {
            const filtered = prev.filter(node => node.id !== selectedNodeIdRef.current);
            return filtered.map(node => ({
              ...node,
              connections: node.connections?.filter(id => id !== selectedNodeIdRef.current)
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
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // --- Canvas Wheel Handler ---
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const vp = viewportRef.current;
      
      if (e.metaKey || e.ctrlKey) {
        const delta = -e.deltaY * 0.001;
        const newScale = Math.min(Math.max(0.1, vp.scale * (1 + delta)), 5);
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const cx = (mx - vp.x) / vp.scale;
        const cy = (my - vp.y) / vp.scale;
        setViewport({ x: mx - cx * newScale, y: my - cy * newScale, scale: newScale });
      } else {
        setViewport(prev => ({ ...prev, x: prev.x - e.deltaX, y: prev.y - e.deltaY }));
      }
    };

    canvas.addEventListener('wheel', handleWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheel);
  }, []);

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
        setSplitRatio(Math.min(Math.max((e.clientY - rect.top) / rect.height, 0.2), 0.8));
        return;
      }
      if (resizingCol) {
        const min = 280, max = 600;
        if (resizingCol === 'left') {
          setLeftWidth(Math.max(min, Math.min(e.clientX, max)));
        } else {
          const offset = leftVisible ? leftWidth : 49;
          setCenterWidth(Math.max(min, Math.min(e.clientX - offset, max)));
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

  // --- Context Menu ---
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setContextMenu({ mouseX: e.clientX + 2, mouseY: e.clientY - 6 });
  };

  const handleCloseContextMenu = () => setContextMenu(null);

  // --- Create Card ---
  const handleCreateCard = (text?: string, position?: { x: number, y: number }) => {
    const content = text || "New note content";
    const id = `c-${Date.now()}`;
    const cx = position?.x ?? (-viewport.x + (canvasRef.current?.clientWidth || 800) / 2) / viewport.scale;
    const cy = position?.y ?? (-viewport.y + (canvasRef.current?.clientHeight || 600) / 2) / viewport.scale;

    setCanvasNodes(prev => [...prev, {
      id,
      type: 'card',
      title: 'New Concept',
      content,
      x: cx - 140,
      y: cy - 100,
      color: 'white',
    }]);
    setContextMenu(null);
  };

  // --- Render Resource Item ---
  const renderResource = (res: Resource) => {
    const isActive = activeResource.id === res.id;
    
    if (viewMode === 'list') {
      return (
        <Box 
          key={res.id} 
          onClick={() => setActiveResource(res)}
          sx={{ 
            display: 'flex', gap: 1.5, p: 1.5, mb: 1, borderRadius: 2, 
            bgcolor: isActive ? '#EFF6FF' : 'transparent', 
            border: '1px solid', 
            borderColor: isActive ? '#BFDBFE' : 'transparent',
            '&:hover': { bgcolor: isActive ? '#EFF6FF' : 'action.hover' }, 
            cursor: 'pointer', 
            transition: 'all 0.2s'
          }}
        >
          <FileText size={16} className={isActive ? "text-blue-600 mt-0.5" : "text-gray-400 mt-0.5"} />
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="body2" fontWeight={isActive ? "500" : "400"} color={isActive ? "primary.main" : "text.primary"} noWrap>
              {res.title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">{res.date}</Typography>
              {res.pages && <Typography variant="caption" color="text.disabled">• {res.pages}p</Typography>}
            </Box>
          </Box>
        </Box>
      );
    }
    
    // Grid Mode
    return (
      <Box key={res.id} onClick={() => setActiveResource(res)}>
        <Paper
          elevation={0}
          sx={{ 
            overflow: 'hidden', 
            borderRadius: 2, 
            border: isActive ? '2px solid' : '1px solid', 
            borderColor: isActive ? 'primary.main' : 'divider',
            cursor: 'pointer', 
            transition: 'all 0.2s', 
            '&:hover': { borderColor: isActive ? 'primary.main' : 'grey.400', transform: 'translateY(-2px)' }
          }}
        >
          <Box sx={{ height: 80, bgcolor: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
            <Box sx={{ width: 40, height: 56, bgcolor: 'white', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', p: 0.5, gap: 0.5 }}>
              <Box sx={{ width: '80%', height: 3, bgcolor: '#E5E7EB', borderRadius: 1 }} />
              <Box sx={{ width: '100%', height: 2, bgcolor: '#F3F4F6' }} />
              <Box sx={{ width: '60%', height: 2, bgcolor: '#F3F4F6' }} />
            </Box>
            {isActive && <Box sx={{ position: 'absolute', top: 6, right: 6, width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.main', border: '2px solid white' }} />}
          </Box>
          <Box sx={{ p: 1.5 }}>
            <Typography variant="caption" fontWeight="600" noWrap title={res.title}>{res.title}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
              <FileText size={10} className="text-gray-400" />
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>{res.date}</Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    );
  };

  // --- Render PDF Viewer ---
  const renderPdfViewer = () => (
    <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <Box 
        onMouseDown={handleVerticalMouseDown} 
        sx={{ 
          height: 44, 
          borderTop: isReaderExpanded ? 'none' : '1px solid', 
          borderBottom: '1px solid', 
          borderColor: 'divider', 
          display: 'flex', 
          alignItems: 'center', 
          px: 2, 
          justifyContent: 'space-between', 
          bgcolor: 'background.default', 
          cursor: isReaderExpanded ? 'default' : 'row-resize', 
          userSelect: 'none',
          flexShrink: 0 
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, overflow: 'hidden' }}>
          <Typography variant="caption" sx={{ color: 'error.main', fontWeight: 'bold', bgcolor: '#FEE2E2', px: 0.5, borderRadius: 0.5 }}>PDF</Typography>
          <Typography variant="subtitle2" fontWeight="600" noWrap>{activeResource.title}</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="caption" color="text.secondary">Pg 3 / {activeResource.pages}</Typography>
          <IconButton size="small" onClick={(e) => { e.stopPropagation(); setIsReaderExpanded(!isReaderExpanded); }}>
            {isReaderExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </IconButton>
        </Box>
      </Box>

      {/* PDF Content */}
      <Box sx={{ p: 3, overflowY: 'auto', flexGrow: 1 }} onClick={handleCloseContextMenu}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>3.2 Attention</Typography>
        <Typography variant="body2" sx={{ lineHeight: 1.8, color: 'text.secondary', mb: 2 }}>
          An attention function can be described as mapping a query and a set of key-value pairs to an output.
        </Typography>
        
        {/* Draggable Highlight */}
        <Box 
          component="span"
          onContextMenu={handleContextMenu}
          draggable
          onDragStart={(e) => {
            e.dataTransfer.setData("text/plain", "The output is computed as a weighted sum of the values.");
            e.dataTransfer.effectAllowed = "copy";
            setIsDraggingFromPdf(true);
          }}
          onDragEnd={() => setIsDraggingFromPdf(false)}
          sx={{ 
            bgcolor: '#FEF9C3', 
            px: 0.5, 
            borderRadius: 0.5, 
            cursor: 'grab',
            display: 'inline',
            '&:hover': { outline: '1px dashed #F59E0B' } 
          }}
        >
          <Typography component="span" variant="body2" sx={{ lineHeight: 1.8, fontWeight: 500 }}>
            The output is computed as a weighted sum of the values.
          </Typography>
        </Box>

        <Typography variant="body2" sx={{ lineHeight: 1.8, color: 'text.secondary', mt: 2 }}>
          The two most commonly used attention functions are additive attention, and dot-product (multiplicative) attention. 
        </Typography>

        {/* Context Menu */}
        <Menu
          open={contextMenu !== null}
          onClose={handleCloseContextMenu}
          anchorReference="anchorPosition"
          anchorPosition={contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined}
          slotProps={{ paper: { sx: { width: 180, borderRadius: 2 } } }}
        >
          <MenuItem onClick={() => handleCreateCard()}>
            <ListItemIcon><Layout size={16} /></ListItemIcon>
            <ListItemText primary="Create Card" />
          </MenuItem>
          <MenuItem onClick={handleCloseContextMenu}>
            <ListItemIcon><Bot size={16} /></ListItemIcon>
            <ListItemText primary="Ask AI" />
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );

  // --- Render Canvas ---
  const renderCanvas = () => (
    <Box 
      ref={canvasRef}
      sx={{ 
        flexGrow: 1, 
        bgcolor: '#FAFAFA', 
        position: 'relative', 
        overflow: 'hidden',
        cursor: isSpacePressed ? (isPanning ? 'grabbing' : 'grab') : 'default',
        touchAction: 'none',
        userSelect: 'none'
      }}
      onMouseDown={(e) => {
        if (isSpacePressed || e.button === 1) {
          setIsPanning(true);
          lastMousePos.current = { x: e.clientX, y: e.clientY };
        } else if (e.button === 0) {
          setSelectedNodeId(null);
          setSelectedConnectionId(null);
          setIsPanning(true);
          lastMousePos.current = { x: e.clientX, y: e.clientY };
        }
      }}
      onMouseMove={(e) => {
        mousePos.current = { x: e.clientX, y: e.clientY };
        
        if (connectingNodeId && canvasRef.current) {
          const rect = canvasRef.current.getBoundingClientRect();
          const x = (e.clientX - rect.left - viewport.x) / viewport.scale;
          const y = (e.clientY - rect.top - viewport.y) / viewport.scale;
          requestAnimationFrame(() => setTempLineEnd({ x, y }));
          return;
        }
        
        if (draggingNodeId) {
          if (dragStartPos.current) {
            if (Math.abs(e.clientX - dragStartPos.current.x) < 3 && Math.abs(e.clientY - dragStartPos.current.y) < 3) return;
            dragStartPos.current = null;
          }
          const dx = (e.clientX - lastMousePos.current.x) / viewport.scale;
          const dy = (e.clientY - lastMousePos.current.y) / viewport.scale;
          setCanvasNodes(prev => prev.map(n => n.id === draggingNodeId ? { ...n, x: n.x + dx, y: n.y + dy } : n));
          lastMousePos.current = { x: e.clientX, y: e.clientY };
        } else if (isPanning) {
          const dx = e.clientX - lastMousePos.current.x;
          const dy = e.clientY - lastMousePos.current.y;
          setViewport(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
          lastMousePos.current = { x: e.clientX, y: e.clientY };
        }
      }}
      onMouseUp={() => {
        setIsPanning(false);
        setDraggingNodeId(null);
        dragStartPos.current = null;
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
      onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; }}
      onDrop={(e) => {
        e.preventDefault();
        const rect = canvasRef.current?.getBoundingClientRect();
        if (rect) {
          const x = (e.clientX - rect.left - viewport.x) / viewport.scale;
          const y = (e.clientY - rect.top - viewport.y) / viewport.scale;
          const text = e.dataTransfer.getData("text/plain");
          if (text) handleCreateCard(text, { x, y });
        }
        setIsDraggingFromPdf(false);
      }}
    >
      {/* Grid Background */}
      <Box 
        sx={{ 
          position: 'absolute', 
          inset: 0, 
          opacity: 0.5, 
          backgroundImage: 'radial-gradient(#D1D5DB 1px, transparent 1px)', 
          backgroundSize: `${20 * viewport.scale}px ${20 * viewport.scale}px`,
          backgroundPosition: `${viewport.x}px ${viewport.y}px`,
          pointerEvents: 'none'
        }} 
      />
      
      {/* Canvas Content */}
      <Box sx={{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})`, transformOrigin: '0 0', position: 'absolute', top: 0, left: 0 }}>
        {/* SVG Connections */}
        <svg style={{ position: 'absolute', top: 0, left: 0, width: 10000, height: 10000, overflow: 'visible', pointerEvents: 'visiblePainted' }}>
          <rect width="10000" height="10000" fill="transparent" style={{ pointerEvents: 'none' }} />
          {canvasNodes.map(node => {
            if (!node.connections?.length) return null;
            return node.connections.map(targetId => {
              const target = canvasNodes.find(n => n.id === targetId);
              if (!target) return null;
              
              const x1 = node.x + 280, y1 = node.y + 60;
              const x2 = target.x, y2 = target.y + 60;
              const ctrl = Math.max(Math.abs(x2 - x1) * 0.4, 50);
              const connId = `${node.id}-${targetId}`;
              const isSelected = selectedConnectionId === connId;

              return (
                <g key={connId}>
                  <path 
                    d={`M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${x2 - ctrl} ${y2}, ${x2} ${y2}`}
                    stroke="transparent" strokeWidth="12" fill="none"
                    style={{ pointerEvents: 'stroke', cursor: 'pointer' }}
                    onClick={(e) => { e.stopPropagation(); setSelectedConnectionId(connId); setSelectedNodeId(null); }}
                  />
                  <path 
                    d={`M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${x2 - ctrl} ${y2}, ${x2} ${y2}`}
                    stroke={isSelected ? "#EF4444" : "#94A3B8"} 
                    strokeWidth={isSelected ? 3 : 2}
                    fill="none"
                    style={{ pointerEvents: 'none' }}
                  />
                  {isSelected && (
                    <g 
                      style={{ cursor: 'pointer', pointerEvents: 'auto' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        const dash = connId.lastIndexOf('-');
                        const src = connId.substring(0, dash);
                        const tgt = connId.substring(dash + 1);
                        setCanvasNodes(prev => prev.map(n => n.id === src && n.connections ? { ...n, connections: n.connections.filter(id => id !== tgt) } : n));
                        setSelectedConnectionId(null);
                      }}
                    >
                      <circle cx={(x1 + x2) / 2} cy={(y1 + y2) / 2} r="10" fill="#EF4444" />
                      <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 + 1} textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="12" fontWeight="bold">×</text>
                    </g>
                  )}
                </g>
              );
            });
          })}

          {/* Temp Connection Line */}
          {connectingNodeId && tempLineEnd && (() => {
            const src = canvasNodes.find(n => n.id === connectingNodeId);
            if (!src) return null;
            const x1 = src.x + 280, y1 = src.y + 50;
            const ctrl = Math.max(Math.abs(tempLineEnd.x - x1) * 0.5, 50);
            return <path d={`M ${x1} ${y1} C ${x1 + ctrl} ${y1}, ${tempLineEnd.x - ctrl} ${tempLineEnd.y}, ${tempLineEnd.x} ${tempLineEnd.y}`} stroke="#3B82F6" strokeWidth="2" fill="none" strokeDasharray="5,5" />;
          })()}
        </svg>

        {/* Nodes */}
        {canvasNodes.map(node => (
          <Paper 
            key={node.id}
            elevation={selectedNodeId === node.id ? 8 : 2} 
            onMouseDown={(e) => {
              e.stopPropagation();
              if (!(e.target as HTMLElement).closest('.conn-handle')) {
                setDraggingNodeId(node.id);
                setSelectedNodeId(node.id);
                setSelectedConnectionId(null);
                lastMousePos.current = { x: e.clientX, y: e.clientY };
                dragStartPos.current = { x: e.clientX, y: e.clientY };
              }
            }}
            onMouseUp={(e) => {
              e.stopPropagation();
              if (connectingNodeId && connectingNodeId !== node.id) {
                setCanvasNodes(prev => prev.map(n => {
                  if (n.id === connectingNodeId) {
                    const conns = n.connections || [];
                    if (conns.includes(node.id)) return n;
                    return { ...n, connections: [...conns, node.id] };
                  }
                  return n;
                }));
              }
              setConnectingNodeId(null);
              setTempLineEnd(null);
              setDraggingNodeId(null);
              dragStartPos.current = null;
            }}
            onMouseEnter={() => setHoveredNodeId(node.id)}
            onMouseLeave={() => setHoveredNodeId(null)}
            sx={{ 
              position: 'absolute', 
              top: node.y, 
              left: node.x, 
              width: 280, 
              borderRadius: 3, 
              border: '2px solid', 
              borderColor: connectingNodeId && connectingNodeId !== node.id ? '#10B981' : (selectedNodeId === node.id ? 'primary.main' : (node.color === 'blue' ? '#3B82F6' : 'transparent')),
              overflow: 'visible',
              cursor: 'grab',
              '&:hover': { boxShadow: 4 }
            }}
          >
            {/* Delete Button */}
            {selectedNodeId === node.id && (
              <Box
                onClick={(e) => {
                  e.stopPropagation();
                  setCanvasNodes(prev => prev.filter(n => n.id !== node.id).map(n => ({ ...n, connections: n.connections?.filter(id => id !== node.id) })));
                  setSelectedNodeId(null);
                }}
                sx={{ position: 'absolute', right: -8, top: -8, width: 20, height: 20, borderRadius: '50%', bgcolor: '#EF4444', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', zIndex: 20, '&:hover': { bgcolor: '#DC2626' } }}
              >
                <Typography sx={{ color: 'white', fontSize: 14, fontWeight: 'bold', lineHeight: 1 }}>×</Typography>
              </Box>
            )}
            
            {/* Connection Handle */}
            <Box
              className="conn-handle"
              onMouseDown={(e) => { e.stopPropagation(); setConnectingNodeId(node.id); }}
              sx={{
                position: 'absolute', right: -6, top: '50%', transform: 'translateY(-50%)',
                width: 12, height: 12, borderRadius: '50%', bgcolor: '#3B82F6', border: '2px solid white',
                cursor: 'crosshair', opacity: hoveredNodeId === node.id || connectingNodeId === node.id ? 1 : 0,
                transition: 'opacity 0.2s', zIndex: 10
              }}
            />
            
            {/* Receiving Handle */}
            {connectingNodeId && connectingNodeId !== node.id && (
              <Box sx={{ position: 'absolute', left: -6, top: '50%', transform: 'translateY(-50%)', width: 12, height: 12, borderRadius: '50%', bgcolor: '#10B981', border: '2px solid white', zIndex: 10 }} />
            )}
            
            {/* Card Content */}
            {node.title === 'SOURCE PDF' ? (
              <Box sx={{ p: 2 }}>
                <Typography variant="caption" color="text.disabled" fontWeight="bold">SOURCE PDF</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  <FileText size={16} className="text-red-500" />
                  <Typography variant="subtitle2" fontWeight="600">{node.content}</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1.5, color: 'text.secondary' }}>
                  <LinkIcon size={12} />
                  <Typography variant="caption">Connected to concepts</Typography>
                </Box>
              </Box>
            ) : (
              <Box sx={{ overflow: 'hidden', borderRadius: 2 }}>
                <Box sx={{ height: 4, bgcolor: node.color === 'blue' ? '#3B82F6' : '#E5E7EB' }} />
                <Box sx={{ p: 2 }}>
                  <Typography variant="subtitle2" fontWeight="bold" gutterBottom>{node.title}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5, mb: 1.5 }}>{node.content}</Typography>
                  {node.tags && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {node.tags.map(tag => <Chip key={tag} label={tag} size="small" sx={{ height: 20, fontSize: 10, bgcolor: '#F3F4F6' }} />)}
                    </Box>
                  )}
                </Box>
              </Box>
            )}
          </Paper>
        ))}
      </Box>
      
      {/* Drop Zone */}
      <Box 
        sx={{ 
          position: 'absolute', bottom: 32, left: '50%', 
          transform: isDraggingFromPdf ? 'translateX(-50%) translateY(0)' : 'translateX(-50%) translateY(80px)', 
          opacity: isDraggingFromPdf ? 1 : 0,
          pointerEvents: 'none',
          width: 320, height: 48, 
          border: '2px dashed', borderColor: 'primary.main', borderRadius: 3, 
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, 
          bgcolor: 'rgba(59, 130, 246, 0.05)', 
          transition: 'all 0.3s ease',
          zIndex: 20 
        }}
      >
        <Plus size={14} />
        <Typography variant="body2" color="primary.main">Drop to create card</Typography>
      </Box>
    </Box>
  );

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.paper' }}>
        
        {/* LEFT: Source Panel */}
        <Box ref={leftColumnRef} sx={{ width: leftVisible ? leftWidth : 48, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', transition: resizingCol ? 'none' : 'width 0.3s ease', overflow: 'hidden', bgcolor: 'background.paper' }}>
          {leftVisible ? (
            <>
              {/* File Browser */}
              <Box sx={{ height: isReaderExpanded ? 0 : `${splitRatio * 100}%`, display: 'flex', flexDirection: 'column', overflow: 'hidden', transition: isVerticalDragging ? 'none' : 'height 0.3s ease' }}>
                <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <FolderOpen size={16} className="text-blue-600" />
                    <Typography variant="subtitle2" fontWeight="bold">Research_v1</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Box sx={{ bgcolor: '#F3F4F6', borderRadius: 1, p: 0.25, display: 'flex' }}>
                      <IconButton size="small" onClick={() => setViewMode('list')} sx={{ p: 0.5, bgcolor: viewMode === 'list' ? '#fff' : 'transparent', borderRadius: 0.5 }}><ListIcon size={12} /></IconButton>
                      <IconButton size="small" onClick={() => setViewMode('grid')} sx={{ p: 0.5, bgcolor: viewMode === 'grid' ? '#fff' : 'transparent', borderRadius: 0.5 }}><LayoutGrid size={12} /></IconButton>
                    </Box>
                    <Tooltip title="Collapse (⌘\)"><IconButton size="small" onClick={() => setLeftVisible(false)}><PanelLeftClose size={14} /></IconButton></Tooltip>
                  </Box>
                </Box>
                <Box sx={{ px: 2, mb: 2 }}>
                  <Button fullWidth variant="contained" size="small" startIcon={<Upload size={14} />} sx={{ bgcolor: '#171717', textTransform: 'none', borderRadius: 1.5, '&:hover': { bgcolor: '#000' } }}>
                    Upload PDF
                  </Button>
                </Box>
                <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 2, pb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, color: 'text.secondary' }}>
                    <ChevronDown size={10} />
                    <Typography variant="caption" fontWeight="bold">PAPERS ({SAMPLE_RESOURCES.length})</Typography>
                  </Box>
                  <Box sx={{ display: viewMode === 'grid' ? 'grid' : 'block', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 1 }}>
                    {SAMPLE_RESOURCES.map(renderResource)}
                  </Box>
                </Box>
              </Box>
              {renderPdfViewer()}
            </>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
              <Box sx={{ height: 48, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
                <Tooltip title="Expand (⌘\)" placement="right">
                  <IconButton onClick={() => setLeftVisible(true)} size="small"><PanelLeftOpen size={18} /></IconButton>
                </Tooltip>
              </Box>
              <Box sx={{ py: 2 }}>
                <Tooltip title={activeResource.title} placement="right">
                  <Box sx={{ p: 1, borderRadius: 1, bgcolor: '#EFF6FF', cursor: 'pointer' }} onClick={() => setLeftVisible(true)}>
                    <FileText size={16} className="text-blue-600" />
                  </Box>
                </Tooltip>
              </Box>
            </Box>
          )}
        </Box>
        {leftVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('left')} />}

        {/* CENTER: AI Assistant */}
        <Box sx={{ width: centerVisible ? centerWidth : 0, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: centerVisible ? '1px solid' : 'none', borderColor: 'divider', transition: resizingCol ? 'none' : 'width 0.3s ease', bgcolor: '#FAFAFA', overflow: 'hidden' }}>
          <Box sx={{ height: 48, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', minWidth: 280 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#10B981' }} />
              <Typography variant="subtitle2" color="text.secondary">Assistant</Typography>
            </Box>
            <Tooltip title="Collapse (⌘.)"><IconButton size="small" onClick={() => setCenterVisible(false)}><PanelRightClose size={14} /></IconButton></Tooltip>
          </Box>
          
          {/* Chat Messages */}
          <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, minWidth: 280 }}>
            <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2, bgcolor: '#fff' }}>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                Ask me anything about the current document. I can help you summarize, explain concepts, or find connections.
              </Typography>
            </Paper>
          </Box>
          
          {/* Chat Input */}
          <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#fff', minWidth: 280 }}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', bgcolor: '#F3F4F6', borderRadius: 2, px: 2, py: 1 }}>
              <TextField 
                fullWidth 
                placeholder="Ask about this document..." 
                variant="standard" 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                InputProps={{ disableUnderline: true, style: { fontSize: 14 } }} 
              />
              <IconButton size="small" color="primary"><Send size={16} /></IconButton>
            </Box>
          </Box>
        </Box>
        {centerVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('center')} />}
        
        {/* Collapsed Center */}
        {!centerVisible && (
          <Box sx={{ width: 40, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: '#FAFAFA' }}>
            <Box sx={{ height: 48, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid', borderColor: 'divider' }}>
              <Tooltip title="Expand (⌘.)" placement="right">
                <IconButton onClick={() => setCenterVisible(true)} size="small"><PanelRightOpen size={18} /></IconButton>
              </Tooltip>
            </Box>
            <Box sx={{ py: 2 }}>
              <Tooltip title="AI Assistant" placement="right">
                <Box sx={{ p: 1, borderRadius: 1, bgcolor: '#ECFDF5', cursor: 'pointer' }} onClick={() => setCenterVisible(true)}>
                  <Bot size={16} className="text-emerald-600" />
                </Box>
              </Tooltip>
            </Box>
          </Box>
        )}

        {/* RIGHT: Canvas */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <Box sx={{ height: 48, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 3, justifyContent: 'space-between', bgcolor: '#FAFAFA' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Layout size={14} className="text-gray-500" />
              <Typography variant="subtitle2" fontWeight="600">Canvas</Typography>
            </Box>
            <Typography variant="caption" color="text.disabled">Auto-saved</Typography>
          </Box>
          {renderCanvas()}
        </Box>
      </Box>
    </GlobalLayout>
  );
}
