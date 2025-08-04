# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a simplified ArXiv paper fetching system that automatically searches for academic papers based on configurable keywords, downloads PDFs, and stores metadata in a local database with deduplication.

## Core Architecture

### Main Components
- **ArXiv Client** (`backend/retrieval/arxiv_client.py`): Academic paper retrieval from ArXiv API
- **Paper Fetcher** (`simple_paper_fetcher.py`): Main application logic for fetching, deduplicating, and storing papers
- **PDF Downloader**: Built-in PDF download and organization system
- **SQLite Database**: Simple database for paper metadata and deduplication
- **Scheduler** (`scheduler.py`): Simple scheduler for automated periodic fetching
- **YAML Configuration** (`config.yaml`): All settings managed via YAML file

## Development Commands

### Installation
```bash
# Install dependencies
pip install -r requirements-simple.txt
```

### Running the System
```bash
# Single run - fetch papers once
python simple_paper_fetcher.py

# With custom config file
python simple_paper_fetcher.py my-config.yaml

# Start scheduler for periodic fetching
python scheduler.py

# Start scheduler with custom config
python scheduler.py my-config.yaml
```

### Repository Cleanup (Optional)
```bash
# Preview files that would be removed
python cleanup_repository.py

# Actually remove unnecessary files
python cleanup_repository.py --execute
```

## Key Configuration

### Main Configuration (`config.yaml`)
All system settings are managed through the YAML configuration file:

#### Search Configuration
- `keywords`: List of search terms for ArXiv
- `max_papers_per_run`: Maximum papers to fetch per execution (default: 100)
- `categories`: ArXiv categories to filter by (e.g., "cs.AI", "cs.LG")
- `days_back`: Only search recent papers (0 = all time, 7 = last week)
- `sort_by`: Sort results by "Relevance", "SubmittedDate", or "LastUpdatedDate"

#### PDF Storage Configuration
- `base_directory`: Where to store downloaded PDFs (default: "./downloaded_papers")
- `create_subdirectories`: Organize PDFs by date (YYYY-MM-DD folders)
- `filename_format`: PDF naming pattern (supports {arxiv_id}, {title_safe}, {date})

#### Scheduler Configuration
- `interval_hours`: How often to run automated fetching (default: 24 hours)
- `run_on_startup`: Whether to run immediately when scheduler starts

#### Database Configuration
- `url`: SQLite database path (default: "sqlite:///papers.db")

## Important Development Notes

### Paper Fetching Process
- Uses the existing `ArxivClient` from `backend/retrieval/arxiv_client.py`
- Supports keyword-based search with advanced filtering
- Handles pagination and rate limiting automatically
- Respects ArXiv API rate limits with configurable delays

### Deduplication System
- SQLite database stores paper metadata for deduplication
- Papers are deduplicated by ArXiv ID before processing
- Existing papers are skipped to avoid redundant downloads
- Database schema includes: id, arxiv_id, title, authors, abstract, categories, published, pdf_url, pdf_path

### PDF Download and Storage
- Downloads PDFs directly from ArXiv using paper.pdf_url
- Organizes files by date in subdirectories (YYYY-MM-DD format)
- Supports configurable filename patterns
- Handles download failures gracefully with logging

### Logging System
- Comprehensive logging to both console and rotating log files
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Log file rotation with size limits and backup counts
- Detailed operation tracking for debugging

### Scheduler Implementation
- Simple threading-based scheduler (no external dependencies)
- Configurable interval-based execution
- Graceful shutdown handling with signal handlers
- Optional immediate execution on startup

## Common Workflows

### Adding New Search Keywords
1. Edit `config.yaml` and add keywords to the `search.keywords` list
2. Optionally add relevant ArXiv categories to `search.categories`
3. Run the fetcher to test: `python simple_paper_fetcher.py`

### Customizing PDF Storage
1. Modify `pdf_storage` section in `config.yaml`
2. Change `base_directory` to your preferred location
3. Customize `filename_format` with available variables: `{arxiv_id}`, `{title_safe}`, `{date}`
4. Set `create_subdirectories: false` to store all PDFs in one directory

### Database Maintenance
1. The SQLite database is created automatically on first run
2. View papers: Use any SQLite browser or command line: `sqlite3 papers.db "SELECT * FROM papers LIMIT 10;"`
3. Reset database: Delete `papers.db` file to start fresh
4. Backup database: Copy `papers.db` file to backup location

### Scheduling for Production
1. For production use, consider setting up as a system service
2. Use `scheduler.py` for simple interval-based scheduling
3. For more complex scheduling, integrate with cron or systemd timers
4. Monitor logs in `paper_fetcher.log` for operational status

### GitHub Actions Integration
1. Create `.github/workflows/fetch-papers.yml` 
2. Set up scheduled workflow with `schedule: - cron: '0 0 * * *'` (daily)
3. Configure repository secrets for any API keys if needed
4. Use actions to commit results back to repository