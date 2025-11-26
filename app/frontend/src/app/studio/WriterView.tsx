'use client';

import { useState } from 'react';
import { 
  Box, Typography, Paper, IconButton, TextField, Chip, Button, Divider, Avatar, Tooltip 
} from '@mui/material';
import { 
  Bold, Italic, List, ListOrdered, Image as ImageIcon, MoreHorizontal, 
  ChevronRight, Search, GripVertical, Wand2, Sparkles, ArrowLeft, Copy, Check
} from 'lucide-react';

// --- Types & Mock Data ---

interface Asset {
  id: string;
  type: 'card' | 'highlight' | 'note';
  title: string;
  content: string;
  source: string;
  tags: string[];
}

const MOCK_ASSETS: Asset[] = [
  { id: 'a1', type: 'card', title: 'RNN Limitations', content: 'Recurrent Neural Networks differ from Feedforward Networks because they have a "memory" (hidden state) that captures information about what has been calculated so far.', source: 'Deep Learning Book', tags: ['#rnn', '#memory'] },
  { id: 'a2', type: 'highlight', title: 'Parallelization Issue', content: 'This sequential nature precludes parallelization within training examples, which becomes critical at longer sequence lengths.', source: 'Attention Is All You Need', tags: ['#performance', '#transformer'] },
  { id: 'a3', type: 'card', title: 'Self-Attention Definition', content: 'Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence.', source: 'Attention Is All You Need', tags: ['#attention', '#core-concept'] },
  { id: 'a4', type: 'note', title: 'My Thought on Vanishing Gradient', content: 'LSTMs solved this partially, but the path length is still O(n). Transformers reduce this to O(1).', source: 'Personal Note', tags: ['#insight'] },
];

