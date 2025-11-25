'use client';

import { useState, useRef, useEffect, useCallback } from "react";
import GlobalLayout from "@/components/layout/GlobalLayout";
import PodcastView from "./PodcastView";
import WriterView from "./WriterView";
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
  Badge,
  ToggleButton,
  ToggleButtonGroup,
  Slider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  LinearProgress
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
  ArrowRight,
  LayoutGrid,
  List as ListIcon,
  PlayCircle,
  Globe,
  Music,
  Play,
  Pause,
  Volume2,
  SkipBack,
  SkipForward,
  ExternalLink,
  Clock,
  X as CloseIcon,
  MoreVertical,
  BrainCircuit,
  Presentation,
  FileQuestion,
  Wand2,
  Loader2,
  PenTool
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

// --- Mock Data ---
type ResourceType = 'pdf' | 'video' | 'audio' | 'link';

interface Resource {
  id: string;
  type: ResourceType;
  title: string;
  date: string;
  duration?: string;
  pages?: number;
  content?: string;
}

const SAMPLE_RESOURCES: Resource[] = [
  { id: '1', type: 'pdf', title: 'Attention Is All You Need.pdf', date: '10:42 AM', pages: 15 },
  { id: '2', type: 'pdf', title: 'BERT_Pre-training.pdf', date: '2d ago', pages: 24 },
  { id: '3', type: 'pdf', title: 'GPT-3_Language_Models.pdf', date: '1w ago', pages: 75 },
];

const SAMPLE_MEDIA: Resource[] = [
  { id: '4', type: 'video', title: 'Lecture_01_Transformers.mp4', date: 'Yesterday', duration: '1:20:00' },
  { id: '5', type: 'audio', title: 'DeepMind_Podcast_#12.mp3', date: '3d ago', duration: '45:12' },
  { id: '6', type: 'link', title: 'HuggingFace Blog', date: '5d ago' },
];

// --- Tab System Types ---
type TabType = 'canvas' | 'podcast' | 'flashcards' | 'ppt' | 'writer';
interface Tab {
  id: string;
  type: TabType;
  title: string;
  status: 'ready' | 'generating';
  progress?: number; // 0-100
}

