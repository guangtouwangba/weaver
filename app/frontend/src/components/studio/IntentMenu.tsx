'use client';

import React from 'react';
import { Surface, Stack, Button, Text } from '@/components/ui';
import { DescriptionIcon, PlaylistAddCheckIcon } from '@/components/ui/icons';
import { colors, shadows } from '@/components/ui/tokens';

export type IntentAction = 'draft_article' | 'action_list';

interface IntentMenuProps {
  position: { x: number; y: number };
  onSelect: (action: IntentAction) => void;
  onClose: () => void;
}

export default function IntentMenu({ position, onSelect, onClose }: IntentMenuProps) {
  return (
    <>
      {/* Backdrop to catch clicks outside */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 1999,
        }}
        onClick={onClose}
      />
      
      {/* Menu */}
      <div
        style={{
          position: 'fixed',
          left: position.x,
          top: position.y,
          zIndex: 2000,
          animation: 'fadeInUp 0.2s ease-out',
        }}
      >
        <Surface
          elevation={2}
          radius="lg"
          bordered
          style={{
            padding: 8,
            minWidth: 180,
            background: `linear-gradient(135deg, 
              rgba(255,255,255,0.95) 0%, 
              rgba(248,250,252,0.95) 100%)`,
            backdropFilter: 'blur(8px)',
            boxShadow: `${shadows.lg}, 0 0 0 1px rgba(102, 126, 234, 0.1)`,
          }}
        >
          <Stack direction="column" gap={1}>
            <Text
              variant="caption"
              color="secondary"
              style={{
                padding: '4px 8px',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                fontSize: '0.65rem',
              }}
            >
              Generate with AI
            </Text>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSelect('draft_article')}
              style={{
                justifyContent: 'flex-start',
                padding: '10px 12px',
                borderRadius: 8,
                transition: 'all 0.15s ease',
              }}
            >
              <Stack direction="row" gap={2} align="center">
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <DescriptionIcon size={16} style={{ color: '#fff' }} />
                </div>
                <Stack direction="column" gap={0} align="start">
                  <Text style={{ fontWeight: 500, fontSize: '0.875rem' }}>Draft Article</Text>
                  <Text variant="caption" color="secondary" style={{ fontSize: '0.7rem' }}>
                    Create a document from selection
                  </Text>
                </Stack>
              </Stack>
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSelect('action_list')}
              style={{
                justifyContent: 'flex-start',
                padding: '10px 12px',
                borderRadius: 8,
                transition: 'all 0.15s ease',
              }}
            >
              <Stack direction="row" gap={2} align="center">
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <PlaylistAddCheckIcon size={16} style={{ color: '#fff' }} />
                </div>
                <Stack direction="column" gap={0} align="start">
                  <Text style={{ fontWeight: 500, fontSize: '0.875rem' }}>Action List</Text>
                  <Text variant="caption" color="secondary" style={{ fontSize: '0.7rem' }}>
                    Extract tasks and action items
                  </Text>
                </Stack>
              </Stack>
            </Button>
          </Stack>
        </Surface>
        
        <style jsx global>{`
          @keyframes fadeInUp {
            from {
              opacity: 0;
              transform: translateY(8px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}</style>
      </div>
    </>
  );
}

