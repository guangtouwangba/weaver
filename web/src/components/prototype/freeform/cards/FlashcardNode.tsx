'use client';

import React, { useState } from 'react';
import { Box, Paper, Typography, IconButton } from '@mui/material';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface FlashcardNodeProps {
    id: string;
    term: string;
    definition?: string;
    currentIndex?: number;
    totalCards?: number;
    isSelected?: boolean;
    accentColor?: string;
    onMouseDown?: (e: React.MouseEvent) => void;
    onDoubleClick?: (e: React.MouseEvent) => void;
    onNext?: () => void;
    onPrev?: () => void;
}

export default function FlashcardNode({
    id,
    term,
    definition,
    currentIndex = 1,
    totalCards = 24,
    isSelected = false,
    accentColor = '#F97316',
    onMouseDown,
    onDoubleClick,
    onNext,
    onPrev
}: FlashcardNodeProps) {
    const [isFlipped, setIsFlipped] = useState(false);

    return (
        <Paper
            onMouseDown={onMouseDown}
            onDoubleClick={onDoubleClick}
            elevation={isSelected ? 8 : 2}
            sx={{
                width: 220,
                borderRadius: '12px',
                backgroundColor: 'white',
                border: `2px solid ${isSelected ? accentColor : `${accentColor}66`}`,
                boxShadow: isSelected 
                    ? `0 8px 24px ${accentColor}22`
                    : '0 2px 8px rgba(0,0,0,0.04)',
                cursor: 'grab',
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
                },
                '&:active': { cursor: 'grabbing' },
                overflow: 'hidden'
            }}
        >
            {/* Header */}
            <Box sx={{ 
                px: 2, 
                py: 1, 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                borderBottom: '1px solid rgba(0,0,0,0.05)'
            }}>
                <Typography 
                    variant="caption" 
                    sx={{ 
                        color: accentColor,
                        fontWeight: 700,
                        fontSize: '0.65rem',
                        letterSpacing: '0.05em'
                    }}
                >
                    FLASHCARD {currentIndex}/{totalCards}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <IconButton 
                        size="small" 
                        onClick={(e) => {
                            e.stopPropagation();
                            onPrev?.();
                        }}
                        sx={{ 
                            p: 0.25,
                            color: 'text.secondary',
                            '&:hover': { color: accentColor }
                        }}
                    >
                        <ChevronLeft size={14} />
                    </IconButton>
                    <IconButton 
                        size="small" 
                        onClick={(e) => {
                            e.stopPropagation();
                            onNext?.();
                        }}
                        sx={{ 
                            p: 0.25,
                            color: 'text.secondary',
                            '&:hover': { color: accentColor }
                        }}
                    >
                        <ChevronRight size={14} />
                    </IconButton>
                </Box>
            </Box>

            {/* Card Content */}
            <Box 
                sx={{ 
                    p: 2.5,
                    minHeight: 80,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer'
                }}
                onClick={(e) => {
                    e.stopPropagation();
                    setIsFlipped(!isFlipped);
                }}
            >
                <Typography 
                    variant="body1" 
                    sx={{ 
                        fontWeight: isFlipped ? 400 : 500,
                        color: isFlipped ? 'text.secondary' : 'text.primary',
                        fontSize: '0.95rem',
                        lineHeight: 1.4,
                        textAlign: 'center',
                        fontStyle: isFlipped ? 'italic' : 'normal'
                    }}
                >
                    {isFlipped ? (definition || 'Definition goes here...') : `"${term}"`}
                </Typography>
            </Box>

            {/* Progress Bar */}
            <Box sx={{ px: 2, pb: 1.5 }}>
                <Box sx={{
                    height: 4,
                    backgroundColor: 'grey.100',
                    borderRadius: '2px',
                    overflow: 'hidden'
                }}>
                    <Box sx={{
                        height: '100%',
                        width: `${(currentIndex / totalCards) * 100}%`,
                        backgroundColor: accentColor,
                        borderRadius: '2px',
                        transition: 'width 0.3s ease'
                    }} />
                </Box>
            </Box>
        </Paper>
    );
}


