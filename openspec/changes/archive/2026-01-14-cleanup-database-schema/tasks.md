# Tasks: Cleanup Database Schema

## 1. 删除所有旧 Migrations
- [x] 1.1 删除 `alembic/versions/` 下的所有 36 个 migration 文件
- [x] 1.2 保留 `__pycache__` 目录结构 (可选)

## 2. 创建新的 Initial Schema Migration
- [x] 2.1 创建 `20260114_000001_initial_schema.py`
- [x] 2.2 包含所有保留表的 CREATE TABLE 语句
- [x] 2.3 包含所有必要的索引和约束
- [x] 2.4 包含 pgvector extension 创建

## 3. 代码清理
- [x] 3.1 从 `models.py` 删除 `DocumentChunkModel`
- [x] 3.2 从 `models.py` 删除 `EntityModel`
- [x] 3.3 从 `models.py` 删除 `RelationModel`
- [x] 3.4 更新 `DocumentModel` 移除 `chunks` relationship

## 4. 依赖代码更新
- [x] 4.1 更新 `document_selector.py` - 改用 ResourceChunkModel
- [x] 4.2 更新 `document_processor.py` - 改用 ResourceChunkModel
- [x] 4.3 移除或重构 `graph_extractor.py`
- [x] 4.4 移除或重构 `canvas_syncer.py`

## 5. 验证
- [x] 5.1 清理本地数据库 (DROP ALL + 重建)
- [x] 5.2 运行 `alembic upgrade head` 验证 schema 创建
- [x] 5.3 运行 pytest 确保无测试失败
- [x] 5.4 启动应用确认正常工作

## 6. 生产环境部署 (Supabase)
- [x] 6.1 备份现有数据库 (如果需要)
- [x] 6.2 在 Supabase SQL Editor 执行清理脚本 (`proposal.md` 中的 SQL)
- [x] 6.3 部署新版本，触发 `alembic upgrade head`
- [x] 6.4 验证应用正常运行

## Dependencies
- 1.x 无前置依赖
- 2.x 依赖 1.x
- 3.x 可与 2.x 并行
- 4.x 依赖 3.x
- 5.x 依赖所有其他任务完成
