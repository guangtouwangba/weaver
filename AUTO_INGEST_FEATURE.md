# 🚀 自动文档处理功能

## ✨ 新功能说明

现在上传文档后会**自动处理入库**，无需手动操作！

### 功能流程

```
用户上传PDF
    ↓
📤 上传文件到服务器
    ↓
🔄 自动处理文档
  ├─ 提取文本内容
  ├─ 分割成chunks
  ├─ 生成embedding向量
  └─ 保存到FAISS向量数据库
    ↓
✅ 生成document_id
    ↓
💾 保存TopicContent记录
    ↓
🎉 完成！可以开始对话
```

---

## 📋 使用方法

### 1. 上传文档

1. 进入主题详情页
2. 点击"📁 文档管理"Tab
3. 点击"添加内容"按钮
4. 选择PDF文件
5. 点击"上传并分析"

### 2. 查看处理状态

上传时会显示：
```
📤 正在上传文件...
    ↓
🔄 正在处理文档（提取文本、生成向量）...
    ↓
✅ 文档上传并处理成功！现在可以开始对话了。
```

如果处理失败：
```
⚠️ 文档已上传，但处理失败。请稍后重试或联系管理员。
```

### 3. 开始对话

1. 切换到"💬 智能对话"Tab
2. 确认"对话范围"显示：`1 / 1 个文档`（不再是0/0）
3. 输入问题，开始对话！

---

## 🔧 技术实现

### 后端修改

**`apps/api/app/routers/topic_contents.py`**

```python
# 新增导入
from rag_core.pipeline.services.ingest_service import build_ingest_payload
from rag_core.graphs.ingest_graph import run_ingest_graph

# 修改upload_file_to_topic函数
async def upload_file_to_topic(...):
    # Step 1: 构建ingest payload
    payload = await build_ingest_payload(file)
    document_id = payload.document_id
    
    # Step 2: 运行ingest graph
    run_ingest_graph(payload)
    
    # Step 3: 创建content记录，包含document_id
    content_data = TopicContentCreate(
        title=file.filename,
        document_id=document_id,  # ✅ 现在有值了
        ...
    )
```

### 前端修改

**`apps/web/src/components/ContentUploadModal.tsx`**

```typescript
// 显示处理状态
const hideProcessing = message.loading(
  '🔄 正在处理文档（提取文本、生成向量）...',
  0
);

const result = await contentApi.uploadFile(...);

if (result.document_id) {
  message.success('✅ 文档上传并处理成功！');
} else {
  message.warning('⚠️ 文档已上传，但处理失败。');
}
```

---

## 🎯 关键改进

### 之前 ❌
```
上传 → 创建记录（document_id = null）
     → 需要手动调用ingest接口
     → document_id仍然为null
     → 无法对话
```

### 现在 ✅
```
上传 → 自动ingest → 获取document_id
     → 创建记录（document_id = "doc-xxx"）
     → 立即可以对话
```

---

## 📊 日志示例

### 成功处理
```
[0.00s] Upload request START - topic_id: xxx, filename: test.pdf
[0.05s] Building ingest payload...
[0.10s] Payload built successfully, document_id: doc-1234567890
[0.15s] Running ingest graph...
[2.50s] Document ingested successfully!
[2.52s] Creating content record...
[2.55s] Upload & Ingest SUCCESS!
  ├─ Content ID: abc-def-ghi
  ├─ Document ID: doc-1234567890
  └─ Status: Ready for chat
```

### 处理失败（降级）
```
[0.00s] Upload request START...
[0.05s] Building ingest payload...
[0.10s] Running ingest graph...
[0.50s] Failed to ingest document: ConnectionError
[0.52s] Document ingest failed, creating content without document_id
[0.55s] Upload SUCCESS! (但无法对话)
```

---

## ⚠️ 注意事项

### 1. 处理时间
- 小文件（<1MB）：1-3秒
- 中等文件（1-10MB）：3-10秒
- 大文件（>10MB）：10-30秒

**请耐心等待，不要关闭浏览器！**

### 2. 错误处理
如果处理失败：
- 文档仍会保存到数据库
- 但`document_id`为null
- 可以在"文档管理"中重新上传

### 3. 支持的文件格式
- ✅ PDF
- ✅ TXT
- ✅ Markdown (`.md`)
- ✅ Word (`.docx`)
- ❌ 图片、视频等多媒体文件

---

## 🐛 故障排查

### 问题1：上传后显示"暂无可用文档"

**原因**：document_id为null

**解决**：
1. 查看后端日志，检查ingest是否失败
2. 检查FAISS向量数据库是否正常
3. 检查embedding模型配置
4. 重新上传文档

### 问题2：处理时间过长

**原因**：大文件或服务器性能

**解决**：
1. 将大文件分割成小文件
2. 增加服务器资源
3. 优化embedding模型（使用更快的模型）

### 问题3：处理失败

**查看日志**：
```bash
# 后端日志
tail -f logs/api.log

# 查找关键词
grep "Upload request START" logs/api.log
grep "Document ingested successfully" logs/api.log
grep "Failed to ingest document" logs/api.log
```

---

## 🚀 未来改进

### Phase 2
- [ ] 后台异步处理（避免阻塞上传）
- [ ] 处理进度条（实时显示）
- [ ] 批量上传多个文件
- [ ] 重新处理失败的文档

### Phase 3
- [ ] 增量更新（只处理新增内容）
- [ ] 智能重试机制
- [ ] 处理队列管理
- [ ] 文档预览功能

---

## ✅ 测试清单

- [ ] 上传小文件（<1MB）
- [ ] 上传中等文件（1-10MB）
- [ ] 上传大文件（>10MB）
- [ ] 上传非PDF文件
- [ ] 检查document_id是否生成
- [ ] 验证Chat功能是否正常
- [ ] 测试错误处理（关闭embedding服务）
- [ ] 检查日志输出

---

**现在就去试试吧！** 🎉

上传一个PDF，看看是否能立即开始对话！

