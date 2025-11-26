'use client';

import { useState } from 'react';
import GlobalLayout from '@/components/layout/GlobalLayout';
import { 
  Box, Typography, Button, TextField, InputAdornment, 
  IconButton, Chip, Menu, MenuItem, Paper, Avatar
} from '@mui/material';
import { 
  Search, Plus, Filter, LayoutGrid, List as ListIcon, 
  MoreVertical, FolderOpen, Archive, Clock, FileText, 
  BrainCircuit, MoreHorizontal
} from 'lucide-react';
import Link from 'next/link';

// --- Mock Data ---
const PROJECTS = [
  { id: 1, title: 'Research_v1 (NLP)', desc: 'Deep dive into Transformer architectures and scaling laws.', updated: '2 mins ago', items: 12, status: 'active', coverColor: '#3B82F6' },
  { id: 2, title: 'Bio_Neuro_Study', desc: 'Exploring the intersection of biological synapses and artificial neural networks.', updated: '5 days ago', items: 8, status: 'active', coverColor: '#10B981' },
  { id: 3, title: 'Comp_Arch_2023', desc: 'Notes on parallel processing and hardware efficiency.', updated: '2 weeks ago', items: 24, status: 'archived', coverColor: '#F59E0B' },
  { id: 4, title: 'Generative Agents', desc: 'Simulating human behavior with LLMs.', updated: '1 month ago', items: 5, status: 'active', coverColor: '#8B5CF6' },
  { id: 5, title: 'Quantum Computing Basics', desc: 'Initial literature review.', updated: '3 months ago', items: 2, status: 'active', coverColor: '#EC4899' },
];

