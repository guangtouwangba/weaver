"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  ArrowUpDown, 
  MoreHorizontal, 
  Play, 
  Pause, 
  Trash2,
  Calendar,
  FileText,
  Copy,
  Eye,
  History
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { formatDistanceToNow } from "date-fns"
import { toast } from "sonner"
import { mutate } from "swr"

// Global API functions - will be set by parent components
declare global {
  interface Window {
    toggleCronJob?: (jobId: string) => Promise<any>
    triggerCronJob?: (jobId: string) => Promise<any>
    deleteCronJob?: (jobId: string) => Promise<any>
    refreshJobs?: () => Promise<any>
  }
}

export type CronjobData = {
  id: string
  name: string
  description: string
  status: "active" | "paused" | "completed" | "failed" | "running"
  schedule: string
  lastRun: Date | null
  nextRun: Date | null
  papersFound: number
  papersProcessed: number
  keywords: string[]
  vectorDb: string
  embeddingModel: string
  createdAt: Date
}

export const columns: ColumnDef<CronjobData>[] = [
  {
    accessorKey: "name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Job Name
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const job = row.original
      return (
        <div className="space-y-1">
          <div className="font-medium">{job.name}</div>
          <div className="text-sm text-muted-foreground line-clamp-2">
            {job.description}
          </div>
          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
            <span>{job.keywords.join(", ")}</span>
          </div>
        </div>
      )
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string
      
      const statusVariants = {
        active: "default",
        paused: "secondary",
        completed: "default",
        failed: "destructive",
        running: "secondary"
      } as const

      return (
        <Badge variant={statusVariants[status as keyof typeof statusVariants]}>
          {status}
        </Badge>
      )
    },
  },
  {
    accessorKey: "schedule",
    header: "Schedule",
    cell: ({ row }) => {
      return (
        <div className="flex items-center space-x-1">
          <Calendar className="h-3 w-3 text-muted-foreground" />
          <span className="text-sm">{row.getValue("schedule")}</span>
        </div>
      )
    },
  },
  {
    accessorKey: "lastRun",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Last Run
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const lastRun = row.getValue("lastRun") as Date | null
      return (
        <div className="text-sm">
          {lastRun ? formatDistanceToNow(lastRun, { addSuffix: true }) : "Never"}
        </div>
      )
    },
  },
  {
    accessorKey: "nextRun",
    header: "Next Run",
    cell: ({ row }) => {
      const nextRun = row.getValue("nextRun") as Date | null
      return (
        <div className="text-sm">
          {nextRun ? formatDistanceToNow(nextRun, { addSuffix: true }) : "Not scheduled"}
        </div>
      )
    },
  },
  {
    accessorKey: "papersFound",
    header: "Papers",
    cell: ({ row }) => {
      const job = row.original
      return (
        <div className="flex items-center space-x-1">
          <FileText className="h-3 w-3 text-muted-foreground" />
          <span className="text-sm">
            {job.papersFound} found / {job.papersProcessed} processed
          </span>
        </div>
      )
    },
  },
  {
    accessorKey: "providers",
    header: "Providers",
    cell: ({ row }) => {
      const job = row.original
      return (
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground">
            Vector: {job.vectorDb}
          </div>
          <div className="text-xs text-muted-foreground">
            Embedding: {job.embeddingModel}
          </div>
        </div>
      )
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const job = row.original

      const handleCopyJobId = async () => {
        try {
          await navigator.clipboard.writeText(job.id)
          toast.success("Job ID copied to clipboard")
        } catch (error) {
          toast.error("Failed to copy job ID")
        }
      }

      const handleViewDetails = () => {
        // TODO: Navigate to job details page
        toast.info("View details - Coming soon")
      }

      const handleViewHistory = () => {
        // TODO: Navigate to job history page
        toast.info("View history - Coming soon")
      }

      const handleToggleJob = async () => {
        try {
          // This will be passed from the parent component
          if (window.toggleCronJob) {
            await window.toggleCronJob(job.id)
            toast.success(job.status === "active" ? "Job paused" : "Job resumed")
          }
        } catch (error) {
          toast.error("Failed to toggle job status")
        }
      }

      const handleRunNow = async () => {
        try {
          // This will be passed from the parent component
          if (window.triggerCronJob) {
            await window.triggerCronJob(job.id)
            toast.success("Job execution started")
          }
        } catch (error) {
          toast.error("Failed to start job execution")
        }
      }

      const handleDeleteJob = async () => {
        console.log("Delete button clicked for job:", job.id)
        
        if (!confirm("Are you sure you want to delete this job? This action cannot be undone.")) {
          console.log("Delete cancelled by user")
          return
        }
        
        try {
          console.log("Checking if window.deleteCronJob exists:", !!window.deleteCronJob)
          // This will be passed from the parent component
          if (window.deleteCronJob) {
            console.log("Calling deleteCronJob for job:", job.id)
            
            // Show loading toast
            const loadingToast = toast.loading("Deleting job...")
            
            await window.deleteCronJob(job.id)
            
            // Dismiss loading toast and show success
            toast.dismiss(loadingToast)
            toast.success("Job deleted successfully")
            console.log("Delete successful")
            
            // Refresh the page data after successful deletion
            // Trigger SWR cache revalidation for all job-related data
            await Promise.all([
              mutate(['cronjobs']),
              mutate(['cronjobs', 0, 100, false]),
              mutate(['cronjobs', 0, 10, false]),
              mutate('dashboard-stats')
            ])
            
            // Also call the refresh function if available
            if (window.refreshJobs) {
              await window.refreshJobs()
            }
          } else {
            console.error("window.deleteCronJob is not available")
            toast.error("Delete function not available")
          }
        } catch (error) {
          console.error("Delete failed:", error)
          toast.error("Failed to delete job")
        }
      }

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem onClick={handleCopyJobId}>
              <Copy className="mr-2 h-4 w-4" />
              Copy job ID
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleViewDetails}>
              <Eye className="mr-2 h-4 w-4" />
              View details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleViewHistory}>
              <History className="mr-2 h-4 w-4" />
              View history
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {job.status === "active" ? (
              <DropdownMenuItem onClick={handleToggleJob}>
                <Pause className="mr-2 h-4 w-4" />
                Pause job
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem onClick={handleToggleJob}>
                <Play className="mr-2 h-4 w-4" />
                Resume job
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={handleRunNow}>
              <Play className="mr-2 h-4 w-4" />
              Run now
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleDeleteJob} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete job
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
]