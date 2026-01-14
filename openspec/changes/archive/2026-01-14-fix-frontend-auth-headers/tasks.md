# Tasks: Fix Frontend Auth Headers

## Overview

修复前端所有 WebSocket 连接缺失认证 token 的问题。

---

## Phase 1: Backend - WebSocket 认证模块

### Task 1.1: 创建 WebSocket 认证工具模块

**文件**: `app/backend/src/research_agent/api/auth/websocket_auth.py`

**操作**: 创建新文件

**具体步骤**:
1. 创建文件 `app/backend/src/research_agent/api/auth/websocket_auth.py`
2. 实现 `verify_websocket_token(websocket, token)` 函数：
   - 接受 `WebSocket` 对象和可选的 `token` 字符串
   - 如果 `settings.auth_bypass_enabled` 为 True，接受连接并返回 `("dev-user-bypass", False)`
   - 如果没有 token，接受连接并返回 `("anonymous", True)`
   - 使用 `verify_supabase_jwt(token)` 验证 token
   - 验证失败时关闭连接并抛出 `WebSocketException`
   - 验证成功时接受连接并返回 `(user_id, False)`
3. 实现 `verify_project_access(project_id, user_id, is_anonymous)` 函数（暂时返回 True）

**验证**: 
- [ ] 文件创建成功
- [ ] 后端服务正常启动不报错

---

### Task 1.2: 修改 WebSocket endpoints 添加认证

**文件**: `app/backend/src/research_agent/api/v1/websocket.py`

**操作**: 修改现有文件

**具体步骤**:

1. **添加导入** (在文件顶部):
   ```python
   from research_agent.api.auth.websocket_auth import verify_websocket_token, verify_project_access
   ```

2. **修改 `project_documents_websocket` 函数** (约第 21-46 行):
   - 添加参数 `token: Optional[str] = None`
   - 在 `await document_notification_service.connect(...)` 之前添加:
     ```python
     try:
         user_id, is_anonymous = await verify_websocket_token(websocket, token)
         await verify_project_access(project_id, user_id, is_anonymous)
     except Exception:
         return
     ```

3. **修改 `document_status_websocket` 函数** (约第 66-91 行):
   - 添加参数 `token: Optional[str] = None`
   - 在 `await document_notification_service.connect(...)` 之前添加同样的认证逻辑

4. **修改 `project_canvas_websocket` 函数** (约第 111-136 行):
   - 添加参数 `token: Optional[str] = None`
   - 在 `await canvas_notification_service.connect(...)` 之前添加认证逻辑

5. **修改 `project_outputs_websocket` 函数** (约第 156-199 行):
   - 添加参数 `token: Optional[str] = None`
   - 在 `await output_notification_service.connect(...)` 之前添加认证逻辑

**验证**: 
- [ ] 后端服务正常启动
- [ ] WebSocket endpoint 接受 `?token=xxx` query parameter

---

## Phase 2: Frontend - API 工具函数

### Task 2.1: 添加 getAuthenticatedWebSocketUrl 函数

**文件**: `app/frontend/src/lib/api.ts`

**操作**: 在现有文件中添加新函数

**具体步骤**:
1. 在 `getWebSocketUrl()` 函数之后（约第 839 行之后）添加新函数:

```typescript
/**
 * Get WebSocket URL with auth token as query parameter.
 * WebSocket connections cannot use HTTP headers, so we pass token via query param.
 * 
 * @param basePath - The WebSocket path (e.g., '/ws/projects/xxx/canvas')
 * @returns Full WebSocket URL with token if available
 */
export async function getAuthenticatedWebSocketUrl(basePath: string): Promise<string> {
  const baseUrl = `${getWebSocketUrl()}${basePath}`;
  
  let token: string | null = null;
  if (_getAuthToken) {
    try {
      token = await _getAuthToken();
    } catch (error) {
      console.warn('[API] Failed to get auth token for WebSocket:', error);
    }
  } else {
    // Fallback: directly get session from Supabase if token getter not set yet
    try {
      const { getSession, isAuthConfigured } = await import('@/lib/supabase');
      if (isAuthConfigured()) {
        const session = await getSession();
        token = session?.access_token || null;
      }
    } catch (error) {
      console.warn('[API] Failed to get session for WebSocket:', error);
    }
  }
  
  if (token) {
    const separator = basePath.includes('?') ? '&' : '?';
    return `${baseUrl}${separator}token=${encodeURIComponent(token)}`;
  }
  
  return baseUrl;
}
```

2. 确保函数已导出（添加到文件的 export 列表中，如果有的话）

**验证**: 
- [ ] TypeScript 编译通过
- [ ] 前端服务正常启动

---

## Phase 3: Frontend - WebSocket Hooks 修改

### Task 3.1: 修改 useCanvasWebSocket

**文件**: `app/frontend/src/hooks/useCanvasWebSocket.ts`

**操作**: 修改现有文件

**具体步骤**:

1. **修改导入** (第 12 行):
   ```typescript
   // 将
   import { getWebSocketUrl, CanvasWebSocketEvent, ... } from '@/lib/api';
   // 改为
   import { getAuthenticatedWebSocketUrl, CanvasWebSocketEvent, ... } from '@/lib/api';
   ```

2. **修改 connect 函数签名** (约第 66 行):
   ```typescript
   // 将
   const connect = useCallback(() => {
   // 改为
   const connect = useCallback(async () => {
   ```

3. **修改 WebSocket URL 获取方式** (约第 71 行):
   ```typescript
   // 将
   const wsUrl = `${getWebSocketUrl()}/ws/projects/${projectId}/canvas`;
   // 改为
   const wsUrl = await getAuthenticatedWebSocketUrl(`/ws/projects/${projectId}/canvas`);
   ```

