#!/bin/bash
# Fix Alembic state when migrations are stuck
# This script helps when tables exist but Alembic version table is missing or outdated

set -e

echo "=== Fixing Alembic Migration State ==="
echo ""

# Change to backend directory (where alembic.ini is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Changing to backend directory: $BACKEND_DIR"
cd "$BACKEND_DIR"
echo ""

# Check if alembic.ini exists
if [ ! -f "alembic.ini" ]; then
    echo "❌ ERROR: alembic.ini not found in $BACKEND_DIR"
    echo "   Please run this script from the app/backend directory"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set"
    echo "   Please set DATABASE_URL environment variable"
    echo ""
    echo "Example:"
    echo "  export DATABASE_URL='postgresql://...'"
    echo "  ./scripts/fix-alembic-state.sh"
    exit 1
fi

echo "Database URL: ${DATABASE_URL:0:50}..."
echo ""

# Option 1: Show current state
echo "1. Checking current migration state..."
if alembic current 2>&1; then
    echo ""
else
    echo "   No current version found or error checking version"
    echo ""
fi

# Option 2: Show migration history
echo "2. Available migrations:"
alembic history | head -20 || echo "   Could not retrieve migration history"
echo ""

# Option 3: Try to stamp database with latest revision
echo "3. Attempting to stamp database with latest revision..."
echo "   This will mark the database as being at the latest migration"
echo "   without running any migrations."
echo ""

read -p "Do you want to stamp the database? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running: alembic stamp head"
    if alembic stamp head; then
        echo "✅ Database stamped successfully"
        echo ""
        echo "Current state:"
        alembic current
    else
        echo "❌ Failed to stamp database"
        echo "   You may need to manually fix the alembic_version table"
        echo ""
        echo "Manual fix SQL:"
        echo "  DELETE FROM alembic_version;"
        echo "  INSERT INTO alembic_version (version_num) VALUES ('20241202_000003_add_evaluation_log');"
    fi
else
    echo "Skipped stamping"
fi

echo ""
echo "=== Next Steps ==="
echo "1. If stamping succeeded, restart your application"
echo "2. If stamping failed, you may need to manually run SQL:"
echo "   - Connect to your database (Supabase SQL Editor or psql)"
echo "   - Run the fix SQL from scripts/fix-alembic-version.sql"
echo "3. Or manually insert version:"
echo "   DELETE FROM alembic_version;"
echo "   INSERT INTO alembic_version (version_num) VALUES ('20241202_000003_add_evaluation_log');"

