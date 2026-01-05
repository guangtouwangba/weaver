'use client';

import { Text } from '@/components/ui';
import { colors, radii, fontWeight as fontWeightTokens } from '@/components/ui/tokens';

interface TagChipProps {
    label: string;
    color?: string;
    size?: 'small' | 'medium';
}

// Map common tags to specific colors based on design
const TAG_COLORS: Record<string, { bg: string; color: string }> = {
    'Strategy': { bg: '#DBEAFE', color: '#1E40AF' },
    'Finance': { bg: '#DCFCE7', color: '#166534' },
    'Product': { bg: '#F3E8FF', color: '#6B21A8' },
    'UX': { bg: colors.neutral[100], color: colors.neutral[700] },
    'Market': { bg: '#FFEDD5', color: '#9A3412' },
    'Q1': { bg: '#E0E7FF', color: '#3730A3' },
};

export default function TagChip({ label, color, size = 'small' }: TagChipProps) {
    const style = TAG_COLORS[label] || (color ? { bg: `${color}20`, color } : { bg: colors.neutral[100], color: colors.neutral[700] });

    const isSmall = size === 'small';

    return (
        <span
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: style.bg,
                color: style.color,
                fontWeight: fontWeightTokens.semibold,
                fontSize: isSmall ? 11 : 13,
                height: isSmall ? 20 : 24,
                paddingLeft: 8,
                paddingRight: 8,
                borderRadius: radii.md,
            }}
        >
            {label}
        </span>
    );
}
