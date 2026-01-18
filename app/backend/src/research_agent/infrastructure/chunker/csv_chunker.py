"""CSV file chunker.

Chunks CSV files by rows for better semantic coherence when
querying tabular data.
"""

import csv
import io
from typing import Any

from research_agent.infrastructure.chunker.base import (
    Chunker,
    ChunkResult,
    PageLike,
)
from research_agent.shared.utils.logger import logger


class CSVChunker(Chunker):
    """
    Chunker for CSV files.

    Chunks CSV data by rows, preserving headers with each chunk
    for better context.
    """

    ROWS_PER_CHUNK = 20  # Number of rows per chunk

    def supported_mime_types(self) -> list[str]:
        return ["text/csv", "application/csv"]

    def supported_extensions(self) -> list[str]:
        return [".csv"]

    def chunk_pages(
        self,
        pages: list[PageLike],
    ) -> ChunkResult:
        """Chunk CSV pages by combining content and processing rows."""
        full_text = "\n".join([page.content for page in pages])
        return self.chunk_text(full_text, {"source": "pages"})

    def chunk_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChunkResult:
        """
        Chunk CSV text by rows.

        Each chunk contains the header row plus a batch of data rows
        for context preservation.
        """
        if not text.strip():
            return ChunkResult(
                chunks=[],
                chunker_name=self.chunker_name,
                strategy_used="csv_rows",
            )

        base_metadata = metadata or {}
        chunks = []
        chunk_index = 0

        try:
            # Parse CSV
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)

            if len(rows) == 0:
                return ChunkResult(
                    chunks=[],
                    chunker_name=self.chunker_name,
                    strategy_used="csv_rows",
                )

            # First row is header
            header = rows[0]
            header_text = ",".join(header)
            data_rows = rows[1:]

            # Chunk by ROWS_PER_CHUNK rows
            for i in range(0, len(data_rows), self.ROWS_PER_CHUNK):
                batch = data_rows[i : i + self.ROWS_PER_CHUNK]

                # Format as CSV with header
                chunk_lines = [header_text]
                for row in batch:
                    chunk_lines.append(",".join(row))

                chunk_content = "\n".join(chunk_lines)

                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk_content,
                        "page_number": 1,
                        "metadata": {
                            **base_metadata,
                            "chunk_type": "csv_rows",
                            "row_start": i + 1,  # 1-indexed, after header
                            "row_end": min(i + self.ROWS_PER_CHUNK, len(data_rows)),
                            "total_rows": len(data_rows),
                            "columns": header,
                        },
                    }
                )
                chunk_index += 1

            logger.info(f"[CSVChunker] Created {len(chunks)} chunks from " f"{len(data_rows)} rows")

        except csv.Error as e:
            # Fallback to simple text chunking if CSV parsing fails
            logger.warning(f"[CSVChunker] CSV parsing failed, using text fallback: {e}")
            chunks.append(
                {
                    "chunk_index": 0,
                    "content": text,
                    "page_number": 1,
                    "metadata": {**base_metadata, "chunk_type": "csv_fallback"},
                }
            )

        return ChunkResult(
            chunks=chunks,
            chunker_name=self.chunker_name,
            strategy_used="csv_rows",
        )
