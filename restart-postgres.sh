#!/bin/bash
set -e

echo "🧹 清理旧容器和数据..."
docker stop knowledge-platform-db 2>/dev/null || true
docker rm knowledge-platform-db 2>/dev/null || true
docker volume rm research-agent-rag_postgres_data 2>/dev/null || true

echo "🚀 启动PostgreSQL容器..."
cd /Users/siqiuchen/Documents/opensource/research-agent-rag
docker-compose up -d postgres

echo "⏳ 等待PostgreSQL准备好（30秒）..."
for i in {1..30}; do
    if docker exec knowledge-platform-db pg_isready -U postgres >/dev/null 2>&1; then
        echo "✅ PostgreSQL已准备好！"
        break
    fi
    echo "   等待中... $i/30"
    sleep 1
done

echo ""
echo "📊 检查容器状态:"
docker ps | grep postgres

echo ""
echo "📝 最后几行日志:"
docker logs knowledge-platform-db --tail 5

echo ""
echo "✨ 现在可以运行迁移了:"
echo "   alembic upgrade head"

