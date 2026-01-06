'use client';

import { Radio, Chip } from '@/components/ui/primitives';
import { Surface, Stack, Text } from '@/components/ui';
import { colors, shadows } from '@/components/ui/tokens';
import { BoltIcon, AttachMoneyIcon, GpsFixedIcon } from '@/components/ui/icons';
import { StrategyOption } from './StrategyTooltip';

interface StrategyCardProps {
  option: StrategyOption;
  selected: boolean;
  onClick: () => void;
}

const costColors = {
  low: '#4caf50',
  medium: '#ff9800',
  high: '#f44336',
  variable: '#9c27b0',
};

const performanceColors = {
  slow: '#f44336',
  medium: '#ff9800',
  fast: '#4caf50',
  variable: '#9c27b0',
};

const costLabels = {
  low: 'Low Cost',
  medium: 'Medium Cost',
  high: 'High Cost',
  variable: 'Variable Cost',
};

const performanceLabels = {
  slow: 'Slow',
  medium: 'Medium',
  fast: 'Fast',
  variable: 'Variable',
};

export default function StrategyCard({ option, selected, onClick }: StrategyCardProps) {
  return (
    <Surface
      elevation={0}
      radius="xl"
      onClick={onClick}
      style={{
        padding: 20,
        cursor: 'pointer',
        border: '2px solid',
        borderColor: selected ? colors.primary[500] : colors.border.default,
        backgroundColor: selected ? `${colors.primary[500]}08` : colors.background.paper,
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        height: '100%',
        position: 'relative',
        boxShadow: selected ? shadows.sm : 'none',
        // Hover effect needs to be handled via CSS or state, but for now inline style limitation
        // We can add a style tag or use a class if we had css modules.
        // For now, I'll rely on the Surface component or just inline style.
        // To handle hover correctly without CSS files, I might need onMouseEnter/Leave state, 
        // but let's stick to simple inline styles for now.
      }}
      className="strategy-card"
    >
      <style dangerouslySetInnerHTML={{
        __html: `
          .strategy-card:hover {
            border-color: ${selected ? colors.primary[500] : colors.text.disabled} !important;
            transform: translateY(-2px);
            box-shadow: ${shadows.sm} !important;
          }
        `
      }} />
      <Stack direction="row" justify="between" align="start">
        <div>
          <Text variant="h6" style={{ fontSize: '1rem', marginBottom: 4 }}>
            {option.label}
          </Text>
          <Text variant="bodySmall" color="secondary" style={{ lineHeight: 1.5, minHeight: 40 }}>
            {option.description}
          </Text>
        </div>
        <Radio
          checked={selected}
          style={{
            marginTop: -4,
            marginRight: -4,
          }}
          onChange={() => {}}
        />
      </Stack>

      <Stack direction="row" gap={8} style={{ flexWrap: 'wrap', marginTop: 'auto' }}>
        <Chip
          icon={<AttachMoneyIcon size={14} />}
          label={costLabels[option.cost]}
          size="sm"
          style={{
            height: 24,
            backgroundColor: `${costColors[option.cost]}15`,
            color: costColors[option.cost],
            fontWeight: 600,
            fontSize: '0.75rem',
            border: `1px solid ${costColors[option.cost]}30`,
          }}
        />
        <Chip
          icon={<BoltIcon size={14} />}
          label={performanceLabels[option.performance]}
          size="sm"
          style={{
            height: 24,
            backgroundColor: `${performanceColors[option.performance]}15`,
            color: performanceColors[option.performance],
            fontWeight: 600,
            fontSize: '0.75rem',
            border: `1px solid ${performanceColors[option.performance]}30`,
          }}
        />
      </Stack>

      {option.best_for && (
        <Stack direction="row" align="start" gap={8} style={{ paddingTop: 16, borderTop: `1px solid ${selected ? `${colors.primary[500]}20` : colors.border.default}` }}>
          <GpsFixedIcon size={14} style={{ marginTop: 3, flexShrink: 0, color: selected ? colors.primary[500] : colors.text.secondary }} />
          <Text variant="caption" color={selected ? 'primary' : 'secondary'} style={{ lineHeight: 1.5 }}>
            <strong>Best for:</strong> {option.best_for}
          </Text>
        </Stack>
      )}
    </Surface>
  );
}
