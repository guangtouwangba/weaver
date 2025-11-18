import React from 'react'

export const Card = ({ 
  title, 
  subtitle,
  actions,
  children, 
  footer,
  ...props 
}) => {
  return (
    <div className="bg-surface-card rounded-lg shadow-soft p-5" {...props}>
      {(title || actions) && (
        <div className="flex items-start justify-between mb-3">
          <div>
            {title && <h3 className="text-title font-semibold text-text-primary">{title}</h3>}
            {subtitle && <p className="text-caption text-text-secondary mt-1">{subtitle}</p>}
          </div>
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
      )}
      
      <div className="space-y-2">
        {children}
      </div>
      
      {footer && (
        <div className="mt-3 pt-3 border-t border-border-subtle">
          {footer}
        </div>
      )}
    </div>
  )
}

export default Card

