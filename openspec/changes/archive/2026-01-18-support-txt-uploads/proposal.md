# Support .txt File Uploads

## Goal
Enable users to upload plain text (`.txt`) files as sources for research and mindmap generation, ensuring feature parity with PDF and Video sources.

## Context
Currently, the system supports PDF, DOCX, CSV, and Images. Users need to analyze plain text notes or logs. Adding `.txt` support requires updating the frontend file picker and the backend processing pipeline to handle text files natively.

## Proposed Changes

### Frontend
- **Update `ImportSourceDialog`**: Add `.txt` to the list of accepted file types.

### Backend
- **Update `documents.py`**:
    - Relax validation in `upload_document` to allow `.txt` extension.
    - Ensure `PresignRequest` allows `text/plain` content type.
- **Implement `TextParser`**:
    - Create a new `TextParser` class in `infrastructure/parser/text_parser.py` that simply reads the text content.
    - Register `TextParser` in `ParserFactory` for `.txt` extension and `text/plain` MIME type.

## Verification Plan
1.  **Manual Test**: Upload a `.txt` file via the UI.
2.  **Verify Processing**: Check that the file status moves to `READY` and text is correctly extracted (visible in "chunks" debug view).
3.  **Verify Output**: Generate a mindmap from the uploaded text file.
