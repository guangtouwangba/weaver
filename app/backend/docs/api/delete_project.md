# Delete Project API

## 概述

删除项目接口用于删除指定的项目以及所有相关的数据和文件。

## 端点

```
DELETE /api/v1/projects/{project_id}
```

## 请求参数

### 路径参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| project_id | UUID | 是 | 项目的唯一标识符 |

## 响应

### 成功响应

**状态码**: 204 No Content

删除成功时返回空响应体。

### 错误响应

**状态码**: 404 Not Found

```json
{
  "detail": "Project {project_id} not found"
}
```

当指定的项目不存在时返回此错误。

## 删除行为

删除项目时会执行以下操作：

1. **数据库清理** - 通过数据库级联删除机制自动删除：
   - 项目文档 (documents)
   - 文档分块 (document_chunks)
   - Canvas 数据 (canvases)
   - 聊天消息 (chat_messages)
   - 知识图谱实体 (entities)
   - 知识图谱关系 (relations)

2. **本地文件清理** - 删除本地存储的项目文件：
   - 路径：`{upload_dir}/projects/{project_id}/`
   - 包含该目录下的所有文件和子目录

3. **远程文件清理** - 如果配置了 Supabase Storage，则删除远程存储的文件：
   - 路径：`projects/{project_id}/`
   - 包含该前缀下的所有文件

## 使用示例

### cURL

```bash
curl -X DELETE \
  http://localhost:8000/api/v1/projects/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json"
```

### Python (requests)

```python
import requests

project_id = "123e4567-e89b-12d3-a456-426614174000"
url = f"http://localhost:8000/api/v1/projects/{project_id}"

response = requests.delete(url)

if response.status_code == 204:
    print("Project deleted successfully")
elif response.status_code == 404:
    print("Project not found")
else:
    print(f"Error: {response.status_code}")
```

### JavaScript (fetch)

```javascript
const projectId = "123e4567-e89b-12d3-a456-426614174000";
const url = `http://localhost:8000/api/v1/projects/${projectId}`;

fetch(url, {
  method: 'DELETE',
})
  .then(response => {
    if (response.status === 204) {
      console.log('Project deleted successfully');
    } else if (response.status === 404) {
      console.log('Project not found');
    } else {
      console.error('Error:', response.status);
    }
  })
  .catch(error => console.error('Error:', error));
```

## 注意事项

1. **不可恢复**: 删除操作是永久性的，无法撤销。删除前请确认。

2. **级联删除**: 删除项目会自动删除所有关联数据，包括文档、聊天记录、知识图谱等。

3. **文件清理容错**: 即使文件删除失败（例如权限问题），数据库记录仍会被删除。文件清理失败会记录警告日志但不会阻止删除操作。

4. **权限**: 目前没有实现权限控制，任何人都可以删除任何项目。在生产环境中应添加适当的认证和授权机制。

## 相关接口

- `GET /api/v1/projects` - 列出所有项目
- `POST /api/v1/projects` - 创建新项目
- `GET /api/v1/projects/{project_id}` - 获取项目详情

