'use client';

import React, { useEffect, useCallback } from 'react';
import { IconButton, Text, Button } from '@/components/ui/primitives';
import { CloseIcon, ExternalLinkIcon } from '@/components/ui/icons';
import { colors, radii, shadows } from '@/components/ui/tokens';

interface YouTubePlayerModalProps {
  open: boolean;
  onClose: () => void;
  videoId: string;
  title?: string;
  channelName?: string;
  viewCount?: string;
  publishedAt?: string;
  sourceUrl?: string;
}

export default function YouTubePlayerModal({
  open,
  onClose,
  videoId,
  title = 'Video',
  channelName,
  viewCount,
  publishedAt,
  sourceUrl,
}: YouTubePlayerModalProps) {
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

  const youtubeUrl = sourceUrl || `https://www.youtube.com/watch?v=${videoId}`;
  const embedUrl = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleOpenInYouTube = () => {
    window.open(youtubeUrl, '_blank', 'noopener,noreferrer');
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
          backgroundColor: colors.background.default,
          borderRadius: radii.xl,
          boxShadow: shadows.xl,
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: `1px solid ${colors.border.default}`,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
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
            <Button
              variant="ghost"
              size="sm"
              onClick={handleOpenInYouTube}
              style={{ gap: 6 }}
            >
              <ExternalLinkIcon size="sm" />
              Open in YouTube
            </Button>
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

        {/* Video Player */}
        <div
          style={{
            position: 'relative',
            width: '100%',
            paddingBottom: '56.25%', // 16:9 aspect ratio
            backgroundColor: '#000',
          }}
        >
          <iframe
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              border: 'none',
            }}
            src={embedUrl}
            title={title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          />
        </div>

        {/* Footer - Video Info */}
        {(channelName || viewCount || publishedAt) && (
          <div
            style={{
              padding: '16px 20px',
              borderTop: `1px solid ${colors.border.default}`,
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            {/* Channel Avatar Placeholder */}
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                backgroundColor: colors.background.muted,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
              }}
            >
              📺
            </div>
            <div>
              {channelName && (
                <Text variant="body" style={{ fontWeight: 500 }}>
                  {channelName}
                </Text>
              )}
              {(viewCount || publishedAt) && (
                <Text variant="bodySmall" color="secondary">
                  {[viewCount, publishedAt].filter(Boolean).join(' • ')}
                </Text>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

