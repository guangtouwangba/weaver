# 故障排查指南

## OpenMP 库冲突 (macOS)

### 问题描述

在 macOS 上使用 PyTorch 和 sentence-transformers 时，可能会遇到以下错误：

```
OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.
```

这会导致 Python 崩溃退出。

### 原因

多个库（PyTorch, NumPy, scikit-learn）都链接了 OpenMP 运行时，导致多个 OpenMP 库被加载到同一进程中。

### 解决方案

#### ✅ 方案 1: 代码自动修复（已实施）

我们的代码已经在以下位置自动设置了环境变量：
- `packages/rag-core/rag_core/rerankers/cross_encoder_reranker.py`
- `examples/test_reranker.py`

**现在你可以直接运行**：
```bash
python examples/test_reranker.py
```

#### 方案 2: 永久设置环境变量

添加到你的 shell 配置文件：

**Zsh (macOS 默认)**:
```bash
echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.zshrc
source ~/.zshrc
```

**Bash**:
```bash
echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.bashrc
source ~/.bashrc
```

**验证**:
```bash
echo $KMP_DUPLICATE_LIB_OK  # 应该输出: TRUE
```

#### 方案 3: 使用 Conda（最稳定）

Conda 能更好地管理依赖，避免库冲突：

```bash
# 1. 安装 Miniconda
# 下载: https://docs.conda.io/en/latest/miniconda.html

# 2. 创建新环境
conda create -n rag-env python=3.11
conda activate rag-env

# 3. 通过 conda 安装 PyTorch（推荐）
conda install pytorch torchvision torchaudio -c pytorch

# 4. 安装项目依赖
pip install -e .

# 5. 测试
python examples/test_reranker.py
```

#### 方案 4: CPU-only PyTorch（更轻量）

如果不需要 GPU 支持：

```bash
# 卸载现有 torch
pip uninstall torch torchvision torchaudio

# 安装 CPU 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 测试
python examples/test_reranker.py
```

#### 方案 5: 诊断和清理

查找冲突的 OpenMP 库：

```bash
# 查找所有 OpenMP 库
find $(python -c 'import sys; print(sys.prefix)') -name 'libomp*.dylib'

# 示例输出（可能有多个）:
# /path/to/venv/lib/python3.13/site-packages/torch/lib/libomp.dylib
# /path/to/venv/lib/python3.13/site-packages/scipy/.dylibs/libomp.dylib
```

如果发现多个 libomp 库，考虑：
1. 重新安装包确保使用相同版本
2. 使用 Conda 环境
3. 使用 CPU-only 版本

### 性能影响

**设置 `KMP_DUPLICATE_LIB_OK=TRUE` 的影响**:
- ✅ 功能正常，不会崩溃
- ⚠️ 可能略微降低性能（5-10%）
- ⚠️ 不推荐用于生产环境（虽然通常没问题）

**更好的解决方案**: 使用 Conda 或确保单一 OpenMP 库。

### 测试验证

运行以下命令验证修复：

```bash
# 测试 Reranker
python examples/test_reranker.py

# 测试 HybridRetriever
python examples/test_hybrid_retriever.py

# 启动 API 服务
python start_backend.py
```

如果看到以下输出，说明成功：
```
✅ Vector store created with 10 documents
✅ Reranker created: CrossEncoderReranker(...)
✅ All tests completed!
```

### 其他常见问题

#### 问题: 模型下载失败

**症状**: `OSError: Can't load model...`

**解决**:
```bash
# 使用 Hugging Face 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或手动下载模型
git clone https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2
# 然后在代码中使用本地路径
```

#### 问题: 内存不足

**症状**: `RuntimeError: CUDA out of memory` 或 `MemoryError`

**解决**:
```bash
# 1. 减小批处理大小
RERANKER_BATCH_SIZE=8  # 默认 32

# 2. 使用更小的模型
RERANKER_MODEL=cross-encoder/ms-marco-TinyBERT-L-2-v2

# 3. 限制候选数量
VECTOR_TOP_K=10  # 默认 20
```

#### 问题: 速度太慢

**优化建议**:

```bash
# 1. 使用更快的模型
RERANKER_MODEL=cross-encoder/ms-marco-TinyBERT-L-2-v2

# 2. 增加批处理大小（如果内存足够）
RERANKER_BATCH_SIZE=64

# 3. 使用 GPU（如果可用）
# PyTorch 会自动检测并使用 GPU

# 4. 减少候选数量
VECTOR_TOP_K=10  # 而不是 20 或 30
```

### 获取帮助

如果问题仍未解决：

1. **查看日志**: 运行时添加 `-v` 或 `--verbose` 标志
2. **检查依赖**: `pip list | grep -E "torch|numpy|scipy"`
3. **提供信息**:
   ```bash
   python --version
   pip list | grep -E "torch|sentence-transformers|numpy|scipy"
   uname -a  # 系统信息
   ```
4. **参考文档**:
   - [RERANKER.md](./RERANKER.md) - Reranker 详细文档
   - [HYBRID_RETRIEVER.md](./HYBRID_RETRIEVER.md) - HybridRetriever 文档
   - [OpenMP Issue](https://github.com/pytorch/pytorch/issues/37377) - PyTorch GitHub Issue

### 快速参考脚本

运行诊断脚本：

```bash
bash scripts/fix_openmp_issue.sh
```

这会显示所有解决方案的详细步骤。

---

**最后更新**: 2025-11-16  
**状态**: OpenMP 冲突已在代码中自动处理

