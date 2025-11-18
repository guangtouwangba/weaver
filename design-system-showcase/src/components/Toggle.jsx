import React from 'react'

export const Toggle = ({ 
  checked = false, 
  onChange,
  label,
  description,
  disabled = false,
  ...props 
}) => {
  return (
    <div className="flex items-center justify-between py-3" {...props}>
      {(label || description) && (
        <div className="flex-1 pr-4">
          {label && (
            <div className="text-body font-medium text-text-primary mb-0.5">
              {label}
            </div>
          )}
          {description && (
            <div className="text-caption text-text-secondary">
              {description}
            </div>
          )}
        </div>
      )}
      
      <label className="relative inline-flex items-center cursor-pointer">
        <input 
          type="checkbox" 
          className="sr-only peer" 
          checked={checked}
          onChange={onChange}
          disabled={disabled}
        />
        <div className={`
          w-11 h-6 rounded-pill
          peer-focus:ring-2 peer-focus:ring-primary-soft
          after:content-[''] after:absolute after:top-[2px] after:left-[2px] 
          after:bg-white after:rounded-full after:h-5 after:w-5 
          after:transition-all after:shadow-soft
          peer-checked:after:translate-x-full peer-checked:after:border-white
          ${disabled 
            ? 'bg-surface-subtle cursor-not-allowed opacity-50' 
            : 'bg-surface-subtle peer-checked:bg-primary-strong'
          }
          transition-colors duration-180
        `}></div>
      </label>
    </div>
  )
}

export default Toggle

