'use client';

import React, { useState } from 'react';
import { Box, Typography, Menu, MenuItem, Button, Chip } from '@mui/material';
import { ChevronDown, Share2 } from 'lucide-react';

const GLOBAL_SIDEBAR_WIDTH = 72;

export interface Project {
    id: string;
    name: string;
    color: string;
    description: string;
}

interface ProjectHeaderProps {
    projects: Project[];
    currentProject: Project;
    onProjectChange: (project: Project) => void;
    isEditable?: boolean;
    lastSaved?: string;
    onShare?: () => void;
}

export default function ProjectHeader({ 
    projects, 
    currentProject, 
    onProjectChange,
    isEditable = true,
    lastSaved = '2 mins ago',
    onShare
}: ProjectHeaderProps) {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const handleOpenMenu = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleCloseMenu = () => {
        setAnchorEl(null);
    };

    const handleSelectProject = (project: Project) => {
        onProjectChange(project);
        handleCloseMenu();
    };

    return (
        <Box
            sx={{
                position: 'fixed',
                top: 0,
                left: GLOBAL_SIDEBAR_WIDTH,
                right: 0,
                height: 56,
                bgcolor: 'background.paper',
                borderBottom: '1px solid',
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 3,
                zIndex: 1100,
            }}
        >
            {/* Left: Project Title with Status */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box>
                    {/* Title Row */}
                    <Box 
                        sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
                    >
                        <Box 
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5, cursor: 'pointer' }}
                            onClick={handleOpenMenu}
                        >
                            <Typography variant="h6" fontWeight={600} sx={{ fontSize: '1rem' }}>
                                {currentProject.name} Whiteboard
                            </Typography>
                            <ChevronDown size={16} color="#9CA3AF" />
                        </Box>

                        {/* Editable Badge */}
                        {isEditable && (
                            <Chip
                                label="EDITABLE"
                                size="small"
                                sx={{
                                    height: 20,
                                    fontSize: '0.6rem',
                                    fontWeight: 600,
                                    letterSpacing: '0.05em',
                                    bgcolor: 'grey.100',
                                    color: 'text.secondary',
                                    '& .MuiChip-label': {
                                        px: 1
                                    }
                                }}
                            />
                        )}
                    </Box>
                    
                    {/* Last Saved Status */}
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                        Last saved {lastSaved}
                    </Typography>
                </Box>

                <Menu
                    anchorEl={anchorEl}
                    open={Boolean(anchorEl)}
                    onClose={handleCloseMenu}
                    PaperProps={{
                        sx: {
                            mt: 1,
                            minWidth: 220,
                            borderRadius: '12px',
                            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                            border: '1px solid',
                            borderColor: 'divider'
                        }
                    }}
                >
                    <Box sx={{ px: 2, py: 1.5 }}>
                        <Typography variant="overline" color="text.secondary" fontWeight={600}>
                            Switch Project
                        </Typography>
                    </Box>
                    {projects.map((project) => (
                        <MenuItem 
                            key={project.id} 
                            onClick={() => handleSelectProject(project)}
                            selected={project.id === currentProject.id}
                            sx={{ py: 1.5, gap: 1.5 }}
                        >
                            <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: project.color }} />
                            <Box>
                                <Typography variant="body2" fontWeight={project.id === currentProject.id ? 600 : 400}>
                                    {project.name}
                                </Typography>
                            </Box>
                        </MenuItem>
                    ))}
                </Menu>
            </Box>

            {/* Right: Share */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {/* Share Button */}
                <Button
                    variant="contained"
                    size="small"
                    startIcon={<Share2 size={14} />}
                    onClick={onShare}
                    sx={{ 
                        textTransform: 'none', 
                        borderRadius: '8px',
                        bgcolor: '#6366F1',
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        px: 2,
                        py: 0.75,
                        boxShadow: 'none',
                        '&:hover': {
                            bgcolor: '#4F46E5',
                            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
                        }
                    }}
                >
                    Share
                </Button>
            </Box>
        </Box>
    );
}

