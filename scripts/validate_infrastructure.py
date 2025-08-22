#!/usr/bin/env python3
"""
Infrastructure validation script.

This script validates that the merged infrastructure modules
work correctly and can connect to the database.
"""

import sys
import asyncio
from typing import Dict, Any


def test_imports() -> Dict[str, bool]:
    """Test that all infrastructure modules can be imported."""
    results = {}

    try:
        from infrastructure.database.config import (
            get_database_config,
            get_database_session,
        )

        results["database_config"] = True
    except Exception as e:
        print(f"❌ Database config import failed: {e}")
        results["database_config"] = False

    try:
        from infrastructure.database.models import Base, get_all_models

        models = get_all_models()
        results["database_models"] = True
        print(f"✅ Found {len(models)} database models")
    except Exception as e:
        print(f"❌ Database models import failed: {e}")
        results["database_models"] = False

    try:
        from infrastructure.database.repositories import BaseRepository

        results["database_repositories"] = True
    except Exception as e:
        print(f"❌ Database repositories import failed: {e}")
        results["database_repositories"] = False

    return results


def test_database_connection() -> bool:
    """Test database connectivity."""
    try:
        from infrastructure.database.config import check_database_connection

        is_connected = check_database_connection()
        if is_connected:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
        return is_connected
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


def test_alembic_integration() -> bool:
    """Test that Alembic can still work with the new structure."""
    try:
        from infrastructure.database.config import db_config
        from infrastructure.database.models import Base

        # Check that config is accessible
        url = db_config.alembic_url
        print(
            f"✅ Alembic URL accessible: {url.split('@')[1] if '@' in url else 'configured'}"
        )

        # Check that Base metadata is accessible
        tables = list(Base.metadata.tables.keys())
        print(f"✅ Found {len(tables)} tables in metadata")

        return True
    except Exception as e:
        print(f"❌ Alembic integration test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🔍 Validating Infrastructure Merge...")
    print("=" * 50)

    # Test imports
    print("\n📦 Testing imports...")
    import_results = test_imports()

    # Test database connection
    print("\n🔌 Testing database connection...")
    connection_ok = test_database_connection()

    # Test Alembic integration
    print("\n🔄 Testing Alembic integration...")
    alembic_ok = test_alembic_integration()

    # Summary
    print("\n📊 Summary:")
    print("=" * 50)

    all_imports_ok = all(import_results.values())
    overall_success = all_imports_ok and connection_ok and alembic_ok

    if all_imports_ok:
        print("✅ All imports successful")
    else:
        failed_imports = [k for k, v in import_results.items() if not v]
        print(f"❌ Import failures: {', '.join(failed_imports)}")

    if connection_ok:
        print("✅ Database connection working")
    else:
        print("❌ Database connection issues")

    if alembic_ok:
        print("✅ Alembic integration working")
    else:
        print("❌ Alembic integration issues")

    if overall_success:
        print("\n🎉 Infrastructure merge validation PASSED!")
        return 0
    else:
        print("\n💥 Infrastructure merge validation FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
