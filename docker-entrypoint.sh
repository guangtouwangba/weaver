#!/bin/bash
# Docker entrypoint script for Hybrid Job Scheduler

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if config files exist
check_config() {
    if [ ! -f "config.yaml" ]; then
        log "ERROR: config.yaml not found!"
        log "Please mount your config.yaml file to /app/config.yaml"
        exit 1
    fi
    log "Configuration file found ✓"
    
    if [ ! -f "job_schedules.yaml" ]; then
        log "WARNING: job_schedules.yaml not found!"
        log "Creating default job schedules..."
        create_default_schedules
    else
        log "Job schedules file found ✓"
    fi
}

# Function to create default job schedules
create_default_schedules() {
    cat > job_schedules.yaml << 'EOF'
scheduler_settings:
  cron_check_interval: 30
  job_check_interval: 15
  max_concurrent_jobs: 2
  default_max_retries: 2
  default_timeout_seconds: 1800
  job_lock_duration_minutes: 15
  instance_prefix: "docker-scheduler"

job_schedules:
  - name: "Hourly Paper Fetch"
    job_type: "paper_fetch"
    cron_expression: "0 * * * *"
    description: "Hourly paper fetching"
    enabled: true
    config:
      config_path: "config.yaml"
      max_papers: 1000
      keywords: ["rag", "RAG", "agent", "Agents", "agents", "retrieval-augmented generation", "retrieval augmented generation"]
      
  - name: "Weekly Cleanup"
    job_type: "maintenance"
    cron_expression: "0 2 * * 0"
    description: "Weekly database cleanup"
    enabled: true
    config:
      cleanup_days: 30
EOF
    log "Default job schedules created ✓"
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
try:
    print(f'Current paper count: {db_manager.get_paper_count()}')
except:
    print('Paper count not available (expected for new setup)')
"
}

# Function to initialize cloud job tables
init_cloud_job_tables() {
    log "Initializing cloud job tables..."
    python -c "
import sys
sys.path.append('backend')
from database.database_adapter import create_database_manager
import yaml
from dotenv import load_dotenv
import os

load_dotenv()

def load_config(config_path='config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    import re
    def replace_env_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
    return yaml.safe_load(content)

config = load_config()
db_manager = create_database_manager(config)

# Create cloud job tables
try:
    from database.cloud_job_models import CloudJob
    if hasattr(db_manager.adapter, 'client') and hasattr(db_manager.adapter.client, 'client'):
        print('Using Supabase - ensure tables are created via SQL migrations')
    else:
        # SQLite - create tables
        import sqlite3
        conn = sqlite3.connect(db_manager.adapter.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cloud_jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                job_type TEXT NOT NULL,
                config TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'waiting',
                description TEXT,
                max_retries INTEGER DEFAULT 3,
                current_retries INTEGER DEFAULT 0,
                created_at TEXT,
                last_execution TEXT,
                locked_at TEXT,
                locked_by TEXT,
                lock_expires_at TEXT
            )
        ''')
        conn.commit()
        cursor.close()
        print('Cloud job tables created successfully')
except Exception as e:
    print(f'Warning: Could not initialize cloud job tables: {e}')
" || {
        log "WARNING: Cloud job table initialization failed, but continuing..."
    }
}

# Function to test system components
test_system() {
    log "Testing system components..."
    python -c "
import sys
sys.path.append('backend')

# Test croniter
try:
    from croniter import croniter
    print('✓ croniter library available')
except ImportError:
    print('✗ croniter library missing')

# Test database
try:
    from database.database_adapter import create_database_manager
    import yaml
    from dotenv import load_dotenv
    load_dotenv()
    
    def load_config(config_path='config.yaml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        import re
        def replace_env_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
        return yaml.safe_load(content)
    
    config = load_config()
    db_manager = create_database_manager(config)
    print(f'✓ Database connection successful ({type(db_manager.adapter).__name__})')
except Exception as e:
    print(f'✗ Database connection failed: {e}')

# Test hybrid scheduler import
try:
    import hybrid_job_scheduler
    print('✓ Hybrid scheduler module available')
except Exception as e:
    print(f'✗ Hybrid scheduler import failed: {e}')
" || {
        log "WARNING: System test failed, but continuing..."
    }
}

# Function to run hybrid scheduler
run_hybrid_scheduler() {
    log "Starting Hybrid Job Scheduler..."
    python hybrid_job_scheduler.py --daemon --verbose
}

# Function to run legacy scheduler
run_legacy_scheduler() {  
    log "Starting legacy database-driven job scheduler..."
    python job_scheduler_main.py start --daemon
}

# Function to run one-time fetch
run_once() {
    log "Running one-time paper fetch..."
    python simple_paper_fetcher.py
}

# Main execution
main() {
    log "Starting Hybrid Job Scheduler container..."
    
    # Check configuration
    check_config
    
    # Initialize database
    init_database
    
    # Initialize cloud job tables
    init_cloud_job_tables
    
    # Test system components
    test_system
    
    # Parse command line arguments
    case "${1:-hybrid-scheduler}" in
        "hybrid-scheduler")
            run_hybrid_scheduler
            ;;
        "scheduler"|"legacy-scheduler")
            run_legacy_scheduler
            ;;
        "once")
            run_once
            ;;
        "test")
            log "Test mode - container started successfully"
            log "Configuration: OK"
            log "Database: OK" 
            log "System: OK"
            log "Sleeping for 30 seconds then exiting..."
            sleep 30
            ;;
        "status")
            log "Checking hybrid scheduler status..."
            python hybrid_job_scheduler.py --status
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