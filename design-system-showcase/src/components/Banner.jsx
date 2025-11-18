import React from 'react'

export const Banner = ({ 
  variant = 'info', 
  icon,
  children,
  onClose,
  action,
  ...props 
}) => {
  const variantClasses = {
    warning: 'bg-orange-soft text-text-on-warning',
    error: 'bg-red-soft text-text-on-warning',
    info: 'bg-primary-soft text-primary-strong',
    success: 'bg-emerald-soft text-emerald-strong',
  }

  return (
    <div className={`flex items-center gap-3 p-4 rounded-lg ${variantClasses[variant]}`} {...props}>
      {icon && <div className="flex-shrink-0">{icon}</div>}
      
      <div className="flex-1 text-body">
        {children}
      </div>
      
      {action && <div className="flex-shrink-0">{action}</div>}
      
      {onClose && (
        <button 
          onClick={onClose}
          className="flex-shrink-0 hover:opacity-70 transition-opacity"
        >
          ✕
        </button>
      )}
    </div>
  )
}

export default Banner

