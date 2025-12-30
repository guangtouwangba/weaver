import { Box, Button, MenuItem, Paper, Select, Typography } from '@mui/material';
import { FolderInput, PlusCircle } from 'lucide-react';
import { useState } from 'react';

// Mock projects for now
const PROJECTS = [
    'Q1 Marketing Strategy',
    'Competitor Analysis 2024',
    'User Research v2',
    'Product Roadmap',
];

interface InboxActionFooterProps {
    onAddToProject: (projectId: string) => void;
    onCreateProject: () => void;
}

export default function InboxActionFooter({ onAddToProject, onCreateProject }: InboxActionFooterProps) {
    const [selectedProject, setSelectedProject] = useState(PROJECTS[0]);

    return (
        <Paper elevation={0} sx={{ p: 3, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'white' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold">Add to Existing Project</Typography>
                <Typography variant="caption" color="text.secondary">Or Start Fresh</Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 2 }}>
                {/* Existing Project Selector */}
                <Box sx={{ flex: 1, display: 'flex', gap: 1 }}>
                    <Select
                        fullWidth
                        size="small"
                        value={selectedProject}
                        onChange={(e) => setSelectedProject(e.target.value)}
                        sx={{
                            bgcolor: 'white',
                            borderRadius: 2,
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: '#E5E7EB' }
                        }}
                    >
                        {PROJECTS.map(p => (
                            <MenuItem key={p} value={p}>{p}</MenuItem>
                        ))}
                    </Select>
                    <Button
                        variant="contained"
                        disableElevation
                        onClick={() => onAddToProject(selectedProject)}
                        sx={{
                            bgcolor: '#EEF2FF', color: 'primary.main', fontWeight: 'bold',
                            textTransform: 'none', borderRadius: 2, px: 3,
                            '&:hover': { bgcolor: '#E0E7FF' }
                        }}
                    >
                        Add
                    </Button>
                </Box>

                {/* Create New Project */}
                <Button
                    variant="contained"
                    startIcon={<PlusCircle size={18} />}
                    onClick={onCreateProject}
                    sx={{
                        bgcolor: '#6366F1',
                        textTransform: 'none',
                        borderRadius: 2,
                        px: 3,
                        '&:hover': { bgcolor: '#4F46E5' }
                    }}
                >
                    Create New Project
                </Button>
            </Box>
        </Paper>
    );
}
