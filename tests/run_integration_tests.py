#!/usr/bin/env python3
"""
Integration test runner script

This script sets up the test environment and runs all integration tests
with proper database setup and cleanup.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_requirements():
    """Check if all required dependencies are available."""
    print("🔍 Checking test requirements...")
    
    required_packages = [
        'pytest',
        'pytest-asyncio', 
        'httpx',
        'fastapi',
        'sqlalchemy',
        'asyncpg'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are available")
    return True

def check_database_connection():
    """Check if test database is accessible."""
    print("🔍 Checking test database connection...")
    
    try:
        import asyncpg
        
        async def test_connection():
            try:
                conn = await asyncpg.connect(
                    "postgresql://rag_user:rag_password@localhost:5432/rag_test_db"
                )
                await conn.close()
                return True
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False
        
        result = asyncio.run(test_connection())
        if result:
            print("✅ Test database connection successful")
            return True
        else:
            return False
            
    except ImportError:
        print("❌ asyncpg not available for database testing")
        return False

def setup_test_database():
    """Set up test database."""
    print("🔧 Setting up test database...")
    
    # Create test database if it doesn't exist
    try:
        import asyncpg
        
        async def create_test_db():
            try:
                # Connect to default postgres db to create test db
                conn = await asyncpg.connect(
                    "postgresql://rag_user:rag_password@localhost:5432/postgres"
                )
                
                # Check if test database exists
                exists = await conn.fetchval(
                    "SELECT 1 FROM pg_database WHERE datname = 'rag_test_db'"
                )
                
                if not exists:
                    await conn.execute("CREATE DATABASE rag_test_db")
                    print("✅ Created test database: rag_test_db")
                else:
                    print("✅ Test database already exists: rag_test_db")
                
                await conn.close()
                return True
            except Exception as e:
                print(f"❌ Failed to create test database: {e}")
                return False
        
        return asyncio.run(create_test_db())
        
    except ImportError:
        print("❌ Cannot setup database without asyncpg")
        return False

def run_integration_tests(test_filter=None, verbose=False, coverage=False):
    """Run integration tests with specified options."""
    print("🚀 Running integration tests...")
    
    # Change to project directory
    os.chdir(project_root)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest", "tests/integration/"]
    
    # Add markers for integration tests
    cmd.extend(["-m", "integration"])
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.extend(["-v", "--tb=short"])
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=modules", "--cov-report=term-missing"])
    
    # Add specific test filter if provided
    if test_filter:
        cmd.extend(["-k", test_filter])
    
    # Add asyncio mode
    cmd.extend(["--asyncio-mode=auto"])
    
    # Run tests
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    
    return result.returncode == 0

def main():
    """Main test runner function."""
    print("🧪 RAG Knowledge Management API - Integration Test Runner")
    print("=" * 60)
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Run integration tests for RAG API")
    parser.add_argument(
        "--skip-checks", 
        action="store_true", 
        help="Skip requirement and database checks"
    )
    parser.add_argument(
        "--test-filter", 
        type=str, 
        help="Filter tests by name pattern"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Run tests with verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only setup test environment, don't run tests"
    )
    
    args = parser.parse_args()
    
    # Check requirements
    if not args.skip_checks:
        if not check_requirements():
            print("❌ Requirements check failed")
            return 1
        
        if not setup_test_database():
            print("⚠️ Database setup failed, but continuing...")
    
    if args.setup_only:
        print("✅ Test environment setup complete")
        return 0
    
    # Run integration tests
    success = run_integration_tests(
        test_filter=args.test_filter,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if success:
        print("\n✅ All integration tests passed!")
        print("🎉 RAG Knowledge Management API is working correctly!")
        return 0
    else:
        print("\n❌ Some integration tests failed!")
        print("🔍 Please check the test output above for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())