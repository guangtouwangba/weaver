import { Box, Button, IconButton, Paper, Typography, Skeleton } from '@mui/material';
import { Pencil, Trash2, ExternalLink, FileText } from 'lucide-react';
import TagChip from './TagChip';
import { InboxItem } from './InboxItemCard';
import InboxActionFooter, { ProjectOption } from './InboxActionFooter';

interface InboxPreviewPanelProps {
    item: InboxItem | null;
    projects: ProjectOption[];
    onEdit: () => void;
    onDelete: () => void;
    onAddToProject: (projectId: string) => void;
    onCreateProject: () => void;
}

export default function InboxPreviewPanel({
    item, projects, onEdit, onDelete, onAddToProject, onCreateProject
}: InboxPreviewPanelProps) {

    if (!item) {
        return (
            <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#F9FAFB' }}>
                <Typography color="text.secondary">Select an item to view details</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', overflow: 'hidden', bgcolor: '#F9FAFB' }}>

            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 4, pb: 2 }}>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <TagChip label={item.type.charAt(0).toUpperCase() + item.type.slice(1)} color="#6366F1" />
                        <Typography variant="caption" color="text.secondary">
                            • Collected via {item.source}
                        </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton size="small" onClick={onEdit}><Pencil size={18} className="text-gray-400" /></IconButton>
                        <IconButton size="small" onClick={onDelete}><Trash2 size={18} className="text-gray-400" /></IconButton>
                    </Box>
                </Box>

                <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ lineHeight: 1.3 }}>
                    {item.title}
                </Typography>
                {item.source_url && (
                    <Button
                        startIcon={<ExternalLink size={14} />}
                        href={item.source_url}
                        target="_blank"
                        sx={{
                            textTransform: 'none',
                            color: 'primary.main',
                            mb: 4,
                            p: 0,
                            minWidth: 0,
                            '&:hover': { bgcolor: 'transparent', textDecoration: 'underline' }
                        }}
                    >
                        {item.source_url}
                    </Button>
                )}

                <Paper elevation={0} sx={{ p: 4, borderRadius: 3, border: '1px solid', borderColor: 'divider', minHeight: 400 }}>
                    <Box sx={{ mb: 4 }}>
                        <Skeleton variant="text" width="80%" height={30} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="100%" height={30} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="90%" height={30} sx={{ mb: 4, bgcolor: '#F3F4F6' }} />

                        <Box sx={{ height: 200, bgcolor: '#F9FAFB', borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 4 }}>
                            <FileText size={48} className="text-gray-300" />
                        </Box>

                        <Skeleton variant="text" width="100%" height={24} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="95%" height={24} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="85%" height={24} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                    </Box>

                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                        <Button
                            variant="outlined"
                            sx={{ borderRadius: 6, textTransform: 'none', color: 'text.secondary', borderColor: '#E5E7EB' }}
                        >
                            Read Full Article
                        </Button>
                    </Box>
                </Paper>

            </Box>

            <InboxActionFooter
                projects={projects}
                onAddToProject={onAddToProject}
                onCreateProject={onCreateProject}
            />

        </Box>
    );
}
