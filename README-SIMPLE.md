# Simple ArXiv Paper Fetcher

A simplified system for automatically fetching academic papers from ArXiv based on configurable keywords, with built-in deduplication and PDF downloading.

## Features

- 🔍 **Keyword-based Search**: Configure search terms in YAML
- 📄 **PDF Download**: Automatically downloads and organizes PDFs
- 🗄️ **Deduplication**: SQLite database prevents duplicate papers
- ⏰ **Scheduling**: Configurable intervals for automated fetching
- 📊 **Logging**: Comprehensive logging with rotation
- 🎛️ **Configurable**: All settings managed via YAML configuration

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-simple.txt
```

### 2. Configure Keywords

Edit `config.yaml` to set your search keywords and preferences:

```yaml
search:
  keywords:
    - "machine learning"
    - "deep learning"
    - "neural networks"
  max_papers_per_run: 100
  days_back: 7  # Only search papers from last 7 days
```

### 3. Run Once

```bash
python simple_paper_fetcher.py
```

### 4. Run Scheduler

For automated periodic fetching:

```bash
python scheduler.py
```

## File Structure

```
├── config.yaml              # Main configuration file
├── simple_paper_fetcher.py  # Core fetching logic
├── scheduler.py              # Automated scheduling
├── papers.db                 # SQLite database (auto-created)
├── downloaded_papers/        # PDF storage directory
│   ├── 2024-01-15/          # Organized by date
│   │   ├── 2401.12345.pdf
│   │   └── 2401.12346.pdf
│   └── 2024-01-16/
└── paper_fetcher.log         # Application logs
```

## Configuration Options

### Search Settings
- `keywords`: List of search terms
- `max_papers_per_run`: Maximum papers to fetch per execution
- `categories`: ArXiv categories to filter by (e.g., "cs.AI", "cs.LG")
- `days_back`: Only search recent papers (0 = all time)
- `sort_by`: Sort results by "Relevance", "SubmittedDate", or "LastUpdatedDate"

### PDF Storage
- `base_directory`: Where to store downloaded PDFs
- `create_subdirectories`: Organize by date (YYYY-MM-DD)
- `filename_format`: PDF naming pattern (supports {arxiv_id}, {title_safe}, {date})

### Scheduler
- `interval_hours`: How often to run (default: 24 hours)
- `run_on_startup`: Run immediately when scheduler starts

### Advanced
- `request_delay`: Delay between ArXiv requests (respect rate limits)
- `download_timeout`: PDF download timeout in seconds
- `max_retries`: Retry attempts for failed downloads

## Database Schema

The SQLite database stores paper metadata:

```sql
CREATE TABLE papers (
    id TEXT PRIMARY KEY,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,        -- Pipe-separated
    abstract TEXT,
    categories TEXT NOT NULL,     -- Pipe-separated
    published DATETIME NOT NULL,
    pdf_url TEXT,
    pdf_path TEXT,               -- Local file path
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### One-time Fetch
```bash
# Use default config.yaml
python simple_paper_fetcher.py

# Use custom config
python simple_paper_fetcher.py my-config.yaml
```

### Scheduled Fetching
```bash
# Start scheduler (runs continuously)
python scheduler.py

# With custom config
python scheduler.py my-config.yaml
```

### View Statistics
```python
from simple_paper_fetcher import SimplePaperFetcher

fetcher = SimplePaperFetcher()
stats = fetcher.get_statistics()
print(f"Total papers: {stats['total_papers']}")
print(f"Papers this week: {stats['papers_this_week']}")
```

## Logging

Logs are written to both console and file with rotation:
- File: `paper_fetcher.log` (configurable)
- Max size: 10MB (configurable)
- Backup count: 3 files (configurable)
- Levels: DEBUG, INFO, WARNING, ERROR

## Deduplication

Papers are deduplicated by ArXiv ID. The system:
1. Loads existing ArXiv IDs from database
2. Filters new search results against existing IDs
3. Only processes truly new papers
4. Updates database with new entries

## Error Handling

- Failed PDF downloads are logged but don't stop processing
- Database errors are caught and logged
- Network timeouts are handled with retries
- Malformed papers are skipped with logging

## Extending the System

The modular design allows easy extension:

### Custom Search Filters
```python
from retrieval.arxiv_client import SearchFilter, DateRange

search_filter = SearchFilter(
    categories=['cs.AI', 'cs.LG'],
    authors=['Yann LeCun'],
    date_range=DateRange.LAST_MONTH
)
```

### Custom PDF Processing
Extend `PDFDownloader` class to add:
- Text extraction
- Metadata parsing  
- Custom storage backends

### Custom Notifications
Add notification hooks in `SimplePaperFetcher.run_once()`:
- Email summaries
- Slack notifications
- Webhook calls

## System Requirements

- Python 3.7+
- ~50MB disk space per 100 papers (PDFs vary in size)
- Internet connection for ArXiv API and PDF downloads
- Minimal CPU/memory requirements

## Rate Limiting

Respects ArXiv rate limits:
- Default 1-second delay between requests
- Configurable via `advanced.request_delay`
- Built-in retry logic for failed requests

## Troubleshooting

### Common Issues

1. **Config file not found**
   ```bash
   # Ensure config.yaml exists or specify path
   python simple_paper_fetcher.py path/to/config.yaml
   ```

2. **Permission errors**
   ```bash
   # Ensure write permissions for PDF directory and database
   chmod 755 downloaded_papers/
   chmod 644 papers.db
   ```

3. **Network timeouts**
   ```yaml
   # Increase timeout in config.yaml
   advanced:
     download_timeout: 600  # 10 minutes
   ```

4. **Database locked**
   ```bash
   # Stop any running processes using the database
   ps aux | grep paper_fetcher
   kill <process_id>
   ```

### Debug Mode

Enable debug logging:
```yaml
logging:
  level: "DEBUG"
```

This provides detailed information about:
- Search queries sent to ArXiv
- PDF download progress
- Database operations
- Error stack traces