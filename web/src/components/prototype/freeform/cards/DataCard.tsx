'use client';

import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { BarChart3 } from 'lucide-react';

export interface DataCardProps {
    id: string;
    name: string;
    metric?: string;
    isSelected?: boolean;
    accentColor?: string;
    onMouseDown?: (e: React.MouseEvent) => void;
    onDoubleClick?: (e: React.MouseEvent) => void;
}

export default function DataCard({
    id,
    name,
    metric,
    isSelected = false,
    accentColor = '#10B981',
    onMouseDown,
    onDoubleClick
}: DataCardProps) {
    return (
        <Paper
            onMouseDown={onMouseDown}
            onDoubleClick={onDoubleClick}
            elevation={isSelected ? 8 : 2}
            sx={{
                width: 180,
                p: 2,
                borderRadius: '16px',
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
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1.5
            }}
        >
            {/* Icon Container */}
            <Box sx={{
                p: 1,
                borderRadius: '10px',
                backgroundColor: `${accentColor}15`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
            }}>
                <BarChart3 size={20} color={accentColor} />
            </Box>

            {/* Content */}
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography 
                    variant="body2" 
                    sx={{ 
                        fontWeight: 600,
                        color: 'text.primary',
                        fontSize: '0.9rem',
                        lineHeight: 1.3,
                        mb: 0.25
                    }}
                >
                    {name}
                </Typography>
                {metric && (
                    <Typography 
                        variant="caption" 
                        sx={{ 
                            color: accentColor,
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            lineHeight: 1.2
                        }}
                    >
                        {metric}
                    </Typography>
                )}
            </Box>
        </Paper>
    );
}





