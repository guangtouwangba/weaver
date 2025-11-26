'use client';

import { useState } from 'react';
import GlobalLayout from '@/components/layout/GlobalLayout';
import { 
  Box, Typography, Paper, InputBase, IconButton, Chip, Button, Divider 
} from '@mui/material';
import { 
  Search, BrainCircuit, Filter, Layers, Hash, FolderOpen, ArrowUpRight
} from 'lucide-react';

// 模拟：跨项目的知识节点
const NODES = [
  { id: 1, label: 'Attention Mechanism', project: 'Research_v1 (NLP)', type: 'concept', x: 400, y: 300, color: '#3B82F6' },
  { id: 2, label: 'Transformer', project: 'Research_v1 (NLP)', type: 'concept', x: 550, y: 250, color: '#3B82F6' },
  { id: 3, label: 'Biological Synapse', project: 'Bio_Neuro_Study', type: 'concept', x: 600, y: 450, color: '#10B981' },
  { id: 4, label: 'Hebbian Learning', project: 'Bio_Neuro_Study', type: 'concept', x: 750, y: 400, color: '#10B981' },
  { id: 5, label: 'Parallel Processing', project: 'Comp_Arch_2023', type: 'concept', x: 200, y: 350, color: '#F59E0B' },
  // 跨项目连接点
  { id: 6, label: 'Neural Plasticity', project: 'Shared Concept', type: 'bridge', x: 500, y: 380, color: '#8B5CF6' }
];

// 模拟连线
const LINKS = [
  { source: 1, target: 2 },
  { source: 3, target: 4 },
  { source: 1, target: 5 }, // NLP <-> Architecture
  { source: 2, target: 6 }, // NLP <-> Bridge
  { source: 3, target: 6 }, // Bio <-> Bridge
];

