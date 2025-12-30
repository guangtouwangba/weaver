import { Box, Paper, Typography } from '@mui/material';
import {
    FileText, Link as LinkIcon, Mic, Video, StickyNote
} from 'lucide-react';
import TagChip from './TagChip';

export interface InboxItem {
    id: string;
    title: string;
    type: 'article' | 'video' | 'note' | 'pdf' | 'link';
    source: string; // 'Web Extension', 'Manual', etc.
    source_url?: string;
    addedAt: string; // 'Added today'
    tags: string[];
    thumbnail?: string;
    isSelected?: boolean;
}

interface InboxItemCardProps {
    item: InboxItem;
    onClick: () => void;
}

export default function InboxItemCard({ item, onClick }: InboxItemCardProps) {
    const Icon = {
        article: FileText,
        link: LinkIcon,
        video: Video,
        note: StickyNote,
        pdf: FileText
    }[item.type] || FileText;

    const iconColor = {
        article: 'text-blue-500',
        link: 'text-green-500',
        video: 'text-red-500',
        note: 'text-yellow-500',
        pdf: 'text-orange-500'
    }[item.type];

    // Map type to tailwind bg colors mostly for reference, but we use sx for MUI Box
    const bgColors: Record<string, string> = {
        article: '#EFF6FF', // blue-50
        link: '#F0FDF4',    // green-50
        video: '#FEF2F2',   // red-50
        note: '#FEFCE8',    // yellow-50
        pdf: '#FFF7ED'      // orange-50
    };

    const bgColor = bgColors[item.type] || '#F3F4F6';

    return (
        <Paper
            elevation={0}
            onClick={onClick}
            sx={{
                p: 2,
                mb: 2,
                cursor: 'pointer',
                borderRadius: 3,
                border: '1px solid',
                borderColor: item.isSelected ? 'primary.main' : 'divider',
                bgcolor: item.isSelected ? '#EFF6FF' : 'white',
                transition: 'all 0.2s',
                '&:hover': {
                    borderColor: item.isSelected ? 'primary.main' : 'grey.400',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                },
                position: 'relative'
            }}
        >
            {item.isSelected && (
                <Box sx={{
                    position: 'absolute', right: 12, top: 12,
                    width: 8, height: 8, borderRadius: '50%',
                    bgcolor: 'primary.main'
                }} />
            )}

            <Box sx={{ display: 'flex', gap: 2 }}>
                {/* Icon / Thumbnail Box */}
                <Box
                    sx={{
                        width: 48, height: 48,
                        borderRadius: 2,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        bgcolor: bgColor
                    }}
                >
                    {/* In real app, show thumbnail if available */}
                    <Icon size={24} className={iconColor} />
                </Box>

                {/* Content */}
                <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle2" fontWeight="600" sx={{ lineHeight: 1.3, mb: 0.5, pr: 2 }}>
                        {item.title}
                    </Typography>

                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        {item.addedAt} • {item.type.charAt(0).toUpperCase() + item.type.slice(1)}
                    </Typography>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {item.tags.map(tag => (
                            <TagChip key={tag} label={tag} />
                        ))}
                    </Box>
                </Box>
            </Box>
        </Paper>
    );
}
