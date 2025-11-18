import React, { useEffect } from 'react'
import Button from './Button'

export const Modal = ({ 
  isOpen = false,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  ...props 
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose?.()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-text-primary bg-opacity-50 animate-fadeIn"
      onClick={onClose}
      {...props}
    >
      <div 
        className={`
          bg-surface-card rounded-lg shadow-medium 
          w-full ${sizeClasses[size]}
          animate-slideUp
        `}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
            <h3 className="text-title font-semibold text-text-primary">
              {title}
            </h3>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-subtle active:bg-surface-page transition-all"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
        
        {/* Body */}
        <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
          {children}
        </div>
        
        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-border-subtle">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

export default Modal

