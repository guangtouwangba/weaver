'use client';

/**
 * CommandPalette - Displays available slash commands with autocomplete
 * 
 * A clean, minimal command palette following the design system's
 * modern, creative aesthetic with Violet accents.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { colors, radii, shadows, fontSize, fontWeight, spacing, fontFamily } from '@/components/ui/tokens';
import { commands, CommandDefinition, filterCommands } from '@/lib/commandParser';

// Command categories with semantic icons and colors from design system
const COMMAND_ICONS: Record<string, { icon: string; color: string }> = {
  'add-node': { icon: '＋', color: colors.primary[600] },
  'delete': { icon: '✕', color: colors.error[500] },
  'update': { icon: '✎', color: colors.warning[600] },
  'move': { icon: '↗', color: colors.info[500] },
  'connect': { icon: '⟷', color: colors.success[600] },
  'disconnect': { icon: '⊘', color: colors.warning[500] },
  'select': { icon: '☐', color: colors.info[600] },
  'zoom': { icon: '◎', color: colors.neutral[600] },
  'pan': { icon: '✥', color: colors.neutral[500] },
  'fit': { icon: '⬜', color: colors.neutral[600] },
  'generate': { icon: '◆', color: colors.primary[500] },
  'synthesize': { icon: '⚡', color: colors.primary[600] },
  'help': { icon: '?', color: colors.neutral[400] },
};

const getCommandIcon = (name: string) => {
  return COMMAND_ICONS[name] || { icon: '▸', color: colors.neutral[500] };
};

interface CommandPaletteProps {
  input: string;
  onSelect: (command: string) => void;
  onClose: () => void;
  maxHeight?: number;
}

export default function CommandPalette({
  input,
  onSelect,
  onClose,
  maxHeight = 340,
}: CommandPaletteProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [prevCommandCount, setPrevCommandCount] = useState(0);

  const filteredCommands = useMemo(() => {
    const query = input.startsWith('/') ? input.slice(1) : input;
    if (!query) {
      return commands.filter(c => c.name !== 'help');
    }
    return filterCommands(query);
  }, [input]);

  if (filteredCommands.length !== prevCommandCount) {
    setPrevCommandCount(filteredCommands.length);
    setSelectedIndex(0);
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(i => Math.min(i + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(i => Math.max(i - 1, 0));
          break;
        case 'Enter':
        case 'Tab':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            onSelect(`/${filteredCommands[selectedIndex].name} `);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredCommands, selectedIndex, onSelect, onClose]);

  if (filteredCommands.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        width: '100%',
        maxHeight,
        backgroundColor: colors.background.paper,
        borderRadius: radii.xl,
        boxShadow: shadows.lg,
        border: `1px solid ${colors.border.default}`,
        overflow: 'hidden',
        zIndex: 1500,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: `${spacing[2]}px ${spacing[4]}px`,
          borderBottom: `1px solid ${colors.border.default}`,
          backgroundColor: colors.background.subtle,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing[2] }}>
          <span style={{ 
            fontSize: fontSize.sm,
            color: colors.primary[600],
            fontWeight: fontWeight.semibold,
          }}>
            /
          </span>
          <span style={{ 
            fontSize: fontSize.sm, 
            color: colors.text.primary,
            fontWeight: fontWeight.medium,
            letterSpacing: '-0.01em',
          }}>
            Commands
          </span>
        </div>
        <span style={{
          fontSize: fontSize.xs,
          color: colors.text.muted,
        }}>
          {filteredCommands.length} available
        </span>
      </div>

      {/* Command List */}
      <div
        style={{
          maxHeight: maxHeight - 88,
          overflowY: 'auto',
          padding: spacing[2],
        }}
      >
        {filteredCommands.map((cmd, index) => (
          <CommandItem
            key={cmd.name}
            command={cmd}
            isSelected={index === selectedIndex}
            onSelect={() => onSelect(`/${cmd.name} `)}
            onHover={() => setSelectedIndex(index)}
          />
        ))}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: `${spacing[2]}px ${spacing[4]}px`,
          borderTop: `1px solid ${colors.border.default}`,
          backgroundColor: colors.background.subtle,
          display: 'flex',
          alignItems: 'center',
          gap: spacing[4],
        }}
      >
        <KeyHint keys={['↑↓']} label="navigate" />
        <KeyHint keys={['enter']} label="select" />
        <KeyHint keys={['esc']} label="close" />
      </div>
    </div>
  );
}

// ============================================================================
// KeyHint Component
// ============================================================================

function KeyHint({ keys, label }: { keys: string[]; label: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: spacing[1] }}>
      {keys.map((key, i) => (
        <span
          key={i}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth: 20,
            height: 20,
            padding: '0 6px',
            fontSize: fontSize.xs,
            fontFamily: fontFamily.mono,
            fontWeight: fontWeight.medium,
            color: colors.text.secondary,
            backgroundColor: colors.background.muted,
            borderRadius: radii.sm,
            border: `1px solid ${colors.border.default}`,
          }}
        >
          {key}
        </span>
      ))}
      <span style={{ fontSize: fontSize.xs, color: colors.text.muted }}>
        {label}
      </span>
    </div>
  );
}

// ============================================================================
// CommandItem Component
// ============================================================================

interface CommandItemProps {
  command: CommandDefinition;
  isSelected: boolean;
  onSelect: () => void;
  onHover: () => void;
}

function CommandItem({ command, isSelected, onSelect, onHover }: CommandItemProps) {
  const iconStyle = getCommandIcon(command.name);
  
  return (
    <div
      onClick={onSelect}
      onMouseEnter={onHover}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: spacing[3],
        padding: `${spacing[2]}px ${spacing[3]}px`,
        cursor: 'pointer',
        backgroundColor: isSelected ? colors.primary[50] : 'transparent',
        borderRadius: radii.lg,
        transition: 'background-color 0.12s ease',
        marginBottom: 2,
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: radii.md,
          backgroundColor: isSelected ? colors.primary[100] : colors.background.muted,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: fontSize.base,
          color: isSelected ? colors.primary[700] : iconStyle.color,
          fontWeight: fontWeight.bold,
          flexShrink: 0,
          transition: 'all 0.12s ease',
        }}
      >
        {iconStyle.icon}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: spacing[2] }}>
          <span
            style={{
              fontSize: fontSize.sm,
              fontWeight: fontWeight.semibold,
              color: isSelected ? colors.primary[700] : colors.text.primary,
              fontFamily: fontFamily.mono,
            }}
          >
            /{command.name}
          </span>
          
          {command.aliases.length > 0 && (
            <span
              style={{
                fontSize: fontSize.xs,
                color: colors.text.muted,
              }}
            >
              {command.aliases.slice(0, 2).join(', ')}
            </span>
          )}
        </div>
        
        <div
          style={{
            fontSize: fontSize.xs,
            color: isSelected ? colors.primary[600] : colors.text.secondary,
            marginTop: 2,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {command.description}
        </div>
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <span
          style={{
            fontSize: fontSize.sm,
            color: colors.primary[500],
            fontWeight: fontWeight.medium,
          }}
        >
          ↵
        </span>
      )}
    </div>
  );
}

// ============================================================================
// useCommandPalette Hook
// ============================================================================

export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');

  return {
    isOpen,
    input,
    setInput: (value: string) => {
      setInput(value);
      if (value === '/' || (value.startsWith('/') && !value.includes(' '))) {
        setIsOpen(true);
      } else if (!value.startsWith('/')) {
        setIsOpen(false);
      }
    },
    handleKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    },
    close: () => setIsOpen(false),
  };
}
