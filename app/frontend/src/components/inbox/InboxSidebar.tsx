import { Chip, Text } from '@/components/ui/primitives';
import { colors } from '@/components/ui/tokens';
import InboxItemCard, { InboxItem } from './InboxItemCard';

interface InboxSidebarProps {
    items: InboxItem[];
    selectedId: string | null;
    onSelect: (id: string) => void;
}

export default function InboxSidebar({ items, selectedId, onSelect }: InboxSidebarProps) {
    return (
        <div style={{
            width: 400,
            height: 'calc(100vh - 64px)',
            borderRight: `1px solid ${colors.border.default}`,
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'white'
        }}>
            <div style={{
                padding: '24px 24px 16px 24px',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between'
            }}>
                <Text variant="caption" style={{ fontWeight: 700, color: colors.text.secondary, letterSpacing: 1 }}>
                    COLLECTED ITEMS
                </Text>
                <Chip
                    label={`${items.length} New`}
                    size="sm"
                    variant="soft"
                    color="primary"
                    style={{ fontWeight: 600 }}
                />
            </div>

            <div style={{ flexGrow: 1, overflowY: 'auto', padding: '0 24px 32px 24px' }}>
                {items.map(item => (
                    <InboxItemCard
                        key={item.id}
                        item={{ ...item, isSelected: item.id === selectedId }}
                        onClick={() => onSelect(item.id)}
                    />
                ))}

                {items.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '64px 0', opacity: 0.5 }}>
                        <Text variant="bodySmall">No items found</Text>
                    </div>
                )}
            </div>
        </div>
    );
}
