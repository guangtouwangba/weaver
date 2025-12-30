import { Box, Chip, Typography } from '@mui/material';
import InboxItemCard, { InboxItem } from './InboxItemCard';

interface InboxSidebarProps {
    items: InboxItem[];
    selectedId: string | null;
    onSelect: (id: string) => void;
}

export default function InboxSidebar({ items, selectedId, onSelect }: InboxSidebarProps) {
    return (
        <Box sx={{
            width: 400,
            height: 'calc(100vh - 64px)',
            borderRight: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            flexDirection: 'column',
            bgcolor: 'white'
        }}>
            <Box sx={{
                p: 3, pb: 2,
                display: 'flex', alignItems: 'center', justifyContent: 'space-between'
            }}>
                <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ letterSpacing: 1 }}>
                    COLLECTED ITEMS
                </Typography>
                <Chip
                    label={`${items.length} New`}
                    size="small"
                    sx={{
                        bgcolor: '#EEF2FF',
                        color: '#4F46E5',
                        fontWeight: 600,
                        fontSize: '11px',
                        height: 24,
                        borderRadius: '12px'
                    }}
                />
            </Box>

            <Box sx={{ flexGrow: 1, overflowY: 'auto', px: 3, pb: 4 }}>
                {items.map(item => (
                    <InboxItemCard
                        key={item.id}
                        item={{ ...item, isSelected: item.id === selectedId }}
                        onClick={() => onSelect(item.id)}
                    />
                ))}

                {items.length === 0 && (
                    <Box sx={{ textAlign: 'center', py: 8, opacity: 0.5 }}>
                        <Typography variant="body2">No items found</Typography>
                    </Box>
                )}
            </Box>
        </Box>
    );
}
