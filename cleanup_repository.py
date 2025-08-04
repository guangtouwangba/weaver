#!/usr/bin/env python3
"""
Repository Cleanup Script
Removes unnecessary files and directories to simplify the repository to core functionality.
"""

import os
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RepositoryCleanup:
    """Handles repository cleanup operations"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.repo_root = Path(__file__).parent
        
    def remove_directory(self, path: Path, reason: str = ""):
        """Remove a directory and all its contents"""
        if not path.exists():
            logging.info(f"Directory doesn't exist: {path}")
            return
            
        if self.dry_run:
            logging.info(f"[DRY RUN] Would remove directory: {path} - {reason}")
        else:
            try:
                shutil.rmtree(path)
                logging.info(f"Removed directory: {path} - {reason}")
            except Exception as e:
                logging.error(f"Failed to remove directory {path}: {e}")
    
    def remove_file(self, path: Path, reason: str = ""):
        """Remove a single file"""
        if not path.exists():
            logging.info(f"File doesn't exist: {path}")
            return
            
        if self.dry_run:
            logging.info(f"[DRY RUN] Would remove file: {path} - {reason}")
        else:
            try:
                path.unlink()
                logging.info(f"Removed file: {path} - {reason}")
            except Exception as e:
                logging.error(f"Failed to remove file {path}: {e}")
    
    def cleanup_frontend(self):
        """Remove entire frontend directory"""
        frontend_dir = self.repo_root / "frontend"
        self.remove_directory(frontend_dir, "Frontend UI not needed in simplified version")
    
    def cleanup_agents(self):
        """Remove multi-agent system"""
        agents_dir = self.repo_root / "backend" / "agents"
        if agents_dir.exists():
            # Keep only the base_agent.py as it might be referenced
            for item in agents_dir.iterdir():
                if item.name != "base_agent.py" and item.name != "__init__.py":
                    if item.is_file():
                        self.remove_file(item, "Multi-agent system not needed")
                    else:
                        self.remove_directory(item, "Multi-agent system not needed")
    
    def cleanup_celery(self):
        """Remove Celery-related files"""
        celery_files = [
            "backend/celery_app.py",
            "backend/manage_celery.py",
            "backend/tasks",
            "start-celery.sh",
            "start-dev-celery.sh"
        ]
        
        for file_path in celery_files:
            path = self.repo_root / file_path
            if path.is_file():
                self.remove_file(path, "Celery task system not needed")
            elif path.is_dir():
                self.remove_directory(path, "Celery task system not needed")
    
    def cleanup_database_extras(self):
        """Remove complex database features"""
        db_extras = [
            "backend/database/vector_db",
            "backend/database/embeddings",
            "backend/database/migrations",
            "backend/database/vector_store.py",
            "backend/database/vector_store_adapter.py"
        ]
        
        for item_path in db_extras:
            path = self.repo_root / item_path
            if path.is_file():
                self.remove_file(path, "Vector DB and embeddings not needed")
            elif path.is_dir():
                self.remove_directory(path, "Vector DB and embeddings not needed")
    
    def cleanup_api_extras(self):
        """Remove complex API components"""
        api_extras = [
            "backend/api/batch_processor.py",
            "backend/api/server.py",  # Keep simple_server.py
            "backend/main.py",  # Complex FastAPI server
            "backend/routes",
            "backend/controllers",
            "backend/services",
            "backend/repositories"
        ]
        
        for item_path in api_extras:
            path = self.repo_root / item_path
            if path.is_file():
                self.remove_file(path, "Complex API features not needed")
            elif path.is_dir():
                self.remove_directory(path, "Complex API features not needed")
    
    def cleanup_infrastructure(self):
        """Remove complex infrastructure"""
        infra_items = [
            "infra/docker",
            "infra/k8s",
            "infra/nginx",
            "infra/scheduler",  # We have our own simple scheduler
            "infra/scripts"
        ]
        
        for item_path in infra_items:
            path = self.repo_root / item_path
            if path.is_dir():
                self.remove_directory(path, "Complex infrastructure not needed")
    
    def cleanup_misc_files(self):
        """Remove miscellaneous files not needed"""
        misc_files = [
            "backend/chat",
            "backend/elasticsearch_config",
            "backend/utils/analysis_websocket_manager.py",
            "backend/utils/elasticsearch_logger.py",
            "backend/utils/websocket_manager.py",
            "backend/test_*.py",
            "CELERY_SETUP.md",
            "ELASTICSEARCH_SETUP.md",
            "VECTOR_DB_CONFIG.md",
            "JOB_LOGS_README.md",
            "docs",
            "tests",
            "logs",
            "scripts",
            "zbpack.json",
            "zeabur.yaml",
            "pyproject.toml",
            "Makefile",
            "check-env.sh",
            "deploy-zeabur.sh",
            "start-*.sh",
            "test-*.sh"
        ]
        
        for item_path in misc_files:
            path = self.repo_root / item_path
            if path.is_file():
                self.remove_file(path, "Not needed in simplified version")
            elif path.is_dir():
                self.remove_directory(path, "Not needed in simplified version")
    
    def cleanup_requirements(self):
        """Remove complex requirements files, keep simple one"""
        req_files = [
            "requirements.txt",
            "requirements.serverless.txt",
            "backend/requirements-minimal.txt",
            "backend/requirements-ultra-minimal.txt",
            "requirements-mvp.txt"
        ]
        
        for req_file in req_files:
            path = self.repo_root / req_file
            self.remove_file(path, "Replaced by requirements-simple.txt")
    
    def cleanup_data_directories(self):
        """Clean up data directories but preserve structure"""
        data_items = [
            "data/vector_db",
            "backend/data"
        ]
        
        for item_path in data_items:
            path = self.repo_root / item_path
            if path.is_dir():
                self.remove_directory(path, "Vector DB data not needed")
    
    def run_cleanup(self):
        """Run all cleanup operations"""
        logging.info(f"Starting repository cleanup (dry_run={self.dry_run})")
        
        # Major component cleanups
        self.cleanup_frontend()
        self.cleanup_agents()
        self.cleanup_celery()
        self.cleanup_database_extras()
        self.cleanup_api_extras()
        self.cleanup_infrastructure()
        self.cleanup_data_directories()
        
        # File cleanups
        self.cleanup_misc_files()
        self.cleanup_requirements()
        
        logging.info("Repository cleanup completed")
        
        if self.dry_run:
            logging.info("This was a DRY RUN. Re-run with --execute to actually remove files.")

def main():
    import sys
    
    # Check for execute flag
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        dry_run = False
        print("WARNING: This will permanently delete files and directories!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Cleanup cancelled.")
            return
    
    cleanup = RepositoryCleanup(dry_run=dry_run)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()