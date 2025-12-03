#!/bin/bash
# Quick fix for stuck migrations
# This script directly updates the alembic_version table

set -e

echo "=== Quick Migration Fix ==="
echo ""
echo "This script will mark your database as being at the latest migration"
echo "without actually running any migrations."
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL is not set"
    echo ""
    echo "Please run:"
    echo "  export DATABASE_URL='your-database-url'"
    echo "  ./scripts/quick-fix-migration.sh"
    exit 1
fi

echo "Database URL: ${DATABASE_URL:0:50}..."
echo ""

# Latest migration version
LATEST_VERSION="20241202_000003_add_evaluation_log"

echo "Latest migration version: $LATEST_VERSION"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Use psql to run the fix
echo "Updating alembic_version table..."

# Extract connection string components for psql
# Convert asyncpg URL to psql URL
PSQL_URL="${DATABASE_URL//postgresql+asyncpg:\/\//postgresql://}"

# Run SQL commands
if psql "$PSQL_URL" -c "DELETE FROM alembic_version;" && \
   psql "$PSQL_URL" -c "INSERT INTO alembic_version (version_num) VALUES ('$LATEST_VERSION');" && \
   psql "$PSQL_URL" -c "SELECT * FROM alembic_version;"; then
    echo ""
    echo "✅ Migration version updated successfully!"
    echo ""
    echo "You can now restart your application."
else
    echo ""
    echo "❌ Failed to update migration version"
    echo ""
    echo "Manual fix:"
    echo "1. Go to Supabase Dashboard > SQL Editor"
    echo "2. Run these commands:"
    echo ""
    echo "   DELETE FROM alembic_version;"
    echo "   INSERT INTO alembic_version (version_num) VALUES ('$LATEST_VERSION');"
    echo "   SELECT * FROM alembic_version;"
    echo ""
fi

