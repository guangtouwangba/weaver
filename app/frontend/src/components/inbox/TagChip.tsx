import { Chip } from '@mui/material';

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
    'UX': { bg: '#F3F4F6', color: '#374151' },
    'Market': { bg: '#FFEDD5', color: '#9A3412' },
    'Q1': { bg: '#E0E7FF', color: '#3730A3' },
};

export default function TagChip({ label, color, size = 'small' }: TagChipProps) {
    const style = TAG_COLORS[label] || (color ? { bg: `${color}20`, color } : { bg: '#F3F4F6', color: '#374151' });

    return (
        <Chip
            label={label}
            size={size}
            sx={{
                bgcolor: style.bg,
                color: style.color,
                fontWeight: 600,
                fontSize: size === 'small' ? '11px' : '13px',
                height: size === 'small' ? '20px' : '24px',
                borderRadius: '6px',
                border: 'none'
            }}
        />
    );
}
