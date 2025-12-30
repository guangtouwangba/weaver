import { Box, Button, IconButton, TextField, InputAdornment, Typography } from '@mui/material';
import { Search, Filter, Plus, Bell } from 'lucide-react';

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
        <Box sx={{
            height: 64,
            borderBottom: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            px: 3,
            bgcolor: 'white',
            justifyContent: 'space-between'
        }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mr: 4 }}>Inbox</Typography>

            <TextField
                placeholder="Search inbox items..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                variant="outlined"
                size="small"
                sx={{
                    width: 400,
                    '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        bgcolor: '#F9FAFB',
                        '& fieldset': { borderColor: '#E5E7EB' },
                        '&:hover fieldset': { borderColor: '#D1D5DB' },
                        '&.Mui-focused fieldset': { borderColor: 'primary.main' },
                    }
                }}
                InputProps={{
                    startAdornment: (
                        <InputAdornment position="start">
                            <Search size={18} className="text-gray-400" />
                        </InputAdornment>
                    ),
                }}
            />

            <Box sx={{ flexGrow: 1 }} />

            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Button
                    variant="outlined"
                    startIcon={<Filter size={16} />}
                    onClick={onFilterClick}
                    sx={{
                        color: 'text.secondary',
                        borderColor: '#E5E7EB',
                        textTransform: 'none',
                        borderRadius: 2
                    }}
                >
                    Filter by Type/Tag
                </Button>

                <Button
                    variant="contained"
                    startIcon={<Plus size={18} />}
                    onClick={onNewItemClick}
                    sx={{
                        textTransform: 'none',
                        borderRadius: 2,
                        bgcolor: '#6366F1',
                        '&:hover': { bgcolor: '#4F46E5' }
                    }}
                >
                    New Item
                </Button>

                <IconButton>
                    <Bell size={20} className="text-gray-400" />
                </IconButton>
            </Box>
        </Box>
    );
}
