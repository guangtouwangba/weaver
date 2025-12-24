'use client';

import React, { useState } from 'react';
import { Box, IconButton, Paper, Typography, Tooltip, Divider, Button } from '@mui/material';
import { 
    ChevronLeft, 
    ChevronRight, 
    Plus, 
    Eye, 
    MoreHorizontal,
    Sparkles, 
    Mic, 
    FileText, 
    CreditCard, 
    Folder,
    Filter
} from 'lucide-react';

const SIDEBAR_WIDTH = 280;
const GLOBAL_SIDEBAR_WIDTH = 72;
const HEADER_HEIGHT = 56;

// Types for generated content
export interface GeneratedContent {
    id: string;
    name: string;
    type: 'mindmap' | 'podcast' | 'summary' | 'flashcards';
    isActive?: boolean;
    isOnCanvas?: boolean;
    duration?: string;      // For podcasts
    pageCount?: number;     // For summaries
    cardCount?: number;     // For flashcards
}

export interface SourceFile {
    id: string;
    name: string;
    type: 'folder' | 'file';
    fileType?: string;
}

interface SidebarProps {
    onToggle?: (isOpen: boolean) => void;
    onReview?: (file: { id: string; name: string; type: string }) => void;
    projectColor?: string;
    projectId?: string;
    onDragStateChange?: (isDragging: boolean) => void;
    files?: any[];
    onFilesChange?: (files: any[]) => void;
    generatedContent?: GeneratedContent[];
    sourceFiles?: SourceFile[];
    onContentDrag?: (content: GeneratedContent) => void;
    onImportSource?: () => void;
}

