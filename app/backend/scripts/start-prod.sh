#!/bin/bash
set -e

echo "=== Research Agent RAG API Starting ==="

# Run database migrations with smart recovery
echo "Running database migrations..."

# Capture migration output for error detection
MIGRATION_OUTPUT=$(timeout 60 alembic upgrade head 2>&1) || MIGRATION_EXIT=$?

if [ -z "$MIGRATION_EXIT" ]; then
    echo "✅ Migrations completed successfully"
else
    if [ "$MIGRATION_EXIT" -eq 124 ]; then
        echo "⏱️  Migration timed out after 60 seconds"
        echo "   This usually means tables already exist or migration is stuck."
        echo ""
        
        # Strategy 1: Try to stamp the database
        echo "🔧 Attempting recovery: Stamping database..."
        if timeout 10 alembic stamp head 2>&1; then
            echo "✅ Database stamped successfully"
        else
            echo "⚠️  Stamp failed, but continuing startup..."
            echo "   Database may already be at the correct version."
            echo "   To fix manually, update alembic_version table in database"
        fi
    else
        echo "❌ Migration failed with exit code $MIGRATION_EXIT"
        echo "$MIGRATION_OUTPUT" | tail -20  # Show last 20 lines of error
        
        # Check for specific "Can't locate revision" error
        if echo "$MIGRATION_OUTPUT" | grep -q "Can't locate revision"; then
            echo ""
            echo "🔍 Detected 'Can't locate revision' error"
            echo "   This usually means:"
            echo "   1. Migration file not deployed to container, OR"
            echo "   2. Database version points to non-existent migration"
            echo ""
            echo "🔧 Attempting automatic recovery..."
            
            # Use Python script to automatically fix the migration version
            FIX_SCRIPT="$(dirname "$0")/fix-migration-auto.py"
            if [ -f "$FIX_SCRIPT" ]; then
                echo "   Running automatic migration fix script..."
                # Capture both stdout (revision) and stderr (info messages)
                FIX_OUTPUT=$(python3 "$FIX_SCRIPT" 2>&1)
                FIX_EXIT=$?
                
                # Extract revision ID (last line should be the revision)
                FIXED_REVISION=$(echo "$FIX_OUTPUT" | tail -1 | grep -E "^[0-9]+_[0-9]+" || echo "")
                
                if [ $FIX_EXIT -eq 0 ] && [ -n "$FIXED_REVISION" ]; then
                    # Show info messages from script
                    echo "$FIX_OUTPUT" | grep -E "^(INFO|WARN|ERROR)" || true
                    echo "✅ Automatically fixed database version to: $FIXED_REVISION"
                    echo "   Retrying migration..."
                    
                    # Retry migration after fix
                    if timeout 60 alembic upgrade head 2>&1; then
                        echo "✅ Migrations completed successfully after auto-fix"
                    else
                        echo "⚠️  Migration still failed after auto-fix, but continuing startup"
                        echo "   Database version has been set to: $FIXED_REVISION"
                    fi
                else
                    echo "⚠️  Auto-fix script failed, trying fallback method..."
                    # Fallback: try to get last revision from alembic history
                    LAST_REVISION=$(alembic history 2>/dev/null | grep -E "^[0-9]+_[0-9]+" | tail -1 | awk '{print $1}' || echo "")
                    
                    if [ -n "$LAST_REVISION" ]; then
                        echo "   Found last available revision: $LAST_REVISION"
                        echo "   Stamping database to this revision..."
                        if alembic stamp "$LAST_REVISION" 2>&1; then
                            echo "✅ Database stamped to $LAST_REVISION"
                        else
                            echo "⚠️  Could not stamp to $LAST_REVISION"
                        fi
                    else
                        echo "⚠️  Could not determine last valid revision"
                    fi
                fi
            else
                echo "⚠️  Auto-fix script not found: $FIX_SCRIPT"
                echo "   Trying fallback method..."
                LAST_REVISION=$(alembic history 2>/dev/null | grep -E "^[0-9]+_[0-9]+" | tail -1 | awk '{print $1}' || echo "")
                
                if [ -n "$LAST_REVISION" ]; then
                    echo "   Found last available revision: $LAST_REVISION"
                    if alembic stamp "$LAST_REVISION" 2>&1; then
                        echo "✅ Database stamped to $LAST_REVISION"
                    fi
                fi
            fi
        else
            # Other errors - try stamp as fallback
            echo "   Attempting recovery..."
            if alembic stamp head 2>&1; then
                echo "✅ Recovery successful (stamped database)"
            else
                echo "⚠️  Could not recover automatically"
                echo "   Service will start, but migrations may be needed."
                echo "   Manual fix: update alembic_version table in database"
            fi
        fi
    fi
fi

echo ""
# Start the server
echo "Starting Uvicorn server..."
exec uvicorn research_agent.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips='*'
