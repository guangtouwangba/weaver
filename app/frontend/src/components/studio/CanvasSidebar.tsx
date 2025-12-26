'use client';

/**
 * Canvas Sidebar - View switcher for Canvas
 * Allows switching between Free Canvas and Thinking Paths views
 */

import { useEffect } from 'react';
import { Box, Tooltip } from '@mui/material';
import { DashboardIcon, PsychologyIcon } from '@/components/ui/icons';
import { useStudio } from '@/contexts/StudioContext';

export default function CanvasSidebar() {
  const {
    currentView,
    switchView,
  } = useStudio();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if Cmd (Mac) or Ctrl (Windows/Linux) is pressed
      const isModifierPressed = e.metaKey || e.ctrlKey;
      
      if (isModifierPressed && e.key === '1') {
        e.preventDefault();
        switchView('free');
      } else if (isModifierPressed && e.key === '2') {
        e.preventDefault();
        switchView('thinking');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [switchView]);

  return (
    <Box
      sx={{
        width: 48,
        bgcolor: '#FAFAFA',
        borderLeft: '1px solid',
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        py: 2,
        gap: 2,
        zIndex: 10,
      }}
    >
      <Tooltip title="自由画布 (⌘1)" placement="left">
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: currentView === 'free' ? 'primary.main' : 'transparent',
            color: currentView === 'free' ? 'white' : 'text.secondary',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              bgcolor: currentView === 'free' ? 'primary.dark' : 'action.hover',
            },
          }}
          onClick={() => switchView('free')}
        >
          <DashboardIcon size={18} />
        </Box>
      </Tooltip>

      <Tooltip title="思考路径 (⌘2)" placement="left">
        <Box
          sx={{
            width: 32,
            height: 32,
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: currentView === 'thinking' ? 'primary.main' : 'transparent',
            color: currentView === 'thinking' ? 'white' : 'text.secondary',
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              bgcolor: currentView === 'thinking' ? 'primary.dark' : 'action.hover',
            },
          }}
          onClick={() => switchView('thinking')}
        >
          <PsychologyIcon size={18} />
        </Box>
      </Tooltip>
    </Box>
  );
}
