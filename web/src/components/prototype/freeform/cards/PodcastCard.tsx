'use client';

import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import { Play } from 'lucide-react';

export interface PodcastCardProps {
    id: string;
    name: string;
    duration?: string;
    isSelected?: boolean;
    accentColor?: string;
    onMouseDown?: (e: React.MouseEvent) => void;
    onDoubleClick?: (e: React.MouseEvent) => void;
}

// Waveform visualization component
const Waveform = ({ color }: { color: string }) => {
    const bars = [3, 5, 8, 6, 9, 4, 7, 5, 8, 6, 4, 7, 5, 3];
    
    return (
        <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '2px',
            height: 24
        }}>
            {bars.map((height, i) => (
                <Box
                    key={i}
                    sx={{
                        width: 3,
                        height: `${height * 2.5}px`,
                        backgroundColor: color,
                        borderRadius: '1px',
                        opacity: 0.7 + (i % 3) * 0.1,
                        animation: `waveform ${0.8 + i * 0.1}s ease-in-out infinite alternate`,
                        '@keyframes waveform': {
                            '0%': { transform: 'scaleY(0.6)' },
                            '100%': { transform: 'scaleY(1)' }
                        }
                    }}
                />
            ))}
        </Box>
    );
};

export default function PodcastCard({
    id,
    name,
    duration = '0:00',
    isSelected = false,
    accentColor = '#8B5CF6',
    onMouseDown,
    onDoubleClick
}: PodcastCardProps) {
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
            }}
        >
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                {/* Play Button */}
                <Box sx={{
                    p: 1,
                    borderRadius: '10px',
                    backgroundColor: `${accentColor}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Play size={18} color={accentColor} fill={accentColor} />
                </Box>

                {/* Title & Duration */}
                <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                    <Typography 
                        variant="body2" 
                        noWrap
                        sx={{ 
                            fontWeight: 600,
                            color: 'text.primary',
                            fontSize: '0.85rem',
                            lineHeight: 1.2
                        }}
                    >
                        {name}
                    </Typography>
                    <Typography 
                        variant="caption" 
                        sx={{ 
                            color: 'text.secondary',
                            fontSize: '0.7rem'
                        }}
                    >
                        Podcast • {duration}
                    </Typography>
                </Box>
            </Box>

            {/* Waveform */}
            <Box sx={{ 
                mt: 1,
                p: 1,
                borderRadius: '8px',
                backgroundColor: `${accentColor}08`
            }}>
                <Waveform color={accentColor} />
            </Box>
        </Paper>
    );
}



