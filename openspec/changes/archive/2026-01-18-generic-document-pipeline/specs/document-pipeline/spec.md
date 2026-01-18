# document-pipeline Specification Delta

## Purpose
Extensible document processing pipeline using Registry pattern for all processing stages.

## ADDED Requirements

### Requirement: ThumbnailGenerator Interface
The system SHALL provide an abstract `ThumbnailGenerator` interface for extensible thumbnail generation.

#### Scenario: Generator registration
- **WHEN** a thumbnail generator is registered with the ThumbnailRegistry
- **THEN** it SHALL be discoverable by MIME type or file extension
- **AND** the registry SHALL return the appropriate generator for each format

#### Scenario: PDF thumbnail generation
- **WHEN** a PDF document is processed
- **THEN** the PDFThumbnailGenerator SHALL extract the first page
- **AND** render it as a 300px-wide WebP image
- **AND** save it to the thumbnails directory

#### Scenario: Text file thumbnail generation
- **WHEN** a text file (.txt, .md) is processed
- **THEN** the TextThumbnailGenerator SHALL read the first N lines
- **AND** render them as a preview image using Pillow
- **AND** save it to the thumbnails directory

#### Scenario: Unsupported format handling
- **WHEN** `ThumbnailFactory.is_supported()` returns False for a file type
- **THEN** thumbnail generation SHALL be skipped
- **AND** no error SHALL be raised
- **AND** the document status SHALL still be set to READY

### Requirement: ThumbnailFactory Public Interface
The system SHALL provide a `ThumbnailFactory` as the public interface for thumbnail generation.

#### Scenario: Check format support
- **WHEN** `ThumbnailFactory.is_supported(mime_type, extension)` is called
- **THEN** it SHALL return True if any registered generator supports the format
- **AND** return False otherwise

#### Scenario: Generate thumbnail
- **WHEN** `ThumbnailFactory.generate(file_path, document_id, output_dir, mime_type, extension)` is called
- **THEN** it SHALL select the appropriate generator from the registry
- **AND** delegate to the generator's `generate()` method
- **AND** return a `ThumbnailResult` with success status and path

### Requirement: Document Processing Pipeline Integration
The document processing endpoints SHALL use ThumbnailFactory for thumbnail decisions.

#### Scenario: confirm_upload uses ThumbnailFactory
- **WHEN** `confirm_upload` endpoint is called
- **THEN** it SHALL use `ThumbnailFactory.is_supported()` to check if thumbnail can be generated
- **AND** only attempt thumbnail generation for supported formats

#### Scenario: DocumentProcessorTask uses ThumbnailFactory
- **WHEN** `DocumentProcessorTask` Step 6 runs
- **THEN** it SHALL use `ThumbnailFactory.is_supported()` to check format support
- **AND** only queue thumbnail generation for supported formats

### Requirement: MIME Type Dynamic Detection
The `confirm_upload` endpoint SHALL use the request content_type instead of hardcoded values.

#### Scenario: Dynamic MIME type storage
- **WHEN** `confirm_upload` is called with `content_type="text/plain"`
- **THEN** the document model SHALL be created with `mime_type="text/plain"`
- **AND NOT** hardcoded to `"application/pdf"`
