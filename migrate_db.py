#!/usr/bin/env python3
"""Run database migrations."""

import subprocess
import sys
import os

def main():
    """Run alembic upgrade head."""
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("🔄 Running database migration...")
    print("=" * 60)
    
    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("=" * 60)
            print("✅ Migration completed successfully!")
            print("\n📋 Created tables:")
            print("  - topic_contents (with indexes)")
            print("\n🚀 You can now:")
            print("  1. Refresh your browser")
            print("  2. Click on a topic to see the detail page")
            print("  3. Click '+ 添加内容' to upload files")
            return 0
        else:
            print("=" * 60)
            print("❌ Migration failed!")
            print("\nError output:")
            print(result.stderr)
            print("\n💡 Troubleshooting:")
            print("  1. Check if PostgreSQL is running:")
            print("     docker-compose ps postgres")
            print("  2. Check database connection in .env:")
            print("     DATABASE_URL=postgresql://postgres:password@localhost:5432/knowledge_platform")
            return 1
            
    except FileNotFoundError:
        print("❌ Error: 'alembic' command not found")
        print("\n💡 Make sure you're in the virtual environment:")
        print("   source .venv/bin/activate  # or")
        print("   conda activate <env_name>")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

