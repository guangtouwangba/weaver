'use client';

import { useState, useRef, useEffect, useCallback } from "react";
import GlobalLayout from "@/components/layout/GlobalLayout";
import PodcastView from "./PodcastView";
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
  Badge
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
  ArrowRight
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

export default function StudioPage() {
  // --- Layout State ---
  const [leftVisible, setLeftVisible] = useState(true);
  const [centerVisible, setCenterVisible] = useState(true);
  
  // --- Resizing State ---
  const [leftWidth, setLeftWidth] = useState(380);
  const [centerWidth, setCenterWidth] = useState(420); // Increased default width
  const [resizingCol, setResizingCol] = useState<'left' | 'center' | null>(null);

  // --- Feature State ---
  const [isReaderExpanded, setIsReaderExpanded] = useState(false);
  const [splitRatio, setSplitRatio] = useState(0.4); 
  const [activeView, setActiveView] = useState<'canvas' | 'podcast'>('canvas');
  const [quietMode, setQuietMode] = useState(false);
  
  // --- Refs ---
  const [isVerticalDragging, setIsVerticalDragging] = useState(false);
  const leftColumnRef = useRef<HTMLDivElement>(null);

  // --- Global Keyboard Shortcuts ---
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
        e.preventDefault();
        setLeftVisible(prev => !prev);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '.') {
        e.preventDefault();
        setCenterVisible(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // --- Resize Logic (Horizontal & Vertical) ---
  
  // 1. Vertical Resize (Left Column: Library vs Reader)
  const handleVerticalMouseDown = useCallback((e: React.MouseEvent) => {
    if (isReaderExpanded) return;
    e.preventDefault();
    setIsVerticalDragging(true);
  }, [isReaderExpanded]);

  // 2. Horizontal Resize (Columns)
  const handleHorizontalMouseDown = (col: 'left' | 'center') => (e: React.MouseEvent) => {
    e.preventDefault();
    setResizingCol(col);
  };

  // Global Mouse Move/Up
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      // Vertical Resize
      if (isVerticalDragging && leftColumnRef.current) {
        const rect = leftColumnRef.current.getBoundingClientRect();
        const relativeY = e.clientY - rect.top;
        const newRatio = Math.min(Math.max(relativeY / rect.height, 0.2), 0.8);
        setSplitRatio(newRatio);
        return;
      }

      // Horizontal Resize
      if (resizingCol) {
        // Calculate available width constraints if needed
        const minWidth = 280;
        const maxWidth = 800;
        
        if (resizingCol === 'left') {
          // Resizing Left Column
          const newWidth = Math.max(minWidth, Math.min(e.clientX, maxWidth));
          setLeftWidth(newWidth);
        } else if (resizingCol === 'center') {
          // Resizing Center Column
          // Center width = MouseX - LeftColumnWidth
          const currentLeftWidth = leftVisible ? leftWidth : 49; // 48 + 1 border
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

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.paper' }}>
        
        {/* ================= LEFT COLUMN: Source ================= */}
        <Box 
          ref={leftColumnRef}
          sx={{ 
            width: leftVisible ? leftWidth : 48,
            flexShrink: 0,
            display: 'flex', 
            flexDirection: 'column', 
            borderRight: '1px solid', 
            borderColor: 'divider',
            transition: resizingCol ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            overflow: 'hidden',
            position: 'relative',
            bgcolor: 'background.paper'
          }}
        >
          {leftVisible ? (
             // --- EXPANDED LEFT CONTENT ---
             <>
              {/* 1. Resource Library (Top) */}
              <Box sx={{ 
                height: isReaderExpanded ? 0 : `${splitRatio * 100}%`, 
                display: 'flex', flexDirection: 'column', overflow: 'hidden',
                transition: isVerticalDragging ? 'none' : 'height 0.3s ease'
              }}>
                {/* Header */}
                <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box component="span" sx={{ color: 'primary.main' }}><FolderOpen size={18} /></Box>
                    <Typography variant="subtitle2" fontWeight="bold">Research_v1</Typography>
                    <ChevronDown size={14} className="text-gray-400" />
                  </Box>
                  <Tooltip title="Collapse Sidebar (Cmd+\)">
                    <IconButton size="small" onClick={() => setLeftVisible(false)}><PanelLeftClose size={16} /></IconButton>
                  </Tooltip>
                </Box>

                {/* Add Button */}
                <Box sx={{ px: 2, mb: 2 }}>
                  <Button 
                    fullWidth variant="contained" startIcon={<Plus size={16} />}
                    sx={{ bgcolor: '#0F172A', color: '#fff', textTransform: 'none', borderRadius: 2, py: 1, '&:hover': { bgcolor: '#1E293B' } }}
                  >
                    Add Resource
                  </Button>
                </Box>

                {/* File List */}
                <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 2 }}>
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, color: 'text.secondary' }}>
                      <ChevronDown size={12} />
                      <Typography variant="caption" fontWeight="bold">PAPERS (3)</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1.5, p: 1.5, mb: 0.5, borderRadius: 2, bgcolor: '#EFF6FF', border: '1px solid', borderColor: '#BFDBFE' }}>
                      <FileText size={16} className="text-blue-600 mt-0.5" />
                      <Box>
                        <Typography variant="body2" fontWeight="500" color="primary.main">Attention Is All You Need.pdf</Typography>
                        <Typography variant="caption" color="text.secondary">10:42 AM</Typography>
                      </Box>
                    </Box>
                    {['BERT_Pre-training.pdf', 'GPT-3_Language_Models.pdf'].map((file, i) => (
                      <Box key={i} sx={{ display: 'flex', gap: 1.5, p: 1.5, borderRadius: 2, '&:hover': { bgcolor: 'action.hover' } }}>
                        <FileText size={16} className="text-gray-400 mt-0.5" />
                        <Box>
                          <Typography variant="body2" color="text.primary">{file}</Typography>
                          <Typography variant="caption" color="text.secondary">{i === 0 ? '2d ago' : '1w ago'}</Typography>
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </Box>
              </Box>

              {/* 2. Reader (Bottom) */}
              <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {/* Resize Handle / Reader Header */}
                <Box 
                  onMouseDown={handleVerticalMouseDown}
                  sx={{ 
                    height: 48, borderTop: isReaderExpanded ? 'none' : '1px solid', borderBottom: '1px solid', borderColor: 'divider', 
                    display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', bgcolor: 'background.default',
                    cursor: isReaderExpanded ? 'default' : 'row-resize', userSelect: 'none', position: 'relative',
                    '&:hover': { bgcolor: isReaderExpanded ? 'background.default' : 'rgba(0,0,0,0.02)' }
                  }}
                >
                  {!isReaderExpanded && (
                    <Box sx={{ position: 'absolute', top: -1, left: '50%', transform: 'translateX(-50%)', width: 40, height: 3, bgcolor: 'transparent', cursor: 'row-resize' }} />
                  )}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" sx={{ color: 'error.main', fontWeight: 'bold', bgcolor: 'error.lighter', px: 0.5, borderRadius: 0.5 }}>PDF</Typography>
                    <Typography variant="subtitle2" fontWeight="600" noWrap sx={{ maxWidth: 140 }}>Attention Is All You Need</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <IconButton size="small" onClick={(e) => { e.stopPropagation(); setIsReaderExpanded(!isReaderExpanded); }}>
                      {isReaderExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                    </IconButton>
                  </Box>
                </Box>

                {/* Reader Body */}
                <Box sx={{ p: 4, overflowY: 'auto', flexGrow: 1 }}>
                   <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>3.2 Attention</Typography>
                   <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: 'text.secondary' }}>
                     An attention function can be described as mapping a query and a set of key-value pairs to an output.
                   </Typography>
                   <Box sx={{ bgcolor: '#FFF9C4', p: 1, borderRadius: 1, mx: -1 }}>
                     <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
                       The output is computed as a weighted sum of the values.
                     </Typography>
                   </Box>
                   <Paper variant="outlined" sx={{ height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', my: 4, borderStyle: 'dashed' }}>
                     <Box sx={{ textAlign: 'center', color: 'text.disabled' }}>
                       <ImageIcon size={24} className="mx-auto mb-2" />
                       <Typography variant="caption">Figure 1: Scaled Dot-Product</Typography>
                     </Box>
                   </Paper>
                </Box>
              </Box>
             </>
          ) : (
             // --- COLLAPSED LEFT STRIP ---
             <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2, gap: 2, width: '100%' }}>
               <Tooltip title="Expand Source (Cmd+\)" placement="right">
                 <IconButton onClick={() => setLeftVisible(true)} size="small">
                   <PanelLeftOpen size={20} />
                 </IconButton>
               </Tooltip>
               <Divider sx={{ width: 20 }} />
               <Tooltip title="Attention Is All You Need.pdf" placement="right">
                  <Box sx={{ p: 1, borderRadius: 1, bgcolor: '#EFF6FF', color: 'primary.main', cursor: 'pointer' }} onClick={() => setLeftVisible(true)}>
                    <FileText size={18} />
                  </Box>
               </Tooltip>
             </Box>
          )}
        </Box>

        {/* RESIZE HANDLE 1 (Left <-> Center) */}
        {leftVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('left')} />}

        {/* ================= CENTER COLUMN: Processor ================= */}
        <Box sx={{ 
           width: centerVisible ? centerWidth : 0,
           flexShrink: 0,
           display: 'flex', 
           flexDirection: 'column', 
           borderRight: centerVisible ? '1px solid' : 'none', 
           borderColor: 'divider',
           transition: resizingCol ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
           bgcolor: '#F9FAFB',
           overflow: 'hidden',
           position: 'relative'
        }}>
          {/* Header */}
          <Box sx={{ height: 56, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', minWidth: 300 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#10B981' }} />
              <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>Processor</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <Tooltip title={quietMode ? "Show All" : "Quiet Mode"}>
                <IconButton 
                  size="small" 
                  onClick={() => setQuietMode(!quietMode)}
                  sx={{ bgcolor: quietMode ? 'primary.main' : 'transparent', color: quietMode ? '#fff' : 'text.secondary', '&:hover': { bgcolor: quietMode ? 'primary.dark' : 'action.hover' } }}
                >
                  <Filter size={14} />
                </IconButton>
              </Tooltip>
              <Tooltip title="Collapse Processor (Cmd+.)">
                <IconButton size="small" onClick={() => setCenterVisible(false)}>
                   <PanelRightClose size={16} />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Content (Stream) */}
          <Box sx={{ p: 2, overflowY: 'auto', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 300 }}>
            {quietMode && (
               <Box sx={{ p: 1, bgcolor: 'grey.100', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                 <Zap size={12} className="text-orange-500" />
                 <Typography variant="caption" color="text.secondary">Focus Mode On</Typography>
               </Box>
            )}

            <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 3, bgcolor: '#fff' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: '#3B82F6' }}>
                  <Sparkles size={14} />
                  <Typography variant="caption" fontWeight="bold">CONCEPT</Typography>
                </Box>
                <IconButton size="small" sx={{ p: 0.5 }}><Plus size={14} /></IconButton>
              </Box>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Self-Attention Mechanism</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', lineHeight: 1.5 }}>
                Mapping a query and a set of key-value pairs to an output.
              </Typography>
            </Paper>

            <Collapse in={!quietMode}>
              <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'orange.200', borderRadius: 3, bgcolor: '#FFF7ED' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: '#F97316' }}>
                    <LinkIcon size={14} />
                    <Typography variant="caption" fontWeight="bold">LINK DETECTED</Typography>
                  </Box>
                  <IconButton size="small" sx={{ p: 0.5 }}><Plus size={14} /></IconButton>
                </Box>
                <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Related to 'LSTM Limitations'</Typography>
                <Button 
                  fullWidth variant="contained" size="small" startIcon={<LinkIcon size={14} />}
                  sx={{ mt: 1, bgcolor: '#fff', color: '#F97316', boxShadow: 'none', border: '1px solid', borderColor: '#FDBA74', '&:hover': { bgcolor: '#FFEDD5', boxShadow: 'none' } }}
                >
                  Merge & Connect
                </Button>
              </Paper>
            </Collapse>
          </Box>

          {/* Footer Input */}
          <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#fff', minWidth: 300 }}>
            <TextField 
              fullWidth placeholder="Ask or summarize..." variant="standard" 
              InputProps={{ disableUnderline: true, style: { fontSize: 14 } }}
              sx={{ bgcolor: '#F3F4F6', px: 2, py: 1, borderRadius: 2 }}
            />
          </Box>
        </Box>

        {/* RESIZE HANDLE 2 (Center <-> Right) */}
        {centerVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('center')} />}

        {/* Expand Center Button (When Collapsed) */}
        {!centerVisible && (
           <Box sx={{ width: 40, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2, bgcolor: '#F9FAFB' }}>
             <Tooltip title="Expand Processor (Cmd+.)" placement="right">
               <IconButton onClick={() => setCenterVisible(true)} size="small">
                 <PanelRightOpen size={20} />
               </IconButton>
             </Tooltip>
             <Divider sx={{ width: 20, my: 2 }} />
             <Badge color="secondary" variant="dot" invisible={quietMode}>
               <Bot size={18} className="text-gray-400" />
             </Badge>
           </Box>
        )}


        {/* ================= RIGHT COLUMN: Output ================= */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          
          {/* Header */}
          <Box sx={{ 
            height: 56, borderBottom: '1px solid', borderColor: 'divider', 
            display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', bgcolor: '#fff'
          }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              {/* Visual Cue for Direct Drag */}
              {!centerVisible && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 2, px: 1.5, py: 0.5, borderRadius: 2, bgcolor: 'blue.50', color: 'blue.600', border: '1px dashed', borderColor: 'blue.200' }}>
                  <ArrowRight size={14} />
                  <Typography variant="caption" fontWeight="600">Direct Drag Active</Typography>
                </Box>
              )}

              <Button 
                startIcon={<Layout size={16} />} 
                onClick={() => setActiveView('canvas')}
                sx={{ 
                  color: activeView === 'canvas' ? 'text.primary' : 'text.secondary', 
                  bgcolor: activeView === 'canvas' ? '#F3F4F6' : 'transparent', 
                  fontWeight: 600, textTransform: 'none', borderRadius: 2, px: 2,
                  '&:hover': { bgcolor: activeView === 'canvas' ? '#F3F4F6' : 'rgba(0,0,0,0.05)' }
                }}
              >
                Canvas
              </Button>
              <Button 
                startIcon={<Mic size={16} />} 
                onClick={() => setActiveView('podcast')}
                sx={{ 
                  color: activeView === 'podcast' ? 'text.primary' : 'text.secondary',
                  bgcolor: activeView === 'podcast' ? '#F3F4F6' : 'transparent',
                  fontWeight: 600, textTransform: 'none', borderRadius: 2, px: 2,
                  '&:hover': { bgcolor: activeView === 'podcast' ? '#F3F4F6' : 'rgba(0,0,0,0.05)' }
                }}
              >
                Podcast
              </Button>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.disabled" fontWeight="600">AUTO-SAVING</Typography>
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#10B981' }} />
            </Box>
          </Box>

          {/* Content Area */}
          {activeView === 'canvas' ? (
            <Box sx={{ flexGrow: 1, bgcolor: '#F9FAFB', position: 'relative', overflow: 'hidden' }}>
              <Box sx={{ position: 'absolute', inset: 0, opacity: 0.4, backgroundImage: 'radial-gradient(#CBD5E1 1.5px, transparent 1.5px)', backgroundSize: '24px 24px' }} />
              
              <Paper elevation={3} sx={{ position: 'absolute', top: 150, left: 80, width: 240, p: 2, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="caption" color="text.disabled" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>SOURCE PDF</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <FileText size={18} className="text-red-500" />
                  <Typography variant="subtitle2" fontWeight="600">Attention Is All You Need</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
                  <LinkIcon size={14} />
                  <Typography variant="caption">Connected to 3 concepts</Typography>
                </Box>
              </Paper>

              <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
                <path d="M 320 200 C 450 200, 450 320, 550 320" stroke="#CBD5E1" strokeWidth="2" fill="none" strokeDasharray="5,5" />
              </svg>

              <Paper elevation={3} sx={{ position: 'absolute', top: 280, left: 550, width: 280, p: 0, borderRadius: 4, border: '1px solid', borderColor: '#3B82F6', overflow: 'hidden' }}>
                <Box sx={{ height: 6, bgcolor: '#3B82F6' }} />
                <Box sx={{ p: 2 }}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Self-Attention</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6, mb: 2 }}>
                    The core mechanism that allows the model to weigh the importance of different words in a sequence.
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 0 }}>
                    <Chip label="#transformer" size="small" sx={{ borderRadius: 1, bgcolor: 'grey.100', fontSize: 11 }} />
                    <Chip label="#nlp" size="small" sx={{ borderRadius: 1, bgcolor: 'grey.100', fontSize: 11 }} />
                  </Box>
                </Box>
                <Box sx={{ position: 'absolute', bottom: 12, right: 12 }}>
                  <Avatar sx={{ width: 24, height: 24, fontSize: 10, bgcolor: 'pink.100', color: 'pink.500' }}>AI</Avatar>
                </Box>
              </Paper>

              {/* Drop Zone */}
              <Box sx={{ 
                position: 'absolute', bottom: 40, left: '50%', transform: 'translateX(-50%)',
                width: 400, height: 60, border: '2px dashed', borderColor: !centerVisible ? 'primary.main' : 'divider', borderRadius: 4,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1,
                bgcolor: !centerVisible ? 'rgba(59, 130, 246, 0.05)' : 'rgba(255,255,255,0.6)', 
                backdropFilter: 'blur(4px)',
                transition: 'all 0.3s ease'
              }}>
                <Plus size={16} className={!centerVisible ? "text-primary-600" : "text-gray-400"} />
                <Typography variant="body2" color={!centerVisible ? "primary.main" : "text.secondary"}>
                  {!centerVisible ? "Drop directly from PDF" : "Drop cards here to create nodes"}
                </Typography>
              </Box>

              <IconButton sx={{ position: 'absolute', bottom: 40, right: 40, bgcolor: '#171717', color: '#fff', width: 48, height: 48, '&:hover': { bgcolor: '#000' } }}>
                <Bot size={24} />
              </IconButton>
            </Box>
          ) : (
            <PodcastView />
          )}
        </Box>
      </Box>
    </GlobalLayout>
  );
}
