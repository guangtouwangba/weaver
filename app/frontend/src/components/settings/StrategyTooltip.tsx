'use client';

import { Chip, Stack, Text } from '@/components/ui/primitives';
import { BoltIcon, AttachMoneyIcon, GpsFixedIcon } from '@/components/ui/icons';

export interface StrategyOption {
  value: string;
  label: string;
  description: string;
  cost: 'low' | 'medium' | 'high' | 'variable';
  performance: 'slow' | 'medium' | 'fast' | 'variable';
  best_for: string;
}

interface StrategyTooltipProps {
  option: StrategyOption;
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

export default function StrategyTooltip({ option }: StrategyTooltipProps) {
  return (
    <div style={{ padding: 8, maxWidth: 280 }}>
      <Text variant="label" style={{ fontWeight: 700, marginBottom: 4, display: 'block' }}>
        {option.label}
      </Text>

      <Text variant="bodySmall" color="secondary" style={{ marginBottom: 12 }}>
        {option.description}
      </Text>

      <Stack direction="row" gap={1} style={{ marginBottom: 12, flexWrap: 'wrap' }}>
        <Chip
          icon={<AttachMoneyIcon size={14} style={{ color: costColors[option.cost] }} />}
          label={costLabels[option.cost]}
          size="sm"
          style={{
            backgroundColor: `${costColors[option.cost]}20`,
            color: costColors[option.cost],
            fontWeight: 600,
            border: 'none',
          }}
        />
        <Chip
          icon={<BoltIcon size={14} style={{ color: performanceColors[option.performance] }} />}
          label={performanceLabels[option.performance]}
          size="sm"
          style={{
            backgroundColor: `${performanceColors[option.performance]}20`,
            color: performanceColors[option.performance],
            fontWeight: 600,
            border: 'none',
          }}
        />
      </Stack>

      <Stack direction="row" align="start" gap={0} style={{ gap: 4 }}>
        <GpsFixedIcon size={14} style={{ marginTop: 3, flexShrink: 0, color: '#666' }} />
        <Text variant="caption" color="secondary">
          <strong>Best for:</strong> {option.best_for}
        </Text>
      </Stack>
    </div>
  );
}
