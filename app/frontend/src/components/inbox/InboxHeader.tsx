import {
    Button,
    IconButton,
    Text,
} from '@/components/ui/primitives';
import { TextField } from '@/components/ui/composites';
import { Search, Filter, Plus, Bell } from 'lucide-react';
import { colors } from '@/components/ui/tokens';

interface InboxHeaderProps {
    searchQuery: string;
    onSearchChange: (query: string) => void;
    onFilterClick: () => void;
    onNewItemClick: () => void;
}

export default function InboxHeader({
    searchQuery,
    onSearchChange,
    onFilterClick,
    onNewItemClick
}: InboxHeaderProps) {
    return (
        <div style={{
            height: 64,
            borderBottom: `1px solid ${colors.border.default}`,
            display: 'flex',
            alignItems: 'center',
            paddingLeft: 24, paddingRight: 24,
            backgroundColor: 'white',
            justifyContent: 'space-between'
        }}>
            <Text variant="h6" style={{ marginRight: 32, fontWeight: 700 }}>Inbox</Text>

            <TextField
                placeholder="Search inbox items..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                size="sm"
                style={{ width: 400 }}
                startAdornment={<Search size={18} color="#9CA3AF" />}
            />

            <div style={{ flexGrow: 1 }} />

            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                <Button
                    variant="outline"
                    icon={<Filter size={16} />}
                    onClick={onFilterClick}
                >
                    Filter by Type/Tag
                </Button>

                <Button
                    variant="primary"
                    icon={<Plus size={18} />}
                    onClick={onNewItemClick}
                >
                    New Item
                </Button>

                <IconButton>
                    <Bell size={20} className="text-gray-400" />
                </IconButton>
            </div>
        </div>
    );
}
