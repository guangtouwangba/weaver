'use client';

import { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Box,
    Typography,
    CircularProgress,
} from '@mui/material';
import { FolderPlus } from 'lucide-react';

interface CreateProjectDialogProps {
    open: boolean;
    onClose: () => void;
    onCreateProject: (name: string, description?: string) => Promise<void>;
}

export default function CreateProjectDialog({
    open,
    onClose,
    onCreateProject,
}: CreateProjectDialogProps) {
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async () => {
        if (!name.trim()) {
            setError('Project name is required');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            await onCreateProject(name.trim(), description.trim() || undefined);
            // Reset form
            setName('');
            setDescription('');
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create project');
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setName('');
            setDescription('');
            setError(null);
            onClose();
        }
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            maxWidth="sm"
            fullWidth
            PaperProps={{
                sx: { borderRadius: 3 }
            }}
        >
            <DialogTitle sx={{ pb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Box sx={{
                        width: 40, height: 40, borderRadius: 2,
                        bgcolor: '#EEF2FF', display: 'flex',
                        alignItems: 'center', justifyContent: 'center'
                    }}>
                        <FolderPlus size={20} className="text-indigo-600" />
                    </Box>
                    <Typography variant="h6" fontWeight="bold">Create New Project</Typography>
                </Box>
            </DialogTitle>

            <DialogContent>
                <Box sx={{ mt: 2 }}>
                    <TextField
                        label="Project Name"
                        placeholder="e.g., Q1 Marketing Research"
                        fullWidth
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={loading}
                        error={!!error}
                        helperText={error}
                        sx={{ mb: 3 }}
                    />

                    <TextField
                        label="Description (optional)"
                        placeholder="Brief description of the project..."
                        fullWidth
                        multiline
                        rows={3}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={loading}
                    />
                </Box>
            </DialogContent>

            <DialogActions sx={{ px: 3, pb: 3 }}>
                <Button
                    onClick={handleClose}
                    disabled={loading}
                    sx={{ textTransform: 'none', color: 'text.secondary' }}
                >
                    Cancel
                </Button>
                <Button
                    variant="contained"
                    onClick={handleSubmit}
                    disabled={loading || !name.trim()}
                    startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
                    sx={{
                        textTransform: 'none',
                        bgcolor: '#6366F1',
                        '&:hover': { bgcolor: '#4F46E5' },
                        borderRadius: 2,
                        px: 3
                    }}
                >
                    {loading ? 'Creating...' : 'Create Project'}
                </Button>
            </DialogActions>
        </Dialog>
    );
}
