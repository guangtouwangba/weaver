import React from 'react'

export const Button = ({ 
  variant = 'primary', 
  children, 
  icon,
  iconPosition = 'left',
  disabled = false,
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-label text-label transition-all duration-normal ease-standard focus:outline-none focus:ring-2 focus:ring-primary-soft disabled:opacity-40 disabled:cursor-not-allowed'
  
  const variantClasses = {
    primary: `
      bg-primary-strong text-text-on-accent 
      hover:bg-primary-hover hover:shadow-soft
      active:bg-primary-pressed active:shadow-none
      rounded-pill h-10 px-5
    `,
    secondary: `
      bg-surface-card text-text-primary 
      border border-border-strong 
      hover:bg-surface-subtle hover:border-border-strong
      active:bg-surface-page 
      rounded-pill h-9 px-[18px]
    `,
    ghost: `
      bg-transparent text-text-secondary 
      hover:bg-surface-subtle 
      active:bg-surface-page 
      rounded-pill h-8 px-4
    `,
    tiny: `
      bg-surface-card text-text-primary 
      border border-border-subtle 
      hover:bg-surface-subtle 
      rounded-pill h-6 px-3 text-[11px]
    `
  }

  return (
    <button 
      className={`${baseClasses} ${variantClasses[variant]}`.trim().replace(/\s+/g, ' ')}
      disabled={disabled}
      {...props}
    >
      {icon && iconPosition === 'left' && <span className="mr-2 flex items-center">{icon}</span>}
      {children}
      {icon && iconPosition === 'right' && <span className="ml-2 flex items-center">{icon}</span>}
    </button>
  )
}

export default Button

