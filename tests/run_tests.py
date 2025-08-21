"""
Comprehensive test runner with different test execution modes.

Provides commands to run different types of tests with appropriate configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time

class TestRunner:
    """Comprehensive test runner for RAG system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_dir = project_root / "tests"
    
    def run_unit_tests(self, coverage: bool = False, verbose: bool = False):
        """Run unit tests."""
        print("🧪 Running Unit Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            "-m", "unit",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=modules",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov/unit"
            ])
        
        return self._run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self, coverage: bool = False, verbose: bool = False):
        """Run integration tests."""
        print("🔧 Running Integration Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "integration"),
            "-m", "integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=modules",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov/integration"
            ])
        
        return self._run_command(cmd, "Integration Tests")
    
    def run_e2e_tests(self, verbose: bool = False):
        """Run end-to-end tests."""
        print("🎯 Running End-to-End Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "e2e"),
            "-m", "e2e",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "End-to-End Tests")
    
    def run_performance_tests(self, verbose: bool = False):
        """Run performance tests."""
        print("⚡ Running Performance Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "performance",
            "--tb=short",
            "--maxfail=1"  # Stop on first failure for performance tests
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "Performance Tests")
    
    def run_api_tests(self, coverage: bool = False, verbose: bool = False):
        """Run API-specific tests."""
        print("🌐 Running API Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "api",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=modules.api",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov/api"
            ])
        
        return self._run_command(cmd, "API Tests")
    
    def run_database_tests(self, verbose: bool = False):
        """Run database-specific tests."""
        print("🗄️ Running Database Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "database",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, "Database Tests")
    
    def run_all_tests(self, coverage: bool = False, verbose: bool = False, fast: bool = False):
        """Run all tests."""
        print("🚀 Running All Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "--tb=short"
        ]
        
        if fast:
            cmd.extend(["-m", "not slow and not performance"])
            print("   (Skipping slow and performance tests for fast run)")
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=modules",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov/all",
                "--cov-report=xml:coverage.xml"
            ])
        
        return self._run_command(cmd, "All Tests")
    
    def run_smoke_tests(self):
        """Run smoke tests (critical functionality only)."""
        print("💨 Running Smoke Tests")
        print("=" * 50)
        
        # Run a subset of critical tests
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-k", "test_create_topic or test_upload_file or test_health_check",
            "--tb=short",
            "--maxfail=3"
        ]
        
        return self._run_command(cmd, "Smoke Tests")
    
    def run_load_tests(self):
        """Run load tests."""
        print("📊 Running Load Tests")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "load_test",
            "--tb=short",
            "-v"
        ]
        
        return self._run_command(cmd, "Load Tests")
    
    def run_custom_tests(self, test_pattern: str, markers: str = None, verbose: bool = False):
        """Run custom test selection."""
        print(f"🎯 Running Custom Tests: {test_pattern}")
        print("=" * 50)
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-k", test_pattern,
            "--tb=short"
        ]
        
        if markers:
            cmd.extend(["-m", markers])
        
        if verbose:
            cmd.append("-v")
        
        return self._run_command(cmd, f"Custom Tests ({test_pattern})")
    
    def _run_command(self, cmd: list, test_type: str) -> bool:
        """Run a test command and return success status."""
        print(f"Command: {' '.join(cmd)}")
        print("-" * 50)
        
        start_time = time.time()
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            end_time = time.time()
            
            duration = end_time - start_time
            
            if result.returncode == 0:
                print(f"✅ {test_type} PASSED in {duration:.1f}s")
                return True
            else:
                print(f"❌ {test_type} FAILED in {duration:.1f}s")
                return False
        
        except Exception as e:
            print(f"💥 {test_type} ERROR: {e}")
            return False
        
        finally:
            print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for RAG knowledge management system"
    )
    
    parser.add_argument(
        "test_type",
        choices=[
            "unit", "integration", "e2e", "performance", 
            "api", "database", "all", "smoke", "load", "custom"
        ],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fast", "-f",
        action="store_true",
        help="Skip slow tests (for 'all' test type)"
    )
    
    parser.add_argument(
        "--pattern", "-p",
        type=str,
        help="Test pattern for custom test selection"
    )
    
    parser.add_argument(
        "--markers", "-m",
        type=str,
        help="Pytest markers for custom test selection"
    )
    
    args = parser.parse_args()
    
    # Find project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    runner = TestRunner(project_root)
    
    print("RAG Knowledge Management System - Test Runner")
    print("=" * 60)
    print()
    
    success = False
    
    if args.test_type == "unit":
        success = runner.run_unit_tests(coverage=args.coverage, verbose=args.verbose)
    
    elif args.test_type == "integration":
        success = runner.run_integration_tests(coverage=args.coverage, verbose=args.verbose)
    
    elif args.test_type == "e2e":
        success = runner.run_e2e_tests(verbose=args.verbose)
    
    elif args.test_type == "performance":
        success = runner.run_performance_tests(verbose=args.verbose)
    
    elif args.test_type == "api":
        success = runner.run_api_tests(coverage=args.coverage, verbose=args.verbose)
    
    elif args.test_type == "database":
        success = runner.run_database_tests(verbose=args.verbose)
    
    elif args.test_type == "all":
        success = runner.run_all_tests(coverage=args.coverage, verbose=args.verbose, fast=args.fast)
    
    elif args.test_type == "smoke":
        success = runner.run_smoke_tests()
    
    elif args.test_type == "load":
        success = runner.run_load_tests()
    
    elif args.test_type == "custom":
        if not args.pattern:
            print("❌ Custom test type requires --pattern argument")
            sys.exit(1)
        success = runner.run_custom_tests(
            test_pattern=args.pattern,
            markers=args.markers,
            verbose=args.verbose
        )
    
    # Print summary
    print("=" * 60)
    if success:
        print("🎉 Test execution completed successfully!")
        sys.exit(0)
    else:
        print("💥 Test execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()