#!/usr/bin/env python3
"""
Docker Setup Test Script
Tests the docker-compose setup for Research Agent RAG System
"""

import subprocess
import time
import requests
import json
import sys
from typing import Dict, List, Tuple

class DockerSetupTester:
    def __init__(self):
        self.base_urls = {
            'backend': 'http://localhost:8000',
            'frontend': 'http://localhost:3000',
            'weaviate': 'http://localhost:8080',
            'postgres': 'localhost:5432',
            'redis': 'localhost:6379'
        }
        
    def run_command(self, command: str, cwd: str = None) -> Tuple[int, str, str]:
        """Run a shell command and return (return_code, stdout, stderr)"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def check_docker_compose_status(self) -> bool:
        """Check if docker-compose services are running"""
        print("🔍 Checking Docker Compose status...")
        
        cmd = "docker-compose ps"
        return_code, stdout, stderr = self.run_command(cmd, cwd="infra/docker")
        
        if return_code != 0:
            print(f"❌ Failed to check docker-compose status: {stderr}")
            return False
            
        print("✅ Docker Compose status:")
        print(stdout)
        return True

    def check_service_health(self, service: str, url: str, endpoint: str = None) -> bool:
        """Check if a service is healthy"""
        try:
            if endpoint:
                full_url = f"{url}{endpoint}"
            else:
                full_url = url
                
            response = requests.get(full_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {service} is healthy")
                return True
            else:
                print(f"❌ {service} returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ {service} is not responding: {e}")
            return False

    def check_postgres_health(self) -> bool:
        """Check PostgreSQL health using docker exec"""
        print("🔍 Checking PostgreSQL health...")
        
        cmd = "docker-compose exec -T postgres pg_isready -U research_user -d research_agent"
        return_code, stdout, stderr = self.run_command(cmd, cwd="infra/docker")
        
        if return_code == 0:
            print("✅ PostgreSQL is healthy")
            return True
        else:
            print(f"❌ PostgreSQL health check failed: {stderr}")
            return False

    def check_redis_health(self) -> bool:
        """Check Redis health using docker exec"""
        print("🔍 Checking Redis health...")
        
        cmd = "docker-compose exec -T redis redis-cli -a redis_password ping"
        return_code, stdout, stderr = self.run_command(cmd, cwd="infra/docker")
        
        if return_code == 0 and "PONG" in stdout:
            print("✅ Redis is healthy")
            return True
        else:
            print(f"❌ Redis health check failed: {stderr}")
            return False

    def test_backend_api(self) -> bool:
        """Test backend API endpoints"""
        print("🔍 Testing backend API...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.base_urls['backend']}/health", timeout=10)
            if response.status_code != 200:
                print(f"❌ Backend health endpoint failed: {response.status_code}")
                return False
                
            # Test API endpoints
            endpoints = [
                "/api/dashboard/stats",
                "/api/cronjobs"
            ]
            
            for endpoint in endpoints:
                response = requests.get(f"{self.base_urls['backend']}{endpoint}", timeout=10)
                if response.status_code != 200:
                    print(f"❌ Backend endpoint {endpoint} failed: {response.status_code}")
                    return False
                    
            print("✅ Backend API is working correctly")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Backend API test failed: {e}")
            return False

    def test_frontend(self) -> bool:
        """Test frontend application"""
        print("🔍 Testing frontend...")
        
        try:
            # Test frontend health
            response = requests.get(f"{self.base_urls['frontend']}/api/health", timeout=10)
            if response.status_code != 200:
                print(f"❌ Frontend health check failed: {response.status_code}")
                return False
                
            # Test main page
            response = requests.get(f"{self.base_urls['frontend']}/", timeout=10)
            if response.status_code != 200:
                print(f"❌ Frontend main page failed: {response.status_code}")
                return False
                
            print("✅ Frontend is working correctly")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Frontend test failed: {e}")
            return False

    def test_weaviate(self) -> bool:
        """Test Weaviate vector database"""
        print("🔍 Testing Weaviate...")
        
        try:
            response = requests.get(f"{self.base_urls['weaviate']}/v1/.well-known/ready", timeout=10)
            if response.status_code == 200:
                print("✅ Weaviate is healthy")
                return True
            else:
                print(f"❌ Weaviate health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Weaviate test failed: {e}")
            return False

    def check_container_logs(self) -> bool:
        """Check container logs for errors"""
        print("🔍 Checking container logs...")
        
        services = ['research-agent-backend', 'research-agent-frontend', 'postgres', 'weaviate', 'redis']
        
        for service in services:
            cmd = f"docker-compose logs --tail=10 {service}"
            return_code, stdout, stderr = self.run_command(cmd, cwd="infra/docker")
            
            if return_code == 0:
                print(f"📋 {service} logs (last 10 lines):")
                print(stdout)
            else:
                print(f"❌ Failed to get logs for {service}: {stderr}")
                
        return True

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🚀 Starting Docker Setup Tests...")
        print("=" * 50)
        
        results = {}
        
        # Check Docker Compose status
        results['docker_compose'] = self.check_docker_compose_status()
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        time.sleep(30)
        
        # Health checks
        results['postgres'] = self.check_postgres_health()
        results['redis'] = self.check_redis_health()
        results['weaviate'] = self.test_weaviate()
        results['backend'] = self.test_backend_api()
        results['frontend'] = self.test_frontend()
        
        # Check logs
        results['logs'] = self.check_container_logs()
        
        return results

    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test:20} {status}")
            if result:
                passed += 1
                
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Docker setup is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the logs above.")
            return False

def main():
    """Main function"""
    tester = DockerSetupTester()
    
    try:
        results = tester.run_all_tests()
        success = tester.print_summary(results)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 