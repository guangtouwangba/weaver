import { Button, Surface, Text } from '@/components/ui/primitives';
import { Menu, MenuItem } from '@/components/ui/composites';
import { colors } from '@/components/ui/tokens';
import { PlusCircle, ChevronDown } from 'lucide-react';
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
    const [anchorPosition, setAnchorPosition] = useState<{ top: number; left: number } | null>(null);
    const [menuWidth, setMenuWidth] = useState<number>(200);

    // Set default when projects load
    useEffect(() => {
        if (projects.length > 0 && !selectedProjectId) {
            setSelectedProjectId(projects[0].id);
        }
    }, [projects, selectedProjectId]);

    const selectedProjectName = projects.find(p => p.id === selectedProjectId)?.name;

    const handleMenuClick = (event: React.MouseEvent<HTMLButtonElement>) => {
        const rect = event.currentTarget.getBoundingClientRect();
        setAnchorPosition({ top: rect.bottom, left: rect.left });
        setMenuWidth(rect.width);
    };

    const handleMenuClose = () => {
        setAnchorPosition(null);
    };

    const handleProjectSelect = (id: string) => {
        setSelectedProjectId(id);
        handleMenuClose();
    };

    return (
        <Surface
            elevation={0}
            style={{
                padding: 24,
                borderTop: `1px solid ${colors.border.default}`,
                backgroundColor: 'white',
                borderRadius: 0 // Footer usually rectangular or inherits
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <Text variant="bodySmall" style={{ fontWeight: 700 }}>Add to Existing Project</Text>
                <Text variant="caption" color="secondary">Or Start Fresh</Text>
            </div>

            <div style={{ display: 'flex', gap: 16 }}>
                <div style={{ flex: 1, display: 'flex', gap: 8 }}>
                    {/* Project Selector mimicking Select */}
                    <div style={{ flex: 1 }}>
                        <Button
                            variant="outline"
                            onClick={handleMenuClick}
                            disabled={disabled || projects.length === 0}
                            iconRight={<ChevronDown size={16} />}
                            style={{
                                width: '100%',
                                justifyContent: 'space-between',
                                borderColor: colors.border.default,
                                fontWeight: 400,
                                color: selectedProjectId ? colors.text.primary : colors.text.muted
                            }}
                        >
                            {selectedProjectName || (projects.length === 0 ? "No projects available" : "Select Project")}
                        </Button>
                        <Menu
                            anchorPosition={anchorPosition || undefined}
                            open={Boolean(anchorPosition)}
                            onClose={handleMenuClose}
                            style={{ width: menuWidth }}
                        >
                            {projects.length === 0 ? (
                                <MenuItem disabled>No projects available</MenuItem>
                            ) : (
                                projects.map(p => (
                                    <MenuItem
                                        key={p.id}
                                        onClick={() => handleProjectSelect(p.id)}
                                        style={{ backgroundColor: p.id === selectedProjectId ? colors.neutral[100] : undefined }}
                                    >
                                        {p.name}
                                    </MenuItem>
                                ))
                            )}
                        </Menu>
                    </div>

                    <Button
                        variant="primary"
                        disabled={disabled || !selectedProjectId}
                        onClick={() => onAddToProject(selectedProjectId)}
                        style={{
                            backgroundColor: '#EEF2FF',
                            color: colors.primary[600],
                            fontWeight: 700,
                        }}
                    >
                        Add
                    </Button>
                </div>

                <Button
                    variant="primary"
                    icon={<PlusCircle size={18} />}
                    onClick={onCreateProject}
                    disabled={disabled}
                    style={{ backgroundColor: colors.primary[500] }}
                >
                    Create New Project
                </Button>
            </div>
        </Surface>
    );
}
