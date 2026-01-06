import React from 'react';
import { Surface, Text } from '@/components/ui/primitives';
import { colors, radii } from '@/components/ui/tokens';
import {
    FileText, Link as LinkIcon, Video, StickyNote
} from 'lucide-react';
import TagChip from './TagChip';

export interface InboxItem {
    id: string;
    title: string;
    type: 'article' | 'video' | 'note' | 'pdf' | 'link';
    source: string;
    source_url?: string;
    addedAt: string;
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

    const bgColors: Record<string, string> = {
        article: '#F0FDFA', // Teal-50
        link: '#F0FDF4',    // Green-50
        video: '#FEF2F2',   // Red-50
        note: '#FEFCE8',    // Yellow-50
        pdf: '#FFF7ED'      // Orange-50
    };

    const bgColor = bgColors[item.type] || '#F5F5F4';

    return (
        <Surface
            elevation={0}
            onClick={onClick}
            style={{
                padding: 16,
                marginBottom: 16,
                cursor: 'pointer',
                borderRadius: radii.xl,
                border: '1px solid',
                borderColor: item.isSelected ? colors.primary[500] : colors.border.default,
                backgroundColor: item.isSelected ? colors.primary[50] : 'white',
                transition: 'all 0.2s',
                position: 'relative',
                transform: 'translateY(0)',
            }}
            // Hover styling handled via CSS class if Tailwind available, or style injection.
            // For now, removing hover transform or relying on parent CSS?
            // I'll add a data attribute and use global css if needed, but for now simple style.
            className={item.isSelected ? 'border-primary-500 bg-primary-50' : 'hover:border-stone-400 hover:shadow-sm hover:-translate-y-[1px]'}
        >
            {item.isSelected && (
                <div style={{
                    position: 'absolute', right: 12, top: 12,
                    width: 8, height: 8, borderRadius: '50%',
                    backgroundColor: colors.primary[500]
                }} />
            )}

            <div style={{ display: 'flex', gap: 16 }}>
                <div
                    style={{
                        width: 48, height: 48,
                        borderRadius: radii.lg,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        backgroundColor: bgColor
                    }}
                >
                    <Icon size={24} className={iconColor} />
                </div>

                <div style={{ flex: 1 }}>
                    <Text variant="h6" style={{ lineHeight: 1.3, marginBottom: 4, paddingRight: 16, fontSize: 14, fontWeight: 600 }}>
                        {item.title}
                    </Text>

                    <Text variant="caption" color="secondary" style={{ display: 'block', marginBottom: 8 }}>
                        {item.addedAt} • {item.type.charAt(0).toUpperCase() + item.type.slice(1)}
                    </Text>

                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {item.tags.map(tag => (
                            <TagChip key={tag} label={tag} />
                        ))}
                    </div>
                </div>
            </div>
        </Surface>
    );
}
