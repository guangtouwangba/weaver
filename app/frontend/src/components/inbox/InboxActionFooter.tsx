import { Box, Button, MenuItem, Paper, Select, Typography } from '@mui/material';
import { PlusCircle } from 'lucide-react';
import { useState, useEffect } from 'react';

export interface ProjectOption {
    id: string;
    name: string;
}

interface InboxActionFooterProps {
    projects: ProjectOption[];
    onAddToProject: (projectId: string) => void;
    onCreateProject: () => void;
    disabled?: boolean;
}

export default function InboxActionFooter({
    projects,
    onAddToProject,
    onCreateProject,
    disabled = false
}: InboxActionFooterProps) {
    const [selectedProjectId, setSelectedProjectId] = useState<string>('');

    // Set default when projects load
    useEffect(() => {
        if (projects.length > 0 && !selectedProjectId) {
            setSelectedProjectId(projects[0].id);
        }
    }, [projects, selectedProjectId]);

    return (
        <Paper elevation={0} sx={{ p: 3, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'white' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold">Add to Existing Project</Typography>
                <Typography variant="caption" color="text.secondary">Or Start Fresh</Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 2 }}>
                <Box sx={{ flex: 1, display: 'flex', gap: 1 }}>
                    <Select
                        fullWidth
                        size="small"
                        value={selectedProjectId}
                        onChange={(e) => setSelectedProjectId(e.target.value)}
                        disabled={disabled || projects.length === 0}
                        displayEmpty
                        sx={{
                            bgcolor: 'white',
                            borderRadius: 2,
                            '& .MuiOutlinedInput-notchedOutline': { borderColor: '#E5E7EB' }
                        }}
                    >
                        {projects.length === 0 ? (
                            <MenuItem value="" disabled>No projects available</MenuItem>
                        ) : (
                            projects.map(p => (
                                <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
                            ))
                        )}
                    </Select>
                    <Button
                        variant="contained"
                        disableElevation
                        disabled={disabled || !selectedProjectId}
                        onClick={() => onAddToProject(selectedProjectId)}
                        sx={{
                            bgcolor: '#EEF2FF', color: 'primary.main', fontWeight: 'bold',
                            textTransform: 'none', borderRadius: 2, px: 3,
                            '&:hover': { bgcolor: '#E0E7FF' },
                            '&:disabled': { bgcolor: '#F3F4F6', color: '#9CA3AF' }
                        }}
                    >
                        Add
                    </Button>
                </Box>

                <Button
                    variant="contained"
                    startIcon={<PlusCircle size={18} />}
                    onClick={onCreateProject}
                    disabled={disabled}
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
