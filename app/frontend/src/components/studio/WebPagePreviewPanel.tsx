'use client';

import React from 'react';
import { Button, Text } from '@/components/ui/primitives';
import { ExternalLinkIcon, AddIcon } from '@/components/ui/icons';
import { colors } from '@/components/ui/tokens';
import Image from 'next/image';

interface WebPagePreviewPanelProps {
  title: string;
  sourceUrl: string;
  content?: string;
  thumbnailUrl?: string;
  onAddToCanvas?: () => void;
}

export default function WebPagePreviewPanel({
  title,
  sourceUrl,
  content,
  thumbnailUrl,
  onAddToCanvas,
}: WebPagePreviewPanelProps) {

  // Extract domain
  const getDomain = (url: string) => {
    try {
      return new URL(url).hostname.replace('www.', '');
    } catch {
      return url;
    }
  };

  const domain = getDomain(sourceUrl);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: 'white',
      overflow: 'hidden'
    }}>
      {/* Header Image / Thumbnail */}
      <div style={{
        height: 160,
        backgroundColor: '#F3F4F6',
        position: 'relative',
        borderBottom: `1px solid ${colors.border.default}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        {thumbnailUrl ? (
          <div style={{ position: 'relative', width: '100%', height: '100%' }}>
            <Image
              src={thumbnailUrl}
              alt={title}
              fill
              style={{ objectFit: 'cover' }}
              unoptimized // If external URL
            />
          </div>
        ) : (
          <div style={{ textAlign: 'center', opacity: 0.5 }}>
            <span style={{ fontSize: 48 }}>🌐</span>
          </div>
        )}

        {/* Domain Badge Overlay */}
        <div style={{
          position: 'absolute',
          bottom: 12,
          left: 12,
          backgroundColor: 'rgba(0,0,0,0.6)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: 4,
          fontSize: 12,
          fontWeight: 500,
        }}>
          {domain}
        </div>
      </div>

      {/* Content Area */}
      <div style={{ flex: 1, padding: 20, overflowY: 'auto' }}>
        <Text variant="h5" style={{ fontWeight: 600, marginBottom: 16, lineHeight: 1.3 }}>
          {title}
        </Text>

        {/* Metadata Row */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 20, fontSize: 13, color: '#6B7280' }}>
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ display: 'flex', alignItems: 'center', gap: 4, color: colors.primary.main, textDecoration: 'none' }}
            >
              <ExternalLinkIcon size={14} /> Open Original
            </a>
        </div>

        {/* Article Preview */}
        <div style={{
          fontSize: 15,
          lineHeight: 1.6,
          color: '#374151',
          fontFamily: 'Inter, system-ui, sans-serif'
        }}>
           {content ? (
             content.substring(0, 1000).split('\n').map((p, i) =>
               p.trim() ? <p key={i} style={{ marginBottom: 12 }}>{p}</p> : null
             )
           ) : (
             <p style={{ fontStyle: 'italic', color: '#9CA3AF' }}>No preview content available.</p>
           )}
           {content && content.length > 1000 && (
             <div style={{
               marginTop: 16,
               padding: 12,
               backgroundColor: '#F9FAFB',
               textAlign: 'center',
               borderRadius: 8,
               fontSize: 13,
               color: '#6B7280'
             }}>
               Preview truncated. Add to canvas to read full content.
             </div>
           )}
        </div>
      </div>

      {/* Footer Actions */}
      <div style={{
        padding: 16,
        borderTop: `1px solid ${colors.border.default}`,
        display: 'flex',
        gap: 12,
        backgroundColor: '#FAFAFA'
      }}>
        <Button
          variant="primary"
          fullWidth
          onClick={onAddToCanvas}
          style={{ justifyContent: 'center', gap: 8 }}
        >
          <AddIcon size={18} /> Add to Canvas
        </Button>
      </div>
    </div>
  );
}
