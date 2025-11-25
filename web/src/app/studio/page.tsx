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
  Avatar
} from "@mui/material";
import { 
  FileText, 
  Maximize2, 
  Minimize2,
  Sparkles, 
  Link as LinkIcon, 
  BookOpen, 
  Send,
  Layout, 
  Mic, 
  Plus, 
  MoreHorizontal,
  Bot,
  Image as ImageIcon,
  FolderOpen,
  ChevronDown,
  Search,
  Settings,
  Video,
  GripHorizontal
} from "lucide-react";
import ColumnContainer from "@/components/layout/ColumnContainer";

export default function StudioPage() {
  const [isReaderExpanded, setIsReaderExpanded] = useState(false);
  const [splitRatio, setSplitRatio] = useState(0.4); // 40% default
  const [isDragging, setIsDragging] = useState(false);
  const leftColumnRef = useRef<HTMLDivElement>(null);

  // Drag handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (isReaderExpanded) return;
    e.preventDefault();
    setIsDragging(true);
  }, [isReaderExpanded]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !leftColumnRef.current) return;
      
      const rect = leftColumnRef.current.getBoundingClientRect();
      const relativeY = e.clientY - rect.top;
      const newRatio = Math.min(Math.max(relativeY / rect.height, 0.2), 0.8); // Clamp between 20% and 80%
      
      setSplitRatio(newRatio);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'row-resize';
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
  }, [isDragging]);

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.paper' }}>
        
        {/* LEFT COLUMN: Library + Reader (Vertical Split) */}
        <Box 
          ref={leftColumnRef}
          sx={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            borderRight: '1px solid', 
            borderColor: 'divider',
            maxWidth: isReaderExpanded ? 'none' : 400, // Optional max width constraint
            minWidth: 280
          }}
        >
          {/* 1. Top Section: Resource Library */}
          <Box sx={{ 
            height: isReaderExpanded ? 0 : `${splitRatio * 100}%`, 
            display: 'flex', 
            flexDirection: 'column', 
            overflow: 'hidden',
            transition: isDragging ? 'none' : 'height 0.3s ease'
          }}>
            {/* Project Header */}
            <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box component="span" sx={{ color: 'primary.main' }}>
                  <FolderOpen size={18} />
                </Box>
                <Typography variant="subtitle2" fontWeight="bold">Research_v1</Typography>
                <ChevronDown size={14} className="text-gray-400" />
              </Box>
              <Box sx={{ display: 'flex', gap: 1, color: 'text.secondary' }}>
                <Search size={16} />
                <Settings size={16} />
              </Box>
            </Box>

            {/* Add Button */}
            <Box sx={{ px: 2, mb: 2 }}>
              <Button 
                fullWidth 
                variant="contained" 
                startIcon={<Plus size={16} />}
                sx={{ 
                  bgcolor: '#0F172A', 
                  color: '#fff',
                  textTransform: 'none',
                  borderRadius: 2,
                  py: 1,
                  '&:hover': { bgcolor: '#1E293B' }
                }}
              >
                Add Resource
              </Button>
            </Box>

            {/* File List */}
            <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 2 }}>
              {/* Papers Group */}
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, color: 'text.secondary' }}>
                  <ChevronDown size={12} />
                  <Typography variant="caption" fontWeight="bold">PAPERS (3)</Typography>
                </Box>
                
                {/* Active File */}
                <Box sx={{ 
                  display: 'flex', gap: 1.5, p: 1.5, mb: 0.5, borderRadius: 2, 
                  bgcolor: '#EFF6FF', border: '1px solid', borderColor: '#BFDBFE' 
                }}>
                  <FileText size={16} className="text-blue-600 mt-0.5" />
                  <Box>
                    <Typography variant="body2" fontWeight="500" color="primary.main">Attention Is All You Need.pdf</Typography>
                    <Typography variant="caption" color="text.secondary">10:42 AM</Typography>
                  </Box>
                </Box>

                {/* Other Files */}
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

              {/* Media Group */}
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, color: 'text.secondary' }}>
                  <ChevronDown size={12} />
                  <Typography variant="caption" fontWeight="bold">MEDIA & LINKS (2)</Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1.5, p: 1.5, borderRadius: 2, '&:hover': { bgcolor: 'action.hover' } }}>
                  <Video size={16} className="text-gray-400 mt-0.5" />
                  <Box>
                    <Typography variant="body2" color="text.primary">Lecture_01_Transformers.mp4</Typography>
                    <Typography variant="caption" color="text.secondary">1hr 20m</Typography>
                  </Box>
                </Box>
              </Box>
            </Box>
          </Box>

          {/* 2. Bottom Section: Reader (Content) */}
          <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            
            {/* Resize Handle / Reader Header */}
            <Box 
              onMouseDown={handleMouseDown}
              sx={{ 
                height: 48, 
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
                position: 'relative',
                '&:hover': {
                  bgcolor: isReaderExpanded ? 'background.default' : 'rgba(0,0,0,0.02)'
                }
              }}
            >
              {/* Drag Indicator (Visual Cue) */}
              {!isReaderExpanded && (
                <Box sx={{ 
                  position: 'absolute', top: -1, left: '50%', transform: 'translateX(-50%)', 
                  width: 40, height: 3, bgcolor: 'transparent',
                  cursor: 'row-resize'
                }} />
              )}

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {!isReaderExpanded && <GripHorizontal size={16} className="text-gray-300" />}
                <Typography variant="caption" sx={{ color: 'error.main', fontWeight: 'bold', bgcolor: 'error.lighter', px: 0.5, borderRadius: 0.5 }}>PDF</Typography>
                <Typography variant="subtitle2" fontWeight="600">Attention Is All You Need</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="caption" color="text.secondary">Pg 3 / 15</Typography>
                <IconButton size="small" onClick={(e) => {
                  e.stopPropagation(); // Prevent drag start
                  setIsReaderExpanded(!isReaderExpanded);
                }}>
                  {isReaderExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                </IconButton>
              </Box>
            </Box>

            {/* Reader Body */}
            <Box sx={{ p: 4, overflowY: 'auto', flexGrow: 1 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>
                3.2 Attention
              </Typography>
              <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: 'text.secondary' }}>
                An attention function can be described as mapping a query and a set of key-value pairs to an output, where the query, keys, values, and output are all vectors.
              </Typography>
              
              <Box sx={{ bgcolor: '#FFF9C4', p: 1, borderRadius: 1, mx: -1 }}>
                <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
                  The output is computed as a weighted sum of the values, where the weight assigned to each value is computed by a compatibility function of the query with the corresponding key.
                </Typography>
              </Box>
              
              <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: 'text.secondary', mt: 2 }}>
                We call our particular attention "Scaled Dot-Product Attention". The input consists of queries and keys of dimension dk, and values of dimension dv.
              </Typography>

              <Paper variant="outlined" sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', my: 4, borderStyle: 'dashed' }}>
                <Box sx={{ textAlign: 'center', color: 'text.disabled' }}>
                  <ImageIcon size={32} className="mx-auto mb-2" />
                  <Typography variant="caption">Figure 1: Scaled Dot-Product Attention</Typography>
                </Box>
              </Paper>
            </Box>
          </Box>
        </Box>

        {/* CENTER COLUMN: Stream (Processor) */}
        <ColumnContainer flex={0.8} borderRight>
          {/* Header */}
          <Box sx={{ 
            height: 56, 
            borderBottom: '1px solid', 
            borderColor: 'divider', 
            display: 'flex', 
            alignItems: 'center', 
            px: 2,
            gap: 1.5
          }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#10B981' }} />
            <Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>Watching your read...</Typography>
          </Box>

          {/* Content (Stream) */}
          <Box sx={{ p: 2, overflowY: 'auto', flexGrow: 1, bgcolor: '#F9FAFB', display: 'flex', flexDirection: 'column', gap: 2 }}>
            
            {/* Card 1: Concept */}
            <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 3 }}>
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

            {/* Card 2: Link Detected */}
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
                fullWidth 
                variant="contained" 
                size="small" 
                startIcon={<LinkIcon size={14} />}
                sx={{ 
                  mt: 1, 
                  bgcolor: '#fff', 
                  color: '#F97316', 
                  boxShadow: 'none',
                  border: '1px solid',
                  borderColor: '#FDBA74',
                  '&:hover': { bgcolor: '#FFEDD5', boxShadow: 'none' }
                }}
              >
                Merge & Connect
              </Button>
            </Paper>

            {/* Card 3: Definition */}
            <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: '#8B5CF6' }}>
                  <BookOpen size={14} />
                  <Typography variant="caption" fontWeight="bold">DEFINITION</Typography>
                </Box>
                <IconButton size="small" sx={{ p: 0.5 }}><Plus size={14} /></IconButton>
              </Box>
              <Typography variant="subtitle2" fontWeight="bold">Scaled Dot-Product</Typography>
            </Paper>

          </Box>

          {/* Footer Input */}
          <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#fff' }}>
            <TextField 
              fullWidth 
              placeholder="Ask or summarize..." 
              variant="standard" 
              InputProps={{ disableUnderline: true, style: { fontSize: 14 } }}
              sx={{ bgcolor: '#F3F4F6', px: 2, py: 1, borderRadius: 2 }}
            />
          </Box>
        </ColumnContainer>

        {/* RIGHT COLUMN: Output (Canvas) */}
        <ColumnContainer flex={1.5}>
          {/* Header */}
          <Box sx={{ 
            height: 56, 
            borderBottom: '1px solid', 
            borderColor: 'divider', 
            display: 'flex', 
            alignItems: 'center', 
            px: 2,
            justifyContent: 'space-between'
          }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button 
                startIcon={<Layout size={16} />} 
                sx={{ color: 'text.primary', bgcolor: '#F3F4F6', fontWeight: 600, textTransform: 'none', borderRadius: 2, px: 2 }}
              >
                Canvas
              </Button>
              <Button 
                startIcon={<Mic size={16} />} 
                sx={{ color: 'text.secondary', textTransform: 'none', '&:hover': { bgcolor: 'transparent' } }}
              >
                Podcast
              </Button>
              <IconButton size="small"><Plus size={16} /></IconButton>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.disabled" fontWeight="600">AUTO-SAVING</Typography>
              <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#10B981' }} />
            </Box>
          </Box>

          {/* Canvas Area */}
          <Box sx={{ flexGrow: 1, bgcolor: '#F9FAFB', position: 'relative', overflow: 'hidden' }}>
            {/* Dot Grid */}
            <Box sx={{ 
              position: 'absolute', 
              inset: 0, 
              opacity: 0.4, 
              backgroundImage: 'radial-gradient(#CBD5E1 1.5px, transparent 1.5px)', 
              backgroundSize: '24px 24px' 
            }} />
            
            {/* Node 1: Source */}
            <Paper elevation={3} sx={{ 
              position: 'absolute', top: 150, left: 80, width: 240, p: 2, borderRadius: 4, 
              border: '1px solid', borderColor: 'divider'
            }}>
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

            {/* Curve Connector (SVG) */}
            <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
              <path 
                d="M 320 200 C 450 200, 450 320, 550 320" 
                stroke="#CBD5E1" 
                strokeWidth="2" 
                fill="none" 
                strokeDasharray="5,5"
              />
            </svg>

            {/* Node 2: Concept */}
            <Paper elevation={3} sx={{ 
              position: 'absolute', top: 280, left: 550, width: 280, p: 0, borderRadius: 4,
              border: '1px solid', borderColor: '#3B82F6', overflow: 'hidden'
            }}>
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
              width: 400, height: 60, border: '2px dashed', borderColor: 'divider', borderRadius: 4,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1,
              bgcolor: 'rgba(255,255,255,0.6)', backdropFilter: 'blur(4px)'
            }}>
              <Plus size={16} className="text-gray-400" />
              <Typography variant="body2" color="text.secondary">Drop cards here to create nodes</Typography>
            </Box>

            {/* FAB */}
            <IconButton 
              sx={{ 
                position: 'absolute', bottom: 40, right: 40, 
                bgcolor: '#171717', color: '#fff', 
                width: 48, height: 48,
                '&:hover': { bgcolor: '#000' }
              }}
            >
              <Bot size={24} />
            </IconButton>

          </Box>
        </ColumnContainer>
      </Box>
    </GlobalLayout>
  );
}

