'use client';

import React from 'react';
import { Box, IconButton, Avatar, Tooltip } from '@mui/material';
import { 
  Home,
  LayoutGrid,
  Settings,
  Grid2x2
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const SIDEBAR_WIDTH = 72;

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  href: string;
  isActive?: boolean;
}

const NavItem = ({ icon: Icon, label, href, isActive }: NavItemProps) => {
  return (
    <Tooltip title={label} placement="right">
      <Link href={href} style={{ textDecoration: 'none' }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '16px', // Rounded square like image
            backgroundColor: isActive 
              ? '#eff6ff' // Light blue/indigo background
              : 'transparent',
            color: isActive 
              ? '#4f46e5' // Indigo icon
              : '#64748b', // Slate-500 for inactive
            '&:hover': {
              backgroundColor: isActive 
                ? '#eff6ff' 
                : 'rgba(0, 0, 0, 0.04)',
              color: isActive ? '#4f46e5' : '#1e293b',
            },
            mb: 2,
            transition: 'all 0.2s ease',
          }}
        >
          <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
        </Box>
      </Link>
    </Tooltip>
  );
};

export default function GlobalSidebar() {
  const pathname = usePathname();

  const isStudioActive = pathname.startsWith('/studio');
  const isDashboardActive = pathname === '/dashboard' || pathname === '/';
  const isSettingsActive = pathname.startsWith('/settings');

  return (
    <Box
      sx={{
        width: SIDEBAR_WIDTH,
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        borderRight: '1px solid',
        borderColor: 'divider',
        backgroundColor: 'background.default',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        py: 4, // Increased padding
        zIndex: 1200,
      }}
    >
      {/* App Logo - Purple Rounded Square */}
      <Box sx={{ mb: 6 }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)', // Indigo gradient
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            boxShadow: '0 8px 16px rgba(79, 70, 229, 0.2)',
          }}
        >
          <Grid2x2 size={24} strokeWidth={2.5} />
        </Box>
      </Box>

      {/* Main Navigation */}
      <NavItem 
        icon={Home} 
        label="Dashboard" 
        href="/dashboard" 
        isActive={isDashboardActive}
      />
      
      <NavItem 
        icon={LayoutGrid} 
        label="Studio" 
        href="/studio" 
        isActive={isStudioActive}
      />

      <NavItem 
        icon={Settings} 
        label="Settings" 
        href="/settings" 
        isActive={isSettingsActive}
      />

      {/* Spacer */}
      <Box sx={{ flexGrow: 1 }} />

      {/* User Zone */}
      <Tooltip title="User Profile" placement="right">
        <IconButton 
          component={Link} 
          href="/settings"
          sx={{ mb: 2, p: 0.5 }}
        >
          <Avatar 
            sx={{ 
              width: 40, 
              height: 40, 
              bgcolor: '#8b5cf6', // Purple
              fontSize: 14,
              fontWeight: 600,
              color: 'white',
              border: '2px solid white',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
          >
            AL
          </Avatar>
        </IconButton>
      </Tooltip>
    </Box>
  );
}