export default function WriterView() {
  const [content, setContent] = useState<string>(`# The Evolution of Sequence Modeling\n\nBefore the advent of Transformers, the dominant architecture for sequence transduction models was based on complex recurrent or convolutional neural networks.\n\n`);
  const [assets, setAssets] = useState<Asset[]>(MOCK_ASSETS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [aiDraft, setAiDraft] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  // Filter assets
  const filteredAssets = assets.filter(a => 
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    a.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.tags.some(t => t.includes(searchQuery.toLowerCase()))
  );

  const handleDragStart = (e: React.DragEvent, asset: Asset) => {
    e.dataTransfer.setData('text/plain', `> ${asset.content} \n> — *${asset.source}*`);
  };

  const toggleAssetSelection = (id: string) => {
    setSelectedAssets(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleMixConcepts = () => {
    if (selectedAssets.length === 0) return;
    setIsGenerating(true);
    setAiDraft(null);
    
    // Simulate AI Generation
    setTimeout(() => {
      const selectedTitles = assets.filter(a => selectedAssets.includes(a.id)).map(a => a.title).join(', ');
      setAiDraft(`Here is a synthesized draft connecting **${selectedTitles}**:\n\nWhile RNNs rely on a hidden state to maintain memory (making them sequential and hard to parallelize), Self-Attention mechanisms allow the model to look at all positions of the sequence at once. This shifts the complexity from temporal dependency to spatial relationship, enabling massive parallelization.`);
      setIsGenerating(false);
    }, 1500);
  };

  const insertDraft = () => {
    if (aiDraft) {
      setContent(prev => prev + '\n\n' + aiDraft);
      setAiDraft(null);
      setSelectedAssets([]);
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100%', bgcolor: '#F9FAFB' }}>
      
      {/* --- LEFT COLUMN: ASSET TRAY (25%) --- */}
      <Box sx={{ width: 300, borderRight: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', bgcolor: 'white' }}>
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Copy size={16} /> Asset Tray
          </Typography>
          <TextField 
            fullWidth 
            placeholder="Search insights..." 
            size="small"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <Search size={14} className="text-gray-400 mr-2" />,
              sx: { fontSize: 13, bgcolor: '#F3F4F6', '& fieldset': { border: 'none' } }
            }}
          />
        </Box>
        
        <Box sx={{ flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {filteredAssets.map(asset => {
            const isSelected = selectedAssets.includes(asset.id);
            return (
              <Paper 
                key={asset.id}
                draggable
                onDragStart={(e) => handleDragStart(e, asset)}
                onClick={() => toggleAssetSelection(asset.id)}
                elevation={0}
                sx={{ 
                  p: 1.5, border: '1px solid', 
                  borderColor: isSelected ? 'primary.main' : 'divider',
                  bgcolor: isSelected ? 'primary.50' : 'white',
                  borderRadius: 2, cursor: 'grab', transition: 'all 0.2s',
                  '&:hover': { borderColor: 'primary.main', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' },
                  position: 'relative'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Chip 
                    label={asset.type} 
                    size="small" 
                    sx={{ height: 16, fontSize: 9, bgcolor: 'grey.100', textTransform: 'uppercase', fontWeight: 700, color: 'text.secondary' }} 
                  />
                  {isSelected && <Check size={14} className="text-blue-600" />}
                </Box>
                <Typography variant="subtitle2" fontWeight="600" sx={{ lineHeight: 1.2, mb: 0.5 }}>{asset.title}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: 1.5 }}>
                  {asset.content}
                </Typography>
                <Box sx={{ mt: 1.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {asset.tags.map(tag => (
                    <Typography key={tag} variant="caption" sx={{ color: 'primary.main', bgcolor: 'primary.50', px: 0.5, borderRadius: 0.5 }}>{tag}</Typography>
                  ))}
                </Box>
              </Paper>
            );
          })}
        </Box>
      </Box>

      {/* --- CENTER COLUMN: EDITOR (50%) --- */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: 'white' }}>
        {/* Toolbar */}
        <Box sx={{ height: 48, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', px: 2, gap: 1 }}>
          <IconButton size="small"><Bold size={16} /></IconButton>
          <IconButton size="small"><Italic size={16} /></IconButton>
          <Divider orientation="vertical" flexItem sx={{ mx: 1, my: 1.5 }} />
          <IconButton size="small"><List size={16} /></IconButton>
          <IconButton size="small"><ListOrdered size={16} /></IconButton>
          <Box sx={{ flex: 1 }} />
          <Typography variant="caption" color="text.disabled">Markdown Supported</Typography>
        </Box>

        {/* Editor Area */}
        <Box sx={{ flex: 1, p: 6, overflowY: 'auto' }}>
          <Box sx={{ maxWidth: 700, mx: 'auto', minHeight: '100%' }}>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Start writing..."
              style={{
                width: '100%', height: '100%', border: 'none', outline: 'none', resize: 'none',
                fontSize: '16px', lineHeight: '1.8', fontFamily: 'ui-serif, Georgia, serif', color: '#1F2937'
              }}
            />
          </Box>
        </Box>
      </Box>

      {/* --- RIGHT COLUMN: CONCEPT MIXER (25%) --- */}
      <Box sx={{ width: 320, borderLeft: '1px solid', borderColor: 'divider', display: 'flex', flexDirection: 'column', bgcolor: '#F9FAFB' }}>
        <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle2" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Sparkles size={16} className="text-purple-500" /> Concept Mixer
          </Typography>
        </Box>

        <Box sx={{ p: 3, flex: 1, overflowY: 'auto' }}>
          {selectedAssets.length > 0 ? (
            <Box>
              <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                SELECTED INGREDIENTS ({selectedAssets.length})
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                {assets.filter(a => selectedAssets.includes(a.id)).map(a => (
                  <Paper key={a.id} elevation={0} sx={{ p: 1, px: 1.5, borderRadius: 4, border: '1px solid', borderColor: 'divider', bgcolor: 'white', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="caption" fontWeight="500" noWrap sx={{ maxWidth: 180 }}>{a.title}</Typography>
                    <IconButton size="small" onClick={() => toggleAssetSelection(a.id)} sx={{ p: 0.5 }}><Check size={12} /></IconButton>
                  </Paper>
                ))}
              </Box>

              <Button 
                fullWidth 
                variant="contained" 
                onClick={handleMixConcepts}
                disabled={isGenerating}
                startIcon={isGenerating ? <Sparkles className="animate-spin" size={16} /> : <Wand2 size={16} />}
                sx={{ 
                  bgcolor: '#171717', color: 'white', borderRadius: 2, mb: 3,
                  textTransform: 'none', py: 1.5, fontWeight: 600,
                  '&:hover': { bgcolor: 'black' }
                }}
              >
                {isGenerating ? 'Synthesizing...' : 'Mix & Generate Draft'}
              </Button>

              {aiDraft && (
                <Paper sx={{ p: 2, bgcolor: 'purple.50', border: '1px solid', borderColor: 'purple.100', borderRadius: 2 }}>
                   <Typography variant="caption" fontWeight="bold" color="purple.700" sx={{ mb: 1, display: 'block' }}>AI SUGGESTION</Typography>
                   <Typography variant="body2" sx={{ fontSize: 13, lineHeight: 1.6, mb: 2, color: 'purple.900' }}>
                     {aiDraft}
                   </Typography>
                   <Button 
                     size="small" 
                     variant="outlined" 
                     color="secondary" 
                     fullWidth
                     onClick={insertDraft}
                     sx={{ bgcolor: 'white' }}
                   >
                     Insert to Editor
                   </Button>
                </Paper>
              )}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', mt: 8, opacity: 0.6 }}>
              <Box sx={{ width: 64, height: 64, borderRadius: '50%', bgcolor: 'grey.200', display: 'flex', alignItems: 'center', justifyContent: 'center', mx: 'auto', mb: 2 }}>
                <GripVertical size={24} className="text-gray-400" />
              </Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Select cards from the Asset Tray<br/>to start mixing concepts.
              </Typography>
            </Box>
          )}
        </Box>
      </Box>

    </Box>
  );
}

