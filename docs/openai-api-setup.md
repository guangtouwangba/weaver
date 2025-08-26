# OpenAI API配置指南

## 🔑 获取OpenAI API密钥

1. 访问 [OpenAI官网](https://platform.openai.com/)
2. 注册或登录账户
3. 进入 [API Keys页面](https://platform.openai.com/api-keys)
4. 点击 "Create new secret key"
5. 复制生成的API密钥（格式：`sk-xxxxxx`）

## ⚙️ 配置方法

### 方法1: 环境变量配置（推荐）

在你的shell中设置环境变量：

```bash
# Chat功能的OpenAI API配置
export AI__CHAT__OPENAI__API_KEY="sk-your-openai-api-key-here"
export AI__CHAT__OPENAI__CHAT_MODEL="gpt-3.5-turbo"
export AI__CHAT__OPENAI__MAX_TOKENS=1024
export AI__CHAT__OPENAI__TEMPERATURE=0.7

# Embedding功能的OpenAI API配置  
export AI__EMBEDDING__OPENAI__API_KEY="sk-your-openai-api-key-here"
export AI__EMBEDDING__OPENAI__EMBEDDING_MODEL="text-embedding-ada-002"

# 设置提供商
export AI__CHAT__PROVIDER="openai"
export AI__EMBEDDING__PROVIDER="openai"
```

### 方法2: .env文件配置

创建项目根目录下的`.env`文件：

```env
# OpenAI API配置 - Chat功能
AI__CHAT__OPENAI__API_KEY=sk-your-openai-api-key-here
AI__CHAT__OPENAI__CHAT_MODEL=gpt-3.5-turbo
AI__CHAT__OPENAI__MAX_TOKENS=1024
AI__CHAT__OPENAI__TEMPERATURE=0.7
AI__CHAT__OPENAI__TIMEOUT=60
AI__CHAT__OPENAI__MAX_RETRIES=3

# OpenAI API配置 - Embedding功能  
AI__EMBEDDING__OPENAI__API_KEY=sk-your-openai-api-key-here
AI__EMBEDDING__OPENAI__EMBEDDING_MODEL=text-embedding-ada-002
AI__EMBEDDING__OPENAI__TIMEOUT=60
AI__EMBEDDING__OPENAI__MAX_RETRIES=3

# 提供商选择
AI__CHAT__PROVIDER=openai
AI__EMBEDDING__PROVIDER=openai
```

### 方法3: 直接命令行启动

```bash
AI__CHAT__OPENAI__API_KEY="sk-your-key" AI__EMBEDDING__OPENAI__API_KEY="sk-your-key" python main.py
```

## 🚀 启动步骤

1. **配置API密钥**（选择上述任一方法）
2. **启动服务器**：
   ```bash
   python main.py
   ```
3. **验证配置**：
   - 查看启动日志中是否有 "✅ OpenAI客户端初始化成功"
   - 访问测试页面：http://localhost:8000/static/chat-test.html
   - 测试流式聊天功能

## 🧪 测试OpenAI连接

创建简单测试脚本 `test_openai.py`：

```python
import asyncio
import os
from openai import AsyncOpenAI

async def test_openai_connection():
    api_key = os.getenv("AI__CHAT__OPENAI__API_KEY") or "your-api-key-here"
    
    if not api_key or api_key == "your-api-key-here":
        print("❌ 请先设置AI__CHAT__OPENAI__API_KEY环境变量")
        return
    
    try:
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test!"}],
            max_tokens=50
        )
        
        print("✅ OpenAI连接成功！")
        print(f"回答: {response.choices[0].message.content}")
        print(f"使用tokens: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"❌ OpenAI连接失败: {e}")
        if "api_key" in str(e).lower():
            print("💡 请检查API密钥是否正确")
        elif "quota" in str(e).lower():
            print("💡 请检查OpenAI账户余额")

if __name__ == "__main__":
    asyncio.run(test_openai_connection())
```

运行测试：
```bash
python test_openai.py
```

## 💡 常见问题

### Q: 提示"未配置OpenAI API密钥，将使用模拟回答"
**A:** 环境变量名称必须精确匹配，注意双下划线 `__`

### Q: API密钥无效错误
**A:** 
- 确保密钥格式正确（以`sk-`开头）
- 检查密钥是否已激活
- 确认账户有足够余额

### Q: 模型不可用错误
**A:**
- 确认账户有对应模型的访问权限
- 尝试使用 `gpt-3.5-turbo` 而非 `gpt-4`

### Q: 请求超时
**A:**
- 检查网络连接
- 增加超时设置：`AI__CHAT__OPENAI__TIMEOUT=120`

## 🎯 推荐配置

生产环境推荐配置：

```env
# 基础配置
AI__CHAT__OPENAI__API_KEY=sk-your-key
AI__CHAT__OPENAI__CHAT_MODEL=gpt-3.5-turbo
AI__CHAT__OPENAI__MAX_TOKENS=2048
AI__CHAT__OPENAI__TEMPERATURE=0.7
AI__CHAT__OPENAI__TIMEOUT=60
AI__CHAT__OPENAI__MAX_RETRIES=3

# Embedding配置
AI__EMBEDDING__OPENAI__API_KEY=sk-your-key
AI__EMBEDDING__OPENAI__EMBEDDING_MODEL=text-embedding-ada-002

# 性能优化
AI__RATE_LIMIT_REQUESTS_PER_MINUTE=60
AI__RATE_LIMIT_TOKENS_PER_MINUTE=100000
AI__ENABLE_CACHING=true
AI__CACHE_TTL=3600
```

配置完成后，重启服务器即可使用真实的OpenAI API进行聊天！🎉
