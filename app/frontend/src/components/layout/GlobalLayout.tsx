'use client';

import React from 'react';
import GlobalSidebar from './GlobalSidebar';
import { colors } from '@/components/ui/tokens';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

const SIDEBAR_WIDTH = 72;

export default function GlobalLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <GlobalSidebar />
        <main
          style={{
            flexGrow: 1,
            marginLeft: SIDEBAR_WIDTH,
            width: `calc(100vw - ${SIDEBAR_WIDTH}px)`,
            maxWidth: `calc(100vw - ${SIDEBAR_WIDTH}px)`,
            overflow: 'hidden',
            minHeight: '100vh',
            backgroundColor: colors.background.paper,
          }}
        >
          {children}
        </main>
      </div>
    </ProtectedRoute>
  );
}
