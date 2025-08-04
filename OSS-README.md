# 阿里云 OSS 集成指南

## 🎯 概述

本项目现已支持阿里云对象存储服务（OSS），可以将下载的 PDF 文件存储到云端，而不是本地文件系统。

### 主要优势：
- ✅ **云端存储**：PDF 文件存储在阿里云 OSS，不占用本地空间
- ✅ **高可用性**：99.995% 的数据持久性
- ✅ **全球访问**：通过 CDN 加速全球访问
- ✅ **成本优化**：按需付费，支持多种存储类型
- ✅ **安全性**：支持服务端加密和访问控制

## 🏗️ 架构变化

### 存储后端支持：
- **本地存储** (`local`): 传统的本地文件系统存储
- **OSS存储** (`oss`): 阿里云对象存储服务

### 数据库变化：
- `pdf_path` 字段现在存储 OSS 对象键（而非本地路径）
- 示例：`papers/2025-08-04/2024.12345v1.pdf`

## ⚙️ 配置说明

### 1. YAML 配置结构

```yaml
# PDF storage settings
pdf_storage:
  # 存储后端选择: "local" 或 "oss"
  backend: "oss"
  
  # 本地存储设置 (当 backend = "local" 时使用)
  local:
    base_directory: "./downloaded_papers"
    create_subdirectories: true
    filename_format: "{arxiv_id}.pdf"
  
  # OSS 存储设置 (当 backend = "oss" 时使用)
  oss:
    # OSS 连接设置
    endpoint: "https://oss-cn-hangzhou.aliyuncs.com"
    access_key_id: "${OSS_ACCESS_KEY_ID}"
    access_key_secret: "${OSS_ACCESS_KEY_SECRET}"
    bucket_name: "your-papers-bucket"
    
    # OSS 存储设置
    base_prefix: "papers"
    create_subdirectories: true
    filename_format: "{arxiv_id}.pdf"
    
    # OSS 高级设置
    multipart_threshold: 100  # MB
    max_concurrency: 3
    server_side_encryption: false
    storage_class: "Standard"
```

### 2. 环境变量配置

创建 `.env` 文件（基于 `.env.example`）：

```bash
# 阿里云 OSS 凭证
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret

# 可选：时区设置
TZ=Asia/Shanghai
```

## 🚀 快速开始

### 1. 创建 OSS Bucket