**验证**: 
- [ ] TypeScript 编译通过
- [ ] Canvas WebSocket 连接 URL 包含 token

---

### Task 3.2: 修改 useOutputWebSocket

**文件**: `app/frontend/src/hooks/useOutputWebSocket.ts`

**操作**: 修改现有文件

**具体步骤**:

1. **修改导入** (第 11 行):
   ```typescript
   import { getAuthenticatedWebSocketUrl, OutputWebSocketEvent, ... } from '@/lib/api';
   ```

2. **修改 connect 函数签名** (约第 72 行):
   ```typescript
   const connect = useCallback(async () => {
   ```

3. **修改 WebSocket URL 构建逻辑** (约第 77-82 行):
   ```typescript
   // Build URL with optional task_id query param
   let basePath = `/ws/projects/${projectId}/outputs`;
   if (taskId) {
     basePath += `?task_id=${taskId}`;
   }
   const wsUrl = await getAuthenticatedWebSocketUrl(basePath);
   ```

**验证**: 
- [ ] TypeScript 编译通过
- [ ] Output WebSocket 连接 URL 包含 token

---

### Task 3.3: 修改 useDocumentWebSocket

**文件**: `app/frontend/src/hooks/useDocumentWebSocket.ts`

**操作**: 修改现有文件

**具体步骤**:

1. **修改导入** (第 11 行):
   ```typescript
   import { getAuthenticatedWebSocketUrl, DocumentWebSocketEvent } from '@/lib/api';
   ```

2. **修改 connect 函数签名** (约第 62 行):
   ```typescript
   const connect = useCallback(async () => {
   ```

3. **修改 WebSocket URL 获取方式** (约第 67 行):
   ```typescript
   const wsUrl = await getAuthenticatedWebSocketUrl(`/ws/projects/${projectId}/documents`);
   ```

**验证**: 
- [ ] TypeScript 编译通过
- [ ] Document WebSocket 连接 URL 包含 token

---

### Task 3.4: 修改 useCanvasActions

**文件**: `app/frontend/src/hooks/useCanvasActions.ts`

**操作**: 修改现有文件

**具体步骤**:

1. **修改导入** (约第 12 行):
   ```typescript
   // 将 getWebSocketUrl 替换为 getAuthenticatedWebSocketUrl
   import {
     CanvasNode,
     CanvasEdge,
     outputsApi,
     canvasApi,
     SummaryData,
     MindmapData,
     MindmapNode,
     MindmapEdge,
     getAuthenticatedWebSocketUrl  // 替换 getWebSocketUrl
   } from '@/lib/api';
   ```

2. **修改 handleGenerateMindmapStreaming 函数** (约第 124-129 行):
   
   原代码:
   ```typescript
   return new Promise<void>((resolve, reject) => {
     const wsUrl = `${getWebSocketUrl()}/ws/projects/${projectId}/outputs?task_id=${task_id}`;
     console.log('[Mindmap WS] Connecting to:', wsUrl);
     
     try {
       const ws = new WebSocket(wsUrl);
   ```
   
   修改为:
   ```typescript
   return new Promise<void>(async (resolve, reject) => {
     const wsUrl = await getAuthenticatedWebSocketUrl(`/ws/projects/${projectId}/outputs?task_id=${task_id}`);
     console.log('[Mindmap WS] Connecting to:', wsUrl);
     
     try {
       const ws = new WebSocket(wsUrl);
   ```

3. **修改 handleMindmapStreamingConcurrent 函数** (约第 580-585 行):
   
   原代码:
   ```typescript
   return new Promise<void>((resolve, reject) => {
     const wsUrl = `${getWebSocketUrl()}/ws/projects/${projectId}/outputs?task_id=${backendTaskId}`;
     console.log('[Mindmap WS Concurrent] Connecting to:', wsUrl);
     
     try {
       const ws = new WebSocket(wsUrl);
   ```
   
   修改为:
   ```typescript
   return new Promise<void>(async (resolve, reject) => {
     const wsUrl = await getAuthenticatedWebSocketUrl(`/ws/projects/${projectId}/outputs?task_id=${backendTaskId}`);
     console.log('[Mindmap WS Concurrent] Connecting to:', wsUrl);
     
     try {
       const ws = new WebSocket(wsUrl);
   ```

**验证**: 
- [ ] TypeScript 编译通过
- [ ] Mindmap 生成的 WebSocket 连接 URL 包含 token

---

## Phase 4: Integration Testing

### Task 4.1: 手动集成测试

**操作**: 手动测试

**具体步骤**:

1. 启动后端和前端服务
2. 登录用户账号
3. 打开浏览器开发者工具 → Network → WS
4. 访问 Studio 页面
5. 验证所有 WebSocket 连接 URL 包含 `?token=xxx` 参数
6. 验证连接成功建立
7. 测试 Chat、Mindmap 生成等功能正常

**验证**: 
- [ ] 所有 WebSocket 连接携带 token
- [ ] 功能正常工作
- [ ] 控制台无认证错误

---

## Checklist Summary

- [ ] 1.1 创建 websocket_auth.py
- [ ] 1.2 修改 websocket.py 添加认证
- [ ] 2.1 添加 getAuthenticatedWebSocketUrl
- [ ] 3.1 修改 useCanvasWebSocket
- [ ] 3.2 修改 useOutputWebSocket
- [ ] 3.3 修改 useDocumentWebSocket
- [ ] 3.4 修改 useCanvasActions
- [ ] 4.1 集成测试通过
