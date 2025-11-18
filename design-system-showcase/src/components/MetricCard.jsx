import React from 'react'

export const MetricCard = ({ 
  value, 
  label, 
  change,
  changeType = 'neutral',
  icon,
  ...props 
}) => {
  const changeColors = {
    positive: 'text-emerald-strong',
    negative: 'text-red-strong',
    neutral: 'text-text-muted',
  }

  return (
    <div className="bg-surface-card rounded-lg shadow-soft p-5" {...props}>
      <div className="flex items-start justify-between mb-2">
        <div className="text-caption text-text-secondary font-medium">{label}</div>
        {icon && <div className="text-text-muted">{icon}</div>}
      </div>
      
      <div className="text-display-md font-semibold text-text-primary mb-1">
        {value}
      </div>
      
      {change && (
        <div className={`text-caption ${changeColors[changeType]}`}>
          {changeType === 'positive' && '↑ '}
          {changeType === 'negative' && '↓ '}
          {change}
        </div>
      )}
    </div>
  )
}

export default MetricCard

