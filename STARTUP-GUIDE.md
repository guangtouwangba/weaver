# 🚀 MVP启动指南

## 快速开始（推荐）

```bash
# 一键启动完整系统
./start-full-mvp.sh
```

然后访问: http://localhost:3000/mvp

## 可用的启动脚本

### 🔍 环境检查
```bash
./check-env.sh          # 检查Python/conda环境，推荐最佳启动方式
```

### 🖥️ 后端启动脚本
```bash
./start-mvp-conda.sh     # 使用conda环境（Python 3.11，最稳定）
./start-mvp-simple.sh    # 使用venv环境（最新依赖版本）
./start-mvp.sh          # 标准启动（使用requirements文件）
```

### 🌐 前端启动脚本
```bash
./start-frontend.sh      # 启动Next.js开发服务器
```

### 🎯 完整系统
```bash
./start-full-mvp.sh      # 自动启动后端+前端
```

## 选择指南

### Python 3.13用户
```bash
./start-full-mvp.sh      # 推荐：自动选择最佳方案
# 或手动使用
./start-mvp-conda.sh     # conda方案最稳定
```

### Python 3.8-3.12用户
```bash
./start-full-mvp.sh      # 推荐：一键启动
# 或任选其他方案
./start-mvp-simple.sh    # 简单快速
./start-mvp.sh          # 标准方案
```

### 首次使用
```bash
./check-env.sh          # 先检查环境
./start-full-mvp.sh     # 然后一键启动
```

## 访问地址

启动成功后：
- **MVP界面**: http://localhost:3000/mvp
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 故障排除

如果遇到问题，按顺序尝试：

1. **检查环境**: `./check-env.sh`
2. **使用conda**: `./start-mvp-conda.sh`
3. **查看详细文档**: `MVP-README.md`
4. **手动安装依赖**:
   ```bash
   # Python依赖
   pip install fastapi uvicorn httpx pydantic python-multipart
   
   # Node.js依赖
   cd frontend && npm install
   ```

## 开发模式

分别启动服务进行开发：

```bash
# 终端1：启动后端
./start-mvp-simple.sh

# 终端2：启动前端
./start-frontend.sh
```

这样可以分别查看后端和前端的日志输出。