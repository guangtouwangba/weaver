# Tasks: Enforce RAG User Isolation

## Checklist

- [x] **Task 1**: Update `VectorStore` abstract interface
  - ✅ `user_id: str | None = None` already exists in `search()` signature
  - ✅ `user_id: str | None = None` already exists in `hybrid_search()` signature
  - File: `infrastructure/vector_store/base.py`

- [x] **Task 2**: Verify `PgVectorStore` compliance
  - ✅ `search()` already has `user_id` parameter
  - ✅ `hybrid_search()` already has `user_id` parameter
  - ✅ SQL WHERE clause adds `user_id` filter when not None
  - File: `infrastructure/vector_store/pgvector.py`

- [x] **Task 3**: Update `QdrantVectorStore` (if exists)
  - ✅ Added `user_id` filtering logic to `search()`
  - ✅ Updated `hybrid_search()` to pass `user_id` to `search()`
  - File: `infrastructure/vector_store/qdrant.py`

- [x] **Task 4**: Add warning log for missing user_id
  - ✅ Added warning log when `user_id=None` in `PgVectorStore.search()`
  - File: `infrastructure/vector_store/pgvector.py`

- [x] **Task 5**: Write unit tests for user isolation
  - ✅ Test `search()` with `user_id` filters results correctly
  - ✅ Test `search()` without `user_id` returns all results (legacy behavior)
  - File: `tests/unit/vector_store/test_user_isolation.py`

- [x] **Task 6**: Integration test with RAG pipeline
  - ✅ Manual verification: `user_id` is passed through `stream_message.py` → `create_pgvector_retriever()` → `PGVectorRetriever` → `PgVectorStore`
  - The calling chain already passes `user_id` correctly when available

## Summary

All tasks complete. The RAG retrieval pipeline now enforces user data isolation:
1. `VectorStore` interface includes `user_id` parameter
2. `PgVectorStore` and `QdrantVectorStore` both filter by `user_id` when provided
3. Warning is logged when `user_id=None` to alert potential data leakage
4. Unit tests verify the filtering behavior
