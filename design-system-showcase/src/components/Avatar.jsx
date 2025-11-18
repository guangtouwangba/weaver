import React from 'react'

export const Avatar = ({ 
  src, 
  alt = 'Avatar', 
  size = 'md',
  fallback,
  className,
  ...props 
}) => {
  const sizeClasses = {
    sm: 'w-6 h-6 text-[10px] leading-none',
    md: 'w-8 h-8 text-caption leading-none',
    lg: 'w-full h-full text-body leading-none',
  }

  const colors = [
    'bg-primary-strong',
    'bg-emerald-strong',
    'bg-secondary-indigo',
    'bg-secondary-purple',
    'bg-secondary-pink',
    'bg-orange-strong',
  ]
  
  const colorClass = colors[Math.floor(Math.random() * colors.length)]

  return (
    <div 
      className={`
        ${sizeClasses[size]} 
        rounded-full flex-shrink-0 flex items-center justify-center
        ${!src ? `${colorClass} text-white font-semibold` : 'bg-surface-subtle'}
        ${className || ''}
      `}
      {...props}
    >
      {src ? (
        <img src={src} alt={alt} className="w-full h-full object-cover" />
      ) : (
        <span className="flex items-center justify-center w-full h-full">
          {fallback || alt.charAt(0).toUpperCase()}
        </span>
      )}
    </div>
  )
}

export const AvatarGroup = ({ avatars = [], max = 3, size = 'md' }) => {
  const displayAvatars = avatars.slice(0, max)
  const remaining = avatars.length - max

  return (
    <div className="flex -space-x-2">
      {displayAvatars.map((avatar, index) => (
        <div key={index} className="ring-2 ring-surface-card rounded-full">
          <Avatar {...avatar} size={size} />
        </div>
      ))}
      
      {remaining > 0 && (
        <div className={`
          ring-2 ring-surface-card rounded-full bg-surface-subtle
          flex items-center justify-center text-text-secondary font-semibold
          ${size === 'sm' ? 'w-6 h-6 text-[10px]' : size === 'lg' ? 'w-10 h-10 text-caption' : 'w-8 h-8 text-[11px]'}
        `}>
          +{remaining}
        </div>
      )}
    </div>
  )
}

export default Avatar

