# Spec: API Layer User Isolation

## ADDED Requirements

### Requirement: Pass User ID in API

The system SHALL pass `user_id` in all API endpoints to ensure data isolation.

#### Scenario: Verify API passes user_id
- **WHEN** an API endpoint is called
- **THEN** the `user_id` SHALL be passed to the repository layer

---

## 1. Documents API

### 文件路径

`app/backend/src/research_agent/api/v1/documents.py`

### 修改 1: confirm_upload 接口

**找到方法**: 搜索 `async def confirm_upload`

**当前代码模式**:
```python
@router.post("/projects/{project_id}/documents/confirm")
async def confirm_upload(
    project_id: UUID,
    request: ConfirmUploadRequest,
    session: AsyncSession = Depends(get_db),
    _: Project = Depends(get_verified_project),
):
    # ... 创建 document 的代码
```

**修改为**:
```python
@router.post("/projects/{project_id}/documents/confirm")
async def confirm_upload(
    project_id: UUID,
    request: ConfirmUploadRequest,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加 user 依赖
    _: Project = Depends(get_verified_project),
):
    # ✅ 获取 user_id
    user_id = user.user_id if user else None
    
    # 找到创建 document 的代码，传递 user_id
    document = await document_repo.create(
        document_data,
        user_id=user_id,  # ✅ 传递 user_id
    )
```

**检查 import**:
```python
# 确保文件顶部有以下 import
from research_agent.api.auth.supabase import UserContext, get_optional_user
```

---

## 2. Chat API

### 文件路径

`app/backend/src/research_agent/api/v1/chat.py`

### 修改 1: stream_message 接口

**找到方法**: 搜索 `async def stream_message`

**当前代码模式**:
```python
@router.post("/projects/{project_id}/chat/stream")
async def stream_message(
    project_id: UUID,
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_db),
    _: Project = Depends(get_verified_project),
):
    # ... 调用 chat service 的代码
```

**修改为**:
```python
@router.post("/projects/{project_id}/chat/stream")
async def stream_message(
    project_id: UUID,
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加 user 依赖
    _: Project = Depends(get_verified_project),
):
    # ✅ 获取 user_id
    user_id = user.user_id if user else None
    
    # 找到调用 chat service 的代码，传递 user_id
    # 示例:
    response = await chat_service.stream_response(
        project_id=project_id,
        message=request.message,
        user_id=user_id,  # ✅ 传递 user_id
    )
```

### 修改 2: get_chat_history 接口

**找到方法**: 搜索 `async def get_chat_history`

**修改为**:
```python
@router.get("/projects/{project_id}/chat/history")
async def get_chat_history(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加 user 依赖
    _: Project = Depends(get_verified_project),
):
    user_id = user.user_id if user else None
    
    messages = await chat_repo.get_history(
        project_id,
        user_id=user_id,  # ✅ 传递 user_id
    )
    return messages
```

---

## 3. Outputs API

### 文件路径

`app/backend/src/research_agent/api/v1/outputs.py`

### 修改 1: 生成接口 (mindmap, summary 等)

**找到方法**: 搜索 `async def generate_mindmap` 或类似方法

**修改模式**:
```python
@router.post("/projects/{project_id}/outputs/mindmap")
async def generate_mindmap(
    project_id: UUID,
    request: GenerateMindmapRequest,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加
    _: Project = Depends(get_verified_project),
):
    user_id = user.user_id if user else None
    
    # 传递 user_id 到 service
    output = await output_service.generate_mindmap(
        project_id=project_id,
        document_ids=request.document_ids,
        user_id=user_id,  # ✅ 传递 user_id
    )
    return output
```

### 修改 2: 查询接口

**找到方法**: 搜索 `async def list_outputs` 或 `async def get_output`

**修改模式**:
```python
@router.get("/projects/{project_id}/outputs")
async def list_outputs(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加
    _: Project = Depends(get_verified_project),
):
    user_id = user.user_id if user else None
    
    outputs = await output_repo.find_by_project_id(
        project_id,
        user_id=user_id,  # ✅ 传递 user_id
    )
    return outputs
```

---

## 4. Canvas API

### 文件路径

`app/backend/src/research_agent/api/v1/canvas.py`

### 修改 1: 保存/更新接口

**找到方法**: 搜索 `async def save_canvas` 或 `async def update_canvas`

**修改模式**:
```python
@router.put("/projects/{project_id}/canvas")
async def save_canvas(
    project_id: UUID,
    request: SaveCanvasRequest,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加
    _: Project = Depends(get_verified_project),
):
    user_id = user.user_id if user else None
    
    canvas = await canvas_repo.save(
        canvas_data,
        user_id=user_id,  # ✅ 传递 user_id
    )
    return canvas
```

### 修改 2: 查询接口

**找到方法**: 搜索 `async def get_canvas`

**修改模式**:
```python
@router.get("/projects/{project_id}/canvas")
async def get_canvas(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加
    _: Project = Depends(get_verified_project),
):
    user_id = user.user_id if user else None
    
    canvas = await canvas_repo.find_by_project_id(
        project_id,
        user_id=user_id,  # ✅ 传递 user_id
    )
    return canvas
```

---

## 5. URL API

### 文件路径

`app/backend/src/research_agent/api/v1/url.py`

### 修改 1: extract_url 接口

**找到方法**: 搜索 `async def extract_url`

**修改模式**:
```python
@router.post("/projects/{project_id}/urls/extract")
async def extract_url(
    project_id: UUID,
    request: ExtractUrlRequest,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),  # ✅ 添加
    _: Project = Depends(get_verified_project),
):
    user_id = user.user_id if user else None
    
    # 创建 url_content 时传递 user_id
    url_content = await url_service.extract(
        url=request.url,
        project_id=project_id,
        user_id=user_id,  # ✅ 传递 user_id
    )
    return url_content
```

---

## 通用修改模板

对于所有项目资源相关的 endpoint，按照以下模板修改：

### Step 1: 添加 user 依赖

```python
# 在 endpoint 函数签名中添加
user: UserContext = Depends(get_optional_user),
```

### Step 2: 获取 user_id

```python
# 在函数体开头添加
user_id = user.user_id if user else None
```

### Step 3: 传递 user_id 到 repository/service

```python
# 调用 repository 或 service 时传递
await some_repo.create(data, user_id=user_id)
await some_repo.find_by_project_id(project_id, user_id=user_id)
```

---

## 检查清单

修改完成后，确保以下 endpoint 都已更新：

### documents.py
- [ ] `confirm_upload`
- [ ] `list_documents`
- [ ] `get_document`
- [ ] `delete_document`

### chat.py
- [ ] `stream_message`
- [ ] `get_chat_history`

### outputs.py
- [ ] `generate_mindmap`
- [ ] `generate_summary`
- [ ] `list_outputs`
- [ ] `get_output`
- [ ] `delete_output`

### canvas.py
- [ ] `get_canvas`
- [ ] `save_canvas`
- [ ] `add_node`
- [ ] `update_node`
- [ ] `delete_node`

### url.py
- [ ] `extract_url`
- [ ] `list_project_url_contents`

---

## 验证方法

```bash
cd app/backend
python -c "
from research_agent.api.v1 import documents, chat, outputs, canvas, url
print('API modules imported successfully')
"
```

如果没有报错，说明语法正确。

然后启动服务器测试：

```bash
cd app/backend
uvicorn research_agent.main:app --reload
```

尝试访问 API，确保没有 500 错误。
