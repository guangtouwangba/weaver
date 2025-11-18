import React, { useState, useRef, useEffect } from 'react'

export const Dropdown = ({ 
  trigger,
  items = [],
  align = 'left',
  ...props 
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const alignClasses = {
    left: 'left-0',
    right: 'right-0',
  }

  return (
    <div className="relative inline-block" ref={dropdownRef} {...props}>
      <div onClick={() => setIsOpen(!isOpen)}>
        {trigger}
      </div>
      
      {isOpen && (
        <div className={`
          absolute ${alignClasses[align]} mt-2 
          min-w-[200px] bg-surface-card 
          border border-border-subtle rounded-lg shadow-medium 
          py-1 z-50
          animate-fadeIn
        `}>
          {items.map((item, index) => (
            <React.Fragment key={index}>
              {item.divider ? (
                <div className="my-1 border-t border-border-subtle" />
              ) : (
                <button
                  onClick={() => {
                    item.onClick?.()
                    if (!item.keepOpen) {
                      setIsOpen(false)
                    }
                  }}
                  disabled={item.disabled}
                  className={`
                    w-full px-4 py-2 text-left text-body
                    flex items-center gap-3
                    transition-colors duration-fast
                    ${item.disabled 
                      ? 'opacity-40 cursor-not-allowed' 
                      : 'hover:bg-surface-subtle cursor-pointer'
                    }
                    ${item.danger ? 'text-red-strong' : 'text-text-primary'}
                  `}
                >
                  {item.icon && (
                    <span className="flex-shrink-0 text-text-secondary">
                      {item.icon}
                    </span>
                  )}
                  <span className="flex-1">{item.label}</span>
                  {item.shortcut && (
                    <span className="text-caption text-text-muted">
                      {item.shortcut}
                    </span>
                  )}
                </button>
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  )
}

export default Dropdown

