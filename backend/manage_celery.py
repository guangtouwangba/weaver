#!/usr/bin/env python3
"""
Celery management script for Research Agent RAG System
"""
import argparse
import os
import sys
import signal
import subprocess
import time
from typing import List, Dict, Any

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config

class CeleryManager:
    """Manager class for Celery worker processes"""
    
    def __init__(self):
        self.workers: List[subprocess.Popen] = []
        self.beat_process: subprocess.Popen = None
        self.flower_process: subprocess.Popen = None
    
    def start_worker(self, queue_name: str = "research", concurrency: int = 2, 
                    loglevel: str = "info") -> subprocess.Popen:
        """Start a Celery worker process"""
        cmd = [
            "celery", "-A", "celery_app", "worker",
            f"--loglevel={loglevel}",
            f"--concurrency={concurrency}",
            f"-Q", queue_name,
            "--without-heartbeat",  # Reduce network chatter
            "--without-gossip",     # Reduce network chatter
        ]
        
        print(f"Starting Celery worker for queue '{queue_name}' with {concurrency} workers...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.workers.append(process)
            print(f"Worker started with PID: {process.pid}")
            return process
            
        except Exception as e:
            print(f"Failed to start worker: {e}")
            return None
    
    def start_beat(self, loglevel: str = "info") -> subprocess.Popen:
        """Start Celery beat scheduler"""
        cmd = [
            "celery", "-A", "celery_app", "beat",
            f"--loglevel={loglevel}",
            "--schedule=/tmp/celerybeat-schedule",
        ]
        
        print("Starting Celery beat scheduler...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            self.beat_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print(f"Beat scheduler started with PID: {self.beat_process.pid}")
            return self.beat_process
            
        except Exception as e:
            print(f"Failed to start beat scheduler: {e}")
            return None
    
    def start_flower(self, port: int = 5555, loglevel: str = "info") -> subprocess.Popen:
        """Start Celery Flower monitoring"""
        broker_url = Config.get_celery_broker_url()
        cmd = [
            "celery", "-A", "celery_app", "flower",
            f"--port={port}",
            f"--broker={broker_url}",
        ]
        
        print(f"Starting Celery Flower monitoring on port {port}...")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            self.flower_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print(f"Flower started with PID: {self.flower_process.pid}")
            print(f"Flower UI available at: http://localhost:{port}")
            return self.flower_process
            
        except Exception as e:
            print(f"Failed to start Flower: {e}")
            return None
    
    def stop_all(self):
        """Stop all Celery processes"""
        print("Stopping all Celery processes...")
        
        # Stop workers
        for worker in self.workers:
            if worker.poll() is None:  # Process is still running
                print(f"Stopping worker PID: {worker.pid}")
                worker.terminate()
                try:
                    worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"Force killing worker PID: {worker.pid}")
                    worker.kill()
        
        # Stop beat scheduler
        if self.beat_process and self.beat_process.poll() is None:
            print(f"Stopping beat scheduler PID: {self.beat_process.pid}")
            self.beat_process.terminate()
            try:
                self.beat_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"Force killing beat scheduler PID: {self.beat_process.pid}")
                self.beat_process.kill()
        
        # Stop Flower
        if self.flower_process and self.flower_process.poll() is None:
            print(f"Stopping Flower PID: {self.flower_process.pid}")
            self.flower_process.terminate()
            try:
                self.flower_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"Force killing Flower PID: {self.flower_process.pid}")
                self.flower_process.kill()
        
        print("All processes stopped.")
    
    def monitor_processes(self):
        """Monitor and restart failed processes"""
        print("Monitoring Celery processes. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(5)
                
                # Check workers
                for i, worker in enumerate(self.workers):
                    if worker.poll() is not None:
                        print(f"Worker {i} (PID: {worker.pid}) has died. Exit code: {worker.returncode}")
                        # You could implement restart logic here
                
                # Check beat scheduler
                if self.beat_process and self.beat_process.poll() is not None:
                    print(f"Beat scheduler (PID: {self.beat_process.pid}) has died. Exit code: {self.beat_process.returncode}")
                
                # Check Flower
                if self.flower_process and self.flower_process.poll() is not None:
                    print(f"Flower (PID: {self.flower_process.pid}) has died. Exit code: {self.flower_process.returncode}")
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.stop_all()
    
    def status(self):
        """Show status of all processes"""
        print("Celery Process Status:")
        print("=" * 50)
        
        # Worker status
        for i, worker in enumerate(self.workers):
            status = "Running" if worker.poll() is None else f"Stopped (exit code: {worker.returncode})"
            print(f"Worker {i} (PID: {worker.pid}): {status}")
        
        # Beat scheduler status
        if self.beat_process:
            status = "Running" if self.beat_process.poll() is None else f"Stopped (exit code: {self.beat_process.returncode})"
            print(f"Beat Scheduler (PID: {self.beat_process.pid}): {status}")
        
        # Flower status
        if self.flower_process:
            status = "Running" if self.flower_process.poll() is None else f"Stopped (exit code: {self.flower_process.returncode})"
            print(f"Flower (PID: {self.flower_process.pid}): {status}")
    
    def health_check(self):
        """Perform health check on Celery system"""
        print("Performing Celery health check...")
        
        try:
            from tasks.research_tasks import health_check
            from celery_app import celery_app
            
            # Test task execution
            print("Testing task execution...")
            task = health_check.delay()
            result = task.get(timeout=30)
            
            if result.get('success'):
                print("✅ Health check passed!")
                print(f"Task ID: {task.id}")
                print(f"Result: {result}")
            else:
                print("❌ Health check failed!")
                print(f"Error: {result.get('error')}")
            
            # Test broker connection
            print("\nTesting broker connection...")
            inspector = celery_app.control.inspect()
            stats = inspector.stats()
            
            if stats:
                print("✅ Broker connection successful!")
                print(f"Active workers: {len(stats)}")
            else:
                print("❌ No active workers found!")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Celery Management for Research Agent RAG")
    parser.add_argument("command", choices=["start", "stop", "status", "monitor", "health"], 
                       help="Command to execute")
    parser.add_argument("--workers", type=int, default=2, help="Number of worker processes")
    parser.add_argument("--concurrency", type=int, default=2, help="Concurrency per worker")
    parser.add_argument("--loglevel", default="info", help="Log level")
    parser.add_argument("--flower", action="store_true", help="Start Flower monitoring")
    parser.add_argument("--beat", action="store_true", help="Start beat scheduler")
    parser.add_argument("--flower-port", type=int, default=5555, help="Flower port")
    
    args = parser.parse_args()
    
    manager = CeleryManager()
    
    # Setup signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived shutdown signal...")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.command == "start":
            # Start workers
            for i in range(args.workers):
                queue_name = "research" if i == 0 else f"processing"
                manager.start_worker(queue_name, args.concurrency, args.loglevel)
            
            # Start beat scheduler if requested
            if args.beat:
                manager.start_beat(args.loglevel)
            
            # Start Flower if requested
            if args.flower:
                manager.start_flower(args.flower_port, args.loglevel)
            
            # Monitor processes
            manager.monitor_processes()
            
        elif args.command == "stop":
            manager.stop_all()
            
        elif args.command == "status":
            manager.status()
            
        elif args.command == "monitor":
            manager.monitor_processes()
            
        elif args.command == "health":
            manager.health_check()
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        manager.stop_all()
    except Exception as e:
        print(f"Error: {e}")
        manager.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()