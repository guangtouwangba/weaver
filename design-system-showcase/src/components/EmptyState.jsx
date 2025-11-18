import React from 'react'

export const EmptyState = ({ 
  icon, 
  title, 
  description, 
  action,
  ...props 
}) => {
  return (
    <div className="bg-surface-card rounded-lg p-6 text-center" {...props}>
      {icon && (
        <div className="flex justify-center mb-4 text-text-muted">
          {icon}
        </div>
      )}
      
      {title && (
        <h3 className="text-subtitle font-semibold text-text-primary mb-2">
          {title}
        </h3>
      )}
      
      {description && (
        <p className="text-body text-text-secondary mb-4 max-w-md mx-auto">
          {description}
        </p>
      )}
      
      {action && (
        <div className="flex justify-center">
          {action}
        </div>
      )}
    </div>
  )
}

export default EmptyState

