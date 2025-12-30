'use client';

import { useState } from 'react';
import { Box } from '@mui/material';
import GlobalLayout from '@/components/layout/GlobalLayout';
import InboxHeader from '@/components/inbox/InboxHeader';
import InboxSidebar from '@/components/inbox/InboxSidebar';
import InboxPreviewPanel from '@/components/inbox/InboxPreviewPanel';
import { InboxItem } from '@/components/inbox/InboxItemCard';

// Mock Data matching the design
const MOCK_ITEMS: InboxItem[] = [
  {
    id: '1',
    title: 'Competitor Analysis: Acme Corp launches new collaboration features',
    type: 'article',
    source: 'Web Extension',
    source_url: 'https://techblog.com/acme-corp-collab',
    addedAt: 'Added today',
    tags: ['Strategy', 'Q1']
  },
  {
    id: '2',
    title: 'Q4 Earnings Call Recording',
    type: 'video',
    source: 'Manual Upload',
    addedAt: 'Added yesterday',
    tags: ['Finance']
  },
  {
    id: '3',
    title: 'Idea: Mobile App Onboarding',
    type: 'note',
    source: 'Quick Note',
    addedAt: 'Added 2 days ago',
    tags: ['Product', 'UX']
  },
  {
    id: '4',
    title: '2024 Design Trends Report.pdf',
    type: 'pdf',
    source: 'Web Extension',
    addedAt: 'Added 3 days ago',
    tags: []
  },
  {
    id: '5',
    title: 'TechCrunch: AI Startups Funding',
    type: 'link',
    source: 'Web Extension',
    source_url: 'https://techcrunch.com/ai-funding',
    addedAt: 'Added 3 days ago',
    tags: ['Market']
  },
];

export default function InboxPage() {
  const [items, setItems] = useState<InboxItem[]>(MOCK_ITEMS);
  const [selectedId, setSelectedId] = useState<string | null>(MOCK_ITEMS[0].id);
  const [searchQuery, setSearchQuery] = useState('');

  const selectedItem = items.find(i => i.id === selectedId) || null;

  const handleSearch = (q: string) => {
    setSearchQuery(q);
    // In real app, this would filter via API or Client-side list
  };

  const handleAddToProject = (projectId: string) => {
    console.log(`Adding item ${selectedId} to project ${projectId}`);
    // Simulate removal
    if (selectedId) {
      const nextItems = items.filter(i => i.id !== selectedId);
      setItems(nextItems);
      setSelectedId(nextItems[0]?.id || null);
    }
  };

  const handleCreateProject = () => {
    console.log('Create new project flow triggered');
  };

  return (
    <GlobalLayout>
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: '#F9FAFB' }}>

        {/* Header */}
        <InboxHeader
          searchQuery={searchQuery}
          onSearchChange={handleSearch}
          onFilterClick={() => { }}
          onNewItemClick={() => { }}
        />

        {/* Main Content: Split View */}
        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

          {/* Left Sidebar */}
          <InboxSidebar
            items={items}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />

          {/* Right Preview Panel */}
          <InboxPreviewPanel
            item={selectedItem}
            onEdit={() => { }}
            onDelete={() => { }}
            onAddToProject={handleAddToProject}
            onCreateProject={handleCreateProject}
          />

        </Box>
      </Box>
    </GlobalLayout>
  );
}
