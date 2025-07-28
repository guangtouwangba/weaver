"use client"

import { useState } from "react"
import { Header } from "@/components/layout/header"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Plus, RefreshCw, AlertTriangle } from "lucide-react"
import { DataTable } from "@/components/data-table/data-table"
import { columns, type CronjobData } from "@/components/data-table/columns"
import { CreateJobForm } from "@/components/forms/create-job-form"
import { useCronJobs, useCronJobMutations, useAvailableProviders } from "@/lib/hooks/api-hooks"
import { Card, CardContent } from "@/components/ui/card"
import { toast } from "sonner"

// Helper function to transform API job data to table format
function transformJobToTableData(job: any): CronjobData {
  return {
    id: job.id,
    name: job.name,
    description: `Keywords: ${job.keywords.join(", ")}`,
    status: job.enabled ? "active" : "paused",
    schedule: job.cron_expression || `Every ${job.interval_hours} hours`,
    lastRun: null, // We'll need to fetch this from job status
    nextRun: null, // We'll need to calculate this
    papersFound: 0, // We'll need to fetch this from job runs
    papersProcessed: 0, // We'll need to fetch this from job runs
    keywords: job.keywords,
    vectorDb: job.vector_db_provider,
    embeddingModel: job.embedding_model,
    createdAt: new Date(job.created_at),
  }
}

export default function JobsPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  // Fetch data using SWR hooks
  const { data: jobs, error: jobsError, isLoading: jobsLoading, mutate: refreshJobs } = useCronJobs()
  const { data: providers, error: providersError } = useAvailableProviders()
  const { createCronJob } = useCronJobMutations()

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      await refreshJobs()
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleCreateJob = async (values: any) => {
    try {
      // Map form values to API format
      const jobData = {
        name: values.name,
        keywords: values.keywords,
        enabled: true,
        max_papers_per_run: values.maxPapers,
        embedding_provider: values.embeddingModel.split('-')[0], // Extract provider from model name
        embedding_model: values.embeddingModel,
        vector_db_provider: values.vectorDb,
        // Set schedule based on form selection
        ...(values.schedule === 'daily' ? { interval_hours: 24 } :
            values.schedule === 'weekly' ? { interval_hours: 168 } :
            values.schedule === 'bi-weekly' ? { interval_hours: 336 } :
            values.schedule === 'monthly' ? { interval_hours: 720 } :
            { cron_expression: values.schedule }) // Custom cron
      }

      await createCronJob(jobData)
      setCreateDialogOpen(false)
      toast.success("Cronjob created successfully!")
    } catch (error: any) {
      console.error("Failed to create job:", error)
      toast.error(error.message || "Failed to create cronjob")
    }
  }

  // Loading state
  if (jobsLoading) {
    return (
      <div className="flex flex-col">
        <Header 
          title="Cronjobs" 
          description="Manage your automated research paper collection jobs"
          action={
            <Button disabled>
              <Plus className="mr-2 h-4 w-4" />
              New Job
            </Button>
          }
        />
        <div className="flex-1 p-6">
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <div className="text-center">
                <RefreshCw className="h-8 w-8 text-muted-foreground animate-spin mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Loading jobs...</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Error state
  if (jobsError) {
    return (
      <div className="flex flex-col">
        <Header 
          title="Cronjobs" 
          description="Manage your automated research paper collection jobs"
          action={
            <Button onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Retry
            </Button>
          }
        />
        <div className="flex-1 p-6">
          <Card>
            <CardContent className="flex items-center justify-center py-8">
              <div className="text-center">
                <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  Failed to load jobs. Please check your connection and try again.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Transform API data to table format
  const tableData = jobs ? jobs.map(transformJobToTableData) : []

  return (
    <div className="flex flex-col">
      <Header 
        title="Cronjobs" 
        description="Manage your automated research paper collection jobs"
        action={
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Job
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New Cronjob</DialogTitle>
                </DialogHeader>
                <CreateJobForm 
                  onSubmit={handleCreateJob}
                  onCancel={() => setCreateDialogOpen(false)}
                  providers={providers}
                />
              </DialogContent>
            </Dialog>
          </div>
        }
      />
      
      <div className="flex-1 p-6">
        <DataTable columns={columns} data={tableData} />
      </div>
    </div>
  )
}