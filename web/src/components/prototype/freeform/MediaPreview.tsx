'use client';

import React from 'react';
import { Box, Typography, Paper, Slider, IconButton, List, ListItem, Chip } from '@mui/material';
import { Play, Pause, Volume2, Maximize2, List as ListIcon } from 'lucide-react';

interface MediaPreviewProps {
    file: {
        name: string;
        type: string;
    };
}

const MOCK_TRANSCRIPT = [
    { time: '00:15', text: 'Welcome to the course. Today we discuss Transformers.' },
    { time: '02:30', text: 'The attention mechanism is the key component of this architecture.', active: true },
    { time: '12:30', text: 'It allows the model to focus on relevant parts of the input sequence.' },
    { time: '15:45', text: 'We will look at multi-head attention and its advantages.' },
    { time: '20:10', text: 'Positional encoding is used to provide sequence order information.' }
];

export default function MediaPreview({ file }: MediaPreviewProps) {
    const isVideo = file.type === 'mp4';

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: 'white' }}>
            {/* Media Header */}
            <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip label={isVideo ? 'VIDEO' : 'AUDIO'} size="small" sx={{ fontWeight: 700, borderRadius: 1 }} />
                <Typography variant="subtitle1" fontWeight={600} noWrap sx={{ flex: 1 }}>
                    {file.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">1:20:00</Typography>
                <IconButton size="small"><Maximize2 size={16} /></IconButton>
            </Box>

            {/* Media Player Area */}
            <Box 
                sx={{ 
                    width: '100%', 
                    aspectRatio: isVideo ? '16/9' : 'auto',
                    bgcolor: 'black',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    color: 'white',
                    p: isVideo ? 0 : 4
                }}
            >
                {isVideo ? (
                    <Typography variant="body2" sx={{ opacity: 0.5 }}>
                        [ Video Placeholder: {file.name} ]
                    </Typography>
                ) : (
                    <Box sx={{ textAlign: 'center' }}>
                        <Box sx={{ fontSize: '48px', mb: 2 }}>📻</Box>
                        <Typography variant="body2">{file.name}</Typography>
                    </Box>
                )}

                {/* Player Controls */}
                <Box 
                    sx={{ 
                        position: 'absolute', 
                        bottom: 0, 
                        left: 0, 
                        right: 0, 
                        p: 2, 
                        background: 'linear-gradient(transparent, rgba(0,0,0,0.7))',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 1
                    }}
                >
                    <Slider 
                        size="small" 
                        defaultValue={20} 
                        sx={{ color: 'white', py: 0 }}
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <IconButton size="small" sx={{ color: 'white' }}><Play size={20} fill="white" /></IconButton>
                            <IconButton size="small" sx={{ color: 'white' }}><Volume2 size={20} /></IconButton>
                        </Box>
                        <Typography variant="caption">12:30 / 1:20:00</Typography>
                    </Box>
                </Box>
            </Box>

            {/* Transcript Section */}
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid', borderColor: 'divider' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <ListIcon size={18} />
                        <Typography variant="subtitle2" fontWeight={700}>Transcript</Typography>
                    </Box>
                    <Chip label="English" size="small" variant="outlined" />
                </Box>

                <List sx={{ p: 0, overflowY: 'auto', flexGrow: 1 }}>
                    {MOCK_TRANSCRIPT.map((item, index) => (
                        <ListItem 
                            key={index} 
                            sx={{ 
                                display: 'flex', 
                                alignItems: 'flex-start', 
                                gap: 2, 
                                py: 2,
                                px: 3,
                                borderBottom: '1px solid rgba(0,0,0,0.03)',
                                bgcolor: item.active ? 'rgba(0, 150, 255, 0.03)' : 'transparent',
                                transition: 'background-color 0.2s'
                            }}
                        >
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, minWidth: 40 }}>
                                {item.time}
                            </Typography>
                            <Paper
                                elevation={0}
                                sx={{
                                    p: item.active ? 2 : 0,
                                    bgcolor: item.active ? 'white' : 'transparent',
                                    border: item.active ? '1px solid rgba(0, 150, 255, 0.2)' : 'none',
                                    borderRadius: 2,
                                    width: '100%'
                                }}
                            >
                                <Typography variant="body2" sx={{ lineHeight: 1.6, color: item.active ? 'text.primary' : 'text.secondary' }}>
                                    {item.text}
                                </Typography>
                            </Paper>
                        </ListItem>
                    ))}
                </List>
            </Box>
        </Box>
    );
}







