'use client';

import React, { useState } from 'react';
import { Box, IconButton, Tooltip, Paper, Typography, Fade, ClickAwayListener } from '@mui/material';
import { Sparkles, MoreHorizontal } from 'lucide-react';

export interface SynthesisAction {
    id: string;
    label: string;
    icon: React.ReactNode;
    handler: () => void;
    category?: 'audio' | 'visual' | 'text' | 'study';
}

interface SynthesisOrbProps {
    x: number;
    y: number;
    actions: SynthesisAction[];
    projectColor: string;
}

export default function SynthesisOrb({ x, y, actions, projectColor }: SynthesisOrbProps) {
    const [menuOpen, setMenuOpen] = useState(false);

    // Determine which actions to show in orbit vs overflow
    const MAX_ORBIT_ITEMS = 4;
    const hasOverflow = actions.length > MAX_ORBIT_ITEMS;

    // If we have overflow, we show (MAX - 1) items + 1 "More" button
    const orbitalActions = hasOverflow ? actions.slice(0, MAX_ORBIT_ITEMS - 1) : actions;
    const overflowActions = hasOverflow ? actions.slice(MAX_ORBIT_ITEMS - 1) : [];

    return (
        <Box
            sx={{
                position: 'absolute',
                left: x,
                top: y,
                transform: 'translate(-50%, -50%)',
                zIndex: 1000,
                pointerEvents: 'auto',
            }}
        >
            {/* The Central Orb */}
            <Box
                sx={{
                    width: 64,
                    height: 64,
                    borderRadius: '50%',
                    background: 'rgba(30, 41, 59, 0.8)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2), inset 0 0 0 1px rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    zIndex: 1100,
                    '&:hover': {
                        transform: 'scale(1.05)',
                        background: 'rgba(30, 41, 59, 0.95)',
                        boxShadow: '0 12px 48px rgba(0, 0, 0, 0.3)',
                    },
                    '&:hover .radial-menu': {
                        opacity: 1,
                        transform: 'translate(-50%, -50%) scale(1)',
                        pointerEvents: 'auto',
                    }
                }}
            >
                <Sparkles size={28} color={projectColor} style={{ filter: 'drop-shadow(0 0 8px ' + projectColor + '66)' }} />

                {/* Radial Menu Container */}
                <Box
                    className="radial-menu"
                    sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        width: 250,
                        height: 250,
                        opacity: menuOpen ? 1 : 0, // Keep visible if menu is open
                        transform: menuOpen ? 'translate(-50%, -50%) scale(1)' : 'translate(-50%, -50%) scale(0.8)',
                        transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
                        pointerEvents: menuOpen ? 'auto' : 'none',
                        zIndex: -1
                    }}
                >
                    {orbitalActions.map((action, index) => {
                        // Distribute in a circle
                        const total = hasOverflow ? MAX_ORBIT_ITEMS : actions.length;
                        const angle = (index / total) * 2 * Math.PI - Math.PI / 2; // Start from top (-90deg)
                        const radius = 80;
                        const ax = 125 + Math.cos(angle) * radius; // Center is 125, 125
                        const ay = 125 + Math.sin(angle) * radius;

                        return (
                            <Tooltip key={action.id} title={action.label} placement="top">
                                <IconButton
                                    onClick={(e) => { e.stopPropagation(); action.handler(); }}
                                    sx={{
                                        position: 'absolute',
                                        left: ax,
                                        top: ay,
                                        transform: 'translate(-50%, -50%)',
                                        bgcolor: 'rgba(30, 41, 59, 0.9)',
                                        backdropFilter: 'blur(4px)',
                                        color: 'white',
                                        border: '1px solid rgba(255, 255, 255, 0.1)',
                                        '&:hover': {
                                            bgcolor: projectColor,
                                            transform: 'translate(-50%, -50%) scale(1.15)',
                                            boxShadow: `0 0 20px ${projectColor}66`
                                        },
                                        boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                                        width: 44,
                                        height: 44,
                                        transition: 'all 0.2s ease'
                                    }}
                                >
                                    {action.icon}
                                </IconButton>
                            </Tooltip>
                        );
                    })}

                    {hasOverflow && (
                        <Tooltip title="More Options" placement="top">
                            <IconButton
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setMenuOpen(!menuOpen);
                                }}
                                sx={{
                                    position: 'absolute',
                                    left: 125 + Math.cos((MAX_ORBIT_ITEMS - 1) / MAX_ORBIT_ITEMS * 2 * Math.PI - Math.PI / 2) * 80,
                                    top: 125 + Math.sin((MAX_ORBIT_ITEMS - 1) / MAX_ORBIT_ITEMS * 2 * Math.PI - Math.PI / 2) * 80,
                                    transform: 'translate(-50%, -50%)',
                                    bgcolor: menuOpen ? projectColor : 'rgba(30, 41, 59, 0.9)',
                                    backdropFilter: 'blur(4px)',
                                    color: 'white',
                                    border: '1px solid rgba(255, 255, 255, 0.1)',
                                    '&:hover': {
                                        bgcolor: projectColor,
                                        transform: 'translate(-50%, -50%) scale(1.15)',
                                    },
                                    width: 44,
                                    height: 44,
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                <MoreHorizontal size={20} />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>
            </Box>

            {/* Galaxy View (Overflow Menu) */}
            <ClickAwayListener onClickAway={() => setMenuOpen(false)}>
                <Fade in={menuOpen}>
                    <Paper
                        sx={{
                            position: 'absolute',
                            left: '50%',
                            top: '50%',
                            mt: 12, // Offset below the orb
                            transform: 'translateX(-50%)',
                            width: 280,
                            maxHeight: 320,
                            overflowY: 'auto',
                            bgcolor: 'rgba(30, 41, 59, 0.95)',
                            backdropFilter: 'blur(12px)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            borderRadius: '16px',
                            p: 2,
                            zIndex: 1050,
                            boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
                        }}
                    >
                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', fontWeight: 700, mb: 1, display: 'block', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            More Synthesis Options
                        </Typography>

                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                            {overflowActions.map(action => (
                                <Box
                                    key={action.id}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        action.handler();
                                        setMenuOpen(false);
                                    }}
                                    sx={{
                                        p: 1.5,
                                        borderRadius: '12px',
                                        bgcolor: 'rgba(255,255,255,0.05)',
                                        border: '1px solid transparent',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: 1,
                                        '&:hover': {
                                            bgcolor: `${projectColor}22`,
                                            borderColor: `${projectColor}66`,
                                            transform: 'translateY(-2px)'
                                        }
                                    }}
                                >
                                    <Box sx={{ color: projectColor }}>
                                        {action.icon}
                                    </Box>
                                    <Typography variant="caption" sx={{ color: 'white', fontWeight: 500, textAlign: 'center' }}>
                                        {action.label}
                                    </Typography>
                                </Box>
                            ))}
                        </Box>
                    </Paper>
                </Fade>
            </ClickAwayListener>
        </Box>
    );
}
