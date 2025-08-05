# Supabase Integration Setup

This guide explains how to set up and use Supabase as the cloud database for the ArXiv Paper Fetcher and RAG system.

## What is Supabase?

Supabase is an open-source Firebase alternative that provides a PostgreSQL database, real-time subscriptions, authentication, and more. Using Supabase allows your local and cloud deployments to access the same database.

## Benefits of Using Supabase

- **Cloud Database**: Access your papers from anywhere
- **Unified Data**: Local and cloud versions share the same database
- **Scalability**: PostgreSQL database scales with your needs
- **Real-time**: Real-time database subscriptions (for future features)
- **Free Tier**: Generous free tier for personal projects

## Setup Instructions

### 1. Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in to your account
3. Click "New Project"
4. Choose your organization
5. Set project name (e.g., "arxiv-paper-fetcher")
6. Set database password
7. Choose region closest to you
8. Click "Create new project"

### 2. Get Your Credentials

Once your project is created:

1. Go to **Settings** → **API**
2. Copy your **Project URL** (looks like `https://your-project.supabase.co`)
3. Copy your **anon public** key (starts with `eyJhbGciOi...`)

### 3. Configure Environment Variables

Create or update your `.env` file:

```bash
# Copy .env.example to .env if you haven't already
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...your-key-here

# Other configurations...
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Create the Database Table

1. Go to your Supabase dashboard
2. Click on **SQL Editor** in the sidebar
3. Create a new query and paste the following SQL:

```sql
-- Create papers table
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    abstract TEXT,
    categories TEXT NOT NULL,
    published TIMESTAMP WITH TIME ZONE NOT NULL,
    pdf_url TEXT,
    pdf_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published);
CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers(categories);

-- Enable Row Level Security (RLS)
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
-- Public read access (adjust as needed for your security requirements)
CREATE POLICY IF NOT EXISTS "Public read access" ON papers
    FOR SELECT TO anon, authenticated
    USING (true);

-- Authenticated write access
CREATE POLICY IF NOT EXISTS "Authenticated write access" ON papers
    FOR ALL TO authenticated
    USING (true);
```

4. Click **Run** to execute the SQL

**Important**: If you get a syntax error with `DO` blocks, use the simplified SQL from `scripts/supabase_job_schema.sql` instead.

### 5. Update Configuration

Edit `config.yaml` to use Supabase:

```yaml
database:
  # Change provider from "sqlite" to "supabase"
  provider: "supabase"
  
  # SQLite configuration (local development)
  url: "sqlite:///papers.db"
  
  # Supabase configuration (cloud deployment)
  supabase_url: "${SUPABASE_URL}"        # Set in .env file
  supabase_key: "${SUPABASE_ANON_KEY}"   # Set in .env file
```

### 6. Install Dependencies

Make sure you have the Supabase client installed:

```bash
pip install -r requirements-simple.txt
# or
pip install supabase==2.9.1 python-dotenv==1.0.1
```

### 7. Test the Integration

Run the test script to verify everything works:

```bash
python scripts/test_supabase.py
```

You should see output like:
```
🧪 Supabase Integration Test
========================================
✅ Supabase URL: https://your-project.supabase.co
✅ Supabase key configured
✅ Database manager created successfully
✅ Test 1 (Database Connection): PASSED
✅ Test 2 (Paper Insertion): PASSED

========================================
Tests completed: 2/2 passed
🎉 All tests passed! Supabase integration is working correctly.
```

## Migrating Existing Data

If you have existing papers in a SQLite database, use the migration script:

```bash
python scripts/migrate_to_supabase.py
```

This script will:
1. Show you the SQL to create the table (if not done already)
2. Migrate all papers from SQLite to Supabase
3. Optionally update your config.yaml to use Supabase by default

## Usage

Once configured, all components work the same way:

### Paper Fetcher
```bash
python simple_paper_fetcher.py
```

### RAG Question Answering
```bash
python rag_main.py
```

The system will automatically use Supabase when configured. You can switch back to SQLite by changing the `provider` in `config.yaml`.

## Monitoring and Management

### View Your Data
1. Go to Supabase dashboard
2. Click **Table Editor**
3. Select the `papers` table
4. View, edit, or query your papers

### Database Logs
1. Go to **Settings** → **Logs**
2. View database queries and performance

### Backup
Supabase automatically backs up your database. You can also:
1. Go to **Settings** → **Database**
2. Use the backup tools

## Troubleshooting

### Common Issues

1. **"supabase library is required"**
   ```bash
   pip install supabase==2.9.1
   ```

2. **"Supabase credentials not found"**
   - Check your `.env` file exists
   - Verify SUPABASE_URL and SUPABASE_ANON_KEY are set correctly

3. **"Table doesn't exist"**
   - Run the SQL table creation script in Supabase dashboard

4. **"new row violates row-level security policy"**
   
   This is the most common issue. You have two solutions:
   
   **Solution A: Allow anonymous write access (Development)**
   
   Run this SQL in your Supabase SQL Editor:
   ```sql
   -- Drop the existing restrictive policy
   DROP POLICY IF EXISTS "Authenticated write access" ON papers;
   
   -- Create a new policy that allows anonymous write access
   CREATE POLICY "Allow anonymous write access" ON papers
       FOR ALL TO anon, authenticated
       USING (true)
       WITH CHECK (true);
   ```
   
   **Solution B: Use service role key (Production)**
   
   1. Go to Settings → API in your Supabase dashboard
   2. Copy the "service_role" key (not the anon key)
   3. Add it to your `.env` file:
   ```bash
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...your-service-role-key
   ```
   
   Note: Service role key bypasses RLS and should be kept secure.

5. **Permission denied errors**
   - Check your RLS policies
   - Make sure you're using the correct key
   - For write operations, use service role key or allow anon writes

### Getting Help

1. Check the [Supabase documentation](https://supabase.com/docs)
2. Verify your environment variables: `python -c "import os; print(os.getenv('SUPABASE_URL'))"`
3. Test the connection: `python scripts/test_supabase.py`

## Security Considerations

- The `anon` key is safe to use in client applications
- Row Level Security (RLS) is enabled for additional protection
- Consider customizing the access policies for your use case
- For production, consider using service role keys and custom authentication

## Cost

Supabase offers a generous free tier:
- 500MB database storage
- 1GB bandwidth
- 50,000 monthly active users

For most personal projects, this is sufficient. See [Supabase pricing](https://supabase.com/pricing) for details.