"use client"

import React from 'react'
import { Loader2, Brain, Search, BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LoadingStateProps {
  message?: string
  submessage?: string
  icon?: 'default' | 'brain' | 'search' | 'book'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const iconMap = {
  default: Loader2,
  brain: Brain,
  search: Search,
  book: BookOpen
}

const sizeMap = {
  sm: {
    icon: 'h-4 w-4',
    text: 'text-sm',
    container: 'p-4'
  },
  md: {
    icon: 'h-6 w-6',
    text: 'text-base',
    container: 'p-6'
  },
  lg: {
    icon: 'h-8 w-8',
    text: 'text-lg',
    container: 'p-8'
  }
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "加载中...",
  submessage,
  icon = 'default',
  size = 'md',
  className
}) => {
  const IconComponent = iconMap[icon]
  const sizes = sizeMap[size]

  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center space-y-3",
      sizes.container,
      className
    )}>
      <IconComponent className={cn(
        "animate-spin text-primary",
        sizes.icon
      )} />
      <div className="space-y-1">
        <p className={cn("font-medium text-foreground", sizes.text)}>
          {message}
        </p>
        {submessage && (
          <p className="text-muted-foreground text-sm">
            {submessage}
          </p>
        )}
      </div>
    </div>
  )
}

// Skeleton loading component for cards/lists
export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn("animate-pulse", className)}>
    <div className="bg-gray-200 rounded-lg p-4 space-y-3">
      <div className="bg-gray-300 h-4 rounded w-3/4"></div>
      <div className="bg-gray-300 h-3 rounded w-1/2"></div>
      <div className="space-y-2">
        <div className="bg-gray-300 h-3 rounded"></div>
        <div className="bg-gray-300 h-3 rounded w-5/6"></div>
      </div>
    </div>
  </div>
)

// Loading overlay for buttons
export const ButtonLoading: React.FC<{ isLoading: boolean; children: React.ReactNode }> = ({
  isLoading,
  children
}) => (
  <>
    {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
    {children}
  </>
)

// Full page loading overlay
export const LoadingOverlay: React.FC<{ 
  isVisible: boolean
  message?: string
  className?: string 
}> = ({ 
  isVisible, 
  message = "处理中...",
  className 
}) => {
  if (!isVisible) return null

  return (
    <div className={cn(
      "fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center",
      className
    )}>
      <LoadingState message={message} size="lg" />
    </div>
  )
}