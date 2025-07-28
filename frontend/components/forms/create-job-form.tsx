"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { X, Plus } from "lucide-react"
import { useState } from "react"

const formSchema = z.object({
  name: z.string().min(2, {
    message: "Job name must be at least 2 characters.",
  }),
  description: z.string().min(10, {
    message: "Description must be at least 10 characters.",
  }),
  keywords: z.array(z.string()).min(1, {
    message: "At least one keyword is required.",
  }),
  schedule: z.string().min(1, {
    message: "Please select a schedule.",
  }),
  vectorDb: z.string().min(1, {
    message: "Please select a vector database.",
  }),
  embeddingModel: z.string().min(1, {
    message: "Please select an embedding model.",
  }),
  maxPapers: z.number().min(1).max(1000, {
    message: "Max papers must be between 1 and 1000.",
  }),
})

interface CreateJobFormProps {
  onSubmit: (values: z.infer<typeof formSchema>) => void
  onCancel: () => void
  providers?: {
    vector_databases: string[]
    embedding_models: string[]
  } | null
}

export function CreateJobForm({ onSubmit, onCancel, providers }: CreateJobFormProps) {
  const [keywordInput, setKeywordInput] = useState("")
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      keywords: [],
      schedule: "",
      vectorDb: "",
      embeddingModel: "",
      maxPapers: 100,
    },
  })

  const keywords = form.watch("keywords")

  const addKeyword = () => {
    if (keywordInput.trim() && !keywords.includes(keywordInput.trim())) {
      form.setValue("keywords", [...keywords, keywordInput.trim()])
      setKeywordInput("")
    }
  }

  const removeKeyword = (keyword: string) => {
    form.setValue("keywords", keywords.filter(k => k !== keyword))
  }

  const handleKeywordKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault()
      addKeyword()
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Job Name</FormLabel>
              <FormControl>
                <Input placeholder="AI Research Papers" {...field} />
              </FormControl>
              <FormDescription>
                A descriptive name for your cronjob.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Input placeholder="Daily collection of AI and machine learning research papers" {...field} />
              </FormControl>
              <FormDescription>
                Detailed description of what this job collects.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="keywords"
          render={() => (
            <FormItem>
              <FormLabel>Keywords</FormLabel>
              <FormControl>
                <div className="space-y-3">
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Enter keywords..."
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyDown={handleKeywordKeyDown}
                    />
                    <Button type="button" onClick={addKeyword} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {keywords.map((keyword) => (
                      <Badge key={keyword} variant="secondary" className="flex items-center gap-1">
                        {keyword}
                        <X 
                          className="h-3 w-3 cursor-pointer" 
                          onClick={() => removeKeyword(keyword)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>
              </FormControl>
              <FormDescription>
                Keywords to search for in research papers. Press Enter or click + to add.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="schedule"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Schedule</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a schedule" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="bi-weekly">Bi-weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="custom">Custom Cron</SelectItem>
                </SelectContent>
              </Select>
              <FormDescription>
                How frequently this job should run.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="vectorDb"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Vector Database</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select vector DB" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {providers?.vector_databases?.map((db) => (
                      <SelectItem key={db} value={db}>
                        {db.charAt(0).toUpperCase() + db.slice(1)}
                      </SelectItem>
                    )) || (
                      <>
                        <SelectItem value="chromadb">ChromaDB</SelectItem>
                        <SelectItem value="pinecone">Pinecone</SelectItem>
                        <SelectItem value="weaviate">Weaviate</SelectItem>
                        <SelectItem value="qdrant">Qdrant</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="embeddingModel"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Embedding Model</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select embedding model" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {providers?.embedding_models?.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    )) || (
                      <>
                        <SelectItem value="openai-ada-002">OpenAI text-embedding-ada-002</SelectItem>
                        <SelectItem value="openai-3-small">OpenAI text-embedding-3-small</SelectItem>
                        <SelectItem value="openai-3-large">OpenAI text-embedding-3-large</SelectItem>
                        <SelectItem value="cohere-english-v3">Cohere embed-english-v3.0</SelectItem>
                        <SelectItem value="huggingface-sentence-transformers">HuggingFace sentence-transformers</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="maxPapers"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Max Papers per Run</FormLabel>
              <FormControl>
                <Input 
                  type="number" 
                  placeholder="100" 
                  {...field}
                  onChange={(e) => field.onChange(parseInt(e.target.value) || 0)}
                />
              </FormControl>
              <FormDescription>
                Maximum number of papers to process in each run (1-1000).
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end space-x-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit">Create Job</Button>
        </div>
      </form>
    </Form>
  )
}