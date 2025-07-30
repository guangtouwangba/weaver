"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient, TaskStatus, TaskProgress } from '@/lib/api'
import { toast } from 'sonner'

interface UseTaskTrackerOptions {
  onComplete?: (result: any) => void
  onError?: (error: string) => void
  onProgress?: (progress: TaskProgress) => void
  pollInterval?: number
  autoStart?: boolean
}

interface UseTaskTrackerReturn {
  taskStatus: TaskStatus | null
  taskProgress: TaskProgress | null
  isLoading: boolean
  error: string | null
  startTracking: (taskId: string) => void
  stopTracking: () => void
  cancelTask: () => Promise<void>
  isActive: boolean
}

export function useTaskTracker(options: UseTaskTrackerOptions = {}): UseTaskTrackerReturn {
  const {
    onComplete,
    onError,
    onProgress,
    pollInterval = 2000, // 2 seconds
    autoStart = true
  } = options

  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [taskProgress, setTaskProgress] = useState<TaskProgress | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isActive, setIsActive] = useState(false)

  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const stopTracking = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsActive(false)
    setIsLoading(false)
  }, [])

  const fetchTaskStatus = useCallback(async (currentTaskId: string) => {
    if (!mountedRef.current) return

    try {
      const [status, progress] = await Promise.all([
        apiClient.getTaskStatus(currentTaskId),
        apiClient.getTaskProgress(currentTaskId).catch(() => null) // Progress might not be available yet
      ])

      if (!mountedRef.current) return

      setTaskStatus(status)
      if (progress) {
        setTaskProgress(progress)
        onProgress?.(progress)
      }

      // Handle terminal states
      if (status.state === 'SUCCESS') {
        stopTracking()
        onComplete?.(status.result)
        toast.success('Task completed successfully')
      } else if (status.state === 'FAILURE') {
        stopTracking()
        const errorMessage = status.error || 'Task failed'
        setError(errorMessage)
        onError?.(errorMessage)
        toast.error(`Task failed: ${errorMessage}`)
      } else if (status.state === 'REVOKED') {
        stopTracking()
        toast.info('Task was cancelled')
      }

      setError(null)
    } catch (err: any) {
      if (!mountedRef.current) return
      
      console.error('Failed to fetch task status:', err)
      setError(err.message || 'Failed to fetch task status')
      
      // If task not found, stop tracking
      if (err.status === 404) {
        stopTracking()
      }
    }
  }, [onComplete, onError, onProgress, stopTracking])

  const startTracking = useCallback((newTaskId: string) => {
    if (!newTaskId) return

    console.log('Starting task tracking for:', newTaskId)
    
    // Stop any existing tracking
    stopTracking()
    
    setTaskId(newTaskId)
    setIsActive(true)
    setIsLoading(true)
    setError(null)
    setTaskStatus(null)
    setTaskProgress(null)

    // Start polling immediately
    fetchTaskStatus(newTaskId)

    // Set up polling interval
    intervalRef.current = setInterval(() => {
      fetchTaskStatus(newTaskId)
    }, pollInterval)

  }, [fetchTaskStatus, pollInterval, stopTracking])

  const cancelTask = useCallback(async () => {
    if (!taskId) {
      toast.error('No active task to cancel')
      return
    }

    try {
      await apiClient.cancelTask(taskId)
      toast.success('Task cancellation requested')
      stopTracking()
    } catch (err: any) {
      console.error('Failed to cancel task:', err)
      toast.error(err.message || 'Failed to cancel task')
    }
  }, [taskId, stopTracking])

  // Auto-start tracking if taskId is provided
  useEffect(() => {
    if (autoStart && taskId && !isActive) {
      startTracking(taskId)
    }
  }, [taskId, autoStart, isActive, startTracking])

  return {
    taskStatus,
    taskProgress,
    isLoading,
    error,
    startTracking,
    stopTracking,
    cancelTask,
    isActive
  }
}