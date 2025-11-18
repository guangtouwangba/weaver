import React from 'react'

export const ListItem = ({ 
  avatar, 
  title, 
  subtitle, 
  status,
  actions,
  ...props 
}) => {
  return (
    <div className="flex items-center h-14 px-4 border-b border-border-subtle last:border-b-0" {...props}>
      {avatar && (
        <div className="mr-3">
          {avatar}
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        <div className="text-body font-medium text-text-primary truncate">{title}</div>
        {subtitle && <div className="text-caption text-text-secondary truncate">{subtitle}</div>}
      </div>
      
      {status && (
        <div className="ml-3">
          {status}
        </div>
      )}
      
      {actions && (
        <div className="ml-3 flex gap-2">
          {actions}
        </div>
      )}
    </div>
  )
}

export default ListItem

