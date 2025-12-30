'use client';

import React from 'react';
import { Box, Paper, Typography, Button } from '@mui/material';

export interface BriefCardProps {
    id: string;
    name: string;
    preview?: string[];
    timestamp?: string;
    isSelected?: boolean;
    accentColor?: string;
    onMouseDown?: (e: React.MouseEvent) => void;
    onDoubleClick?: (e: React.MouseEvent) => void;
    onOpen?: () => void;
}

export default function BriefCard({
    id,
    name,
    preview = [],
    timestamp,
    isSelected = false,
    accentColor = '#3B82F6',
    onMouseDown,
    onDoubleClick,
    onOpen
}: BriefCardProps) {
    return (
        <Paper
            onMouseDown={onMouseDown}
            onDoubleClick={onDoubleClick}
            elevation={isSelected ? 8 : 2}
            sx={{
                width: 220,
                borderRadius: '12px',
                backgroundColor: 'white',
                border: isSelected ? `2px solid ${accentColor}` : '1px solid rgba(0,0,0,0.06)',
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
                overflow: 'hidden',
                display: 'flex'
            }}
        >
            {/* Left Accent Border */}
            <Box sx={{
                width: 4,
                backgroundColor: accentColor,
                flexShrink: 0
            }} />

            {/* Content */}
            <Box sx={{ p: 2, flexGrow: 1 }}>
                {/* Title */}
                <Typography 
                    variant="body2" 
                    sx={{ 
                        fontWeight: 600,
                        color: 'text.primary',
                        fontSize: '0.9rem',
                        lineHeight: 1.3,
                        mb: 1
                    }}
                >
                    {name}
                </Typography>

                {/* Preview Lines */}
                <Box sx={{ mb: 1.5 }}>
                    {[0, 1, 2].map((i) => (
                        <Box
                            key={i}
                            sx={{
                                height: 6,
                                backgroundColor: 'grey.100',
                                borderRadius: '3px',
                                mb: 0.5,
                                width: i === 2 ? '60%' : '100%'
                            }}
                        />
                    ))}
                </Box>

                {/* Footer */}
                <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between'
                }}>
                    <Typography 
                        variant="caption" 
                        sx={{ 
                            color: 'text.secondary',
                            fontSize: '0.7rem'
                        }}
                    >
                        {timestamp || 'Generated 2h ago'}
                    </Typography>
                    <Typography
                        component="span"
                        onClick={(e) => {
                            e.stopPropagation();
                            onOpen?.();
                        }}
                        sx={{
                            color: accentColor,
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            cursor: 'pointer',
                            '&:hover': {
                                textDecoration: 'underline'
                            }
                        }}
                    >
                        Open
                    </Typography>
                </Box>
            </Box>
        </Paper>
    );
}




