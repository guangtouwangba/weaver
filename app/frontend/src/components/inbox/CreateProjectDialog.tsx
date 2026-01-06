'use client';

import { useState } from 'react';
import {
    Modal,
    Button,
    Spinner,
    Text,
} from '@/components/ui/primitives';
import { TextField } from '@/components/ui/composites';
import { FolderPlus } from 'lucide-react';
import { colors } from '@/components/ui/tokens';

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
        <Modal
            open={open}
            onClose={handleClose}
            size="md" // sm in MUI (sm=600px). Modal md=520, sm=400. Close enough, or use md.
        >
            <Modal.Header>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                        width: 40, height: 40, borderRadius: 8,
                        backgroundColor: '#F0FDFA', display: 'flex', // Teal-50
                        alignItems: 'center', justifyContent: 'center'
                    }}>
                        <FolderPlus size={20} className="text-teal-600" />
                    </div>
                    <Text variant="h6" style={{ fontWeight: 700 }}>Create New Project</Text>
                </div>
            </Modal.Header>

            <Modal.Content>
                <div style={{ marginTop: 16 }}>
                    <TextField
                        label="Project Name"
                        placeholder="e.g., Q1 Marketing Research"
                        fullWidth
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={loading}
                        error={!!error}
                        helperText={error || undefined}
                        style={{ marginBottom: 24 }}
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
                </div>
            </Modal.Content>

            <Modal.Footer>
                <Button
                    variant="ghost"
                    onClick={handleClose}
                    disabled={loading}
                    style={{ color: colors.text.secondary }}
                >
                    Cancel
                </Button>
                <Button
                    variant="primary"
                    onClick={handleSubmit}
                    disabled={loading || !name.trim()}
                    loading={loading} // Button primitive supports loading
                >
                    {loading ? 'Creating...' : 'Create Project'}
                </Button>
            </Modal.Footer>
        </Modal>
    );
}
