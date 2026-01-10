'use client';

import React from 'react';
import { Stack, Tooltip, IconButton } from '@/components/ui';
import { UserMenu } from '@/components/UserMenu';
import { colors, radii, shadows } from '@/components/ui/tokens';
import {
  HomeIcon,
  GridViewIcon,
  SettingsIcon,
  InboxIcon
} from '@/components/ui/icons';
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
        <div
          style={{
            width: 48,
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: radii.xl,
            backgroundColor: isActive ? colors.primary[50] : 'transparent',
            color: isActive ? colors.primary[600] : colors.neutral[500],
            marginBottom: 16,
            transition: 'all 0.2s ease',
            cursor: 'pointer',
          }}
          onMouseEnter={(e) => {
            if (!isActive) {
              e.currentTarget.style.backgroundColor = colors.neutral[100];
              e.currentTarget.style.color = colors.neutral[800];
            }
          }}
          onMouseLeave={(e) => {
            if (!isActive) {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = colors.neutral[500];
            }
          }}
        >
          <Icon size={24} />
        </div>
      </Link>
    </Tooltip>
  );
};

export default function GlobalSidebar() {
  const pathname = usePathname();

  const isStudioActive = pathname.startsWith('/studio');
  const isDashboardActive = pathname === '/dashboard' || pathname === '/';
  const isInboxActive = pathname.startsWith('/inbox');
  const isSettingsActive = pathname.startsWith('/settings');

  return (
    <div
      style={{
        width: SIDEBAR_WIDTH,
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        borderRight: `1px solid ${colors.border.default}`,
        backgroundColor: colors.neutral[100], // Slightly darker base for depth (#F5F5F4)
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 32,
        paddingBottom: 32,
        zIndex: 1200,
      }}
    >
      {/* App Logo - Purple Rounded Square */}
      <div style={{ marginBottom: 48 }}>
        <Tooltip title="Home" placement="right">
          <Link href="/dashboard" style={{ textDecoration: 'none' }}>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: radii.xl,
                backgroundColor: 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: colors.primary[600],
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = colors.primary[50];
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <GridViewIcon size="lg" />
            </div>
          </Link>
        </Tooltip>
      </div>

      {/* Main Navigation */}
      <NavItem
        icon={HomeIcon}
        label="Dashboard"
        href="/dashboard"
        isActive={isDashboardActive}
      />

      <NavItem
        icon={InboxIcon}
        label="Inbox"
        href="/inbox"
        isActive={isInboxActive}
      />

      <NavItem
        icon={GridViewIcon}
        label="Studio"
        href="/studio"
        isActive={isStudioActive}
      />

      <NavItem
        icon={SettingsIcon}
        label="Settings"
        href="/settings"
        isActive={isSettingsActive}
      />

      {/* Spacer */}
      <div style={{ flexGrow: 1 }} />

      {/* User Zone */}
      <div style={{ marginBottom: 16 }}>
        <UserMenu minimized={true} />
      </div>
    </div>
  );
}
