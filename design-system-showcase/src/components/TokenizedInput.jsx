import React, { useState, useRef } from 'react'
import Chip from './Chip'
import Avatar from './Avatar'

export const TokenizedInput = ({ 
  label,
  placeholder = "Type",
  tokens = [],
  onAddToken,
  onRemoveToken,
  error,
  disabled = false,
  showAvatar = false,
  maxVisibleRows = 2,
  ...props 
}) => {
  const [inputValue, setInputValue] = useState('')
  const [isFocused, setIsFocused] = useState(false)
  const inputRef = useRef(null)

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault()
      onAddToken?.(inputValue.trim())
      setInputValue('')
    } else if (e.key === 'Backspace' && !inputValue && tokens.length > 0) {
      onRemoveToken?.(tokens.length - 1)
    }
  }

  const handleContainerClick = () => {
    inputRef.current?.focus()
  }

  const handleRemoveToken = (index) => {
    if (!disabled) {
      onRemoveToken?.(index)
    }
  }

  return (
    <div className="w-full" {...props}>
      {label && (
        <label className="block text-caption text-text-secondary mb-1 font-medium">
          {label}
        </label>
      )}
      
      <div 
        onClick={handleContainerClick}
        className={`
          flex flex-wrap items-center gap-2 px-3 py-2
          bg-surface-card border-2 rounded-xl
          transition-all duration-normal ease-standard cursor-text
          ${error 
            ? 'border-red-strong' 
            : isFocused 
              ? 'border-border-focus shadow-soft' 
              : 'border-border-subtle'
          }
          ${disabled ? 'opacity-40 cursor-not-allowed' : ''}
          min-h-[44px]
        `}
        style={{ maxHeight: maxVisibleRows > 1 ? `${maxVisibleRows * 32 + 16}px` : 'auto' }}
      >
        {/* Tokens */}
        {tokens.map((token, index) => (
          <div 
            key={index}
            className={`
              inline-flex items-center h-6 bg-surface-card border border-border-subtle rounded-pill text-label font-label text-text-primary
              ${showAvatar && token.avatar ? 'pl-1 pr-2 gap-1.5' : 'px-[10px] gap-1.5'}
            `}
          >
            {showAvatar && token.avatar && (
              <Avatar {...token.avatar} size="sm" className="flex-shrink-0" />
            )}
            <span className="flex-shrink-0 truncate max-w-[120px]">
              {token.label || token}
            </span>
            {!disabled && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleRemoveToken(index)
                }}
                className="flex-shrink-0 flex items-center justify-center w-4 h-4 rounded-full hover:bg-surface-subtle transition-colors ml-0.5"
                title="Remove"
              >
                <svg className="w-2.5 h-2.5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        ))}
        
        {/* Input */}
        {!disabled && (
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={tokens.length === 0 ? placeholder : ''}
            className="flex-1 min-w-[60px] bg-transparent text-body outline-none placeholder:text-text-muted"
            disabled={disabled}
          />
        )}
      </div>
      
      {error && (
        <p className="mt-1 text-caption text-red-strong">
          {error}
        </p>
      )}
    </div>
  )
}

export default TokenizedInput

