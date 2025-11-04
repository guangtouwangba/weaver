"""Background tasks for asynchronous document processing."""

import logging
import os
import traceback
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from domain_models import ProcessingStatus, TopicContent
from rag_core.graphs.ingest_graph import run_ingest_graph
from rag_core.pipeline.services.ingest_service import build_ingest_payload

logger = logging.getLogger(__name__)


async def process_uploaded_document(
    content_id: str,
    file_path: str,
    filename: str,
    db_session: Session,
) -> None:
    """
    Background task to process an uploaded document.
    
    Steps:
    1. Read the file from disk
    2. Build ingest payload
    3. Run ingest graph
    4. Update content record with document_id and status
    
    Args:
        content_id: TopicContent UUID
        file_path: Path to the uploaded file
        filename: Original filename
        db_session: Database session (should be created within this function for thread safety)
    """
    logger.info(f"🔄 [BG] Starting document processing for content_id={content_id}")
    logger.info(f"  ├─ File: {filename}")
    logger.info(f"  └─ Path: {file_path}")
    
    try:
        # Step 1: Read file from disk
        logger.info(f"📂 [BG] Reading file from disk...")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_size_mb = len(file_content) / (1024 * 1024)
        logger.info(f"✅ [BG] File read successfully ({file_size_mb:.2f} MB)")
        
        # Step 2: Create UploadFile object for ingest
        logger.info(f"📦 [BG] Building ingest payload (this may take a while for large files)...")
        fake_file = UploadFile(
            filename=filename,
            file=BytesIO(file_content)
        )
        
        payload = await build_ingest_payload(fake_file)
        document_id = payload.document_id
        logger.info(f"✅ [BG] Payload built successfully, document_id: {document_id}")
        
        # Step 3: Run ingest graph
        logger.info(f"💾 [BG] Running ingest graph (vector embeddings, chunking, etc.)...")
        await run_ingest_graph(payload)
        logger.info(f"✅ [BG] Ingest completed successfully")
        
        # Step 4: Update content record (direct DB update)
        logger.info(f"🔄 [BG] Updating content record with document_id...")
        content_uuid = UUID(content_id) if isinstance(content_id, str) else content_id
        content = db_session.query(TopicContent).filter(TopicContent.id == content_uuid).first()
        
        if content:
            content.document_id = document_id
            content.processing_status = ProcessingStatus.COMPLETED.value
            content.processing_error = None
            db_session.commit()
            logger.info(f"✅ [BG] Content updated successfully")
            logger.info(f"🎉 [BG] Document {document_id} is now ready for chat!")
        else:
            logger.error(f"❌ [BG] Content record not found: {content_id}")
            raise ValueError(f"Content record not found: {content_id}")
        
    except Exception as e:
        logger.error(f"❌ [BG] Document processing failed: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        # Update content record with error (direct DB update)
        try:
            content_uuid = UUID(content_id) if isinstance(content_id, str) else content_id
            content = db_session.query(TopicContent).filter(TopicContent.id == content_uuid).first()
            
            if content:
                content.processing_status = ProcessingStatus.FAILED.value
                content.processing_error = str(e)[:1000]  # Limit error message length
                db_session.commit()
                logger.info(f"⚠️ [BG] Content status updated to FAILED")
            else:
                logger.error(f"❌ [BG] Content not found for error update: {content_id}")
        except Exception as update_error:
            logger.error(f"❌ [BG] Failed to update content status: {str(update_error)}")
    
    finally:
        # Optional: Clean up uploaded file after processing
        # Uncomment if you want to delete files after processing
        # try:
        #     if os.path.exists(file_path):
        #         os.remove(file_path)
        #         logger.info(f"🗑️  [BG] Cleaned up file: {file_path}")
        # except Exception as cleanup_error:
        #     logger.error(f"Failed to clean up file: {str(cleanup_error)}")
        pass
    
    logger.info(f"✅ [BG] Background processing completed for content_id={content_id}")


def get_upload_dir() -> Path:
    """Get the upload directory path."""
    upload_dir = Path(__file__).parent.parent.parent.parent / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