export default function StudioPage() {
  // --- Layout State ---
  const [leftVisible, setLeftVisible] = useState(true);
  const [centerVisible, setCenterVisible] = useState(true);
  
  // --- Resizing State ---
  const [leftWidth, setLeftWidth] = useState(380);
  const [centerWidth, setCenterWidth] = useState(420); 
  const [resizingCol, setResizingCol] = useState<'left' | 'center' | null>(null);

  // --- Feature State ---
  const [isReaderExpanded, setIsReaderExpanded] = useState(false);
  const [splitRatio, setSplitRatio] = useState(0.4); 
  const [quietMode, setQuietMode] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid');
  
  // --- Selection State ---
  const [activeResource, setActiveResource] = useState<Resource>(SAMPLE_RESOURCES[0]);

  // --- Tab System State ---
  const [tabs, setTabs] = useState<Tab[]>([
    { id: 't1', type: 'canvas', title: 'Main Canvas', status: 'ready' }
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('t1');
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  // --- Refs ---
  const [isVerticalDragging, setIsVerticalDragging] = useState(false);
  const leftColumnRef = useRef<HTMLDivElement>(null);

  // --- Tab Handlers ---
  const handleTabClose = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    const newTabs = tabs.filter(t => t.id !== tabId);
    if (newTabs.length === 0) {
      // Ensure at least one tab? Or show empty state. Let's keep one canvas.
      setTabs([{ id: 'new-canvas', type: 'canvas', title: 'Canvas', status: 'ready' }]);
      setActiveTabId('new-canvas');
    } else {
      setTabs(newTabs);
      if (activeTabId === tabId) {
        setActiveTabId(newTabs[newTabs.length - 1].id);
      }
    }
  };

  const handleAddTab = (type: TabType) => {
    setMenuAnchor(null);
    const newId = `t-${Date.now()}`;
    
    let title = 'New Tab';
    let isGen = false;

    switch (type) {
      case 'canvas': title = 'New Canvas'; break;
      case 'podcast': title = 'Podcast'; isGen = true; break;
      case 'flashcards': title = 'Flashcards'; isGen = true; break;
      case 'ppt': title = 'Slides'; isGen = true; break;
      case 'writer': title = 'Writer'; break;
    }

    const newTab: Tab = { 
      id: newId, 
      type, 
      title, 
      status: isGen ? 'generating' : 'ready',
      progress: 0
    };

    setTabs([...tabs, newTab]);
    setActiveTabId(newId);

    // Simulate Generation
    if (isGen) {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress >= 100) {
          clearInterval(interval);
          setTabs(prev => prev.map(t => t.id === newId ? { ...t, status: 'ready' } : t));
        } else {
          setTabs(prev => prev.map(t => t.id === newId ? { ...t, progress } : t));
        }
      }, 800);
    }
  };

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
      const relativeY = e.clientY - rect.top;
        const newRatio = Math.min(Math.max(relativeY / rect.height, 0.2), 0.8);
      setSplitRatio(newRatio);
        return;
      }
      if (resizingCol) {
        const minWidth = 280;
        const maxWidth = 800;
        if (resizingCol === 'left') {
          const newWidth = Math.max(minWidth, Math.min(e.clientX, maxWidth));
          setLeftWidth(newWidth);
        } else if (resizingCol === 'center') {
          const currentLeftWidth = leftVisible ? leftWidth : 49;
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

  // --- Render Helpers ---
  const renderResource = (res: Resource) => {
    const isActive = activeResource.id === res.id;
    if (viewMode === 'list') {
  return (
        <Box 
          key={res.id} onClick={() => setActiveResource(res)}
          sx={{ 
            display: 'flex', gap: 1.5, p: 1.5, mb: 1, borderRadius: 2, 
            bgcolor: isActive ? '#EFF6FF' : 'transparent', 
            border: isActive ? '1px solid' : '1px solid', borderColor: isActive ? '#BFDBFE' : 'transparent',
            '&:hover': { bgcolor: isActive ? '#EFF6FF' : 'action.hover' }, cursor: 'pointer', transition: 'all 0.2s'
          }}
        >
          {res.type === 'pdf' && <FileText size={16} className={isActive ? "text-blue-600 mt-0.5" : "text-gray-400 mt-0.5"} />}
          {res.type === 'video' && <Video size={16} className="text-gray-400 mt-0.5" />}
          {res.type === 'audio' && <Music size={16} className="text-gray-400 mt-0.5" />}
          {res.type === 'link' && <LinkIcon size={16} className="text-gray-400 mt-0.5" />}
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="body2" fontWeight={isActive ? "500" : "400"} color={isActive ? "primary.main" : "text.primary"} noWrap>{res.title}</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">{res.date}</Typography>
              {(res.duration || res.pages) && <Typography variant="caption" color="text.disabled">•</Typography>}
              {res.duration && <Typography variant="caption" sx={{ color: 'text.secondary', bgcolor: 'action.hover', px: 0.5, borderRadius: 0.5 }}>{res.duration}</Typography>}
              {res.pages && <Typography variant="caption" color="text.secondary">{res.pages}p</Typography>}
              </Box>
              </Box>
            </Box>
      );
    }
    // Grid Mode
    return (
      <Box key={res.id} sx={{ position: 'relative', group: 'card' }} onClick={() => setActiveResource(res)}>
        <Paper
          elevation={0}
                sx={{ 
            p: 0, overflow: 'hidden', borderRadius: 2, border: isActive ? '2px solid' : '1px solid', borderColor: isActive ? 'primary.main' : 'divider',
            cursor: 'pointer', transition: 'all 0.2s', '&:hover': { borderColor: isActive ? 'primary.main' : 'grey.400', transform: 'translateY(-2px)' }, display: 'flex', flexDirection: 'column'
          }}
        >
          <Box sx={{ height: 100, bgcolor: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', borderBottom: '1px solid', borderColor: 'divider' }}>
            {res.type === 'pdf' && (
              <Box sx={{ width: 50, height: 70, bgcolor: 'white', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', display: 'flex', flexDirection: 'column', p: 0.5, gap: 0.5 }}>
                <Box sx={{ width: '80%', height: 4, bgcolor: '#E5E7EB', borderRadius: 1 }} /><Box sx={{ width: '100%', height: 2, bgcolor: '#F3F4F6' }} /><Box sx={{ width: '100%', height: 2, bgcolor: '#F3F4F6' }} /><Box sx={{ width: '60%', height: 2, bgcolor: '#F3F4F6' }} />
                <Box sx={{ position: 'absolute', top: 0, right: 0, borderStyle: 'solid', borderWidth: '0 8px 8px 0', borderColor: 'transparent #F3F4F6 transparent transparent' }} />
              </Box>
            )}
            {res.type === 'video' && (
              <Box sx={{ width: '100%', height: '100%', bgcolor: '#1F2937', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <PlayCircle size={32} className="text-white opacity-80" />
                <Box sx={{ position: 'absolute', bottom: 4, right: 4, bgcolor: 'rgba(0,0,0,0.7)', color: '#fff', px: 0.5, borderRadius: 0.5, fontSize: 10, fontWeight: 600 }}>{res.duration}</Box>
              </Box>
            )}
             {res.type === 'audio' && (
              <Box sx={{ width: '100%', height: '100%', bgcolor: '#1F2937', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Music size={32} className="text-purple-400 opacity-80" />
                <Box sx={{ position: 'absolute', bottom: 4, right: 4, bgcolor: 'rgba(0,0,0,0.7)', color: '#fff', px: 0.5, borderRadius: 0.5, fontSize: 10, fontWeight: 600 }}>{res.duration}</Box>
              </Box>
            )}
             {res.type === 'link' && <Box sx={{ width: '100%', height: '100%', bgcolor: '#EEF2FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Globe size={32} className="text-blue-300" /></Box>}
            {isActive && <Box sx={{ position: 'absolute', top: 8, right: 8, width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.main', border: '2px solid white' }} />}
              </Box>
          <Box sx={{ p: 1.5 }}>
            <Typography variant="caption" fontWeight="600" sx={{ display: 'block', lineHeight: 1.2, mb: 0.5 }} noWrap title={res.title}>{res.title}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
               {res.type === 'pdf' && <FileText size={12} className="text-gray-400" />}{res.type === 'video' && <Video size={12} className="text-gray-400" />}{res.type === 'audio' && <Music size={12} className="text-gray-400" />}{res.type === 'link' && <LinkIcon size={12} className="text-gray-400" />}
               <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>{res.date}</Typography>
            </Box>
                </Box>
              </Paper>
            </Box>
    );
  };

  // --- Render Content Viewer (Bottom Panel) ---
  const renderContentViewer = () => {
    const { type, title, duration } = activeResource;
    return (
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Box onMouseDown={handleVerticalMouseDown} sx={{ height: 48, borderTop: isReaderExpanded ? 'none' : '1px solid', borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', bgcolor: 'background.default', cursor: isReaderExpanded ? 'default' : 'row-resize', userSelect: 'none', position: 'relative', flexShrink: 0 }}>
          {!isReaderExpanded && <Box sx={{ position: 'absolute', top: -1, left: '50%', transform: 'translateX(-50%)', width: 40, height: 3, bgcolor: 'transparent', cursor: 'row-resize' }} />}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, overflow: 'hidden' }}>
            <Typography variant="caption" sx={{ color: type === 'pdf' ? 'error.main' : type === 'video' ? 'primary.main' : type === 'audio' ? 'purple.main' : 'blue.main', fontWeight: 'bold', bgcolor: type === 'pdf' ? 'error.lighter' : type === 'video' ? 'grey.200' : type === 'audio' ? 'purple.50' : 'blue.50', px: 0.5, borderRadius: 0.5, textTransform: 'uppercase' }}>{type}</Typography>
            <Typography variant="subtitle2" fontWeight="600" noWrap>{title}</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexShrink: 0 }}>
            {type === 'pdf' && <Typography variant="caption" color="text.secondary">Pg 3 / 15</Typography>}
            {(type === 'video' || type === 'audio') && duration && <Typography variant="caption" color="text.secondary">{duration}</Typography>}
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); setIsReaderExpanded(!isReaderExpanded); }}>{isReaderExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}</IconButton>
          </Box>
        </Box>

        {type === 'pdf' && (
          <Box sx={{ p: 4, overflowY: 'auto', flexGrow: 1 }}>
            <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ mb: 3 }}>3.2 Attention</Typography>
            <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: 'text.secondary' }}>An attention function can be described as mapping a query and a set of key-value pairs to an output.</Typography>
            <Box sx={{ bgcolor: '#FFF9C4', p: 1, borderRadius: 1, mx: -1 }}><Typography variant="body1" sx={{ lineHeight: 1.8 }}>The output is computed as a weighted sum of the values.</Typography></Box>
            <Paper variant="outlined" sx={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'grey.50', my: 4, borderStyle: 'dashed' }}><Box sx={{ textAlign: 'center', color: 'text.disabled' }}><ImageIcon size={32} className="mx-auto mb-2" /><Typography variant="caption">Figure 1: Scaled Dot-Product Attention</Typography></Box></Paper>
          </Box>
        )}
        {type === 'video' && (
          <Box sx={{ bgcolor: '#000', flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', position: 'relative' }}>
            <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Typography variant="body2" sx={{ color: 'grey.500' }}>[ Video Placeholder: {title} ]</Typography></Box>
            <Box sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}><Slider size="small" defaultValue={30} sx={{ color: '#fff', mb: 1 }} /><Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#fff' }}><Box sx={{ display: 'flex', gap: 2 }}><Play size={20} fill="currentColor" /><Volume2 size={20} /></Box><Typography variant="caption">12:30 / {duration}</Typography></Box></Box>
          </Box>
        )}
        {type === 'audio' && (
          <Box sx={{ bgcolor: '#1F2937', flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4 }}>
            <Box sx={{ width: 120, height: 120, borderRadius: 4, bgcolor: 'primary.main', mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 20px 40px rgba(0,0,0,0.3)' }}><Music size={48} color="#fff" /></Box>
            <Typography variant="h6" sx={{ color: '#fff', mb: 1 }}>{title}</Typography>
            <Typography variant="body2" sx={{ color: 'grey.400', mb: 4 }}>Added {activeResource.date}</Typography>
            <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', height: 40, mb: 4 }}>{[...Array(20)].map((_, i) => (<Box key={i} sx={{ width: 4, height: Math.random() * 40 + 10, bgcolor: i === 10 ? '#fff' : 'grey.600', borderRadius: 2 }} />))}</Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 4, color: '#fff' }}><SkipBack size={24} /><Box sx={{ width: 64, height: 64, borderRadius: '50%', bgcolor: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#000' }}><Play size={24} fill="currentColor" className="ml-1" /></Box><SkipForward size={24} /></Box>
          </Box>
        )}
        {type === 'link' && (
           <Box sx={{ flexGrow: 1, bgcolor: '#F9FAFB', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4 }}>
             <Box sx={{ textAlign: 'center', mb: 4 }}><Globe size={48} className="text-gray-300 mb-2 mx-auto" /><Typography variant="h6" gutterBottom>External Resource</Typography><Button variant="outlined" startIcon={<ExternalLink size={16} />} href="https://huggingface.co" target="_blank">Open in Browser</Button></Box>
           </Box>
        )}
      </Box>
    );
  };

  // --- Render Tab Content ---
  const renderTabContent = () => {
    const activeTab = tabs.find(t => t.id === activeTabId) || tabs[0];
    
    // Loading State
    if (activeTab.status === 'generating') {
      return (
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', bgcolor: '#F9FAFB' }}>
           <Box sx={{ position: 'relative', display: 'inline-flex', mb: 3 }}>
             <CircularProgress size={60} thickness={4} sx={{ color: 'primary.main' }} />
             <Box sx={{ top: 0, left: 0, bottom: 0, right: 0, position: 'absolute', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               {activeTab.type === 'podcast' && <Mic size={24} className="text-primary-main" />}
               {activeTab.type === 'flashcards' && <BrainCircuit size={24} className="text-primary-main" />}
               {activeTab.type === 'ppt' && <Presentation size={24} className="text-primary-main" />}
             </Box>
           </Box>
           <Typography variant="h6" fontWeight="bold" gutterBottom>Generating {activeTab.title}...</Typography>
           <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>AI is analyzing your resources and synthesizing content.</Typography>
           <Box sx={{ width: 300 }}>
             <LinearProgress variant="determinate" value={activeTab.progress || 0} sx={{ borderRadius: 2, height: 6 }} />
                </Box>
              </Box>
      );
    }

    // Ready State
    switch (activeTab.type) {
      case 'podcast': return <PodcastView />;
      case 'writer': return <WriterView />;
      case 'canvas': 
      default:
        return (
          <Box sx={{ flexGrow: 1, bgcolor: '#F9FAFB', position: 'relative', overflow: 'hidden' }}>
            <Box sx={{ position: 'absolute', inset: 0, opacity: 0.4, backgroundImage: 'radial-gradient(#CBD5E1 1.5px, transparent 1.5px)', backgroundSize: '24px 24px' }} />
            <Paper elevation={3} sx={{ position: 'absolute', top: 150, left: 80, width: 240, p: 2, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.disabled" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>SOURCE PDF</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}><FileText size={18} className="text-red-500" /><Typography variant="subtitle2" fontWeight="600">Attention Is All You Need</Typography></Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}><LinkIcon size={14} /><Typography variant="caption">Connected to 3 concepts</Typography></Box>
            </Paper>
            <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}><path d="M 320 200 C 450 200, 450 320, 550 320" stroke="#CBD5E1" strokeWidth="2" fill="none" strokeDasharray="5,5" /></svg>
            <Paper elevation={3} sx={{ position: 'absolute', top: 280, left: 550, width: 280, p: 0, borderRadius: 4, border: '1px solid', borderColor: '#3B82F6', overflow: 'hidden' }}>
              <Box sx={{ height: 6, bgcolor: '#3B82F6' }} /><Box sx={{ p: 2 }}><Typography variant="subtitle1" fontWeight="bold" gutterBottom>Self-Attention</Typography><Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6, mb: 2 }}>The core mechanism that allows the model to weigh the importance of different words in a sequence.</Typography><Box sx={{ display: 'flex', gap: 1, mb: 0 }}><Chip label="#transformer" size="small" sx={{ borderRadius: 1, bgcolor: 'grey.100', fontSize: 11 }} /><Chip label="#nlp" size="small" sx={{ borderRadius: 1, bgcolor: 'grey.100', fontSize: 11 }} /></Box></Box><Box sx={{ position: 'absolute', bottom: 12, right: 12 }}><Avatar sx={{ width: 24, height: 24, fontSize: 10, bgcolor: 'pink.100', color: 'pink.500' }}>AI</Avatar></Box>
            </Paper>
            <Box sx={{ position: 'absolute', bottom: 40, left: '50%', transform: 'translateX(-50%)', width: 400, height: 60, border: '2px dashed', borderColor: !centerVisible ? 'primary.main' : 'divider', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, bgcolor: !centerVisible ? 'rgba(59, 130, 246, 0.05)' : 'rgba(255,255,255,0.6)', backdropFilter: 'blur(4px)', transition: 'all 0.3s ease' }}>
              <Plus size={16} className={!centerVisible ? "text-primary-600" : "text-gray-400"} /><Typography variant="body2" color={!centerVisible ? "primary.main" : "text.secondary"}>{!centerVisible ? "Drop directly from PDF" : "Drop cards here to create nodes"}</Typography>
            </Box>
            <IconButton sx={{ position: 'absolute', bottom: 40, right: 40, bgcolor: '#171717', color: '#fff', width: 48, height: 48, '&:hover': { bgcolor: '#000' } }}><Bot size={24} /></IconButton>
          </Box>
        );
    }
  };

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.paper' }}>
        
        {/* LEFT & CENTER COLUMN (Keep existing code structure) */}
        <Box ref={leftColumnRef} sx={{ width: leftVisible ? leftWidth : 48, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid', borderColor: 'divider', transition: resizingCol ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)', overflow: 'hidden', position: 'relative', bgcolor: 'background.paper' }}>
           {leftVisible ? (
             <>
              <Box sx={{ height: isReaderExpanded ? 0 : `${splitRatio * 100}%`, display: 'flex', flexDirection: 'column', overflow: 'hidden', transition: isVerticalDragging ? 'none' : 'height 0.3s ease' }}>
                 <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                   <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Box component="span" sx={{ color: 'primary.main' }}><FolderOpen size={18} /></Box><Typography variant="subtitle2" fontWeight="bold">Research_v1</Typography></Box>
                   <Box sx={{ display: 'flex', gap: 0.5 }}><Box sx={{ bgcolor: '#F3F4F6', borderRadius: 1, p: 0.5, display: 'flex' }}><IconButton size="small" onClick={() => setViewMode('list')} sx={{ p: 0.5, bgcolor: viewMode === 'list' ? '#fff' : 'transparent', boxShadow: viewMode === 'list' ? '0 1px 2px rgba(0,0,0,0.1)' : 'none', borderRadius: 1 }}><ListIcon size={14} /></IconButton><IconButton size="small" onClick={() => setViewMode('grid')} sx={{ p: 0.5, bgcolor: viewMode === 'grid' ? '#fff' : 'transparent', boxShadow: viewMode === 'grid' ? '0 1px 2px rgba(0,0,0,0.1)' : 'none', borderRadius: 1 }}><LayoutGrid size={14} /></IconButton></Box><Tooltip title="Collapse Sidebar (Cmd+\)"><IconButton size="small" onClick={() => setLeftVisible(false)}><PanelLeftClose size={16} /></IconButton></Tooltip></Box>
                 </Box>
                 <Box sx={{ px: 2, mb: 2 }}><Button fullWidth variant="contained" startIcon={<Plus size={16} />} sx={{ bgcolor: '#0F172A', color: '#fff', textTransform: 'none', borderRadius: 2, py: 1, '&:hover': { bgcolor: '#1E293B' } }}>Add Resource</Button></Box>
                 <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 2, pb: 2 }}>
                   <Box sx={{ mb: 3 }}><Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, color: 'text.secondary' }}><ChevronDown size={12} /><Typography variant="caption" fontWeight="bold">PAPERS ({SAMPLE_RESOURCES.length})</Typography></Box><Box sx={{ display: viewMode === 'grid' ? 'grid' : 'block', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 1.5 }}>{SAMPLE_RESOURCES.map(renderResource)}</Box></Box>
                   <Box><Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, color: 'text.secondary' }}><ChevronDown size={12} /><Typography variant="caption" fontWeight="bold">MEDIA & LINKS ({SAMPLE_MEDIA.length})</Typography></Box><Box sx={{ display: viewMode === 'grid' ? 'grid' : 'block', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 1.5 }}>{SAMPLE_MEDIA.map(renderResource)}</Box></Box>
                </Box>
              </Box>
              {renderContentViewer()}
             </>
           ) : (
             <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2, gap: 2, width: '100%' }}><Tooltip title="Expand Source (Cmd+\)" placement="right"><IconButton onClick={() => setLeftVisible(true)} size="small"><PanelLeftOpen size={20} /></IconButton></Tooltip><Divider sx={{ width: 20 }} /><Tooltip title="Attention Is All You Need.pdf" placement="right"><Box sx={{ p: 1, borderRadius: 1, bgcolor: '#EFF6FF', color: 'primary.main', cursor: 'pointer' }} onClick={() => setLeftVisible(true)}><FileText size={18} /></Box></Tooltip></Box>
           )}
        </Box>
        {leftVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('left')} />}

        <Box sx={{ width: centerVisible ? centerWidth : 0, flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: centerVisible ? '1px solid' : 'none', borderColor: 'divider', transition: resizingCol ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)', bgcolor: '#F9FAFB', overflow: 'hidden', position: 'relative' }}>
          <Box sx={{ height: 56, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', minWidth: 300 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}><Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: '#10B981' }} /><Typography variant="subtitle2" sx={{ color: 'text.secondary' }}>Processor</Typography></Box>
            <Box sx={{ display: 'flex', gap: 0.5 }}><Tooltip title={quietMode ? "Show All" : "Quiet Mode"}><IconButton size="small" onClick={() => setQuietMode(!quietMode)} sx={{ bgcolor: quietMode ? 'primary.main' : 'transparent', color: quietMode ? '#fff' : 'text.secondary', '&:hover': { bgcolor: quietMode ? 'primary.dark' : 'action.hover' } }}><Filter size={14} /></IconButton></Tooltip><Tooltip title="Collapse Processor (Cmd+.)"><IconButton size="small" onClick={() => setCenterVisible(false)}><PanelRightClose size={16} /></IconButton></Tooltip></Box>
          </Box>
          <Box sx={{ p: 2, overflowY: 'auto', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 300 }}>
            {quietMode && <Box sx={{ p: 1, bgcolor: 'grey.100', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}><Zap size={12} className="text-orange-500" /><Typography variant="caption" color="text.secondary">Focus Mode On</Typography></Box>}
            <Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 3, bgcolor: '#fff' }}><Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}><Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: '#3B82F6' }}><Sparkles size={14} /><Typography variant="caption" fontWeight="bold">CONCEPT</Typography></Box><IconButton size="small" sx={{ p: 0.5 }}><Plus size={14} /></IconButton></Box><Typography variant="subtitle2" fontWeight="bold" gutterBottom>Self-Attention Mechanism</Typography><Typography variant="caption" color="text.secondary" sx={{ display: 'block', lineHeight: 1.5 }}>Mapping a query and a set of key-value pairs to an output.</Typography></Paper>
            <Collapse in={!quietMode}><Paper elevation={0} sx={{ p: 2, border: '1px solid', borderColor: 'orange.200', borderRadius: 3, bgcolor: '#FFF7ED' }}><Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}><Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: '#F97316' }}><LinkIcon size={14} /><Typography variant="caption" fontWeight="bold">LINK DETECTED</Typography></Box><IconButton size="small" sx={{ p: 0.5 }}><Plus size={14} /></IconButton></Box><Typography variant="subtitle2" fontWeight="bold" gutterBottom>Related to 'LSTM Limitations'</Typography><Button fullWidth variant="contained" size="small" startIcon={<LinkIcon size={14} />} sx={{ mt: 1, bgcolor: '#fff', color: '#F97316', boxShadow: 'none', border: '1px solid', borderColor: '#FDBA74', '&:hover': { bgcolor: '#FFEDD5', boxShadow: 'none' } }}>Merge & Connect</Button></Paper></Collapse>
          </Box>
          <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: '#fff', minWidth: 300 }}><TextField fullWidth placeholder="Ask or summarize..." variant="standard" InputProps={{ disableUnderline: true, style: { fontSize: 14 } }} sx={{ bgcolor: '#F3F4F6', px: 2, py: 1, borderRadius: 2 }} /></Box>
        </Box>
        {centerVisible && <VerticalResizeHandle onMouseDown={handleHorizontalMouseDown('center')} />}
        {!centerVisible && <Box sx={{ width: 40, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2, bgcolor: '#F9FAFB' }}><Tooltip title="Expand Processor (Cmd+.)" placement="right"><IconButton onClick={() => setCenterVisible(true)} size="small"><PanelRightOpen size={20} /></IconButton></Tooltip><Divider sx={{ width: 20, my: 2 }} /><Badge color="secondary" variant="dot" invisible={quietMode}><Bot size={18} className="text-gray-400" /></Badge></Box>}


        {/* ================= RIGHT COLUMN: Output OS (Tabs + Launcher) ================= */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          
          {/* Header (Tab Bar) */}
          <Box sx={{ 
            height: 56, borderBottom: '1px solid', borderColor: 'divider', 
            display: 'flex', alignItems: 'flex-end', px: 2, justifyContent: 'space-between', bgcolor: '#F9FAFB'
          }}>
            {/* Tabs Container */}
            <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', width: '100%', '::-webkit-scrollbar': { display: 'none' } }}>
              {tabs.map(tab => (
                <Box
                  key={tab.id}
                  onClick={() => setActiveTabId(tab.id)}
                  sx={{
                    display: 'flex', alignItems: 'center', gap: 1,
                    px: 2, py: 1.5,
                    bgcolor: activeTabId === tab.id ? '#fff' : 'transparent',
                    borderTopLeftRadius: 8, borderTopRightRadius: 8,
                    border: '1px solid',
                    borderBottom: activeTabId === tab.id ? 'none' : '1px solid',
                    borderColor: 'divider',
                    position: 'relative', top: 1, // overlap bottom border
                    cursor: 'pointer',
                    userSelect: 'none',
                    minWidth: 120,
                    maxWidth: 200,
                    '&:hover': { bgcolor: activeTabId === tab.id ? '#fff' : 'rgba(0,0,0,0.03)' }
                  }}
                >
                  {tab.status === 'generating' ? <Loader2 size={14} className="animate-spin text-blue-600" /> : 
                   tab.type === 'podcast' ? <Mic size={14} className="text-purple-500" /> :
                   tab.type === 'flashcards' ? <BrainCircuit size={14} className="text-orange-500" /> :
                   tab.type === 'ppt' ? <Presentation size={14} className="text-pink-500" /> :
                   tab.type === 'writer' ? <PenTool size={14} className="text-green-600" /> :
                   <Layout size={14} className="text-gray-500" />
                  }
                  <Typography variant="caption" fontWeight={activeTabId === tab.id ? 600 : 400} noWrap sx={{ flex: 1 }}>{tab.title}</Typography>
                  <IconButton size="small" onClick={(e) => handleTabClose(e, tab.id)} sx={{ p: 0.5, opacity: 0.6, '&:hover': { opacity: 1, bgcolor: 'error.lighter', color: 'error.main' } }}>
                    <CloseIcon size={12} />
                  </IconButton>
                </Box>
              ))}
              
              {/* Add Tab Button */}
              <IconButton size="small" onClick={(e) => setMenuAnchor(e.currentTarget)} sx={{ mb: 1, ml: 0.5 }}>
                <Plus size={16} />
              </IconButton>

              {/* Capability Launcher Menu */}
              <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={() => setMenuAnchor(null)}
                PaperProps={{ sx: { width: 220, borderRadius: 3, mt: 1 } }}
              >
                <Typography variant="caption" sx={{ px: 2, py: 1, display: 'block', color: 'text.secondary', fontWeight: 600 }}>CREATE NEW</Typography>
                <MenuItem onClick={() => handleAddTab('canvas')}>
                  <ListItemIcon><Layout size={16} /></ListItemIcon>
                  <ListItemText primary="Canvas" secondary="Whiteboard" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <MenuItem onClick={() => handleAddTab('writer')}>
                  <ListItemIcon><PenTool size={16} className="text-green-600" /></ListItemIcon>
                  <ListItemText primary="Writer" secondary="Drafting & Mixing" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <Divider />
                <Typography variant="caption" sx={{ px: 2, py: 1, display: 'block', color: 'text.secondary', fontWeight: 600 }}>GENERATE WITH AI</Typography>
                <MenuItem onClick={() => handleAddTab('podcast')}>
                  <ListItemIcon><Mic size={16} className="text-purple-500" /></ListItemIcon>
                  <ListItemText primary="Podcast" secondary="Audio Overview" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <MenuItem onClick={() => handleAddTab('flashcards')}>
                  <ListItemIcon><BrainCircuit size={16} className="text-orange-500" /></ListItemIcon>
                  <ListItemText primary="Flashcards" secondary="Study Aid" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
                <MenuItem onClick={() => handleAddTab('ppt')}>
                  <ListItemIcon><Presentation size={16} className="text-pink-500" /></ListItemIcon>
                  <ListItemText primary="Slides" secondary="Presentation" secondaryTypographyProps={{ fontSize: 10 }} />
                </MenuItem>
              </Menu>
            </Box>

            {/* Right Header Actions */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, pl: 2 }}>
              {/* Direct Drag Indicator - Global */}
              {!centerVisible && activeTabId.startsWith('t') && tabs.find(t => t.id === activeTabId)?.type === 'canvas' && (
                 <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, px: 1, py: 0.5, borderRadius: 1, bgcolor: 'blue.50', color: 'blue.600', border: '1px dashed', borderColor: 'blue.200' }}>
                   <ArrowRight size={12} />
                   <Typography variant="caption" fontWeight="600" sx={{ whiteSpace: 'nowrap' }}>Drag Active</Typography>
                 </Box>
              )}
              <Typography variant="caption" color="text.disabled" fontWeight="600" sx={{ whiteSpace: 'nowrap' }}>SAVED</Typography>
            </Box>
          </Box>

          {/* Active Tab Content */}
          {renderTabContent()}

          </Box>
      </Box>
    </GlobalLayout>
  );
}