export default function ProjectsPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filter, setFilter] = useState<'all' | 'active' | 'archived'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter logic
  const filteredProjects = PROJECTS.filter(p => {
    const matchesSearch = p.title.toLowerCase().includes(searchQuery.toLowerCase()) || p.desc.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filter === 'all' ? true : p.status === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <GlobalLayout>
      <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto', minHeight: '100vh' }}>
        
        {/* 1. Header & Actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
          <Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>Projects</Typography>
            <Typography variant="body1" color="text.secondary">
              Manage your research workspaces and knowledge bases.
            </Typography>
          </Box>
          <Button 
            variant="contained" 
            size="large"
            startIcon={<Plus />}
            sx={{ bgcolor: '#171717', borderRadius: 2, textTransform: 'none', px: 3 }}
          >
            New Project
          </Button>
        </Box>

        {/* 2. Control Bar */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4, gap: 2, flexWrap: 'wrap' }}>
          
          {/* Left: Search & Filter */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
            <TextField
              placeholder="Search projects..."
              size="small"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              sx={{ bgcolor: 'white', width: 320 }}
              InputProps={{
                startAdornment: <InputAdornment position="start"><Search size={18} className="text-gray-400" /></InputAdornment>,
                sx: { borderRadius: 2 }
              }}
            />
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip 
                label="All" 
                onClick={() => setFilter('all')}
                sx={{ 
                  bgcolor: filter === 'all' ? 'primary.main' : 'transparent', 
                  color: filter === 'all' ? 'white' : 'text.secondary',
                  fontWeight: 600,
                  '&:hover': { bgcolor: filter === 'all' ? 'primary.dark' : 'action.hover' }
                }} 
              />
              <Chip 
                label="Active" 
                onClick={() => setFilter('active')}
                sx={{ 
                  bgcolor: filter === 'active' ? 'primary.main' : 'transparent', 
                  color: filter === 'active' ? 'white' : 'text.secondary',
                  fontWeight: 600,
                  '&:hover': { bgcolor: filter === 'active' ? 'primary.dark' : 'action.hover' }
                }} 
              />
              <Chip 
                label="Archived" 
                onClick={() => setFilter('archived')}
                sx={{ 
                  bgcolor: filter === 'archived' ? 'primary.main' : 'transparent', 
                  color: filter === 'archived' ? 'white' : 'text.secondary',
                  fontWeight: 600,
                  '&:hover': { bgcolor: filter === 'archived' ? 'primary.dark' : 'action.hover' }
                }} 
              />
            </Box>
          </Box>

          {/* Right: View Toggle */}
          <Box sx={{ bgcolor: 'white', border: '1px solid', borderColor: 'divider', borderRadius: 2, p: 0.5, display: 'flex' }}>
            <IconButton 
              size="small" 
              onClick={() => setViewMode('grid')}
              sx={{ 
                borderRadius: 1.5, 
                bgcolor: viewMode === 'grid' ? 'grey.100' : 'transparent',
                color: viewMode === 'grid' ? 'text.primary' : 'text.secondary'
              }}
            >
              <LayoutGrid size={18} />
            </IconButton>
            <IconButton 
              size="small" 
              onClick={() => setViewMode('list')}
              sx={{ 
                borderRadius: 1.5, 
                bgcolor: viewMode === 'list' ? 'grey.100' : 'transparent',
                color: viewMode === 'list' ? 'text.primary' : 'text.secondary'
              }}
            >
              <ListIcon size={18} />
            </IconButton>
          </Box>
        </Box>

        {/* 3. Project Grid/List */}
        {viewMode === 'grid' ? (
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 3 }}>
            {filteredProjects.map((project) => (
              <Link href="/studio" key={project.id} style={{ textDecoration: 'none' }}>
                <Paper 
                  elevation={0}
                  sx={{ 
                    border: '1px solid', borderColor: 'divider', borderRadius: 3, overflow: 'hidden',
                    transition: 'all 0.2s', cursor: 'pointer',
                    '&:hover': { transform: 'translateY(-4px)', boxShadow: '0 12px 24px rgba(0,0,0,0.05)', borderColor: 'primary.main' }
                  }}
                >
                  {/* Cover Area */}
                  <Box sx={{ height: 140, bgcolor: project.coverColor, position: 'relative', p: 3, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Box sx={{ bgcolor: 'rgba(255,255,255,0.2)', p: 2, borderRadius: '50%', backdropFilter: 'blur(8px)' }}>
                      <BrainCircuit size={32} color="white" />
                    </Box>
                    {project.status === 'archived' && (
                      <Chip label="Archived" size="small" sx={{ position: 'absolute', top: 12, right: 12, bgcolor: 'rgba(0,0,0,0.4)', color: 'white', backdropFilter: 'blur(4px)' }} />
                    )}
                  </Box>
                  
                  {/* Content Area */}
                  <Box sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="h6" fontWeight="bold" color="text.primary" sx={{ lineHeight: 1.3 }}>{project.title}</Typography>
                      <IconButton size="small" onClick={(e) => { e.preventDefault(); e.stopPropagation(); }} sx={{ mt: -0.5, mr: -1 }}>
                        <MoreVertical size={16} />
                      </IconButton>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3, height: 40, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {project.desc}
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, color: 'text.secondary' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <FileText size={14} />
                          <Typography variant="caption">{project.items}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Clock size={14} />
                          <Typography variant="caption">{project.updated}</Typography>
                        </Box>
                      </Box>
                      <Avatar sx={{ width: 24, height: 24, bgcolor: 'grey.200', fontSize: 10, color: 'text.primary' }}>AL</Avatar>
                    </Box>
                  </Box>
                </Paper>
              </Link>
            ))}
          </Box>
        ) : (
          // LIST VIEW
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {filteredProjects.map((project) => (
              <Link href="/studio" key={project.id} style={{ textDecoration: 'none' }}>
                <Paper 
                  elevation={0}
                  sx={{ 
                    p: 2, display: 'flex', alignItems: 'center', gap: 3,
                    border: '1px solid', borderColor: 'divider', borderRadius: 2,
                    transition: 'all 0.2s', cursor: 'pointer',
                    '&:hover': { bgcolor: 'grey.50', borderColor: 'grey.300' }
                  }}
                >
                  <Box sx={{ width: 40, height: 40, borderRadius: 2, bgcolor: project.coverColor, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <FolderOpen size={20} color="white" />
                  </Box>
                  
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle1" fontWeight="600" color="text.primary">{project.title}</Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>{project.desc}</Typography>
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 4, color: 'text.secondary' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 80 }}>
                      <FileText size={16} />
                      <Typography variant="body2">{project.items} items</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
                      <Clock size={16} />
                      <Typography variant="body2">{project.updated}</Typography>
                    </Box>
                  </Box>

                  <IconButton size="small" onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}>
                    <MoreHorizontal size={18} />
                  </IconButton>
                </Paper>
              </Link>
            ))}
          </Box>
        )}

      </Box>
    </GlobalLayout>
  );
}

