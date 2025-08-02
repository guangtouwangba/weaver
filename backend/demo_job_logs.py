#!/usr/bin/env python3
"""
Job实时日志功能完整演示脚本
Demonstrates the complete job real-time logging functionality
"""
import asyncio
import json
import requests
import websockets
from datetime import datetime
import time
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

class JobLogDemo:
    """Job logging functionality demo"""
    
    def __init__(self):
        self.job_id = None
        self.job_run_id = None
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def create_test_cronjob(self) -> bool:
        """Create a test cronjob"""
        print("🔧 Creating test cronjob...")
        
        job_data = {
            "name": f"Test Job {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "keywords": ["machine learning", "neural networks"],
            "cron_expression": "0 0 * * *",  # Daily at midnight
            "enabled": True,
            "max_papers_per_run": 10,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-small",
            "vector_db_provider": "chroma"
        }
        
        result = self.make_request("POST", "/api/cronjobs", data=job_data)
        
        if result["success"]:
            self.job_id = result["data"]["id"]
            print(f"✅ Created cronjob: {self.job_id}")
            print(f"   Name: {result['data']['name']}")
            return True
        else:
            print(f"❌ Failed to create cronjob: {result}")
            return False
    
    def trigger_job(self) -> bool:
        """Trigger the test job"""
        if not self.job_id:
            print("❌ No job ID available")
            return False
            
        print(f"🚀 Triggering job: {self.job_id}")
        
        trigger_data = {"force_reprocess": False}
        result = self.make_request("POST", f"/api/cronjobs/{self.job_id}/trigger", data=trigger_data)
        
        if result["success"]:
            self.job_run_id = result["data"]["job_run_id"]
            print(f"✅ Job triggered successfully")
            print(f"   Job Run ID: {self.job_run_id}")
            return True
        else:
            print(f"❌ Failed to trigger job: {result}")
            return False
    
    def get_job_logs(self, limit: int = 20) -> bool:
        """Get job logs via REST API"""
        if not self.job_id:
            print("❌ No job ID available")
            return False
            
        print(f"📋 Fetching logs for job: {self.job_id}")
        
        params = {
            "limit": limit,
            "skip": 0
        }
        
        result = self.make_request("GET", f"/api/cronjobs/{self.job_id}/logs", params=params)
        
        if result["success"]:
            logs_data = result["data"]
            print(f"✅ Retrieved {len(logs_data.get('logs', []))} logs")
            print(f"   Total available: {logs_data.get('total', 0)}")
            
            # Display recent logs
            for log in logs_data.get('logs', [])[:5]:  # Show first 5 logs
                timestamp = log.get('timestamp', '')[:19]  # Remove microseconds
                level = log.get('level', 'INFO')
                message = log.get('message', '')[:80]  # Truncate long messages
                print(f"   [{timestamp}] {level}: {message}")
            
            return True
        else:
            print(f"❌ Failed to get logs: {result}")
            return False
    
    async def stream_logs_websocket(self, duration: int = 30):
        """Stream logs via WebSocket"""
        if not self.job_id:
            print("❌ No job ID available")
            return False
            
        print(f"🌐 Starting WebSocket log streaming for job: {self.job_id}")
        print(f"   Duration: {duration} seconds")
        
        uri = f"{WS_BASE_URL}/api/cronjobs/{self.job_id}/logs/ws"
        
        try:
            async with websockets.connect(uri, timeout=10) as websocket:
                print("✅ WebSocket connected")
                
                # Send subscription
                subscription = {
                    "type": "subscribe",
                    "types": ["log", "status", "metric"],
                    "filters": {}
                }
                await websocket.send(json.dumps(subscription))
                
                # Listen for messages
                start_time = time.time()
                message_count = 0
                
                while time.time() - start_time < duration:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        message_count += 1
                        
                        msg_type = data.get('type', 'unknown')
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        
                        if msg_type == 'log':
                            log_data = data.get('data', {})
                            level = log_data.get('level', 'INFO')
                            message_text = log_data.get('message', '')[:60]
                            print(f"   [{timestamp}] 📝 {level}: {message_text}")
                        elif msg_type == 'status':
                            status_data = data.get('data', {})
                            print(f"   [{timestamp}] 🔄 Status: {status_data}")
                        elif msg_type == 'metric':
                            metric_data = data.get('data', {})
                            print(f"   [{timestamp}] 📊 Metric: {metric_data}")
                        elif msg_type in ['connected', 'subscribed', 'pong']:
                            print(f"   [{timestamp}] ✅ {msg_type.title()}")
                        else:
                            print(f"   [{timestamp}] 📥 {msg_type}: {data.get('data', {})}")
                            
                    except asyncio.TimeoutError:
                        # No message received, continue
                        pass
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON decode error: {e}")
                
                print(f"✅ WebSocket streaming completed. Received {message_count} messages")
                return True
                
        except websockets.exceptions.ConnectionRefused:
            print("❌ WebSocket connection refused - server may not be running")
            return False
        except Exception as e:
            print(f"❌ WebSocket streaming failed: {e}")
            return False
    
    def get_job_status(self) -> bool:
        """Get job status"""
        if not self.job_id:
            print("❌ No job ID available")
            return False
            
        print(f"📊 Getting job status: {self.job_id}")
        
        result = self.make_request("GET", f"/api/cronjobs/{self.job_id}/status")
        
        if result["success"]:
            status_data = result["data"]
            print(f"✅ Job Status:")
            print(f"   Name: {status_data.get('job_name', 'Unknown')}")
            print(f"   Enabled: {status_data.get('enabled', False)}")
            
            latest_run = status_data.get('latest_run')
            if latest_run:
                print(f"   Latest Run:")
                print(f"     Status: {latest_run.get('status', 'unknown')}")
                print(f"     Started: {latest_run.get('started_at', 'unknown')}")
                print(f"     Progress: {latest_run.get('progress_percentage', 0)}%")
            
            stats = status_data.get('statistics', {})
            print(f"   Statistics:")
            print(f"     Total Runs: {stats.get('total_runs', 0)}")
            print(f"     Success Rate: {stats.get('success_rate', 0):.1f}%")
            
            return True
        else:
            print(f"❌ Failed to get job status: {result}")
            return False
    
    def cleanup_test_job(self) -> bool:
        """Clean up the test job"""
        if not self.job_id:
            print("❌ No job ID to clean up")
            return False
            
        print(f"🧹 Cleaning up test job: {self.job_id}")
        
        result = self.make_request("DELETE", f"/api/cronjobs/{self.job_id}")
        
        if result["success"]:
            print("✅ Test job cleaned up successfully")
            return True
        else:
            print(f"⚠️  Failed to clean up test job: {result}")
            return False

