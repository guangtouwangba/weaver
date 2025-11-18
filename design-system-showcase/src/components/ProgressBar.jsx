import React from 'react'

export const ProgressBar = ({ 
  value = 0, 
  max = 100, 
  label,
  showLabel = false,
  color = 'primary',
  ...props 
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))
  
  const colorClasses = {
    primary: 'bg-primary-strong',
    emerald: 'bg-emerald-strong',
    orange: 'bg-orange-strong',
    red: 'bg-red-strong',
  }

  return (
    <div className="w-full" {...props}>
      {(label || showLabel) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-caption text-text-secondary">{label}</span>}
          {showLabel && <span className="text-caption text-text-muted">{Math.round(percentage)}%</span>}
        </div>
      )}
      
      <div className="w-full h-1.5 bg-surface-subtle rounded-pill overflow-hidden">
        <div 
          className={`h-full rounded-pill transition-all duration-300 ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export default ProgressBar

