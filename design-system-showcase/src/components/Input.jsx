import React from 'react'

export const Input = ({ 
  label, 
  placeholder, 
  helperText,
  error,
  icon,
  ...props 
}) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-caption text-text-secondary mb-1 font-medium">
          {label}
        </label>
      )}
      
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
            {icon}
          </div>
        )}
        
        <input
          className={`
            w-full h-10 px-3 bg-surface-card border rounded-lg text-body
            transition-all duration-normal ease-standard
            ${icon ? 'pl-10' : ''}
            ${error 
              ? 'border-red-strong focus:border-red-strong focus:ring-2 focus:ring-red-soft' 
              : 'border-border-subtle focus:border-border-focus focus:ring-2 focus:ring-primary-soft'
            }
            placeholder:text-text-muted
            outline-none
          `}
          placeholder={placeholder}
          {...props}
        />
      </div>
      
      {(helperText || error) && (
        <p className={`mt-1 text-caption ${error ? 'text-red-strong' : 'text-text-muted'}`}>
          {error || helperText}
        </p>
      )}
    </div>
  )
}

export default Input

