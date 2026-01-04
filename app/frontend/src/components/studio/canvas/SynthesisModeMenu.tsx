import React from 'react';
import { Paper, Box, Typography, Stack, IconButton, Divider } from '@mui/material';
import {
    AutoAwesomeIcon,
    LinkIcon,
    BoltIcon,
    CloseIcon
} from '@/components/ui/icons';

export type SynthesisMode = 'connect' | 'inspire' | 'debate';

interface SynthesisModeMenuProps {
    onSelect: (mode: SynthesisMode) => void;
    onCancel: () => void;
    isSynthesizing: boolean;
    position?: { x: number; y: number }; // Screen position for the menu
}

export default function SynthesisModeMenu({
    onSelect,
    onCancel,
    isSynthesizing,
    position
}: SynthesisModeMenuProps) {

    // Calculate menu position - if position provided, use it; otherwise center
    const menuStyle = position ? {
        position: 'absolute' as const,
        left: position.x,
        top: position.y,
        transform: 'translate(-50%, -100%)', // Position above and centered on the point
        zIndex: 2000,
    } : {
        position: 'absolute' as const,
        top: '20%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 2000,
    };

    if (isSynthesizing) {
        return (
            <Paper
                elevation={4}
                sx={{
                    ...menuStyle,
                    p: 3,
                    borderRadius: 3,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 2,
                }}
            >
                <Typography variant="subtitle1" fontWeight={600} color="#8B5CF6">
                    Synthesizing...
                </Typography>
            </Paper>
        );
    }

    return (
        <Paper
            elevation={4}
            sx={{
                ...menuStyle,
                p: 0,
                borderRadius: 3,
                overflow: 'hidden',
                minWidth: 320,
                animation: 'popIn 0.2s ease-out',
                '@keyframes popIn': {
                    from: { opacity: 0, transform: position ? 'translate(-50%, -90%) scale(0.9)' : 'translate(-50%, -40%) scale(0.9)' },
                    to: { opacity: 1, transform: position ? 'translate(-50%, -100%) scale(1)' : 'translate(-50%, -50%) scale(1)' },
                },
            }}
        >
            {/* Header */}
            <Box sx={{ p: 2, bgcolor: '#F9FAFB', borderBottom: '1px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AutoAwesomeIcon size="sm" color="warning" />
                    <Typography variant="subtitle2" fontWeight={600}>
                        Merge with AI
                    </Typography>
                </Box>
                <IconButton size="small" onClick={onCancel}>
                    <CloseIcon size="xs" />
                </IconButton>
            </Box>

            {/* Options */}
            <Stack spacing={0} sx={{ p: 1 }}>
                <ModeOption
                    icon={<LinkIcon size="md" color="primary" />}
                    title="Connect"
                    description="Find hidden links and commonalities"
                    onClick={() => onSelect('connect')}
                    color="#EFF6FF"
                />
                <ModeOption
                    icon={<AutoAwesomeIcon size="md" color="warning" />}
                    title="Inspire"
                    description="Reframe A with B's perspective"
                    onClick={() => onSelect('inspire')}
                    color="#FFFBEB"
                />
                <ModeOption
                    icon={<BoltIcon size="md" color="error" />}
                    title="Debate"
                    description="Identify conflicts and trade-offs"
                    onClick={() => onSelect('debate')}
                    color="#FEF2F2"
                />
            </Stack>
        </Paper>
    );
}

function ModeOption({
    icon,
    title,
    description,
    onClick,
    color
}: {
    icon: React.ReactNode,
    title: string,
    description: string,
    onClick: () => void,
    color: string
}) {
    return (
        <Box
            onClick={onClick}
            sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                p: 2,
                borderRadius: 2,
                cursor: 'pointer',
                transition: 'all 0.1s',
                '&:hover': {
                    bgcolor: color,
                    transform: 'translateX(4px)',
                },
            }}
        >
            <Box sx={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                bgcolor: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                border: '1px solid #F3F4F6'
            }}>
                {icon}
            </Box>
            <Box>
                <Typography variant="subtitle2" fontWeight={600} color="#1F2937">
                    {title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {description}
                </Typography>
            </Box>
        </Box>
    );
}
