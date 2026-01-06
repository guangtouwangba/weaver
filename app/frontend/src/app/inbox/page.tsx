'use client';

import { useState, useEffect, useCallback } from 'react';
import { Stack, Spinner } from '@/components/ui/primitives';
import GlobalLayout from '@/components/layout/GlobalLayout';
import InboxHeader from '@/components/inbox/InboxHeader';
import InboxSidebar from '@/components/inbox/InboxSidebar';
import InboxPreviewPanel from '@/components/inbox/InboxPreviewPanel';
import CreateProjectDialog from '@/components/dialogs/CreateProjectDialog';
import { InboxItem as InboxItemCardType } from '@/components/inbox/InboxItemCard';
import { ProjectOption } from '@/components/inbox/InboxActionFooter';
import { inboxApi, projectsApi, InboxItem, Project } from '@/lib/api';

// Transform API response to component format
function transformItem(item: InboxItem): InboxItemCardType {
    const now = new Date();
    const collected = new Date(item.collected_at);
    const diffMs = now.getTime() - collected.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    let addedAt = 'Added today';
    if (diffDays === 1) addedAt = 'Added yesterday';
    else if (diffDays > 1) addedAt = `Added ${diffDays} days ago`;

    return {
        id: item.id,
        title: item.title || 'Untitled',
        type: item.type as InboxItemCardType['type'],
        source: item.source_type === 'extension' ? 'Web Extension' :
            item.source_type === 'manual' ? 'Manual' : item.source_type,
        source_url: item.source_url || undefined,
        addedAt,
        tags: item.tags.map(t => t.name),
    };
}

export default function InboxPage() {
    const [items, setItems] = useState<InboxItemCardType[]>([]);
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [projects, setProjects] = useState<ProjectOption[]>([]);
    const [createDialogOpen, setCreateDialogOpen] = useState(false);

    // Fetch inbox items
    const fetchItems = useCallback(async () => {
        try {
            setLoading(true);
            const response = await inboxApi.list({
                is_processed: false,
                q: searchQuery || undefined
            });
            const transformed = response.items.map(transformItem);
            setItems(transformed);
            if (transformed.length > 0 && !selectedId) {
                setSelectedId(transformed[0].id);
            }
        } catch (error) {
            console.error('Failed to fetch inbox items:', error);
        } finally {
            setLoading(false);
        }
    }, [searchQuery, selectedId]);

    // Fetch projects for assignment dropdown
    const fetchProjects = useCallback(async () => {
        try {
            const response = await projectsApi.list();
            setProjects(response.items.map(p => ({ id: p.id, name: p.name })));
        } catch (error) {
            console.error('Failed to fetch projects:', error);
        }
    }, []);

    useEffect(() => {
        fetchItems();
        fetchProjects();
    }, [fetchItems, fetchProjects]);

    const selectedItem = items.find(i => i.id === selectedId) || null;

    const handleSearch = (q: string) => {
        setSearchQuery(q);
    };

    const handleAddToProject = async (projectId: string) => {
        if (!selectedId) return;
        try {
            await inboxApi.assignToProject(selectedId, projectId);
            // Remove from list
            const nextItems = items.filter(i => i.id !== selectedId);
            setItems(nextItems);
            setSelectedId(nextItems[0]?.id || null);
        } catch (error) {
            console.error('Failed to assign item to project:', error);
        }
    };

    const handleDelete = async () => {
        if (!selectedId) return;
        try {
            await inboxApi.delete(selectedId);
            const nextItems = items.filter(i => i.id !== selectedId);
            setItems(nextItems);
            setSelectedId(nextItems[0]?.id || null);
        } catch (error) {
            console.error('Failed to delete item:', error);
        }
    };

    const handleProjectCreated = async (newProject: any) => {
        // Add to project list
        setProjects(prev => [...prev, { id: newProject.id, name: newProject.name }]);
        // Optionally auto-assign current item to new project
        if (selectedId) {
            await handleAddToProject(newProject.id);
        }
    };

    if (loading) {
        return (
            <GlobalLayout>
                <Stack align="center" justify="center" sx={{ height: '100vh' }}>
                    <Spinner />
                </Stack>
            </GlobalLayout>
        );
    }

    return (
        <GlobalLayout>
            <Stack sx={{ height: '100vh', bgcolor: '#F9FAFB' }}>

                <InboxHeader
                    searchQuery={searchQuery}
                    onSearchChange={handleSearch}
                    onFilterClick={() => { }}
                    onNewItemClick={() => { }}
                />

                <Stack direction="row" sx={{ flex: 1, overflow: 'hidden' }}>

                    <InboxSidebar
                        items={items}
                        selectedId={selectedId}
                        onSelect={setSelectedId}
                    />

                    <InboxPreviewPanel
                        item={selectedItem}
                        projects={projects}
                        onEdit={() => { }}
                        onDelete={handleDelete}
                        onAddToProject={handleAddToProject}
                        onCreateProject={() => setCreateDialogOpen(true)}
                    />

                </Stack>
            </Stack>

            <CreateProjectDialog
                open={createDialogOpen}
                onClose={() => setCreateDialogOpen(false)}
                onProjectCreated={handleProjectCreated}
            />
        </GlobalLayout>
    );
}
