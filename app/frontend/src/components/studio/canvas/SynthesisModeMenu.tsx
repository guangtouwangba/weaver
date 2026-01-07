'use client';

import React from 'react';
import { Surface, Stack, Text, IconButton, Spinner } from '@/components/ui';
import { colors, radii, shadows, spacing } from '@/components/ui/tokens';
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
                style={{
                    ...menuStyle,
                    padding: spacing[3],
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: spacing[2],
                }}
            >
                <Spinner size="sm" />
                <Text variant="label" style={{ color: '#8B5CF6' }}>
                    Synthesizing...
                </Text>
            </Surface>
        );
    }

    return (
        <Surface
            elevation={3}
            radius="lg"
            style={{
                ...menuStyle,
                padding: 0,
                overflow: 'hidden',
                minWidth: 320,
                backgroundColor: colors.background.paper,
            }}
        >
            {/* Header */}
            <Stack
                direction="row"
                justify="between"
                align="center"
                style={{
                    padding: spacing[2],
                    backgroundColor: colors.background.subtle,
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
            <Stack gap={0} style={{ padding: spacing[1] }}>
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
    const [isHovered, setIsHovered] = React.useState(false);

    return (
        <Stack
            direction="row"
            align="center"
            gap={2}
            onClick={onClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            style={{
                padding: spacing[2],
                borderRadius: radii.md,
                cursor: 'pointer',
                transition: 'all 0.1s',
                backgroundColor: isHovered ? color : 'transparent',
                transform: isHovered ? 'translateX(4px)' : 'none',
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
                    flexShrink: 0,
                }}
            >
                {icon}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Text variant="label" style={{ color: colors.text.primary, display: 'block', marginBottom: 2 }}>
                    {title}
                </Text>
                <Text variant="caption" color="secondary" style={{ display: 'block' }}>
                    {description}
                </Text>
            </div>
        </Stack>
    );
}
