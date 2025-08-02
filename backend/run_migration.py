#!/usr/bin/env python3
"""
Database migration script
"""
import os
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.database import init_database, get_database
from core.dependencies import get_db_session
from database.models import Base
from config import Config
from sqlalchemy import text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Run all database migrations"""
    try:
        db_session = get_db_session()
        
        logger.info("Starting database migrations...")
        
        # Create all tables
        Base.metadata.create_all(bind=db_session.bind)
        logger.info("✓ All tables created successfully")
        
        # Run custom SQL migrations
        run_sql_migrations(db_session)
        
        logger.info("✓ All migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        db_session.close()

def run_sql_migrations(db_session):
    """Run SQL-based migrations"""
    migrations_dir = backend_dir / "database" / "migrations"
    
    # Get all SQL migration files
    sql_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    for sql_file in sql_files:
        logger.info(f"Running migration: {sql_file.name}")
        
        try:
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    db_session.execute(text(statement))
            
            db_session.commit()
            logger.info(f"✓ Migration {sql_file.name} completed")
            
        except Exception as e:
            logger.error(f"Migration {sql_file.name} failed: {e}")
            db_session.rollback()
            raise

if __name__ == "__main__":
    run_migrations() 