1. 登录[阿里云控制台](https://oss.console.aliyun.com/)
2. 创建新的 Bucket
   - **名称**: `your-papers-bucket`（替换为你的 bucket 名）
   - **地域**: 选择就近地域
   - **权限**: 私有（推荐）
   - **版本控制**: 根据需求选择

### 2. 获取访问凭证

1. 访问[RAM 控制台](https://ram.console.aliyun.com/)
2. 创建 RAM 用户
3. 为用户添加 OSS 权限：
   ```json
   {
     "Version": "1",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "oss:PutObject",
           "oss:GetObject",
           "oss:DeleteObject",
           "oss:GetBucketInfo"
         ],
         "Resource": [
           "acs:oss:*:*:your-papers-bucket",
           "acs:oss:*:*:your-papers-bucket/*"
         ]
       }
     ]
   }
   ```
4. 获取 AccessKey ID 和 AccessKey Secret

### 3. 配置项目

1. **修改配置文件**：
   ```yaml
   pdf_storage:
     backend: "oss"
     oss:
       endpoint: "https://oss-cn-hangzhou.aliyuncs.com"  # 替换为你的 endpoint
       bucket_name: "your-papers-bucket"  # 替换为你的 bucket
   ```

2. **设置环境变量**：
   ```bash
   export OSS_ACCESS_KEY_ID="your_access_key_id"
   export OSS_ACCESS_KEY_SECRET="your_access_key_secret"
   ```

3. **安装 OSS SDK**：
   ```bash
   pip install -r requirements-simple.txt
   ```

### 4. 运行系统

```bash
# 单次运行
python simple_paper_fetcher.py

# 或者启动调度器
python scheduler.py
```

## 🐳 Docker 部署

### 1. 使用 Docker Compose

```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. 编辑 .env 文件，设置 OSS 凭证
# OSS_ACCESS_KEY_ID=your_access_key_id
# OSS_ACCESS_KEY_SECRET=your_access_key_secret

# 3. 启动服务
docker-compose up -d
```

### 2. 直接使用 Docker

```bash
docker run -d \
  --name arxiv-fetcher \
  -e OSS_ACCESS_KEY_ID=your_access_key_id \
  -e OSS_ACCESS_KEY_SECRET=your_access_key_secret \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/papers.db:/app/papers.db \
  arxiv-paper-fetcher
```

## 📁 文件组织结构

### OSS 中的文件结构：
```
your-papers-bucket/
├── papers/                    # 基础前缀
│   ├── 2025-08-04/           # 按日期分组
│   │   ├── 2508.00123.pdf
│   │   ├── 2508.00124.pdf
│   │   └── ...
│   ├── 2025-08-05/
│   │   └── ...
│   └── ...
```

### 数据库中的记录：
```sql
INSERT INTO papers (
  arxiv_id, 
  pdf_path, 
  ...
) VALUES (
  '2508.00123v1',
  'papers/2025-08-04/2508.00123.pdf',  -- OSS 对象键
  ...
);
```

## 🔧 高级配置

### 1. 存储类型优化

```yaml
oss:
  storage_class: "IA"  # 低频访问，适合归档
  # 选项: Standard, IA, Archive, ColdArchive
```

### 2. 服务端加密

```yaml
oss:
  server_side_encryption: true
```

### 3. 多部分上传优化

```yaml
oss:
  multipart_threshold: 50    # MB，超过此大小使用多部分上传
  max_concurrency: 5         # 最大并发上传数
```

### 4. 自定义文件命名

```yaml
oss:
  filename_format: "{date}/{arxiv_id}_{title_safe}.pdf"
  # 可用变量: {arxiv_id}, {title_safe}, {date}
```

## 🔄 迁移指南

### 从本地存储迁移到 OSS

1. **配置 OSS**：按上述步骤配置 OSS
2. **切换后端**：修改 `config.yaml` 中的 `backend` 为 `"oss"`
3. **可选数据迁移**：编写脚本将现有 PDF 上传到 OSS

### 示例迁移脚本：

```python
#!/usr/bin/env python3
import os
import sys
import sqlite3
from pathlib import Path

sys.path.append('backend')
from storage.oss_client import create_oss_client

def migrate_local_to_oss():
    # 配置 OSS 客户端
    oss_config = {
        'endpoint': 'https://oss-cn-hangzhou.aliyuncs.com',
        'access_key_id': os.getenv('OSS_ACCESS_KEY_ID'),
        'access_key_secret': os.getenv('OSS_ACCESS_KEY_SECRET'),
        'bucket_name': 'your-papers-bucket'
    }
    
    oss_client = create_oss_client(oss_config)
    
    # 从数据库获取本地文件记录
    with sqlite3.connect('papers.db') as conn:
        cursor = conn.execute(
            "SELECT arxiv_id, pdf_path FROM papers WHERE pdf_path LIKE './downloaded_papers%'"
        )
        
        for arxiv_id, local_path in cursor.fetchall():
            if os.path.exists(local_path):
                # 上传到 OSS
                object_key = oss_client.upload_file(local_path, arxiv_id, datetime.now())
                
                # 更新数据库记录
                conn.execute(
                    "UPDATE papers SET pdf_path = ? WHERE arxiv_id = ?",
                    (object_key, arxiv_id)
                )
                
                print(f"Migrated {arxiv_id}: {local_path} -> {object_key}")
        
        conn.commit()

if __name__ == "__main__":
    migrate_local_to_oss()
```

## 🔍 监控和管理

### 1. 查看存储使用情况

通过阿里云控制台查看：
- 存储用量
- 请求次数
- 流量统计
- 费用详情

### 2. 设置生命周期规则

在 OSS 控制台设置自动转换存储类型：
```
标准存储 -> 30天后 -> 低频访问存储 -> 90天后 -> 归档存储
```

### 3. 访问日志

启用 OSS 访问日志，监控文件访问情况。

## 💰 成本优化

### 1. 选择合适的存储类型
- **标准存储**：经常访问的文件
- **低频访问**：偶尔访问的文件（30天后）
- **归档存储**：长期保存的文件（90天后）

### 2. 设置生命周期策略
自动将文件转移到更便宜的存储类型。

### 3. 启用压缩
对于文本较多的 PDF，可以考虑启用压缩。

## 🛠️ 故障排除

### 常见问题

1. **访问凭证错误**
   ```
   错误: AccessDenied
   解决: 检查 OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET 是否正确
   ```

2. **Bucket 不存在**
   ```
   错误: NoSuchBucket
   解决: 确认 bucket_name 正确，且已创建
   ```

3. **权限不足**
   ```
   错误: AccessDenied
   解决: 为 RAM 用户添加适当的 OSS 权限
   ```

4. **网络连接问题**
   ```
   错误: Connection timeout
   解决: 检查网络连接，或更换 endpoint
   ```

### 调试命令

```bash
# 测试 OSS 连接
python -c "
import os, sys
sys.path.append('backend')
from storage.oss_client import create_oss_client

config = {
    'endpoint': 'https://oss-cn-hangzhou.aliyuncs.com',
    'access_key_id': os.getenv('OSS_ACCESS_KEY_ID'),
    'access_key_secret': os.getenv('OSS_ACCESS_KEY_SECRET'),
    'bucket_name': 'your-papers-bucket'
}

client = create_oss_client(config)
print('OSS connection successful!')
print('Bucket info:', client.get_bucket_info())
"
```

## 📞 支持

如遇到问题，请：

1. 检查[阿里云 OSS 文档](https://help.aliyun.com/product/31815.html)
2. 查看项目 Issues
3. 提供详细的错误日志和配置信息

---

## 📋 配置检查清单

- [ ] 创建了 OSS Bucket
- [ ] 获取了 AccessKey 凭证
- [ ] 设置了正确的 RAM 权限
- [ ] 配置了 `config.yaml` 中的 OSS 设置
- [ ] 设置了环境变量
- [ ] 安装了 OSS2 SDK
- [ ] 测试了连接和上传功能

完成以上步骤后，您的 ArXiv 论文获取系统就可以使用阿里云 OSS 进行云端存储了！