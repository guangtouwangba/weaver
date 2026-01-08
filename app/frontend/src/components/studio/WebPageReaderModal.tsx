'use client';

import React, { useEffect, useCallback } from 'react';
import { IconButton, Text, Button } from '@/components/ui/primitives';
import { CloseIcon, ExternalLinkIcon } from '@/components/ui/icons';
import { colors, radii, shadows } from '@/components/ui/tokens';

interface WebPageReaderModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  content: string;
  sourceUrl?: string;
  domain?: string;
}

export default function WebPageReaderModal({
  open,
  onClose,
  title = 'Web Page',
  content,
  sourceUrl,
  domain,
}: WebPageReaderModalProps) {
  // Handle Escape key to close
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, handleKeyDown]);

  if (!open) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleOpenInBrowser = () => {
    if (sourceUrl) {
      window.open(sourceUrl, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        padding: 24,
      }}
      onClick={handleBackdropClick}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 960,
          height: '85vh',
          backgroundColor: colors.background.default,
          borderRadius: radii.xl,
          boxShadow: shadows.xl,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 24px',
            borderBottom: `1px solid ${colors.border.default}`,
            backgroundColor: 'white',
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              {domain && (
                <Text
                    variant="bodySmall"
                    style={{
                        color: colors.primary.main,
                        fontWeight: 500,
                        backgroundColor: colors.primary.muted,
                        padding: '2px 8px',
                        borderRadius: 4,
                    }}
                >
                    {domain}
                </Text>
              )}
            </div>
            <Text
              variant="h6"
              style={{
                fontWeight: 600,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {title}
            </Text>
          </div>
          <div style={{ display: 'flex', gap: 8, marginLeft: 16 }}>
            {sourceUrl && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleOpenInBrowser}
                style={{ gap: 6 }}
              >
                <ExternalLinkIcon size="sm" />
                Open Original
              </Button>
            )}
            <IconButton
              variant="ghost"
              size="sm"
              onClick={onClose}
              aria-label="Close"
            >
              <CloseIcon size="sm" />
            </IconButton>
          </div>
        </div>

        {/* Reader Content */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '40px 60px',
            backgroundColor: '#FCFCFC',
          }}
        >
          <div style={{ maxWidth: 720, margin: '0 auto' }}>
             {/* Article Header */}
             <div style={{ marginBottom: 32 }}>
                <Text variant="h3" style={{ fontWeight: 700, lineHeight: 1.3, marginBottom: 16 }}>
                    {title}
                </Text>
                {sourceUrl && (
                    <Text variant="bodySmall" color="secondary" style={{ display: 'block' }}>
                        Source: <a href={sourceUrl} target="_blank" rel="noopener noreferrer" style={{ color: colors.primary.main }}>{sourceUrl}</a>
                    </Text>
                )}
             </div>

             {/* Main Content */}
             <div style={{
                 fontSize: 18,
                 lineHeight: 1.7,
                 color: '#374151',
                 fontFamily: 'Inter, system-ui, sans-serif'
             }}>
                 {content ? (
                     content.split('\n').map((paragraph, idx) => (
                         paragraph.trim() ? <p key={idx} style={{ marginBottom: 20 }}>{paragraph}</p> : <br key={idx} />
                     ))
                 ) : (
                     <div style={{
                         display: 'flex',
                         flexDirection: 'column',
                         alignItems: 'center',
                         justifyContent: 'center',
                         padding: 60,
                         color: '#9CA3AF',
                         textAlign: 'center'
                     }}>
                         <Text style={{ fontSize: 48, marginBottom: 16 }}>📄</Text>
                         <Text>No readable content extracted from this page.</Text>
                         {sourceUrl && (
                             <Button
                                variant="outlined"
                                onClick={handleOpenInBrowser}
                                style={{ marginTop: 16 }}
                             >
                                Open in Browser
                             </Button>
                         )}
                     </div>
                 )}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