// Icon component for generated content types
const getContentIcon = (type: string, isActive?: boolean) => {
    const iconProps = { size: 18 };
    
    switch (type) {
        case 'mindmap':
            return (
                <Box sx={{ 
                    p: 0.75, 
                    borderRadius: '8px', 
                    bgcolor: isActive ? '#6366F1' : '#EEF2FF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Sparkles {...iconProps} color={isActive ? 'white' : '#6366F1'} />
                </Box>
            );
        case 'podcast':
            return (
                <Box sx={{ 
                    p: 0.75, 
                    borderRadius: '8px', 
                    bgcolor: '#F3E8FF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Mic {...iconProps} color="#8B5CF6" />
                </Box>
            );
        case 'summary':
            return (
                <Box sx={{ 
                    p: 0.75, 
                    borderRadius: '8px', 
                    bgcolor: '#DBEAFE',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <FileText {...iconProps} color="#3B82F6" />
                </Box>
            );
        case 'flashcards':
            return (
                <Box sx={{ 
                    p: 0.75, 
                    borderRadius: '8px', 
                    bgcolor: '#FEF3C7',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <CreditCard {...iconProps} color="#F59E0B" />
                </Box>
            );
        default:
            return (
                <Box sx={{ 
                    p: 0.75, 
                    borderRadius: '8px', 
                    bgcolor: '#F3F4F6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <FileText {...iconProps} color="#6B7280" />
                </Box>
            );
    }
};

// Get type label and metadata
const getTypeLabel = (content: GeneratedContent) => {
    switch (content.type) {
        case 'mindmap':
            return content.isActive ? 'Mind Map • Active' : 'Mind Map';
        case 'podcast':
            return `Podcast • ${content.duration || '0m'}`;
        case 'summary':
            return `Summary • ${content.pageCount || 0} pgs`;
        case 'flashcards':
            return `${content.cardCount || 0} Cards`;
        default:
            return content.type;
    }
};

// Default mock data
const DEFAULT_GENERATED_CONTENT: GeneratedContent[] = [
    { id: 'gc1', name: 'Q1 Market Overview', type: 'mindmap', isActive: true, isOnCanvas: true },
    { id: 'gc2', name: 'Key Insights Q1', type: 'podcast', duration: '12m' },
    { id: 'gc3', name: 'Executive Brief', type: 'summary', pageCount: 2 },
    { id: 'gc4', name: 'Market Terms', type: 'flashcards', cardCount: 24 },
];

const DEFAULT_SOURCE_FILES: SourceFile[] = [
    { id: 'sf1', name: 'Q1_Raw_Data_Folder', type: 'folder' },
];

export default function Sidebar({ 
    onToggle, 
    onReview, 
    projectColor = '#6366F1', 
    projectId, 
    onDragStateChange, 
    files = [], 
    onFilesChange,
    generatedContent = DEFAULT_GENERATED_CONTENT,
    sourceFiles = DEFAULT_SOURCE_FILES,
    onContentDrag,
    onImportSource
}: SidebarProps) {
    const [isOpen, setIsOpen] = useState(true);
    
    const handleToggle = () => {
        const nextState = !isOpen;
        setIsOpen(nextState);
        if (onToggle) onToggle(nextState);
    };

    const handleDragStart = (e: React.DragEvent, content: GeneratedContent) => {
        onDragStateChange?.(true);
        e.dataTransfer.setData('application/json', JSON.stringify({
            ...content,
            sourceType: 'generated'
        }));
        e.dataTransfer.effectAllowed = 'move';
    };

    const handleFileDragStart = (e: React.DragEvent, file: SourceFile) => {
        onDragStateChange?.(true);
        e.dataTransfer.setData('application/json', JSON.stringify({
            ...file,
            sourceType: 'file'
        }));
        e.dataTransfer.effectAllowed = 'move';
    };

    const handleDragEnd = () => {
        onDragStateChange?.(false);
    };

    return (
        <Box
            sx={{
                position: 'fixed',
                left: GLOBAL_SIDEBAR_WIDTH,
                top: HEADER_HEIGHT,
                height: `calc(100vh - ${HEADER_HEIGHT}px)`,
                width: isOpen ? SIDEBAR_WIDTH : 0,
                transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                zIndex: 1050,
                backgroundColor: 'background.paper',
                borderRight: isOpen ? '1px solid' : 'none',
                borderColor: 'divider',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'visible',
            }}
        >
            {/* Toggle Button */}
            <IconButton
                onClick={handleToggle}
                sx={{
                    position: 'absolute',
                    right: -20,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    width: 40,
                    height: 40,
                    backgroundColor: 'background.paper',
                    border: '1px solid',
                    borderColor: 'divider',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                    '&:hover': {
                        backgroundColor: 'grey.100',
                    },
                    zIndex: 1101,
                }}
            >
                {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
            </IconButton>

            {/* Sidebar Content */}
            {isOpen && (
                <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    {/* Header */}
                    <Box sx={{ 
                        p: 2.5, 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        borderBottom: '1px solid',
                        borderColor: 'divider'
                    }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'text.primary', letterSpacing: '-0.01em' }}>
                            LIBRARY
                        </Typography>
                        <IconButton size="small" sx={{ color: 'text.secondary' }}>
                            <Filter size={16} />
                        </IconButton>
                    </Box>

                    {/* Import Source Button */}
                    <Box sx={{ px: 2.5, py: 2 }}>
                        <Button
                            fullWidth
                            variant="outlined"
                            startIcon={<Plus size={18} />}
                            onClick={onImportSource}
                            sx={{
                                borderStyle: 'dashed',
                                borderColor: 'divider',
                                color: 'text.secondary',
                                py: 1.5,
                                borderRadius: '12px',
                                textTransform: 'none',
                                fontWeight: 500,
                                '&:hover': {
                                    borderColor: projectColor,
                                    color: projectColor,
                                    bgcolor: `${projectColor}08`
                                }
                            }}
                        >
                            Import Source
                        </Button>
                    </Box>

                    {/* Scrollable Content Area */}
                    <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 2.5 }}>
                        {/* Generated Content Section */}
                        <Box sx={{ mb: 3 }}>
                            <Box sx={{ 
                                display: 'flex', 
                                alignItems: 'center', 
                                justifyContent: 'space-between',
                                mb: 1.5
                            }}>
                                <Typography 
                                    variant="caption" 
                                    sx={{ 
                                        fontWeight: 600, 
                                        color: 'text.secondary',
                                        letterSpacing: '0.05em',
                                        fontSize: '0.7rem'
                                    }}
                                >
                                    GENERATED CONTENT
                                </Typography>
                                <IconButton size="small" sx={{ p: 0.5 }}>
                                    <MoreHorizontal size={14} color="#9CA3AF" />
                                </IconButton>
                            </Box>

                            {/* Content Items */}
                            {generatedContent.map((content) => (
                                <Box
                                    key={content.id}
                                    draggable
                                    onDragStart={(e) => handleDragStart(e, content)}
                                    onDragEnd={handleDragEnd}
                                    sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        p: 1.5,
                                        mb: 0.75,
                                        borderRadius: '10px',
                                        backgroundColor: content.isOnCanvas ? `${projectColor}08` : 'transparent',
                                        border: content.isOnCanvas ? `1px solid ${projectColor}22` : '1px solid transparent',
                                        cursor: 'grab',
                                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                        '&:hover': { 
                                            backgroundColor: content.isOnCanvas ? `${projectColor}12` : 'grey.50',
                                            transform: 'translateX(2px)',
                                        },
                                        '&:active': { cursor: 'grabbing' }
                                    }}
                                >
                                    {/* Icon */}
                                    <Box sx={{ mr: 1.5 }}>
                                        {getContentIcon(content.type, content.isActive)}
                                    </Box>
                                    
                                    {/* Text Content */}
                                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                                        <Typography 
                                            variant="body2" 
                                            noWrap 
                                            sx={{ 
                                                fontWeight: 500,
                                                color: 'text.primary',
                                                fontSize: '0.875rem'
                                            }}
                                        >
                                            {content.name}
                                        </Typography>
                                        <Typography 
                                            variant="caption" 
                                            sx={{ 
                                                color: content.isActive ? projectColor : 'text.secondary',
                                                fontWeight: content.isActive ? 500 : 400,
                                                fontSize: '0.75rem'
                                            }}
                                        >
                                            {getTypeLabel(content)}
                                        </Typography>
                                    </Box>

                                    {/* On Canvas Indicator */}
                                    {content.isOnCanvas && (
                                        <Tooltip title="On Canvas" placement="left">
                                            <Box sx={{ 
                                                color: projectColor,
                                                display: 'flex',
                                                alignItems: 'center'
                                            }}>
                                                <Eye size={14} />
                                            </Box>
                                        </Tooltip>
                                    )}
                                </Box>
                            ))}
                        </Box>

                        {/* Source Files Section */}
                        <Box>
                            <Typography 
                                variant="caption" 
                                sx={{ 
                                    fontWeight: 600, 
                                    color: 'text.secondary',
                                    letterSpacing: '0.05em',
                                    fontSize: '0.7rem',
                                    display: 'block',
                                    mb: 1.5
                                }}
                            >
                                SOURCE FILES
                            </Typography>

                            {/* Source File Items */}
                            {sourceFiles.map((file) => (
                                <Box
                                    key={file.id}
                                    draggable
                                    onDragStart={(e) => handleFileDragStart(e, file)}
                                    onDragEnd={handleDragEnd}
                                    sx={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        p: 1.5,
                                        mb: 0.75,
                                        borderRadius: '10px',
                                        cursor: 'grab',
                                        transition: 'all 0.2s',
                                        '&:hover': { 
                                            backgroundColor: 'grey.50',
                                            transform: 'translateX(2px)',
                                        },
                                        '&:active': { cursor: 'grabbing' }
                                    }}
                                >
                                    <Box sx={{ 
                                        mr: 1.5, 
                                        color: 'text.secondary',
                                        display: 'flex',
                                        alignItems: 'center'
                                    }}>
                                        <Folder size={18} />
                                    </Box>
                                    <Typography 
                                        variant="body2" 
                                        noWrap 
                                        sx={{ 
                                            fontWeight: 400,
                                            color: 'text.primary',
                                            fontSize: '0.875rem'
                                        }}
                                    >
                                        {file.name}
                                    </Typography>
                                </Box>
                            ))}
                        </Box>
                    </Box>
                </Box>
            )}
        </Box>
    );
}
