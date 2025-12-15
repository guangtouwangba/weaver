import { Box, Paper, Typography, Radio, Chip } from '@mui/material';
import { Zap, DollarSign, Target, Check } from 'lucide-react';
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
    <Paper
      elevation={0}
      onClick={onClick}
      sx={{
        p: 2.5,
        cursor: 'pointer',
        border: '2px solid',
        borderColor: selected ? 'primary.main' : 'divider',
        borderRadius: 4,
        bgcolor: selected ? 'rgba(var(--mui-palette-primary-mainChannel) / 0.03)' : 'background.paper',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        height: '100%',
        position: 'relative',
        '&:hover': {
          borderColor: selected ? 'primary.main' : 'text.disabled',
          transform: 'translateY(-2px)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.04)',
        },
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Box>
            <Typography variant="h6" fontWeight={700} sx={{ fontSize: '1rem', mb: 0.5 }}>
            {option.label}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5, minHeight: 40 }}>
            {option.description}
            </Typography>
        </Box>
        <Radio 
          checked={selected} 
          sx={{ 
            p: 0.5, 
            mt: -0.5, 
            mr: -0.5,
            '&.Mui-checked': { color: 'primary.main' } 
          }} 
        />
      </Box>

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 'auto' }}>
        <Chip
          icon={<DollarSign size={14} />}
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
          icon={<Zap size={14} />}
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
      </Box>
      
      {option.best_for && (
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, pt: 1.5, borderTop: '1px solid', borderColor: 'divider' }}>
            <Target size={14} style={{ marginTop: 3, flexShrink: 0, color: '#666' }} />
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                Best for: {option.best_for}
            </Typography>
        </Box>
      )}
    </Paper>
  );
}














