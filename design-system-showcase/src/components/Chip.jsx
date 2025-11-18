import React from 'react'
import Avatar from './Avatar'

export const Chip = ({ 
  variant = 'active', 
  children,
  avatar,
  onRemove,
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center gap-1.5 rounded-pill h-6 px-[10px] text-label font-label'
  
  const variantClasses = {
    // Semantic status variants per design.json
    pending: 'bg-yellow-soft text-text-on-warning',
    confirmed: 'bg-emerald-soft text-emerald-strong',
    alert: 'bg-red-soft text-red-strong',
    active: 'bg-primary-soft text-primary-strong',
    closed: 'bg-surface-subtle text-text-muted',
    
    // Additional semantic variants
    info: 'bg-primary-soft text-status-info',
    success: 'bg-emerald-soft text-status-success',
    warning: 'bg-orange-soft text-text-on-warning',
    error: 'bg-red-soft text-red-strong',
    
    // Neutral tag variant
    tag: 'bg-surface-subtle text-text-secondary border border-border-subtle',
  }

  return (
    <span className={`${baseClasses} ${variantClasses[variant]}`} {...props}>
      {avatar && (
        <Avatar {...avatar} size="sm" />
      )}
      <span>{children}</span>
      {onRemove && (
        <button
          onClick={onRemove}
          className="flex items-center justify-center w-4 h-4 rounded-full hover:bg-black hover:bg-opacity-10 transition-colors"
          title="Remove"
        >
          <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </span>
  )
}

export default Chip

