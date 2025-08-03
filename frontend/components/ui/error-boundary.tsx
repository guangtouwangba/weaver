"use client"

import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './button'
import { Alert, AlertDescription, AlertTitle } from './alert'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  retry = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      const Fallback = this.props.fallback
      if (Fallback && this.state.error) {
        return <Fallback error={this.state.error} retry={this.retry} />
      }

      return <DefaultErrorFallback error={this.state.error} retry={this.retry} />
    }

    return this.props.children
  }
}

interface ErrorFallbackProps {
  error?: Error
  retry: () => void
}

export const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ error, retry }) => (
  <Alert variant="destructive" className="m-4">
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>出现错误</AlertTitle>
    <AlertDescription className="mt-2">
      <p className="mb-4">
        {error?.message || '应用运行时出现未知错误，请重试或刷新页面。'}
      </p>
      <Button onClick={retry} variant="outline" size="sm" className="gap-2">
        <RefreshCw className="h-4 w-4" />
        重试
      </Button>
    </AlertDescription>
  </Alert>
)

// API Error display component
export interface ApiErrorDisplayProps {
  error: string | Error | null
  onDismiss?: () => void
  className?: string
}

export const ApiErrorDisplay: React.FC<ApiErrorDisplayProps> = ({ 
  error, 
  onDismiss,
  className = ""
}) => {
  if (!error) return null

  const errorMessage = typeof error === 'string' ? error : error.message

  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>操作失败</AlertTitle>
      <AlertDescription className="mt-2">
        <p className="mb-2">{errorMessage}</p>
        {onDismiss && (
          <Button onClick={onDismiss} variant="outline" size="sm">
            关闭
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}