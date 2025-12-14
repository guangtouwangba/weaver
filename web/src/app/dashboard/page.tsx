'use client';

import { useState } from 'react';
import GlobalLayout from "@/components/layout/GlobalLayout";
import { Box, Typography, Button } from "@mui/material";
import { Plus } from "lucide-react";
import Link from 'next/link';
import CreateProjectDialog from "@/components/dialogs/CreateProjectDialog";

export default function DashboardPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  return (
    <GlobalLayout>
      <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb: 6 }}>
          <Typography variant="h4" fontWeight="600" gutterBottom>
            Welcome back, Alex
          </Typography>
          <Typography variant="body1" color="text.secondary">
            You have 12 cards due for review today.
          </Typography>
        </Box>

        {/* Smart Ingestion Zone Placeholder */}
        <Box 
          sx={{ 
            border: '2px dashed', 
            borderColor: 'divider', 
            borderRadius: 4, 
            p: 6, 
            textAlign: 'center',
            mb: 6,
            bgcolor: 'background.default'
          }}
        >
          <Typography variant="h6" gutterBottom>
            Create New Knowledge Project
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Drag folders here to start, or drop files to Inbox
          </Typography>
          <Button 
            variant="contained" 
            startIcon={<Plus />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Project
          </Button>
        </Box>

        {/* Create Project Dialog */}
        <CreateProjectDialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
        />

        {/* Active Projects Placeholder */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" fontWeight="600">
            Active Projects
          </Typography>
          <Button 
            variant="text" 
            size="small" 
            component={Link}
            href="/projects"
            sx={{ color: 'text.secondary', textTransform: 'none' }}
          >
            View All
          </Button>
        </Box>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 3 }}>
          {[1, 2, 3].map((i) => (
            <Box 
              key={i}
              sx={{ 
                p: 3, 
                borderRadius: 3, 
                border: '1px solid', 
                borderColor: 'divider',
                bgcolor: 'background.paper',
                cursor: 'pointer',
                '&:hover': { borderColor: 'primary.main' }
              }}
            >
              <Typography variant="subtitle1" fontWeight="600">
                Project Alpha {i}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Last edited 2 mins ago
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </GlobalLayout>
  );
}

