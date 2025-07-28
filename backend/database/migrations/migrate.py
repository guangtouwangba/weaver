#!/usr/bin/env python3
"""
Database migration tool for Research Agent RAG system
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.database import get_database

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Handles database migrations"""
    
    def __init__(self):
        self.db_manager = get_database()
        self.migrations_dir = Path(__file__).parent
        
    def get_migration_files(self) -> List[Path]:
        """Get all migration files in order"""
        migration_files = []
        for file_path in self.migrations_dir.glob("*.sql"):
            if file_path.name.startswith("00") and file_path.name.endswith(".sql"):
                migration_files.append(file_path)
        
        # Sort by filename to ensure proper order
        migration_files.sort(key=lambda x: x.name)
        return migration_files
    
    def create_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        try:
            with self.db_manager.get_session() as session:
                session.execute(create_table_sql)
                session.commit()
            logger.info("Migration tracking table created/verified")
        except Exception as e:
            logger.error(f"Error creating migration table: {e}")
            raise
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            with self.db_manager.get_session() as session:
                result = session.execute("SELECT migration_name FROM schema_migrations ORDER BY applied_at")
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration file"""
        migration_name = migration_file.stem
        
        try:
            # Read migration file
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Apply migration
            with self.db_manager.get_session() as session:
                # Execute migration SQL
                session.execute(migration_sql)
                
                # Record migration as applied
                session.execute(
                    "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
                    (migration_name,)
                )
                
                session.commit()
            
            logger.info(f"✅ Applied migration: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply migration {migration_name}: {e}")
            return False
    
    def run_migrations(self) -> Dict[str, Any]:
        """Run all pending migrations"""
        logger.info("🚀 Starting database migrations...")
        
        try:
            # Create migration table
            self.create_migration_table()
            
            # Get migration files and applied migrations
            migration_files = self.get_migration_files()
            applied_migrations = set(self.get_applied_migrations())
            
            # Find pending migrations
            pending_migrations = []
            for migration_file in migration_files:
                migration_name = migration_file.stem
                if migration_name not in applied_migrations:
                    pending_migrations.append(migration_file)
            
            if not pending_migrations:
                logger.info("✅ No pending migrations found")
                return {
                    'status': 'success',
                    'applied_count': 0,
                    'total_migrations': len(migration_files),
                    'pending_migrations': []
                }
            
            logger.info(f"Found {len(pending_migrations)} pending migrations")
            
            # Apply pending migrations
            successful_migrations = []
            failed_migrations = []
            
            for migration_file in pending_migrations:
                if self.apply_migration(migration_file):
                    successful_migrations.append(migration_file.stem)
                else:
                    failed_migrations.append(migration_file.stem)
                    break  # Stop on first failure
            
            # Summary
            result = {
                'status': 'success' if not failed_migrations else 'partial',
                'applied_count': len(successful_migrations),
                'total_migrations': len(migration_files),
                'successful_migrations': successful_migrations,
                'failed_migrations': failed_migrations
            }
            
            if successful_migrations:
                logger.info(f"✅ Successfully applied {len(successful_migrations)} migrations")
            
            if failed_migrations:
                logger.error(f"❌ Failed to apply {len(failed_migrations)} migrations")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Migration process failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'applied_count': 0
            }
    
    def rollback_migration(self, migration_name: str) -> bool:
        """Rollback a specific migration (if rollback SQL exists)"""
        rollback_file = self.migrations_dir / f"{migration_name}_rollback.sql"
        
        if not rollback_file.exists():
            logger.error(f"No rollback file found for migration: {migration_name}")
            return False
        
        try:
            # Read rollback file
            with open(rollback_file, 'r', encoding='utf-8') as f:
                rollback_sql = f.read()
            
            # Apply rollback
            with self.db_manager.get_session() as session:
                # Execute rollback SQL
                session.execute(rollback_sql)
                
                # Remove migration record
                session.execute(
                    "DELETE FROM schema_migrations WHERE migration_name = %s",
                    (migration_name,)
                )
                
                session.commit()
            
            logger.info(f"✅ Rolled back migration: {migration_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to rollback migration {migration_name}: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            migration_files = self.get_migration_files()
            applied_migrations = set(self.get_applied_migrations())
            
            migrations_status = []
            for migration_file in migration_files:
                migration_name = migration_file.stem
                migrations_status.append({
                    'name': migration_name,
                    'file_path': str(migration_file),
                    'applied': migration_name in applied_migrations
                })
            
            pending_count = len([m for m in migrations_status if not m['applied']])
            
            return {
                'total_migrations': len(migration_files),
                'applied_migrations': len(applied_migrations),
                'pending_migrations': pending_count,
                'migrations': migrations_status
            }
            
        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {'error': str(e)}

def main():
    """Main migration runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Migration Tool')
    parser.add_argument('action', choices=['migrate', 'status', 'rollback'], 
                       help='Action to perform')
    parser.add_argument('--migration', help='Migration name for rollback')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        runner = MigrationRunner()
        
        if args.action == 'migrate':
            result = runner.run_migrations()
            print(f"\nMigration Result: {result}")
            
        elif args.action == 'status':
            status = runner.get_migration_status()
            print(f"\nMigration Status: {status}")
            
        elif args.action == 'rollback':
            if not args.migration:
                print("Error: --migration parameter required for rollback")
                sys.exit(1)
            
            success = runner.rollback_migration(args.migration)
            print(f"Rollback {'successful' if success else 'failed'}")
            
    except Exception as e:
        logger.error(f"Migration tool failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()