'use client';

import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { TrendingUp, Target, Zap, Lightbulb } from 'lucide-react';

export interface TopicCardProps {
    id: string;
    name: string;
    subtitle?: string;
    accentColor?: string;
    iconType?: 'trending' | 'target' | 'zap' | 'lightbulb';
    isSelected?: boolean;
    onMouseDown?: (e: React.MouseEvent) => void;
    onDoubleClick?: (e: React.MouseEvent) => void;
}

const getIcon = (iconType: string, color: string) => {
    const iconProps = { size: 20, color };
    switch (iconType) {
        case 'trending':
            return <TrendingUp {...iconProps} />;
        case 'target':
            return <Target {...iconProps} />;
        case 'zap':
            return <Zap {...iconProps} />;
        case 'lightbulb':
        default:
            return <Lightbulb {...iconProps} />;
    }
};

export default function TopicCard({
    id,
    name,
    subtitle,
    accentColor = '#F97316',
    iconType = 'lightbulb',
    isSelected = false,
    onMouseDown,
    onDoubleClick
}: TopicCardProps) {
    return (
        <Paper
            onMouseDown={onMouseDown}
            onDoubleClick={onDoubleClick}
            elevation={isSelected ? 8 : 2}
            sx={{
                width: 200,
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
                {getIcon(iconType, accentColor)}
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
                {subtitle && (
                    <Typography 
                        variant="caption" 
                        sx={{ 
                            color: 'text.secondary',
                            fontSize: '0.75rem',
                            lineHeight: 1.2
                        }}
                    >
                        {subtitle}
                    </Typography>
                )}
            </Box>
        </Paper>
    );
}



