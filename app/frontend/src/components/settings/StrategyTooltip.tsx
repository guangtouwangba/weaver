'use client';

import { Chip } from '@mui/material';
import { Stack, Text } from '@/components/ui';
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
      <Text variant="label" sx={{ fontWeight: 700, mb: 0.5, display: 'block' }}>
        {option.label}
      </Text>

      <Text variant="bodySmall" color="secondary" sx={{ mb: 1.5 }}>
        {option.description}
      </Text>

      <Stack direction="row" gap={1} sx={{ mb: 1.5, flexWrap: 'wrap' }}>
        <Chip
          icon={<AttachMoneyIcon size={14} />}
          label={costLabels[option.cost]}
          size="small"
          sx={{
            bgcolor: `${costColors[option.cost]}20`,
            color: costColors[option.cost],
            fontWeight: 600,
            '& .MuiChip-icon': { color: costColors[option.cost] },
          }}
        />
        <Chip
          icon={<BoltIcon size={14} />}
          label={performanceLabels[option.performance]}
          size="small"
          sx={{
            bgcolor: `${performanceColors[option.performance]}20`,
            color: performanceColors[option.performance],
            fontWeight: 600,
            '& .MuiChip-icon': { color: performanceColors[option.performance] },
          }}
        />
      </Stack>

      <Stack direction="row" align="start" gap={0} sx={{ gap: 0.5 }}>
        <GpsFixedIcon size={14} style={{ marginTop: 3, flexShrink: 0, color: '#666' }} />
        <Text variant="caption" color="secondary">
          <strong>Best for:</strong> {option.best_for}
        </Text>
      </Stack>
    </div>
  );
}
