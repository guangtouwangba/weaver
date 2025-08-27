# OpenAI API 代理配置指南

## 问题描述
在中国大陆访问OpenAI API时，由于网络限制，需要通过代理服务器进行连接。

## 💡 推荐方案：使用 .env 文件配置

### 步骤1: 创建 .env 文件

在项目根目录创建 `.env` 文件：

```bash
# .env 文件内容
OPENAI_API_KEY=sk-your-openai-api-key-here

# 使用标准代理环境变量
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
```

### 步骤2: 根据您的代理软件调整端口

```bash
# Clash 代理 (默认端口)
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

# V2Ray 代理
HTTP_PROXY=http://127.0.0.1:10809
HTTPS_PROXY=http://127.0.0.1:10809

# Shadowsocks 本地 HTTP 代理
HTTP_PROXY=http://127.0.0.1:1087
HTTPS_PROXY=http://127.0.0.1:1087
```

### 步骤3: 测试配置

```bash
python scripts/test_openai_connection.py
```

### 步骤4: 重启服务

```bash
make worker-stop
make worker-background
```

## 🔧 备选方案：环境变量配置

如果不使用 .env 文件，可以直接设置环境变量：

### 临时设置（当前会话）
```bash
export OPENAI_API_KEY=sk-your-api-key
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

### 永久设置

#### bash用户 (~/.bashrc)
```bash
echo 'export HTTP_PROXY=http://127.0.0.1:7890' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://127.0.0.1:7890' >> ~/.bashrc
source ~/.bashrc
```

#### zsh用户 (~/.zshrc)  
```bash
echo 'export HTTP_PROXY=http://127.0.0.1:7890' >> ~/.zshrc
echo 'export HTTPS_PROXY=http://127.0.0.1:7890' >> ~/.zshrc
source ~/.zshrc
```

## 📋 完整的 .env 配置示例

```bash
# ===== OpenAI 配置 =====
OPENAI_API_KEY=sk-your-openai-api-key-here

# ===== 代理配置 (中国大陆用户必需) =====
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

# ===== 数据库配置 =====
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__NAME=rag_system
DATABASE__USER=postgres
DATABASE__PASSWORD=your_password_here

# ===== Redis 配置 =====
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# ===== 其他配置 =====
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## 🧪 测试连接

运行测试脚本验证配置：

```bash
python scripts/test_openai_connection.py
```

**成功输出示例：**
```
✅ OpenAI API 连接成功！
✅ 摘要服务初始化成功！
✅ 摘要生成测试成功！
🎉 所有测试通过！摘要功能应该可以正常工作。
```

## 🔍 常见问题

### Q: 如何确定我的代理端口？
A: 查看你的代理软件设置：
- **Clash**: 通常是 7890
- **V2Ray**: 通常是 10809
- **Shadowsocks**: 通常是 1087

### Q: 代理设置后仍然连接失败？
A: 请检查：
1. 代理软件是否正在运行
2. 端口号是否正确
3. 防火墙是否阻止了连接
4. API Key是否有效

### Q: 如何验证代理是否生效？
A: 运行以下命令测试：
```bash
curl -x http://127.0.0.1:7890 https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## 🚀 优势说明

### 使用标准环境变量的好处：
1. **标准兼容**: `HTTP_PROXY` 和 `HTTPS_PROXY` 是业界标准
2. **工具兼容**: 大部分工具和库都自动识别这些变量
3. **简化配置**: 不需要特殊的自定义变量名
4. **易于维护**: 统一的配置管理

### 使用 .env 文件的好处：
1. **版本控制**: 可以有 `.env.example` 模板
2. **环境隔离**: 不同环境使用不同的 `.env` 文件
3. **自动加载**: 程序启动时自动读取
4. **安全性**: `.env` 文件通常被 `.gitignore` 排除
