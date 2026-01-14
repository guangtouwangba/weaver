# Design: WebSocket Authentication

## Overview

本设计文档描述了如何为 WebSocket 连接添加认证支持。

## Problem

WebSocket 协议 (RFC 6455) 在握手阶段使用 HTTP，但标准 JavaScript `WebSocket` API **不支持自定义 HTTP headers**。这意味着我们无法像普通 HTTP 请求那样通过 `Authorization: Bearer xxx` header 传递 JWT token。

```javascript
// ❌ 这样做是无效的 - WebSocket API 不支持自定义 headers
const ws = new WebSocket(url, {
  headers: { 'Authorization': 'Bearer xxx' }
});
```

## Solution Options

### Option A: URL Query Parameter (推荐)

通过 URL query parameter 传递 token：

```javascript
const ws = new WebSocket(`wss://api.example.com/ws?token=${jwtToken}`);
```

**优点:**
- 实现简单
- 与 FastAPI query parameter 自然集成
- 可在连接建立时立即验证

**缺点:**
- Token 可能出现在服务器日志中
- URL 长度限制（通常 2048 字符，JWT 约 1KB，足够）

### Option B: 连接后首消息认证

WebSocket 连接建立后，第一条消息发送认证信息：

```javascript
const ws = new WebSocket('wss://api.example.com/ws');
ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'auth', token: jwtToken }));
};
```

**优点:**
- Token 不暴露在 URL 中
- 可以处理更复杂的认证场景

**缺点:**
- 需要修改消息协议
- 存在认证前的竞态条件窗口
- 服务端需要缓存未认证连接的消息

### Option C: Cookie-based Authentication

依赖 HTTP-only cookie 进行认证（如果前后端同域）。

**优点:**
- 自动携带，无需额外代码
- 更安全（HTTP-only cookie 不可被 JS 访问）

**缺点:**
- 需要同域部署
- Supabase JWT 不使用 cookie 机制
- 与当前架构不兼容

## Decision

采用 **Option A: URL Query Parameter**

原因：
1. 与现有 Supabase JWT 架构一致
2. 实现简单，修改量最小
3. FastAPI 原生支持 query parameter
4. Token 过期时间短（1小时），降低泄露风险

## Security Considerations

### Token in URL

虽然 token 会出现在 URL 中，但：

1. **HTTPS 加密**: WebSocket 使用 `wss://`，URL 在传输中加密
2. **短期有效**: Supabase JWT 默认 1 小时过期
3. **不记录 query params**: 配置 NGINX/CDN 不记录 query parameters
4. **Referer Policy**: 使用 `Referrer-Policy: no-referrer` 防止泄露

### Recommendation

```nginx
# NGINX 配置建议
log_format noquery '$remote_addr - $remote_user [$time_local] '
                   '"$request_method $uri" $status $body_bytes_sent';
access_log /var/log/nginx/access.log noquery;
```

## Implementation Details

### Backend Flow

```
Client                              Server
  |                                    |
  |-- WebSocket handshake ------------>|
  |   GET /ws/project/xxx?token=JWT    |
  |                                    |
  |                          (1) Extract token from query param
  |                          (2) Verify JWT signature
  |                          (3) Check token expiration
  |                          (4) Extract user_id from 'sub' claim
  |                          (5) Verify project access
  |                                    |
  |<---- 101 Switching Protocols ------|  (if valid)
  |<---- Close with 1008 Policy -------|  (if invalid)
```

### Frontend Flow

```
                    Auth Context                    WebSocket Hook
                         |                               |
                         |                               |
                   getAccessToken()                      |
                         |                               |
                         v                               |
                   Return JWT or null                    |
                         |                               |
                         +-----> Build URL with token -->|
                                                         |
                                                    Create WebSocket
                                                         |
                                                    Handle events
```

## Error Handling

| Error Code | Meaning | Frontend Action |
|------------|---------|-----------------|
| 1008 | Policy Violation (auth failed) | Show login dialog |
| 1011 | Unexpected Condition | Retry with exponential backoff |
| 1006 | Abnormal Closure | Reconnect automatically |

## Migration Path

1. **Phase 1**: 添加后端 token 验证支持，但允许无 token 连接（向后兼容）
2. **Phase 2**: 前端全部添加 token 传递
3. **Phase 3**: 后端严格要求 token（除 bypass 模式外）
