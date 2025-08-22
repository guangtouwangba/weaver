#!/usr/bin/env python3
"""
Dependency checker for RAG system.

This script checks if all required dependencies are installed and available.
"""

import sys
import importlib
from typing import List, Tuple, Dict, Any


def check_import(module_name: str, package_name: str = None) -> Tuple[bool, str]:
    """
    Check if a module can be imported.

    Args:
        module_name: Name of the module to import
        package_name: Name of the package (for display purposes)

    Returns:
        Tuple of (success, error_message)
    """
    try:
        importlib.import_module(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def check_dependencies() -> Dict[str, Any]:
    """Check all required dependencies."""

    # Core dependencies
    core_deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("alembic", "Alembic"),
    ]

    # Infrastructure dependencies
    infra_deps = [
        ("minio", "MinIO"),
        ("redis", "Redis"),
        ("asyncpg", "AsyncPG"),
        ("psycopg2", "psycopg2"),
        ("httpx", "HTTPX"),
    ]

    # Optional dependencies
    optional_deps = [
        ("pytest", "pytest"),
        ("black", "Black"),
        ("isort", "isort"),
        ("mypy", "mypy"),
    ]

    results = {
        "core": {},
        "infrastructure": {},
        "optional": {},
        "summary": {"total": 0, "passed": 0, "failed": 0},
    }

    # Check core dependencies
    print("🔍 Checking core dependencies...")
    for module, name in core_deps:
        success, error = check_import(module)
        results["core"][name] = {"success": success, "error": error}
        results["summary"]["total"] += 1
        if success:
            results["summary"]["passed"] += 1
            print(f"  ✅ {name}")
        else:
            results["summary"]["failed"] += 1
            print(f"  ❌ {name}: {error}")

    # Check infrastructure dependencies
    print("\n🏗️  Checking infrastructure dependencies...")
    for module, name in infra_deps:
        success, error = check_import(module)
        results["infrastructure"][name] = {"success": success, "error": error}
        results["summary"]["total"] += 1
        if success:
            results["summary"]["passed"] += 1
            print(f"  ✅ {name}")
        else:
            results["summary"]["failed"] += 1
            print(f"  ❌ {name}: {error}")

    # Check optional dependencies
    print("\n🔧 Checking optional dependencies...")
    for module, name in optional_deps:
        success, error = check_import(module)
        results["optional"][name] = {"success": success, "error": error}
        results["summary"]["total"] += 1
        if success:
            results["summary"]["passed"] += 1
            print(f"  ✅ {name}")
        else:
            results["summary"]["failed"] += 1
            print(f"  ⚠️  {name}: {error}")

    return results


def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    version = sys.version_info

    if version >= (3, 9):
        print(
            f"  ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)"
        )
        return True
    else:
        print(
            f"  ❌ Python {version.major}.{version.minor}.{version.micro} (requires >= 3.9)"
        )
        return False


def check_critical_modules():
    """Check if critical modules can be imported."""
    print("\n🎯 Checking critical application modules...")

    critical_modules = [
        "domain.topic",
        "infrastructure",
        "application.topic",
        "api.topic_routes",
        "main",
    ]

    success_count = 0
    total_count = len(critical_modules)

    for module in critical_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
            success_count += 1
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
        except Exception as e:
            print(f"  ⚠️  {module}: {e}")

    return success_count, total_count


def main():
    """Main function."""
    print("🚀 RAG System Dependency Checker")
    print("=" * 50)

    # Check Python version
    python_ok = check_python_version()

    # Check dependencies
    results = check_dependencies()

    # Check critical modules
    critical_success, critical_total = check_critical_modules()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary")
    print(f"Python Version: {'✅ Compatible' if python_ok else '❌ Incompatible'}")
    print(
        f"Dependencies: {results['summary']['passed']}/{results['summary']['total']} passed"
    )
    print(f"Critical Modules: {critical_success}/{critical_total} available")

    # Core dependencies status
    core_failed = [
        name for name, result in results["core"].items() if not result["success"]
    ]
    infra_failed = [
        name
        for name, result in results["infrastructure"].items()
        if not result["success"]
    ]

    if core_failed:
        print(f"\n❌ Missing core dependencies: {', '.join(core_failed)}")
        print("   Run: make install-server")

    if infra_failed:
        print(f"\n❌ Missing infrastructure dependencies: {', '.join(infra_failed)}")
        print("   Run: make install-server")

    # Overall status
    all_critical_ok = (
        python_ok
        and not core_failed
        and not infra_failed
        and critical_success == critical_total
    )

    if all_critical_ok:
        print("\n🎉 All critical dependencies are available!")
        print("✅ You can start the server with: make server")
    else:
        print("\n⚠️  Some dependencies are missing or unavailable.")
        print("🔧 Run the following commands to fix issues:")
        print("   1. make install-server")
        print("   2. make setup-dev  # for development")
        print("   3. make server     # to start the server")

    # Exit with appropriate code
    sys.exit(0 if all_critical_ok else 1)


if __name__ == "__main__":
    main()