export default function BrainPage() {
  const [selectedNode, setSelectedNode] = useState<any>(NODES[5]); // Default select the bridge node

  return (
    <GlobalLayout>
      <Box sx={{ height: '100vh', bgcolor: '#F9FAFB', color: 'text.primary', position: 'relative', overflow: 'hidden' }}>
        
        {/* Background Grid (Matching Canvas) */}
        <Box sx={{ 
          position: 'absolute', 
          inset: 0, 
          opacity: 0.4, 
          backgroundImage: 'radial-gradient(#CBD5E1 1.5px, transparent 1.5px)', 
          backgroundSize: '24px 24px' 
        }} />

        {/* 1. Header / Search Overlay */}
        <Box sx={{ position: 'absolute', top: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 10, width: '100%', maxWidth: 600 }}>
          <Paper 
            elevation={3}
            sx={{ 
              p: '2px 4px', display: 'flex', alignItems: 'center', 
              bgcolor: 'background.paper', 
              border: '1px solid', borderColor: 'divider',
              borderRadius: 24 
            }}
          >
            <IconButton sx={{ p: '10px', color: 'text.secondary' }}><Search size={20} /></IconButton>
            <InputBase
              sx={{ ml: 1, flex: 1, color: 'text.primary' }}
              placeholder="Search across all 12 projects..."
            />
            <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
            <IconButton sx={{ p: '10px', color: 'text.secondary' }}><Filter size={20} /></IconButton>
          </Paper>
          
          {/* Stats / Filters */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 2 }}>
            <Chip 
              icon={<Layers size={14} />} 
              label="12 Projects" 
              sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', fontWeight: 500 }} 
            />
            <Chip 
              icon={<Hash size={14} />} 
              label="1,240 Concepts" 
              sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', fontWeight: 500 }} 
            />
            <Chip 
              icon={<BrainCircuit size={14} className="text-purple-500" />} 
              label="85 Connections Found" 
              sx={{ bgcolor: 'purple.50', color: 'purple.700', border: '1px solid', borderColor: 'purple.100', fontWeight: 600 }} 
            />
          </Box>
        </Box>

        {/* 2. Visualization Area (Mock SVG Graph) */}
        <svg style={{ width: '100%', height: '100%' }}>
          {/* Links */}
          {LINKS.map((link, i) => {
            const s = NODES.find(n => n.id === link.source)!;
            const t = NODES.find(n => n.id === link.target)!;
            return (
              <line 
                key={i} 
                x1={s.x} y1={s.y} x2={t.x} y2={t.y} 
                stroke="#CBD5E1" 
                strokeWidth="2" 
                strokeDasharray="4 4"
              />
            );
          })}

          {/* Nodes */}
          {NODES.map((node) => (
            <g 
              key={node.id} 
              onClick={() => setSelectedNode(node)} 
              style={{ cursor: 'pointer' }}
              transform={`translate(${node.x}, ${node.y})`}
            >
              {/* Glow effect for selected or bridge nodes */}
              {(selectedNode?.id === node.id || node.type === 'bridge') && (
                 <circle r="30" fill={node.color} opacity="0.15" />
              )}
              
              {/* Node Circle */}
              <circle r="8" fill={node.color} stroke="white" strokeWidth="2" />
              
              {/* Label Background for readability */}
              <rect x="12" y="-8" width={node.label.length * 7} height="20" rx="4" fill="rgba(255,255,255,0.8)" />
              <text 
                x="15" y="5" 
                fill="#1e293b" 
                fontSize="12" 
                fontWeight="600"
                style={{ pointerEvents: 'none' }}
              >
                {node.label}
              </text>
            </g>
          ))}
        </svg>

        {/* 3. Insight Panel (Right Side, Contextual) */}
        {selectedNode && (
          <Paper 
            elevation={3}
            sx={{ 
              position: 'absolute', top: 160, right: 24, width: 320, 
              maxHeight: 'calc(100vh - 200px)',
              overflowY: 'auto',
              bgcolor: 'background.paper',
              border: '1px solid', borderColor: 'divider', borderRadius: 3,
              p: 3,
              zIndex: 20
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
              <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: selectedNode.color }} />
              <Typography variant="subtitle1" fontWeight="bold" color="text.primary">{selectedNode.label}</Typography>
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>APPEARS IN PROJECT</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3, p: 1.5, borderRadius: 2, bgcolor: 'grey.50', border: '1px solid', borderColor: 'divider' }}>
              <FolderOpen size={16} className="text-blue-500" />
              <Typography variant="body2" fontWeight="500">{selectedNode.project}</Typography>
            </Box>

            <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mb: 1, display: 'block' }}>AI INSIGHT</Typography>
            <Typography variant="body2" sx={{ lineHeight: 1.6, color: 'text.secondary', mb: 2 }}>
              This concept links <span className="text-blue-600 font-medium">NLP</span> and <span className="text-green-600 font-medium">Biology</span>.
              <br/><br/>
              It suggests that <b>Attention</b> might share mechanics with <b>Synaptic Plasticity</b>.
            </Typography>

            <Button 
              fullWidth variant="outlined" 
              endIcon={<ArrowUpRight size={16} />}
              sx={{ 
                color: 'text.primary', 
                borderColor: 'divider', 
                textTransform: 'none',
                '&:hover': { bgcolor: 'grey.50', borderColor: 'grey.400' } 
              }}
            >
              Open Project
            </Button>
          </Paper>
        )}

        {/* Legend */}
        <Box sx={{ position: 'absolute', bottom: 24, left: 24, display: 'flex', flexDirection: 'column', gap: 1 }}>
           <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Box sx={{ borderRadius: '50%', bgcolor: '#3B82F6', width: 8, height: 8 }} /><Typography variant="caption" color="text.secondary">NLP Project</Typography></Box>
           <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Box sx={{ borderRadius: '50%', bgcolor: '#10B981', width: 8, height: 8 }} /><Typography variant="caption" color="text.secondary">Biology Project</Typography></Box>
           <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Box sx={{ borderRadius: '50%', bgcolor: '#F59E0B', width: 8, height: 8 }} /><Typography variant="caption" color="text.secondary">Arch Project</Typography></Box>
        </Box>

      </Box>
    </GlobalLayout>
  );
}
