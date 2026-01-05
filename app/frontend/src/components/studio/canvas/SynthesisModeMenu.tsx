'use client';

import React from 'react';
import { Surface, Stack, Text, IconButton } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
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
    const menuStyle: React.CSSProperties = position ? {
        position: 'absolute',
        left: position.x,
        top: position.y,
        transform: 'translate(-50%, -100%)', // Position above and centered on the point
        zIndex: 2000,
    } : {
        position: 'absolute',
        top: '20%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 2000,
    };

    if (isSynthesizing) {
        return (
            <Surface
                elevation={3}
                radius="lg"
                sx={{
                    ...menuStyle,
                    p: 3,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 2,
                }}
            >
                <Text variant="label" sx={{ color: '#8B5CF6' }}>
                    Synthesizing...
                </Text>
            </Surface>
        );
    }

    return (
        <Surface
            elevation={3}
            radius="lg"
            sx={{
                ...menuStyle,
                p: 0,
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
            <Stack
                direction="row"
                justify="between"
                align="center"
                sx={{
                    p: 2,
                    bgcolor: colors.background.subtle,
                    borderBottom: `1px solid ${colors.border.default}`,
                }}
            >
                <Stack direction="row" align="center" gap={1}>
                    <AutoAwesomeIcon size="sm" color="warning" />
                    <Text variant="label">
                        Merge with AI
                    </Text>
                </Stack>
                <IconButton size="sm" variant="ghost" onClick={onCancel}>
                    <CloseIcon size="xs" />
                </IconButton>
            </Stack>

            {/* Options */}
            <Stack gap={0} sx={{ p: 1 }}>
                <ModeOption
                    icon={<LinkIcon size="md" color="primary" />}
                    title="Connect"
                    description="Find hidden links and commonalities"
                    onClick={() => onSelect('connect')}
                    color={colors.primary[50]}
                />
                <ModeOption
                    icon={<AutoAwesomeIcon size="md" color="warning" />}
                    title="Inspire"
                    description="Reframe A with B's perspective"
                    onClick={() => onSelect('inspire')}
                    color={colors.warning[50]}
                />
                <ModeOption
                    icon={<BoltIcon size="md" color="error" />}
                    title="Debate"
                    description="Identify conflicts and trade-offs"
                    onClick={() => onSelect('debate')}
                    color={colors.error[50]}
                />
            </Stack>
        </Surface>
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
        <Stack
            direction="row"
            align="center"
            gap={2}
            onClick={onClick}
            sx={{
                p: 2,
                borderRadius: `${radii.md}px`,
                cursor: 'pointer',
                transition: 'all 0.1s',
                '&:hover': {
                    bgcolor: color,
                    transform: 'translateX(4px)',
                },
            }}
        >
            <div
                style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    backgroundColor: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: shadows.xs,
                    border: `1px solid ${colors.neutral[100]}`,
                }}
            >
                {icon}
            </div>
            <div>
                <Text variant="label" sx={{ color: colors.text.primary }}>
                    {title}
                </Text>
                <Text variant="caption" color="secondary">
                    {description}
                </Text>
            </div>
        </Stack>
    );
}
