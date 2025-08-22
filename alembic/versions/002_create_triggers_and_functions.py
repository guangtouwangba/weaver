"""Create triggers and functions

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 10:05:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create function to update updated_at column
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create triggers for updated_at
    op.execute(
        """
        CREATE TRIGGER update_topics_updated_at 
            BEFORE UPDATE ON topics 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_conversations_updated_at 
            BEFORE UPDATE ON conversations 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # Create function to update tag usage count
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_tag_usage_count()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE tags SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE tags SET usage_count = usage_count - 1 WHERE id = OLD.tag_id;
                RETURN OLD;
            END IF;
            RETURN NULL;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create trigger for tag usage count
    op.execute(
        """
        CREATE TRIGGER update_tag_usage_count_trigger
            AFTER INSERT OR DELETE ON topic_tags
            FOR EACH ROW
            EXECUTE FUNCTION update_tag_usage_count();
    """
    )

    # Create function for soft delete
    op.execute(
        """
        CREATE OR REPLACE FUNCTION soft_delete_record()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.is_deleted = TRUE;
            NEW.deleted_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create function to update last_accessed_at
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_last_accessed_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.last_accessed_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create triggers for last_accessed_at
    op.execute(
        """
        CREATE TRIGGER update_topics_last_accessed_at 
            BEFORE UPDATE ON topics 
            FOR EACH ROW 
            EXECUTE FUNCTION update_last_accessed_at();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_topic_resources_last_accessed_at 
            BEFORE UPDATE ON topic_resources 
            FOR EACH ROW 
            EXECUTE FUNCTION update_last_accessed_at();
    """
    )

    # Create function to update conversation message count
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_conversation_message_count()
        RETURNS TRIGGER AS $$
        BEGIN
            -- This function would be used if we had a messages table
            -- For now, it's a placeholder for future use
            RETURN COALESCE(NEW, OLD);
        END;
        $$ language 'plpgsql';
    """
    )

    # Create validation function for resource types
    op.execute(
        """
        CREATE OR REPLACE FUNCTION validate_resource_file_extension()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Validate file extension matches resource type
            CASE NEW.resource_type
                WHEN 'pdf' THEN
                    IF NOT (NEW.file_name ~* '\.pdf$') THEN
                        RAISE EXCEPTION 'File extension does not match resource type PDF';
                    END IF;
                WHEN 'doc' THEN
                    IF NOT (NEW.file_name ~* '\.doc$') THEN
                        RAISE EXCEPTION 'File extension does not match resource type DOC';
                    END IF;
                WHEN 'docx' THEN
                    IF NOT (NEW.file_name ~* '\.docx$') THEN
                        RAISE EXCEPTION 'File extension does not match resource type DOCX';
                    END IF;
                WHEN 'image' THEN
                    IF NOT (NEW.file_name ~* '\.(jpg|jpeg|png|gif|bmp|tiff|webp)$') THEN
                        RAISE EXCEPTION 'File extension does not match resource type IMAGE';
                    END IF;
                WHEN 'text' THEN
                    IF NOT (NEW.file_name ~* '\.(txt|md|csv|json|xml)$') THEN
                        RAISE EXCEPTION 'File extension does not match resource type TEXT';
                    END IF;
                ELSE
                    -- For other types like video, audio, url - no validation for now
                    NULL;
            END CASE;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create trigger for resource validation (optional - can be disabled if too strict)
    # op.execute("""
    #     CREATE TRIGGER validate_topic_resource_file_extension
    #         BEFORE INSERT OR UPDATE ON topic_resources
    #         FOR EACH ROW
    #         EXECUTE FUNCTION validate_resource_file_extension();
    # """)


def downgrade() -> None:
    # Drop triggers first
    op.execute(
        "DROP TRIGGER IF EXISTS update_topic_resources_last_accessed_at ON topic_resources;"
    )
    op.execute("DROP TRIGGER IF EXISTS update_topics_last_accessed_at ON topics;")
    op.execute("DROP TRIGGER IF EXISTS update_tag_usage_count_trigger ON topic_tags;")
    op.execute(
        "DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;"
    )
    op.execute("DROP TRIGGER IF EXISTS update_topics_updated_at ON topics;")
    op.execute(
        "DROP TRIGGER IF EXISTS validate_topic_resource_file_extension ON topic_resources;"
    )

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS validate_resource_file_extension();")
    op.execute("DROP FUNCTION IF EXISTS update_conversation_message_count();")
    op.execute("DROP FUNCTION IF EXISTS update_last_accessed_at();")
    op.execute("DROP FUNCTION IF EXISTS soft_delete_record();")
    op.execute("DROP FUNCTION IF EXISTS update_tag_usage_count();")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
