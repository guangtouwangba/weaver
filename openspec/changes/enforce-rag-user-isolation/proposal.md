# Proposal: Enforce RAG User Isolation

## Why

RAG 检索过程中存在数据隔离漏洞。虽然 `PgVectorStore` 的 `search()` 和 `hybrid_search()` 方法支持 `user_id` 参数，但此参数在 `VectorStore` 抽象接口中未定义，且 `user_id=None` 时不会添加过滤条件，导致可能检索到其他用户的文档。

**问题根源：**
1. `VectorStore` 接口签名缺少 `user_id` 参数
2. 调用链中 `user_id` 是可选的，可能为 `None`
3. 当 `user_id=None` 时，SQL 查询不添加用户过滤条件

## What Changes

### Spec Modifications

#### vector-store
- **MODIFIED** `search()` 和 `hybrid_search()` 方法签名，添加 `user_id: str | None` 参数
- **ADDED** 用户隔离过滤的 Scenario

### Code Impact
- `VectorStore` 抽象接口 (`base.py`)
- `PgVectorStore` 实现 (已有 `user_id` 支持，无需修改)
- `QdrantVectorStore` 实现（如存在）
- `PGVectorRetriever` LangChain wrapper
- `RAGTools.vector_retrieve()` 工具方法

## Out of Scope
- 前端 `user_id` 传递（已在 auth spec 中定义）
- ORM 模型 `user_id` 字段（已存在）
- Repository 层 `user_id` 支持（已在 repositories spec 中定义）
- 数据回填 migration（属于 ops/migration 范畴）

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| 现有数据缺少 `user_id` | 不影响新数据；建议后续单独创建回填 migration |
| 破坏 API 签名 | 参数保持 Optional，向后兼容 |
