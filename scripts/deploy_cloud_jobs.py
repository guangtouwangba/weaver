#!/usr/bin/env python3
"""
Deploy Cloud Job System
Automated deployment script for cloud job system
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description="", fail_on_error=True):
    """Run a shell command"""
    print(f"🔄 {description}")
    print(f"   Running: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - Success")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
    else:
        print(f"❌ {description} - Failed")
        if result.stderr.strip():
            print(f"   Error: {result.stderr.strip()}")
        if fail_on_error:
            sys.exit(1)
    
    return result.returncode == 0

def check_prerequisites():
    """Check system prerequisites"""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}")
    
    # Check if we're in the right directory
    if not os.path.exists('cloud_job_runner.py'):
        print("❌ Please run from the project root directory")
        return False
    print("✅ Project directory found")
    
    # Check config file
    if not os.path.exists('config.yaml'):
        print("⚠️  config.yaml not found - using defaults")
    else:
        print("✅ config.yaml found")
    
    return True

def setup_environment():
    """Setup Python environment"""
    print("\n🐍 Setting up Python environment...")
    
    # Install/upgrade pip
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    if os.path.exists('requirements-simple.txt'):
        run_command("pip install -r requirements-simple.txt", "Installing requirements")
    elif os.path.exists('requirements.txt'):
        run_command("pip install -r requirements.txt", "Installing requirements")
    else:
        print("⚠️  No requirements file found")
    
    # Install additional dependencies for cloud deployment
    cloud_deps = [
        "python-dotenv>=1.0.0",
        "supabase>=2.9.1",
        "pyyaml>=6.0"
    ]
    
    for dep in cloud_deps:
        run_command(f"pip install '{dep}'", f"Installing {dep}", fail_on_error=False)

def initialize_database():
    """Initialize database tables"""
    print("\n🗄️  Initializing database...")
    
    # Check environment variables
    if not os.getenv('SUPABASE_URL'):
        print("⚠️  SUPABASE_URL not set - using SQLite for local testing")
    else:
        print(f"✅ Supabase URL: {os.getenv('SUPABASE_URL')}")
    
    # Initialize tables
    run_command("python scripts/init_cloud_job_tables.py", "Initializing cloud job tables")

def run_tests():
    """Run system tests"""
    print("\n🧪 Running system tests...")
    
    run_command("python scripts/test_cloud_job_system.py", "Testing cloud job system")

def create_sample_jobs():
    """Create sample jobs for testing"""
    print("\n📋 Creating sample jobs...")
    
    # Paper fetch job
    run_command(
        'python cloud_job_manager.py create "Sample Paper Fetch" paper_fetch --description "Sample paper fetching job"',
        "Creating paper fetch job",
        fail_on_error=False
    )
    
    # Maintenance job  
    run_command(
        'python cloud_job_manager.py create "Sample Maintenance" maintenance --description "Sample maintenance job" --job-config cleanup_days=7',
        "Creating maintenance job",
        fail_on_error=False
    )

def show_deployment_info():
    """Show deployment information"""
    print("\n🎉 Deployment Summary")
    print("=" * 50)
    
    # Show job statistics
    print("📊 Current Job Statistics:")
    run_command("python cloud_job_manager.py stats", "Getting job statistics", fail_on_error=False)
    
    print("\n🚀 Next Steps:")
    print("1. Test single job execution:")
    print("   python cloud_job_runner.py --dry-run")
    print("   python cloud_job_runner.py")
    
    print("\n2. Monitor jobs:")
    print("   python cloud_job_manager.py list")
    print("   python cloud_job_manager.py show <job_id>")
    
    print("\n3. Create production jobs:")
    print("   python cloud_job_manager.py create 'Production Fetch' paper_fetch")
    
    print("\n4. Deploy to cloud:")
    print("   - AWS Lambda: See CLOUD_JOB_RUNNER.md")
    print("   - Kubernetes: See deployment examples")
    print("   - Docker: docker build -t cloud-job-runner .")
    
    print("\n📚 Documentation:")
    print("   - Full guide: CLOUD_JOB_RUNNER.md")
    print("   - Troubleshooting: python scripts/test_cloud_job_system.py")

def deploy_docker():
    """Deploy with Docker"""
    print("\n🐳 Docker Deployment...")
    
    # Create Dockerfile if it doesn't exist
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements-simple.txt

ENV PYTHONPATH=/app/backend
CMD ["python", "cloud_job_runner.py"]
"""
    
    if not os.path.exists('Dockerfile'):
        with open('Dockerfile', 'w') as f:
            f.write(dockerfile_content)
        print("✅ Created Dockerfile")
    
    # Build Docker image
    run_command("docker build -t cloud-job-runner .", "Building Docker image")
    
    # Show run instructions
    print("\n🚀 Docker image built successfully!")
    print("To run:")
    print("  docker run --env-file .env cloud-job-runner")
    print("  docker run -e SUPABASE_URL=... -e SUPABASE_ANON_KEY=... cloud-job-runner")

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Cloud Job System")
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--skip-samples', action='store_true', help='Skip creating sample jobs')
    parser.add_argument('--docker', action='store_true', help='Build Docker image')
    parser.add_argument('--env-file', help='Environment file to load')
    
    args = parser.parse_args()
    
    print("🚀 Cloud Job System Deployment")
    print("=" * 50)
    
    # Load environment file
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
        print(f"✅ Loaded environment from {args.env_file}")
    
    # Run deployment steps
    try:
        if not check_prerequisites():
            sys.exit(1)
        
        setup_environment()
        initialize_database()
        
        if not args.skip_tests:
            run_tests()
        
        if not args.skip_samples:
            create_sample_jobs()
        
        if args.docker:
            deploy_docker()
        
        show_deployment_info()
        
        print("\n🎉 Deployment completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()