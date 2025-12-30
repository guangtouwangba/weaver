'use client';

import React from 'react';
import { Box, Typography, IconButton, Slider, Avatar, Paper, Chip } from "@mui/material";
import { Play, Download, Share2, Headphones } from "lucide-react";

// Mock data: Conversation script based on multiple sources
const SCRIPT_DATA = [
  {
    id: 1,
    role: "host",
    name: "Alice (Host)",
    text: "Welcome back to the Deep Dive. Today we're looking at the research findings you just synthesized from multiple sources. It seems like a cornerstone for the Q1 strategy, doesn't it?",
    timestamp: "00:00",
    sourceId: 'src-1'
  },
  {
    id: 2,
    role: "expert",
    name: "Bob (AI Expert)",
    text: "Absolutely. By combining the market survey with the technical roadmap, we get a much clearer picture of the parallel processing needs for next year.",
    timestamp: "00:15",
    isActive: true,
    sourceId: 'src-2'
  },
  {
    id: 3,
    role: "host",
    name: "Alice (Host)",
    text: "Source A mentioned a potential bottleneck in latency. How does that sync with the results from the user interviews?",
    timestamp: "00:32",
    sourceId: 'src-1'
  },
  {
    id: 4,
    role: "expert",
    name: "Bob (AI Expert)",
    text: "That's the friction point. While the users want more speed, the interviews suggest they aren't willing to sacrifice data privacy, which adds to that latency.",
    timestamp: "00:45",
    sourceId: 'src-3'
  }
];

export default function PodcastView({ fileName, sourceNames = [] }: { fileName: string; sourceNames?: string[] }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: '#F9FAFB' }}>
      
      {/* 1. Top Player Bar */}
      <Paper elevation={0} sx={{ 
        p: 2, borderBottom: '1px solid', borderColor: 'divider', 
        display: 'flex', alignItems: 'center', gap: 3, bgcolor: '#fff' 
      }}>
        <IconButton sx={{ bgcolor: '#171717', color: '#fff', '&:hover': { bgcolor: '#000' } }}>
          <Play size={20} fill="currentColor" />
        </IconButton>
        
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip icon={<Headphones size={12} />} label={sourceNames.length > 1 ? "MULTI-SOURCE SUMMARY" : "AUDIO SUMMARY"} size="small" sx={{ height: 20, fontSize: '10px', fontWeight: 700, bgcolor: sourceNames.length > 1 ? 'primary.100' : 'grey.100', color: sourceNames.length > 1 ? 'primary.main' : 'text.primary' }} />
            <Typography variant="caption" color="text.secondary" fontWeight="600">00:15 / 12:30</Typography>
          </Box>
          <Typography variant="subtitle2" fontWeight="bold" noWrap>{fileName}</Typography>
          <Slider size="small" defaultValue={15} sx={{ color: '#171717', p: 0.5 }} />
        </Box>

        <Box sx={{ display: 'flex', gap: 0.5 }}>
           <IconButton size="small"><Download size={16} /></IconButton>
           <IconButton size="small"><Share2 size={16} /></IconButton>
        </Box>
      </Paper>

      {/* 2. Source Legend for Multi-Source */}
      {sourceNames.length > 1 && (
        <Box sx={{ px: 3, py: 1.5, borderBottom: '1px solid', borderColor: 'divider', bgcolor: '#fff', display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="caption" sx={{ width: '100%', mb: 0.5, fontWeight: 700, color: 'text.disabled' }}>SOURCES USED IN THIS PODCAST:</Typography>
          {sourceNames.map((name, i) => (
            <Chip key={i} label={name} size="small" variant="outlined" sx={{ fontSize: '10px', height: 22 }} />
          ))}
        </Box>
      )}

      {/* 3. Script Stream */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {SCRIPT_DATA.map((item) => (
            <Box key={item.id} sx={{ 
              display: 'flex', 
              gap: 2,
              opacity: item.isActive ? 1 : 0.6,
              transition: 'all 0.3s ease',
              borderLeft: item.isActive ? '3px solid' : '3px solid transparent',
              borderColor: 'primary.main',
              pl: 1
            }}>
              <Avatar 
                sx={{ 
                  width: 28, height: 28, 
                  bgcolor: item.role === 'host' ? 'grey.200' : 'primary.main',
                  color: item.role === 'host' ? 'text.primary' : '#fff',
                  fontSize: 10,
                  fontWeight: 700
                }}
              >
                {item.role === 'host' ? 'A' : 'AI'}
              </Avatar>
              
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="caption" fontWeight="bold" color="text.secondary">
                      {item.name}
                    </Typography>
                    <Typography variant="caption" color="text.disabled">
                      {item.timestamp}
                    </Typography>
                  </Box>
                  {sourceNames.length > 1 && (
                    <Typography variant="caption" sx={{ color: 'primary.main', fontWeight: 600, fontSize: '9px', textTransform: 'uppercase' }}>
                      Ref: {sourceNames[parseInt(item.sourceId.split('-')[1]) % sourceNames.length]}
                    </Typography>
                  )}
                </Box>
                
                <Typography variant="body2" sx={{ lineHeight: 1.6, fontWeight: item.isActive ? 500 : 400 }}>
                  {item.text}
                </Typography>
                
                {item.isActive && (
                   <Box sx={{ mt: 1, display: 'inline-flex', alignItems: 'center', gap: 0.5, px: 1, py: 0.3, bgcolor: 'primary.50', borderRadius: 1 }}>
                     <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main', animation: 'pulse 1s infinite' }} />
                     <Typography variant="caption" color="primary.main" fontWeight={600}>Currently Reading</Typography>
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