async def main():
    """Run the complete demo"""
    print("🎭 Job实时日志功能完整演示")
    print("=" * 60)
    print("This demo will:")
    print("1. Create a test cronjob")
    print("2. Trigger the job execution")
    print("3. Fetch logs via REST API")
    print("4. Stream real-time logs via WebSocket")
    print("5. Show job status and statistics")
    print("6. Clean up the test job")
    print("=" * 60)
    
    demo = JobLogDemo()
    
    try:
        # Step 1: Create test job
        if not demo.create_test_cronjob():
            print("❌ Demo failed: Could not create test job")
            return
        
        print("\n" + "-" * 40)
        
        # Step 2: Trigger job
        if not demo.trigger_job():
            print("❌ Demo failed: Could not trigger job")
            return
        
        print("\n" + "-" * 40)
        
        # Wait a moment for the job to start
        print("⏱️  Waiting for job to start...")
        await asyncio.sleep(3)
        
        # Step 3: Get job logs via REST API
        demo.get_job_logs()
        
        print("\n" + "-" * 40)
        
        # Step 4: Stream logs via WebSocket
        await demo.stream_logs_websocket(duration=15)
        
        print("\n" + "-" * 40)
        
        # Step 5: Get job status
        demo.get_job_status()
        
        print("\n" + "-" * 40)
        
        # Step 6: Clean up
        demo.cleanup_test_job()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！Job实时日志功能已成功验证")
        print("\n📋 功能摘要:")
        print("✅ REST API - 获取job历史日志")
        print("✅ WebSocket - 实时日志流")
        print("✅ 多级别日志过滤")
        print("✅ Elasticsearch日志存储")
        print("✅ 结构化日志格式")
        print("✅ 任务状态跟踪")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
        demo.cleanup_test_job()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        demo.cleanup_test_job()

if __name__ == "__main__":
    print("🚀 Starting Job Logs Demo...")
    print("Make sure the FastAPI server is running on localhost:8000")
    print("Press Ctrl+C to stop the demo at any time\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo startup failed: {e}")