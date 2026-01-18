# Design: Text File Support

## Architecture
We will introduce a `TextParser` that implements the `DocumentParser` interface. It will handle `text/plain` MIME types and `.txt` extensions.

## Components

### TextParser
- **Location**: `infrastructure/parser/text_parser.py`
- **Responsibility**: Read file content as UTF-8 string. Return `ParseResult` with a single page containing the full text.
- **Handling**:
    - `page_count`: 1 (Text files don't have inherent pages, treat as one continuous flow or split by length if needed? For now, 1 page is fine as chunker handles splitting).
    - `metadata`: Basic file info.

### Integration
- **Factory**: Registered in `ParserFactory`.
- **API**: `upload_document` and `presign` endpoints updated to allow `.txt`.

## Trade-offs
- **Pagination**: Text files lack pages. We initially map everything to Page 1. The chunking service will slice it up anyway. This matches the behavior for other non-paginated sources like text dumps.
