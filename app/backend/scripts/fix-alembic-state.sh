#!/bin/bash
# Fix Alembic state when migrations are stuck
# This script helps when tables exist but Alembic version table is missing or outdated

set -e

echo "=== Fixing Alembic Migration State ==="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set"
    echo "   Please set DATABASE_URL environment variable"
    exit 1
fi

echo "Database URL: ${DATABASE_URL:0:50}..."
echo ""

# Option 1: Show current state
echo "1. Checking current migration state..."
alembic current 2>&1 || echo "   No current version found"
echo ""

# Option 2: Show migration history
echo "2. Available migrations:"
alembic history | head -20
echo ""

# Option 3: Try to stamp database with latest revision
echo "3. Attempting to stamp database with latest revision..."
echo "   This will mark the database as being at the latest migration"
echo "   without running any migrations."
echo ""

read -p "Do you want to stamp the database? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if alembic stamp head; then
        echo "✅ Database stamped successfully"
        echo ""
        echo "Current state:"
        alembic current
    else
        echo "❌ Failed to stamp database"
        echo "   You may need to manually fix the alembic_version table"
    fi
else
    echo "Skipped stamping"
fi

echo ""
echo "=== Next Steps ==="
echo "1. If stamping succeeded, restart your application"
echo "2. If stamping failed, you may need to manually check the database:"
echo "   - Check if tables exist: \\dt in psql"
echo "   - Check alembic_version table: SELECT * FROM alembic_version;"
echo "   - Manually insert version if needed:"
echo "     INSERT INTO alembic_version VALUES ('20241202_000003_add_evaluation_log');"

