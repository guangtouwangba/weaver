'use client';

import { useState } from 'react';
import GlobalLayout from '@/components/layout/GlobalLayout';
import { 
  Box, Typography, Paper, IconButton, Button, TextField, 
  Chip, Divider, Avatar 
} from '@mui/material';
import { 
  Inbox as InboxIcon, Plus, FileText, Link as LinkIcon, 
  Mic, Trash2, ArrowRight, Sparkles, FolderInput, 
  MoreHorizontal, CheckCircle2, Clock
} from 'lucide-react';

// 模拟：Inbox 中的待处理项
const INBOX_ITEMS = [
  { 
    id: '1', type: 'pdf', title: 'Scaling Laws for Neural Language Models.pdf', 
    added: '10 mins ago', 
    summary: 'Empirical laws for scaling model size, dataset size, and compute.',
    suggestedProject: 'Research_v1 (NLP)',
    confidence: 'High'
  },
  { 
    id: '2', type: 'link', title: 'Andrej Karpathy: State of GPT', 
    added: '2 hours ago', 
    summary: 'Keynote speech about the current capabilities and future of GPT models.',
    suggestedProject: 'Research_v1 (NLP)',
    confidence: 'High'
  },
  { 
    id: '3', type: 'audio', title: 'Voice Note: Idea for new architecture', 
    added: 'Yesterday', 
    summary: 'Raw thoughts on modifying the attention head structure.',
    suggestedProject: 'Bio_Neuro_Study', 
    confidence: 'Low' // AI 不确定
  },
];

export default function InboxPage() {
  const [items, setItems] = useState(INBOX_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(items[0]?.id);

  const selectedItem = items.find(i => i.id === selectedId);

  const handleProcess = (id: string) => {
    // 模拟处理完成，移除该项
    const newItems = items.filter(i => i.id !== id);
    setItems(newItems);
    if (newItems.length > 0) {
      setSelectedId(newItems[0].id);
    } else {
      setSelectedId(null);
    }
  };

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#F9FAFB' }}>
        
        {/* LEFT COLUMN: The Pile */}
        <Box sx={{ width: 400, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', bgcolor: 'white' }}>
          
          {/* Header */}
          <Box sx={{ p: 3, pb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
              <InboxIcon size={24} className="text-gray-700" />
              <Typography variant="h6" fontWeight="bold">Inbox</Typography>
              <Chip label={items.length} size="small" sx={{ bgcolor: 'primary.main', color: 'white', height: 20, fontSize: 11, fontWeight: 600 }} />
            </Box>
            <Typography variant="body2" color="text.secondary">Capture thoughts and resources here.</Typography>
          </Box>

          {/* Quick Capture Input */}
          <Box sx={{ px: 3, pb: 3 }}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: '2px 4px', display: 'flex', alignItems: 'center', 
                border: '1px solid', borderColor: 'divider', borderRadius: 2,
                bgcolor: '#F9FAFB'
              }}
            >
              <IconButton sx={{ p: '10px' }}><Plus size={20} className="text-gray-400" /></IconButton>
              <TextField 
                fullWidth 
                placeholder="Paste link or type note..." 
                variant="standard"
                InputProps={{ disableUnderline: true }}
              />
            </Paper>
          </Box>

          {/* List */}
          <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 3 }}>
            {items.length === 0 ? (
              <Box sx={{ textAlign: 'center', mt: 10, opacity: 0.5 }}>
                <CheckCircle2 size={48} className="mx-auto mb-2 text-green-500" />
                <Typography variant="subtitle1">Inbox Zero</Typography>
                <Typography variant="body2">You&apos;re all caught up!</Typography>
              </Box>
            ) : (
              items.map(item => (
                <Paper
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  elevation={0}
                  sx={{ 
                    p: 2, mb: 2, borderRadius: 3, cursor: 'pointer',
                    border: '1px solid', 
                    borderColor: selectedId === item.id ? 'primary.main' : 'divider',
                    bgcolor: selectedId === item.id ? '#F8FAFC' : 'white',
                    transition: 'all 0.2s',
                    '&:hover': { borderColor: selectedId === item.id ? 'primary.main' : 'grey.400', transform: 'translateY(-1px)' }
                  }}
                >
                  <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
                    <Box sx={{ mt: 0.5, color: item.type === 'pdf' ? 'red.500' : item.type === 'audio' ? 'purple.500' : 'blue.500' }}>
                      {item.type === 'pdf' && <FileText size={18} />}
                      {item.type === 'link' && <LinkIcon size={18} />}
                      {item.type === 'audio' && <Mic size={18} />}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle2" fontWeight="600" sx={{ lineHeight: 1.3, mb: 0.5 }}>{item.title}</Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Clock size={12} className="text-gray-400" />
                        <Typography variant="caption" color="text.secondary">{item.added}</Typography>
                      </Box>
                    </Box>
                  </Box>
                </Paper>
              ))
            )}
          </Box>
        </Box>

        {/* RIGHT COLUMN: Triage Station */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 6, bgcolor: '#F9FAFB' }}>
          {selectedItem ? (
            <Box sx={{ maxWidth: 600, width: '100%' }}>
              
              {/* Preview Card (Placeholder) */}
              <Paper elevation={3} sx={{ height: 300, borderRadius: 4, mb: 4, bgcolor: 'grey.100', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed', borderColor: 'grey.300' }}>
                <Typography color="text.secondary">[ Preview Area for {selectedItem.type} ]</Typography>
              </Paper>

              {/* AI Triage Card */}
              <Paper elevation={3} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'primary.main', position: 'relative', overflow: 'hidden' }}>
                {/* AI Badge */}
                <Box sx={{ position: 'absolute', top: 0, left: 0, bgcolor: 'primary.main', px: 1.5, py: 0.5, borderBottomRightRadius: 12 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Sparkles size={12} className="text-yellow-400" />
                    <Typography variant="caption" fontWeight="bold" color="white">AI ANALYSIS</Typography>
                  </Box>
                </Box>

                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1" fontWeight="500" gutterBottom>{selectedItem.summary}</Typography>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mb: 1.5, display: 'block' }}>SUGGESTED ACTION</Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button 
                      variant="contained" 
                      fullWidth
                      onClick={() => handleProcess(selectedItem.id)}
                      startIcon={<FolderInput size={18} />}
                      sx={{ 
                        bgcolor: '#EFF6FF', color: 'primary.main', 
                        border: '1px solid', borderColor: 'primary.main',
                        justifyContent: 'space-between',
                        px: 2, py: 1.5,
                        '&:hover': { bgcolor: '#DBEAFE' }
                      }}
                    >
                      <Box sx={{ textAlign: 'left' }}>
                        <Typography variant="caption" display="block" color="text.secondary">Move to Project</Typography>
                        <Typography variant="body2" fontWeight="bold">{selectedItem.suggestedProject}</Typography>
                      </Box>
                      <ArrowRight size={18} />
                    </Button>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                    <Button fullWidth variant="outlined" color="inherit" startIcon={<MoreHorizontal size={16} />}>Other Project</Button>
                    <Button fullWidth variant="outlined" color="error" startIcon={<Trash2 size={16} />} onClick={() => handleProcess(selectedItem.id)}>Delete</Button>
                  </Box>

                </Box>
              </Paper>

            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', opacity: 0.5 }}>
              <InboxIcon size={64} className="mx-auto mb-4 text-gray-300" />
              <Typography variant="h6" color="text.secondary">Select an item to triage</Typography>
            </Box>
          )}
        </Box>

      </Box>
    </GlobalLayout>
  );
}
