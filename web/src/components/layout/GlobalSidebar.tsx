'use client';

import React from 'react';
import { Box, IconButton, Avatar, Tooltip, Divider } from '@mui/material';
import { 
  Command, 
  Inbox, 
  Layout, 
  Brain, 
  Settings,
  FolderKanban
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const SIDEBAR_WIDTH = 72;

interface NavItemProps {
  icon: React.ElementType;
  label: string;
  href: string;
  isActive?: boolean;
  isLogo?: boolean;
}

const NavItem = ({ icon: Icon, label, href, isActive, isLogo }: NavItemProps) => {
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
            borderRadius: isLogo ? 2 : '12px', // Rounded rect for Logo, Circle/Rounded for others
            backgroundColor: isActive 
              ? 'rgba(0, 0, 0, 0.05)' 
              : isLogo 
                ? 'common.black' 
                : 'transparent',
            color: isLogo 
              ? 'common.white' 
              : isActive 
                ? 'primary.main' 
                : 'text.secondary',
            '&:hover': {
              backgroundColor: isLogo 
                ? 'common.black' 
                : 'rgba(0, 0, 0, 0.05)',
              color: isLogo ? 'common.white' : 'primary.main',
            },
            mb: 2,
            transition: 'all 0.2s ease',
          }}
        >
          <Icon size={isLogo ? 20 : 24} strokeWidth={isLogo ? 3 : 2} />
        </Box>
      </Link>
    </Tooltip>
  );
};

export default function GlobalSidebar() {
  const pathname = usePathname();

  const isStudioActive = pathname.startsWith('/studio');
  const isDashboardActive = pathname === '/dashboard' || pathname === '/';

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
        py: 3,
        zIndex: 1200, // Highest z-index
      }}
    >
      {/* Weaver Logo Zone */}
      <NavItem 
        icon={Command} 
        label="Weaver" 
        href="/dashboard" 
        isLogo 
      />

      <Divider sx={{ width: '40px', mb: 3 }} />

      {/* Context Zone */}
      <NavItem 
        icon={Inbox} 
        label="Inbox Mode" 
        href="/inbox" 
        isActive={pathname.startsWith('/inbox')}
      />

      <NavItem 
        icon={FolderKanban} 
        label="All Projects" 
        href="/projects" 
        isActive={pathname.startsWith('/projects')}
      />
      
      <NavItem 
        icon={Layout} 
        label="Studio Mode" 
        href="/studio" 
        isActive={isStudioActive}
      />
      
      <NavItem 
        icon={Brain} 
        label="Brain Mode" 
        href="/brain" 
        isActive={pathname.startsWith('/brain')}
      />

      {/* Spacer */}
      <Box sx={{ flexGrow: 1 }} />

      {/* User Zone */}
      <Tooltip title="User Settings" placement="right">
        <IconButton 
          component={Link} 
          href="/settings"
          sx={{ mb: 2 }}
        >
          <Avatar 
            sx={{ 
              width: 36, 
              height: 36, 
              bgcolor: 'grey.300',
              fontSize: 14,
              color: 'text.primary'
            }}
          >
            AL
          </Avatar>
        </IconButton>
      </Tooltip>
    </Box>
  );
}

