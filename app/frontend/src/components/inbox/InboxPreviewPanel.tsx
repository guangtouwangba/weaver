import {
    Button,
    IconButton,
    Surface,
    Text,
    Skeleton,
} from '@/components/ui/primitives';
import { colors, radii } from '@/components/ui/tokens';
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
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F9FAFB' }}>
                <Text color="secondary">Select an item to view details</Text>
            </div>
        );
    }

    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', overflow: 'hidden', backgroundColor: '#F9FAFB' }}>

            <div style={{ flexGrow: 1, overflowY: 'auto', padding: 32, paddingBottom: 16 }}>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <TagChip label={item.type.charAt(0).toUpperCase() + item.type.slice(1)} color="#6366F1" />
                        <Text variant="caption" color="secondary">
                            • Collected via {item.source}
                        </Text>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <IconButton size="sm" onClick={onEdit}><Pencil size={18} className="text-gray-400" /></IconButton>
                        <IconButton size="sm" onClick={onDelete}><Trash2 size={18} className="text-gray-400" /></IconButton>
                    </div>
                </div>

                <Text variant="h5" style={{ fontWeight: 700, lineHeight: 1.3, marginBottom: 8 }}>
                    {item.title}
                </Text>
                {item.source_url && (
                    <Button
                        variant="ghost"
                        icon={<ExternalLink size={14} />}
                        onClick={() => window.open(item.source_url, '_blank')}
                        style={{
                            textTransform: 'none',
                            color: colors.primary[500],
                            marginBottom: 32,
                            padding: 0,
                            minWidth: 0,
                            height: 'auto',
                            justifyContent: 'flex-start'
                        }}
                    >
                        {item.source_url}
                    </Button>
                )}

                <Surface
                    elevation={0}
                    style={{
                        padding: 32,
                        borderRadius: radii.xl,
                        border: `1px solid ${colors.border.default}`,
                        minHeight: 400
                    }}
                >
                    <div style={{ marginBottom: 32 }}>
                        <Skeleton variant="text" width="80%" height={30} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="100%" height={30} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="90%" height={30} sx={{ mb: 4, bgcolor: '#F3F4F6' }} />

                        <div style={{ height: 200, backgroundColor: '#F9FAFB', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 32 }}>
                            <FileText size={48} className="text-gray-300" />
                        </div>

                        <Skeleton variant="text" width="100%" height={24} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="95%" height={24} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                        <Skeleton variant="text" width="85%" height={24} sx={{ mb: 1, bgcolor: '#F3F4F6' }} />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <Button
                            variant="outline"
                            style={{ borderRadius: 24, color: colors.text.secondary, borderColor: colors.border.default }}
                        >
                            Read Full Article
                        </Button>
                    </div>
                </Surface>

            </div>

            <InboxActionFooter
                projects={projects}
                onAddToProject={onAddToProject}
                onCreateProject={onCreateProject}
            />

        </div>
    );
}
