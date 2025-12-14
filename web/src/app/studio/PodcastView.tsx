import React from 'react';
import { Box, Typography, IconButton, Slider, Avatar, Paper } from "@mui/material";
import { Play, SkipBack, SkipForward, Download, Share2 } from "lucide-react";

// 模拟数据：Canvas 上的节点被转化为了线性的对话脚本
const SCRIPT_DATA = [
  {
    id: 1,
    role: "host",
    name: "Alice (Host)",
    text: "Welcome back to the Deep Dive. Today we're looking at the 'Attention Is All You Need' paper. It seems like a cornerstone for modern AI, doesn't it?",
    timestamp: "00:00"
  },
  {
    id: 2,
    role: "expert",
    name: "Bob (AI)",
    text: "Absolutely. Before this paper, we relied heavily on RNNs and LSTMs. But this introduced the 'Transformer' architecture, which changed everything by allowing parallel processing.",
    timestamp: "00:15",
    relatedNodeId: "node-1" // 关联到 Canvas 上的 "Source PDF" 节点
  },
  {
    id: 3,
    role: "host",
    name: "Alice (Host)",
    text: "So, what exactly is 'Self-Attention'? That seems to be the key concept here.",
    timestamp: "00:32"
  },
  {
    id: 4,
    role: "expert",
    name: "Bob (AI)",
    text: "Think of it as the model's ability to weigh the importance of different words in a sentence relative to each other. It's like reading a sentence and knowing which words link together to form meaning, regardless of how far apart they are.",
    timestamp: "00:45",
    relatedNodeId: "node-2", // 关联到 Canvas 上的 "Self-Attention" 节点
    isActive: true // 当前正在播放
  }
];

export default function PodcastView() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: '#F9FAFB' }}>
      
      {/* 1. Top Player Bar (Sticky) */}
      <Paper elevation={0} sx={{ 
        p: 2, borderBottom: '1px solid', borderColor: 'divider', 
        display: 'flex', alignItems: 'center', gap: 3, bgcolor: '#fff' 
      }}>
        <IconButton sx={{ bgcolor: '#171717', color: '#fff', '&:hover': { bgcolor: '#000' } }}>
          <Play size={20} fill="currentColor" />
        </IconButton>
        
        <Box sx={{ flex: 1 }}>
          <Typography variant="caption" color="text.secondary" fontWeight="600">PLAYING • 00:45 / 12:30</Typography>
          <Typography variant="subtitle2" fontWeight="bold">Understanding Transformers</Typography>
          <Slider size="small" defaultValue={30} sx={{ color: '#171717', p: 1 }} />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
           <IconButton size="small"><Download size={18} /></IconButton>
           <IconButton size="small"><Share2 size={18} /></IconButton>
        </Box>
      </Paper>

      {/* 2. Script Stream (Scrollable) */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 4 }}>
        <Box sx={{ maxWidth: 600, mx: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
          {SCRIPT_DATA.map((item) => (
            <Box key={item.id} sx={{ 
              display: 'flex', 
              gap: 2,
              opacity: item.isActive ? 1 : 0.6, // 非活跃段落稍微变淡，聚焦当前
              transition: 'opacity 0.3s ease'
            }}>
              <Avatar 
                sx={{ 
                  width: 32, height: 32, 
                  bgcolor: item.role === 'host' ? 'grey.200' : 'primary.main',
                  color: item.role === 'host' ? 'text.primary' : '#fff',
                  fontSize: 12
                }}
              >
                {item.role === 'host' ? 'A' : 'AI'}
              </Avatar>
              
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography variant="caption" fontWeight="bold" color="text.secondary">
                    {item.name}
                  </Typography>
                  <Typography variant="caption" color="text.disabled">
                    {item.timestamp}
                  </Typography>
                </Box>
                
                <Typography variant="body1" sx={{ lineHeight: 1.6, fontWeight: item.isActive ? 500 : 400 }}>
                  {item.text}
                </Typography>
                
                {/* Source Link Indicator */}
                {item.relatedNodeId && (
                   <Box sx={{ mt: 1, display: 'inline-flex', alignItems: 'center', gap: 0.5, px: 1, py: 0.5, bgcolor: 'grey.100', borderRadius: 1, cursor: 'pointer' }}>
                     <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'blue.500' }} />
                     <Typography variant="caption" color="text.secondary">Linked to Concept</Typography>
                   </Box>
                )}
              </Box>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
}

