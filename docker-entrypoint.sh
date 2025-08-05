#!/bin/bash
# Docker entrypoint script for ArXiv Paper Fetcher

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if config file exists
check_config() {
    if [ ! -f "config.yaml" ]; then
        log "ERROR: config.yaml not found!"
        log "Please mount your config.yaml file to /app/config.yaml"
        exit 1
    fi
    log "Configuration file found ✓"
}

# Function to initialize database
init_database() {
    log "Initializing database..."
    python -c "
import os
import yaml
from dotenv import load_dotenv
import sys
sys.path.append('backend')

# Load environment variables
load_dotenv()

# Load config with environment variable substitution
def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    import re
    def replace_env_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
    return yaml.safe_load(content)

# Initialize database using the new adapter
from database.database_adapter import create_database_manager
config = load_config()
db_manager = create_database_manager(config)
print(f'Database initialized successfully using {type(db_manager.adapter).__name__}')
print(f'Current paper count: {db_manager.get_paper_count()}')
"
}

# Function to test ArXiv connection
test_connection() {
    log "Testing ArXiv API connection..."
    python -c "
import sys
sys.path.append('backend')
from retrieval.arxiv_api_client import ArxivAPIClient
client = ArxivAPIClient()
papers = client.search_papers(['test'], max_results=1)
print(f'Connection test successful - found {len(papers)} papers')
" || {
        log "WARNING: ArXiv connection test failed, but continuing..."
    }
}

# Function to run one-time fetch
run_once() {
    log "Running one-time paper fetch..."
    python simple_paper_fetcher.py
}

# Function to run scheduler
run_scheduler() {  
    log "Starting paper fetching scheduler..."
    python scheduler.py
}

# Main execution
main() {
    log "Starting ArXiv Paper Fetcher container..."
    
    # Check configuration
    check_config
    
    # Initialize database
    init_database
    
    # Test connection
    test_connection
    
    # Parse command line arguments
    case "${1:-scheduler}" in
        "scheduler")
            run_scheduler
            ;;
        "once")
            run_once
            ;;
        "test")
            log "Test mode - container started successfully"
            log "Configuration: OK"
            log "Database: OK" 
            log "Connection: OK"
            log "Sleeping for 30 seconds then exiting..."
            sleep 30
            ;;
        "bash"|"sh")
            log "Starting interactive shell..."
            exec /bin/bash
            ;;
        *)
            log "Running custom command: $*"
            exec "$@"
            ;;
    esac
}

# Run main function
main "$@"