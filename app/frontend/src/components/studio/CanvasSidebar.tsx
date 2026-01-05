'use client';

/**
 * Canvas Sidebar - View switcher for Canvas
 * Allows switching between Free Canvas and Thinking Paths views
 */

import { useEffect } from 'react';
import { Stack, Tooltip, IconButton } from '@/components/ui';
import { colors, radii } from '@/components/ui/tokens';
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
    <Stack
      direction="column"
      align="center"
      gap={2}
      sx={{
        width: 48,
        bgcolor: colors.background.subtle,
        borderLeft: `1px solid ${colors.border.default}`,
        py: 2,
        zIndex: 10,
      }}
    >
      <Tooltip title="自由画布 (⌘1)" placement="left">
        <IconButton
          size="sm"
          variant={currentView === 'free' ? 'default' : 'ghost'}
          active={currentView === 'free'}
          onClick={() => switchView('free')}
          sx={{
            bgcolor: currentView === 'free' ? colors.primary[500] : 'transparent',
            color: currentView === 'free' ? 'white' : colors.text.secondary,
            '&:hover': {
              bgcolor: currentView === 'free' ? colors.primary[600] : colors.neutral[100],
            },
          }}
        >
          <DashboardIcon size={18} />
        </IconButton>
      </Tooltip>

      <Tooltip title="思考路径 (⌘2)" placement="left">
        <IconButton
          size="sm"
          variant={currentView === 'thinking' ? 'default' : 'ghost'}
          active={currentView === 'thinking'}
          onClick={() => switchView('thinking')}
          sx={{
            bgcolor: currentView === 'thinking' ? colors.primary[500] : 'transparent',
            color: currentView === 'thinking' ? 'white' : colors.text.secondary,
            '&:hover': {
              bgcolor: currentView === 'thinking' ? colors.primary[600] : colors.neutral[100],
            },
          }}
        >
          <PsychologyIcon size={18} />
        </IconButton>
      </Tooltip>
    </Stack>
  );
}
