#!/usr/bin/env python3
"""
Migration script to move data from SQLite to Supabase
Helps users transition from local SQLite database to cloud Supabase database
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database.database_adapter import DatabaseManager, SQLiteAdapter, SupabaseAdapter
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable substitution"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Substitute environment variables in the format ${VAR_NAME}
            import re
            def replace_env_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            
            content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
            
            return yaml.safe_load(content)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)

def validate_supabase_credentials():
    """Validate that Supabase credentials are available"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found!")
        logger.error("Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
        logger.error("Example:")
        logger.error("  SUPABASE_URL=https://your-project.supabase.co")
        logger.error("  SUPABASE_ANON_KEY=your_anon_key_here")
        return False
    
    return True

def create_supabase_table_sql():
    """Return SQL to create papers table in Supabase"""
    return """
-- Create papers table in Supabase
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    arxiv_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    abstract TEXT,
    categories TEXT NOT NULL,
    published TIMESTAMP WITH TIME ZONE NOT NULL,
    pdf_url TEXT,
    pdf_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX IF NOT EXISTS idx_papers_published ON papers(published);
CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers(categories);

-- Enable Row Level Security
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access (adjust as needed)
CREATE POLICY IF NOT EXISTS "Public read access" ON papers
    FOR SELECT TO anon, authenticated
    USING (true);

-- Create policy for authenticated write access
CREATE POLICY IF NOT EXISTS "Authenticated write access" ON papers
    FOR ALL TO authenticated
    USING (true);
"""

def migrate_data(config: Dict[str, Any], sqlite_path: str = None):
    """Migrate data from SQLite to Supabase"""
    try:
        # Determine SQLite database path
        if not sqlite_path:
            db_config = config.get('database', {})
            db_url = db_config.get('url', 'sqlite:///papers.db')
            if db_url.startswith('sqlite:///'):
                sqlite_path = db_url.replace('sqlite:///', '')
            else:
                sqlite_path = 'papers.db'
        
        # Check if SQLite database exists
        if not os.path.exists(sqlite_path):
            logger.error(f"SQLite database not found: {sqlite_path}")
            return False
        
        logger.info(f"Migrating data from SQLite database: {sqlite_path}")
        
        # Create SQLite adapter
        sqlite_adapter = SQLiteAdapter(sqlite_path)
        
        # Get paper count from SQLite
        sqlite_count = sqlite_adapter.get_paper_count()
        logger.info(f"Found {sqlite_count} papers in SQLite database")
        
        if sqlite_count == 0:
            logger.warning("No papers found in SQLite database. Nothing to migrate.")
            return True
        
        # Create Supabase adapter
        supabase_adapter = SupabaseAdapter()
        
        # Perform migration
        logger.info("Starting migration to Supabase...")
        migration_result = supabase_adapter.migrate_from_sqlite(sqlite_path)
        
        # Display results
        logger.info("Migration completed!")
        logger.info(f"Total papers in source: {migration_result['total_papers']}")
        logger.info(f"Successfully migrated: {migration_result['migrated_papers']}")
        logger.info(f"Skipped papers: {migration_result['skipped_papers']}")
        
        if migration_result['errors']:
            logger.warning(f"Encountered {len(migration_result['errors'])} errors:")
            for error in migration_result['errors'][:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
            if len(migration_result['errors']) > 5:
                logger.warning(f"  ... and {len(migration_result['errors']) - 5} more errors")
        
        # Verify migration
        supabase_count = supabase_adapter.get_paper_count()
        logger.info(f"Verification: Supabase now has {supabase_count} papers")
        
        success_rate = migration_result['migrated_papers'] / migration_result['total_papers'] * 100
        logger.info(f"Migration success rate: {success_rate:.1f}%")
        
        return success_rate > 90  # Consider successful if >90% migrated
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def update_config_for_supabase(config_path: str = "config.yaml"):
    """Update config.yaml to use Supabase by default"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update database provider to supabase
        content = content.replace(
            'provider: "sqlite"  # Change to "supabase" for cloud database',
            'provider: "supabase"  # Change to "sqlite" for local database'
        )
        
        # Uncomment Supabase configuration lines
        content = content.replace(
            '  # supabase_url: "${SUPABASE_URL}"        # Set in .env file\n  # supabase_key: "${SUPABASE_ANON_KEY}"   # Set in .env file',
            '  supabase_url: "${SUPABASE_URL}"        # Set in .env file\n  supabase_key: "${SUPABASE_ANON_KEY}"   # Set in .env file'
        )
        
        # Create backup
        backup_path = f"{config_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(config_path, 'r', encoding='utf-8') as original:
                f.write(original.read())
        
        # Write updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Updated {config_path} to use Supabase")
        logger.info(f"Backup saved as {backup_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return False

def main():
    """Main migration process"""
    print("🚀 ArXiv Paper Fetcher - SQLite to Supabase Migration")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Validate Supabase credentials
    if not validate_supabase_credentials():
        sys.exit(1)
    
    # Load configuration
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    config = load_config(config_path)
    
    # Display Supabase table creation SQL
    print("\n📋 First, create the papers table in your Supabase project:")
    print("   1. Go to your Supabase dashboard")
    print("   2. Open the SQL Editor")
    print("   3. Run the following SQL:")
    print("\n" + "─" * 60)
    print(create_supabase_table_sql())
    print("─" * 60)
    
    # Confirm table creation
    response = input("\n✅ Have you created the papers table in Supabase? (y/N): ")
    if response.lower() != 'y':
        print("Please create the table first, then run this script again.")
        sys.exit(0)
    
    # Determine SQLite path
    sqlite_path = None
    if len(sys.argv) > 2:
        sqlite_path = sys.argv[2]
    
    # Perform migration
    print("\n📊 Starting data migration...")
    success = migrate_data(config, sqlite_path)
    
    if success:
        print("\n✅ Migration completed successfully!")
        
        # Ask if user wants to update config
        response = input("\n🔧 Update config.yaml to use Supabase by default? (y/N): ")
        if response.lower() == 'y':
            if update_config_for_supabase(config_path):
                print("✅ Configuration updated!")
                print("\n🎉 Migration complete! Your system is now using Supabase.")
                print("\n💡 Next steps:")
                print("   1. Test the paper fetcher: python simple_paper_fetcher.py")
                print("   2. Test the RAG system: python rag_main.py")
            else:
                print("❌ Failed to update configuration. Please update manually.")
        else:
            print("\n💡 To use Supabase, manually update your config.yaml:")
            print('   - Change database.provider to "supabase"')
            print("   - Uncomment the supabase_url and supabase_key lines")
    else:
        print("\n❌ Migration failed or incomplete. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()