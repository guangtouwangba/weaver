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
  FileText
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
            <DropdownMenuItem
              onClick={() => navigator.clipboard.writeText(job.id)}
            >
              Copy job ID
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              View details
            </DropdownMenuItem>
            <DropdownMenuItem>
              View history
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {job.status === "active" ? (
              <DropdownMenuItem>
                <Pause className="mr-2 h-4 w-4" />
                Pause job
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem>
                <Play className="mr-2 h-4 w-4" />
                Resume job
              </DropdownMenuItem>
            )}
            <DropdownMenuItem>
              <Play className="mr-2 h-4 w-4" />
              Run now
            </DropdownMenuItem>
            <DropdownMenuItem className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete job
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
]