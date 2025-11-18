import React, { useState, useRef, useEffect } from 'react'

export const Select = ({ 
  label,
  options = [],
  value,
  onChange,
  placeholder = "Select an option",
  error,
  disabled = false,
  ...props 
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const selectRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectedOption = options.find(opt => opt.value === value)

  const handleSelect = (option) => {
    onChange?.(option.value)
    setIsOpen(false)
  }

  return (
    <div className="w-full relative" ref={selectRef} {...props}>
      {label && (
        <label className="block text-caption text-text-secondary mb-1 font-medium">
          {label}
        </label>
      )}
      
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full h-10 px-3 bg-surface-card border rounded-lg text-body
          flex items-center justify-between
          transition-all duration-normal ease-standard
          ${error 
            ? 'border-red-strong' 
            : isOpen 
              ? 'border-border-focus ring-2 ring-primary-soft' 
              : 'border-border-subtle hover:border-border-strong'
          }
          ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
          outline-none
        `}
      >
        <span className={selectedOption ? 'text-text-primary' : 'text-text-muted'}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <svg 
          className={`w-4 h-4 text-text-muted transition-transform duration-fast ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-surface-card border border-border-subtle rounded-lg shadow-medium max-h-60 overflow-auto animate-slideDown">
          {options.map((option, index) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleSelect(option)}
              className={`
                w-full px-3 py-2 text-left text-body
                transition-colors duration-fast
                ${value === option.value 
                  ? 'bg-primary-soft text-primary-strong font-medium' 
                  : 'text-text-primary hover:bg-surface-subtle'
                }
                ${index !== 0 ? 'border-t border-border-subtle' : ''}
              `}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
      
      {error && (
        <p className="mt-1 text-caption text-red-strong">
          {error}
        </p>
      )}
    </div>
  )
}

export default Select

