# Research Agent - Cronjob Management UI

A modern web interface for managing automated research paper collection jobs built with Next.js 14 and shadcn/ui.

## Features

### 🎯 Dashboard
- **Statistics Overview**: Total jobs, success rate, papers processed, and failed runs
- **Recent Jobs**: Quick view of latest job executions with status indicators
- **System Health**: Real-time monitoring of API server, database, vector database, and job scheduler
- **Quick Actions**: Fast access to create jobs, run all jobs, and view reports

### 📊 Job Management
- **Data Table**: Sortable, filterable table with job information
- **Job Creation**: Comprehensive form for creating new cronjobs with:
  - Job name and description
  - Keyword-based search configuration
  - Schedule selection (daily, weekly, bi-weekly, monthly, custom cron)
  - Vector database provider selection (ChromaDB, Pinecone, Weaviate, Qdrant)
  - Embedding model selection (OpenAI, Cohere, HuggingFace)
  - Maximum papers per run configuration
- **Job Actions**: Start, pause, resume, delete, and view job details
- **Real-time Status**: Live updates of job execution status

### 🎨 Modern UI Components
Built with shadcn/ui components:
- **Responsive Design**: Mobile-first approach with breakpoint-based layouts
- **Dark/Light Theme**: Consistent theming across all components
- **Accessible Components**: WCAG compliant UI elements
- **Interactive Elements**: Buttons, forms, dialogs, dropdowns, tables
- **Status Indicators**: Badges, progress indicators, and health checks

## Technology Stack

- **Framework**: Next.js 14 with App Router
- **UI Library**: shadcn/ui with Radix UI primitives
- **Styling**: Tailwind CSS
- **Data Tables**: TanStack Table
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React
- **Notifications**: Sonner
- **Date Handling**: date-fns

## Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── (dashboard)/             # Dashboard layout group
│   │   ├── page.tsx            # Main dashboard
│   │   ├── jobs/               # Job management
│   │   │   └── page.tsx        # Jobs listing page
│   │   └── layout.tsx          # Dashboard layout with sidebar
│   ├── globals.css             # Global styles
│   └── layout.tsx              # Root layout
├── components/
│   ├── ui/                     # shadcn/ui components
│   │   ├── button.tsx          # Button variants
│   │   ├── card.tsx            # Card container
│   │   ├── badge.tsx           # Status badges
│   │   ├── table.tsx           # Table primitives
│   │   ├── dialog.tsx          # Modal dialogs
│   │   ├── form.tsx            # Form components
│   │   ├── input.tsx           # Input fields
│   │   ├── select.tsx          # Dropdown selects
│   │   ├── label.tsx           # Form labels
│   │   └── dropdown-menu.tsx   # Context menus
│   ├── layout/                 # Layout components
│   │   ├── header.tsx          # Page header with search and actions
│   │   └── sidebar.tsx         # Navigation sidebar
│   ├── data-table/             # Data table implementation
│   │   ├── columns.tsx         # Table column definitions
│   │   └── data-table.tsx      # Table component with sorting/filtering
│   └── forms/                  # Form components
│       └── create-job-form.tsx # Job creation form
├── lib/
│   └── utils.ts                # Utility functions
└── types/                      # TypeScript type definitions
```

## Pages and Navigation

### Dashboard (`/`)
- Overview statistics cards
- Recent jobs with status and actions
- System health monitoring
- Quick action buttons

### Jobs (`/jobs`)
- Comprehensive job listing table
- Create new job dialog
- Job management actions
- Search and filtering

### Navigation Sidebar
- Dashboard
- Jobs
- History (placeholder)
- Analytics (placeholder)
- Providers (placeholder)
- Settings (placeholder)

## Key Components

### Data Table Features
- **Sorting**: Click column headers to sort
- **Filtering**: Search by job name
- **Column Visibility**: Show/hide columns
- **Pagination**: Navigate through large datasets
- **Row Actions**: Dropdown menu for each job

### Job Creation Form
- **Form Validation**: Zod schema validation
- **Dynamic Keywords**: Add/remove keyword tags
- **Provider Selection**: Choose vector DB and embedding models
- **Schedule Configuration**: Various scheduling options
- **Real-time Feedback**: Form validation and error messages

### Status Management
- **Active**: Job running on schedule
- **Paused**: Job temporarily stopped
- **Running**: Job currently executing
- **Failed**: Job encountered errors
- **Completed**: Job finished successfully

## Getting Started

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Run Development Server**:
   ```bash
   npm run dev
   ```

3. **View Application**:
   Open [http://localhost:3000](http://localhost:3000) in your browser

## Development Commands

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
```

## Integration Points

This frontend is designed to integrate with the research-agent-rag backend API:

- **Cronjob Management**: `/api/cronjobs` endpoints for CRUD operations
- **Job Execution**: `/api/cronjobs/{id}/run` for manual job execution
- **Status Updates**: WebSocket or polling for real-time updates
- **Provider Configuration**: `/api/providers` for vector DB and embedding models
- **Job History**: `/api/cronjobs/{id}/history` for execution logs

## Future Enhancements

- **Real-time Updates**: WebSocket integration for live status updates
- **Job History Page**: Detailed execution logs and analytics
- **Provider Configuration**: UI for managing vector DB and embedding providers
- **Settings Page**: User preferences and system configuration
- **Analytics Dashboard**: Job performance and paper collection metrics
- **Export Functionality**: Download job data and reports

## Contributing

This project follows modern React and TypeScript best practices:
- Functional components with hooks
- TypeScript for type safety
- Server-side rendering with Next.js
- Responsive design with Tailwind CSS
- Accessible UI with Radix primitives