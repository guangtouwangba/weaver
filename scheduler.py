#!/usr/bin/env python3
"""
Simple Scheduler for ArXiv Paper Fetcher
Runs the paper fetching process at regular intervals.
"""

import os
import sys
import time
import signal
import threading
from datetime import datetime, timedelta
from typing import Optional
import logging

from simple_paper_fetcher import SimplePaperFetcher

class PaperFetchScheduler:
    """Simple scheduler for running paper fetching at regular intervals"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.fetcher = SimplePaperFetcher(config_path)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.next_run_time: Optional[datetime] = None
        
        # Load scheduler configuration
        self.interval_hours = self.fetcher.config['scheduler']['interval_hours']
        self.run_on_startup = self.fetcher.config['scheduler']['run_on_startup']
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logging.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _calculate_next_run_time(self) -> datetime:
        """Calculate the next run time"""
        return datetime.now() + timedelta(hours=self.interval_hours)
    
    def _run_fetch_job(self):
        """Run a single fetch job"""
        try:
            logging.info("Starting scheduled paper fetch")
            result = self.fetcher.run_once()
            
            if result['success']:
                logging.info(f"Scheduled fetch completed successfully: {result['new_papers']} new papers")
            else:
                logging.error(f"Scheduled fetch failed: {result['error']}")
                
        except Exception as e:
            logging.error(f"Unexpected error in scheduled fetch: {e}")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        # Run immediately on startup if configured
        if self.run_on_startup:
            logging.info("Running initial fetch on startup")
            self._run_fetch_job()
        
        # Calculate first run time
        self.next_run_time = self._calculate_next_run_time()
        logging.info(f"Next scheduled run: {self.next_run_time}")
        
        while self.running:
            current_time = datetime.now()
            
            # Check if it's time to run
            if self.next_run_time and current_time >= self.next_run_time:
                self._run_fetch_job()
                self.next_run_time = self._calculate_next_run_time()
                logging.info(f"Next scheduled run: {self.next_run_time}")
            
            # Sleep for a short interval before checking again
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logging.warning("Scheduler is already running")
            return
        
        logging.info(f"Starting paper fetch scheduler (interval: {self.interval_hours} hours)")
        self.running = True
        
        # Start the scheduler in a separate thread
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=False)
        self.thread.start()
        
        logging.info("Scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        logging.info("Stopping scheduler...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=30)
        
        logging.info("Scheduler stopped")
    
    def get_status(self) -> dict:
        """Get scheduler status information"""
        return {
            'running': self.running,
            'interval_hours': self.interval_hours,
            'next_run_time': self.next_run_time.isoformat() if self.next_run_time else None,
            'run_on_startup': self.run_on_startup
        }
    
    def run_now(self):
        """Trigger an immediate fetch run"""
        logging.info("Triggering immediate fetch run")
        self._run_fetch_job()
        # Update next scheduled run time
        self.next_run_time = self._calculate_next_run_time()
        logging.info(f"Next scheduled run updated to: {self.next_run_time}")

def main():
    """Main entry point for the scheduler"""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.yaml"
    
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        print("Please create a config.yaml file or specify the path as an argument.")
        sys.exit(1)
    
    # Create and start the scheduler
    scheduler = PaperFetchScheduler(config_path)
    
    try:
        scheduler.start()
        
        # Keep the main thread alive
        while scheduler.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    main()