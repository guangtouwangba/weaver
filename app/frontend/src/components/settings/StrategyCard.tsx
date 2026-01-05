'use client';

import { Radio, Chip } from '@mui/material';
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
      sx={{
        p: 2.5,
        cursor: 'pointer',
        border: '2px solid',
        borderColor: selected ? colors.primary[500] : colors.border.default,
        bgcolor: selected ? `${colors.primary[500]}08` : colors.background.paper,
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        height: '100%',
        position: 'relative',
        '&:hover': {
          borderColor: selected ? colors.primary[500] : colors.text.disabled,
          transform: 'translateY(-2px)',
          boxShadow: shadows.sm,
        },
      }}
    >
      <Stack direction="row" justify="between" align="start">
        <div>
          <Text variant="h6" sx={{ fontSize: '1rem', mb: 0.5 }}>
            {option.label}
          </Text>
          <Text variant="bodySmall" color="secondary" sx={{ lineHeight: 1.5, minHeight: 40 }}>
            {option.description}
          </Text>
        </div>
        <Radio
          checked={selected}
          sx={{
            p: 0.5,
            mt: -0.5,
            mr: -0.5,
            '&.Mui-checked': { color: colors.primary[500] }
          }}
        />
      </Stack>

      <Stack direction="row" gap={1} sx={{ flexWrap: 'wrap', mt: 'auto' }}>
        <Chip
          icon={<AttachMoneyIcon size={14} />}
          label={costLabels[option.cost]}
          size="small"
          sx={{
            height: 24,
            bgcolor: `${costColors[option.cost]}15`,
            color: costColors[option.cost],
            fontWeight: 600,
            fontSize: '0.75rem',
            border: '1px solid',
            borderColor: `${costColors[option.cost]}30`,
            '& .MuiChip-icon': { color: costColors[option.cost] },
          }}
        />
        <Chip
          icon={<BoltIcon size={14} />}
          label={performanceLabels[option.performance]}
          size="small"
          sx={{
            height: 24,
            bgcolor: `${performanceColors[option.performance]}15`,
            color: performanceColors[option.performance],
            fontWeight: 600,
            fontSize: '0.75rem',
            border: '1px solid',
            borderColor: `${performanceColors[option.performance]}30`,
            '& .MuiChip-icon': { color: performanceColors[option.performance] },
          }}
        />
      </Stack>

      {option.best_for && (
        <Stack
          direction="row"
          align="start"
          gap={1}
          sx={{ pt: 1.5, borderTop: `1px solid ${colors.border.default}` }}
        >
          <GpsFixedIcon size={14} style={{ marginTop: 3, flexShrink: 0, color: '#666' }} />
          <Text variant="caption" color="secondary" sx={{ fontWeight: 500 }}>
            Best for: {option.best_for}
          </Text>
        </Stack>
      )}
    </Surface>
  );
}
