# Chat系统前端设计方案

## 📋 概述

Chat系统前端基于React技术栈，提供现代化的聊天界面，支持实时对话、文档引用展示、流式响应等功能。

## 🎨 UI/UX设计

### 1. 整体布局

```
┌─────────────────────────────────────────────────────────────┐
│                    Header (导航栏)                         │
├─────────────────┬─────────────────────────────────────────────┤
│                 │                                           │
│    侧边栏        │                主聊天区域                    │
│  (会话列表)      │                                           │
│                 │  ┌─────────────────────────────────────┐   │
│                 │  │           消息历史区域               │   │
│                 │  │                                     │   │
│                 │  │                                     │   │
│                 │  └─────────────────────────────────────┘   │
│                 │  ┌─────────────────────────────────────┐   │
│                 │  │           输入区域                  │   │
│                 │  └─────────────────────────────────────┘   │
├─────────────────┼─────────────────────────────────────────────┤
│                 │                右侧面板                    │
│                 │          (文档引用/设置)                   │
└─────────────────┴─────────────────────────────────────────────┘
```

### 2. 组件设计

#### 2.1 聊天界面组件 (ChatInterface)

```jsx
// components/ChatInterface.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Layout, Spin } from 'antd';
import SessionSidebar from './SessionSidebar';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ReferencePanel from './ReferencePanel';
import { useChatStore } from '../stores/chatStore';
import { useWebSocket } from '../hooks/useWebSocket';

const { Sider, Content } = Layout;

const ChatInterface = () => {
    const {
        currentSession,
        messages,
        isLoading,
        sendMessage,
        createSession
    } = useChatStore();
    
    const { connect, disconnect, isConnected } = useWebSocket();
    
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [showReferences, setShowReferences] = useState(true);
    
    useEffect(() => {
        if (currentSession?.session_id) {
            connect(currentSession.session_id);
        }
        
        return () => disconnect();
    }, [currentSession?.session_id]);
    
    const handleSendMessage = async (content, metadata) => {
        if (!currentSession) {
            // 创建新会话
            const session = await createSession();
            if (session) {
                await sendMessage(session.session_id, content, metadata);
            }
        } else {
            await sendMessage(currentSession.session_id, content, metadata);
        }
    };
    
    return (
        <Layout className="chat-interface">
            <Sider
                width={320}
                collapsed={sidebarCollapsed}
                onCollapse={setSidebarCollapsed}
                className="chat-sidebar"
            >
                <SessionSidebar />
            </Sider>
            
            <Content className="chat-main">
                <div className="chat-container">
                    <MessageList 
                        messages={messages}
                        isLoading={isLoading}
                        sessionId={currentSession?.session_id}
                    />
                    
                    <MessageInput
                        onSendMessage={handleSendMessage}
                        disabled={!isConnected || isLoading}
                        placeholder="输入您的问题..."
                    />
                </div>
            </Content>
            
            {showReferences && (
                <Sider width={400} className="reference-panel">
                    <ReferencePanel 
                        sessionId={currentSession?.session_id}
                    />
                </Sider>
            )}
        </Layout>
    );
};

export default ChatInterface;
```

#### 2.2 消息列表组件 (MessageList)

```jsx
// components/MessageList.jsx
import React, { useEffect, useRef } from 'react';
import { List, Avatar, Typography, Skeleton } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import MessageBubble from './MessageBubble';
import StreamingMessage from './StreamingMessage';
import { useChatStore } from '../stores/chatStore';

const MessageList = ({ messages, isLoading, sessionId }) => {
    const listRef = useRef(null);
    const { streamingMessage } = useChatStore();
    
    // 自动滚动到底部
    useEffect(() => {
        if (listRef.current) {
            listRef.current.scrollTop = listRef.current.scrollHeight;
        }
    }, [messages, streamingMessage]);
    
    const renderMessage = (message) => {
        const isUser = message.role === 'user';
        const avatar = isUser ? <UserOutlined /> : <RobotOutlined />;
        
        return (
            <div className={`message-item ${isUser ? 'user' : 'assistant'}`}>
                <Avatar 
                    icon={avatar}
                    className={`message-avatar ${isUser ? 'user-avatar' : 'assistant-avatar'}`}
                />
                <MessageBubble 
                    message={message}
                    className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}
                />
            </div>
        );
    };
    
    return (
        <div className="message-list" ref={listRef}>
            <List
                dataSource={messages}
                renderItem={renderMessage}
                split={false}
                className="messages"
            />
            
            {/* 流式消息 */}
            {streamingMessage && (
                <StreamingMessage 
                    message={streamingMessage}
                    className="streaming-message"
                />
            )}
            
            {/* 加载状态 */}
            {isLoading && !streamingMessage && (
                <div className="message-item assistant">
                    <Avatar icon={<RobotOutlined />} className="assistant-avatar" />
                    <div className="message-bubble assistant-bubble">
                        <Skeleton active paragraph={{ rows: 2 }} />
                    </div>
                </div>
            )}
        </div>
    );
};

export default MessageList;
```

#### 2.3 消息气泡组件 (MessageBubble)

```jsx
// components/MessageBubble.jsx
import React, { useState } from 'react';
import { Card, Button, Tooltip, Space, Tag } from 'antd';
import { CopyOutlined, LikeOutlined, DislikeOutlined, RedoOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import MessageReferences from './MessageReferences';
import { formatMessageTime } from '../utils/dateUtils';

const MessageBubble = ({ message, className }) => {
    const [copied, setCopied] = useState(false);
    
    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(message.content);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('复制失败:', error);
        }
    };
    
    const handleRegenerate = () => {
        // 重新生成回复逻辑
        console.log('重新生成回复:', message.message_id);
    };
    
    const renderMarkdown = (content) => {
        return (
            <ReactMarkdown
                components={{
                    code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                            <SyntaxHighlighter
                                style={tomorrow}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                            >
                                {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                        ) : (
                            <code className={className} {...props}>
                                {children}
                            </code>
                        );
                    }
                }}
            >
                {content}
            </ReactMarkdown>
        );
    };
    
    const isAssistant = message.role === 'assistant';
    
    return (
        <Card 
            className={`message-bubble ${className}`}
            size="small"
            bordered={false}
        >
            <div className="message-content">
                {message.content_type === 'markdown' ? 
                    renderMarkdown(message.content) : 
                    <div className="message-text">{message.content}</div>
                }
            </div>
            
            {/* 文档引用 */}
            {isAssistant && message.references && message.references.length > 0 && (
                <MessageReferences references={message.references} />
            )}
            
            <div className="message-meta">
                <div className="message-time">
                    {formatMessageTime(message.created_at)}
                </div>
                
                {/* 模型和Token信息 */}
                {isAssistant && (
                    <div className="message-stats">
                        {message.model && <Tag size="small">{message.model}</Tag>}
                        {message.tokens && <Tag size="small">{message.tokens} tokens</Tag>}
                        {message.processing_time_ms && (
                            <Tag size="small">{message.processing_time_ms}ms</Tag>
                        )}
                    </div>
                )}
                
                {/* 操作按钮 */}
                <Space className="message-actions" size="small">
                    <Tooltip title={copied ? "已复制" : "复制"}>
                        <Button 
                            type="text" 
                            icon={<CopyOutlined />} 
                            size="small"
                            onClick={handleCopy}
                        />
                    </Tooltip>
                    
                    {isAssistant && (
                        <>
                            <Tooltip title="有用">
                                <Button 
                                    type="text" 
                                    icon={<LikeOutlined />} 
                                    size="small"
                                />
                            </Tooltip>
                            
                            <Tooltip title="无用">
                                <Button 
                                    type="text" 
                                    icon={<DislikeOutlined />} 
                                    size="small"
                                />
                            </Tooltip>
                            
                            <Tooltip title="重新生成">
                                <Button 
                                    type="text" 
                                    icon={<RedoOutlined />} 
                                    size="small"
                                    onClick={handleRegenerate}
                                />
                            </Tooltip>
                        </>
                    )}
                </Space>
            </div>
        </Card>
    );
};

export default MessageBubble;
```

#### 2.4 流式消息组件 (StreamingMessage)

```jsx
// components/StreamingMessage.jsx
import React, { useEffect, useState } from 'react';
import { Card, Avatar, Typography } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';

const StreamingMessage = ({ message, className }) => {
    const [displayContent, setDisplayContent] = useState('');
    const [cursorVisible, setCursorVisible] = useState(true);
    
    useEffect(() => {
        setDisplayContent(message.content || '');
    }, [message.content]);
    
    // 光标闪烁效果
    useEffect(() => {
        const interval = setInterval(() => {
            setCursorVisible(prev => !prev);
        }, 500);
        
        return () => clearInterval(interval);
    }, []);
    
    return (
        <div className={`message-item assistant ${className}`}>
            <Avatar icon={<RobotOutlined />} className="assistant-avatar" />
            
            <Card className="message-bubble assistant-bubble streaming" size="small" bordered={false}>
                <div className="streaming-content">
                    <ReactMarkdown>
                        {displayContent}
                    </ReactMarkdown>
                    
                    {/* 打字机光标 */}
                    <span className={`typing-cursor ${cursorVisible ? 'visible' : ''}`}>
                        |
                    </span>
                </div>
                
                {/* 状态指示器 */}
                <div className="streaming-status">
                    <span className="status-text">AI正在思考中...</span>
                    <div className="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default StreamingMessage;
```

#### 2.5 消息输入组件 (MessageInput)

```jsx
// components/MessageInput.jsx
import React, { useState, useRef } from 'react';
import { Input, Button, Upload, Tooltip, Space } from 'antd';
import { SendOutlined, PaperClipOutlined, MicrophoneOutlined } from '@ant-design/icons';

const { TextArea } = Input;

const MessageInput = ({ onSendMessage, disabled, placeholder }) => {
    const [message, setMessage] = useState('');
    const [isComposing, setIsComposing] = useState(false);
    const textAreaRef = useRef(null);
    
    const handleSend = () => {
        if (message.trim() && !disabled) {
            onSendMessage(message.trim(), {
                timestamp: new Date().toISOString()
            });
            setMessage('');
            
            // 重置文本域高度
            if (textAreaRef.current) {
                textAreaRef.current.focus();
            }
        }
    };
    
    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
            e.preventDefault();
            handleSend();
        }
    };
    
    const handleFileUpload = (file) => {
        // 文件上传逻辑
        console.log('上传文件:', file);
        return false; // 阻止默认上传行为
    };
    
    return (
        <div className="message-input-container">
            <div className="input-wrapper">
                <TextArea
                    ref={textAreaRef}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    onCompositionStart={() => setIsComposing(true)}
                    onCompositionEnd={() => setIsComposing(false)}
                    placeholder={placeholder}
                    disabled={disabled}
                    autoSize={{ minRows: 1, maxRows: 6 }}
                    className="message-textarea"
                />
                
                <div className="input-actions">
                    <Space>
                        <Upload
                            beforeUpload={handleFileUpload}
                            showUploadList={false}
                            multiple
                        >
                            <Tooltip title="上传文件">
                                <Button 
                                    type="text" 
                                    icon={<PaperClipOutlined />} 
                                    disabled={disabled}
                                />
                            </Tooltip>
                        </Upload>
                        
                        <Tooltip title="语音输入">
                            <Button 
                                type="text" 
                                icon={<MicrophoneOutlined />} 
                                disabled={disabled}
                            />
                        </Tooltip>
                        
                        <Button
                            type="primary"
                            icon={<SendOutlined />}
                            onClick={handleSend}
                            disabled={disabled || !message.trim()}
                            className="send-button"
                        >
                            发送
                        </Button>
                    </Space>
                </div>
            </div>
            
            {/* 输入提示 */}
            <div className="input-hint">
                按 Enter 发送，Shift + Enter 换行
            </div>
        </div>
    );
};

export default MessageInput;
```

## 🔄 状态管理

### Chat Store (Zustand)

```javascript
// stores/chatStore.js
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { chatAPI } from '../services/chatAPI';

export const useChatStore = create(
    subscribeWithSelector((set, get) => ({
        // 状态
        sessions: [],
        currentSession: null,
        messages: [],
        streamingMessage: null,
        isLoading: false,
        error: null,
        
        // WebSocket状态
        wsConnection: null,
        isConnected: false,
        
        // Actions
        setSessions: (sessions) => set({ sessions }),
        
        setCurrentSession: (session) => set({ 
            currentSession: session,
            messages: [] // 清空消息，等待加载
        }),
        
        setMessages: (messages) => set({ messages }),
        
        addMessage: (message) => set((state) => ({
            messages: [...state.messages, message]
        })),
        
        updateMessage: (messageId, updates) => set((state) => ({
            messages: state.messages.map(msg => 
                msg.message_id === messageId ? { ...msg, ...updates } : msg
            )
        })),
        
        setStreamingMessage: (message) => set({ streamingMessage: message }),
        
        setLoading: (isLoading) => set({ isLoading }),
        
        setError: (error) => set({ error }),
        
        // 异步操作
        loadSessions: async () => {
            try {
                set({ isLoading: true });
                const response = await chatAPI.getSessions();
                set({ sessions: response.data.sessions });
            } catch (error) {
                set({ error: error.message });
            } finally {
                set({ isLoading: false });
            }
        },
        
        createSession: async (sessionData = {}) => {
            try {
                set({ isLoading: true });
                const response = await chatAPI.createSession(sessionData);
                const newSession = response.data;
                
                set((state) => ({
                    sessions: [newSession, ...state.sessions],
                    currentSession: newSession
                }));
                
                return newSession;
            } catch (error) {
                set({ error: error.message });
                return null;
            } finally {
                set({ isLoading: false });
            }
        },
        
        loadMessages: async (sessionId) => {
            try {
                set({ isLoading: true });
                const response = await chatAPI.getMessages(sessionId);
                set({ messages: response.data.messages });
            } catch (error) {
                set({ error: error.message });
            } finally {
                set({ isLoading: false });
            }
        },
        
        sendMessage: async (sessionId, content, metadata = {}) => {
            try {
                // 立即添加用户消息
                const userMessage = {
                    message_id: `temp_${Date.now()}`,
                    session_id: sessionId,
                    role: 'user',
                    content,
                    content_type: 'text',
                    metadata,
                    status: 'completed',
                    created_at: new Date().toISOString()
                };
                
                get().addMessage(userMessage);
                
                // 发送到服务器
                const response = await chatAPI.sendMessage(sessionId, {
                    content,
                    content_type: 'text',
                    metadata
                });
                
                // 更新用户消息ID
                get().updateMessage(userMessage.message_id, {
                    message_id: response.data.message_id
                });
                
                // 如果有立即回复，添加助手消息
                if (response.data.assistant_response) {
                    get().addMessage(response.data.assistant_response);
                }
                
            } catch (error) {
                set({ error: error.message });
            }
        },
        
        // WebSocket处理
        handleStreamMessage: (streamData) => {
            const { type, data } = streamData;
            
            switch (type) {
                case 'stream_start':
                    set({
                        streamingMessage: {
                            message_id: data.message_id,
                            role: 'assistant',
                            content: '',
                            content_type: 'markdown',
                            status: 'streaming'
                        }
                    });
                    break;
                    
                case 'content_chunk':
                    set((state) => ({
                        streamingMessage: state.streamingMessage ? {
                            ...state.streamingMessage,
                            content: state.streamingMessage.content + data.content
                        } : null
                    }));
                    break;
                    
                case 'reference_chunk':
                    set((state) => ({
                        streamingMessage: state.streamingMessage ? {
                            ...state.streamingMessage,
                            references: [
                                ...(state.streamingMessage.references || []),
                                data.reference
                            ]
                        } : null
                    }));
                    break;
                    
                case 'stream_end':
                    const finalMessage = get().streamingMessage;
                    if (finalMessage) {
                        get().addMessage({
                            ...finalMessage,
                            ...data,
                            status: 'completed'
                        });
                    }
                    set({ streamingMessage: null });
                    break;
                    
                case 'error':
                    set({ 
                        error: data.error_message,
                        streamingMessage: null 
                    });
                    break;
            }
        }
    }))
);
```

## 🔌 WebSocket Hook

```javascript
// hooks/useWebSocket.js
import { useEffect, useRef } from 'react';
import { useChatStore } from '../stores/chatStore';

export const useWebSocket = () => {
    const wsRef = useRef(null);
    const { handleStreamMessage } = useChatStore();
    
    const connect = (sessionId) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }
        
        const token = localStorage.getItem('auth_token');
        const wsUrl = `ws://localhost:8000/api/v1/chat/sessions/${sessionId}/stream?token=${token}`;
        
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
            console.log('WebSocket connected');
            useChatStore.setState({ isConnected: true });
        };
        
        wsRef.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleStreamMessage(data);
            } catch (error) {
                console.error('WebSocket message parse error:', error);
            }
        };
        
        wsRef.current.onclose = () => {
            console.log('WebSocket disconnected');
            useChatStore.setState({ isConnected: false });
        };
        
        wsRef.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            useChatStore.setState({ 
                isConnected: false,
                error: 'WebSocket连接失败'
            });
        };
    };
    
    const disconnect = () => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
            useChatStore.setState({ isConnected: false });
        }
    };
    
    const sendMessage = (message) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        }
    };
    
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, []);
    
    return {
        connect,
        disconnect,
        sendMessage,
        isConnected: useChatStore((state) => state.isConnected)
    };
};
```

## 🎨 样式设计 (CSS/Less)

```less
// styles/chat.less
.chat-interface {
    height: 100vh;
    
    .chat-sidebar {
        background: #f5f5f5;
        border-right: 1px solid #d9d9d9;
    }
    
    .chat-main {
        display: flex;
        flex-direction: column;
        height: 100%;
        
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }
    }
    
    .reference-panel {
        background: #fafafa;
        border-left: 1px solid #d9d9d9;
    }
}

.message-list {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    
    .message-item {
        display: flex;
        margin-bottom: 16px;
        
        &.user {
            flex-direction: row-reverse;
            
            .message-bubble {
                margin-right: 0;
                margin-left: 48px;
                background: #1890ff;
                color: white;
            }
        }
        
        &.assistant {
            .message-bubble {
                margin-left: 48px;
                margin-right: 48px;
                background: white;
                border: 1px solid #d9d9d9;
            }
        }
    }
    
    .message-avatar {
        flex-shrink: 0;
        margin-top: 4px;
        
        &.user-avatar {
            background: #1890ff;
        }
        
        &.assistant-avatar {
            background: #52c41a;
        }
    }
}

.message-bubble {
    max-width: 80%;
    border-radius: 8px;
    
    .message-content {
        margin-bottom: 8px;
        
        .message-text {
            line-height: 1.6;
            word-wrap: break-word;
        }
        
        // Markdown样式
        h1, h2, h3, h4, h5, h6 {
            margin: 16px 0 8px 0;
            font-weight: 600;
        }
        
        p {
            margin: 8px 0;
            line-height: 1.6;
        }
        
        code {
            background: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }
        
        pre {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            
            code {
                background: none;
                padding: 0;
            }
        }
        
        blockquote {
            border-left: 4px solid #d9d9d9;
            padding-left: 16px;
            margin: 16px 0;
            color: #666;
        }
        
        ul, ol {
            padding-left: 24px;
            margin: 8px 0;
        }
    }
    
    .message-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: #999;
        
        .message-time {
            font-size: 11px;
        }
        
        .message-stats {
            display: flex;
            gap: 4px;
        }
        
        .message-actions {
            opacity: 0;
            transition: opacity 0.2s;
        }
    }
    
    &:hover .message-actions {
        opacity: 1;
    }
    
    &.streaming {
        border: 1px solid #1890ff;
        
        .streaming-content {
            position: relative;
            
            .typing-cursor {
                opacity: 0;
                transition: opacity 0.1s;
                
                &.visible {
                    opacity: 1;
                }
            }
        }
        
        .streaming-status {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 8px;
            font-size: 12px;
            color: #1890ff;
            
            .typing-dots {
                display: flex;
                gap: 2px;
                
                span {
                    width: 4px;
                    height: 4px;
                    border-radius: 50%;
                    background: #1890ff;
                    animation: typing 1.4s infinite ease-in-out;
                    
                    &:nth-child(1) { animation-delay: -0.32s; }
                    &:nth-child(2) { animation-delay: -0.16s; }
                }
            }
        }
    }
}

@keyframes typing {
    0%, 80%, 100% {
        transform: scale(0);
        opacity: 0.5;
    }
    40% {
        transform: scale(1);
        opacity: 1;
    }
}

.message-input-container {
    padding: 16px;
    border-top: 1px solid #d9d9d9;
    background: white;
    
    .input-wrapper {
        display: flex;
        align-items: flex-end;
        gap: 8px;
        
        .message-textarea {
            flex: 1;
            resize: none;
            border: 1px solid #d9d9d9;
            border-radius: 6px;
            padding: 8px 12px;
            
            &:focus {
                border-color: #1890ff;
                box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
            }
        }
        
        .input-actions {
            display: flex;
            align-items: flex-end;
            
            .send-button {
                height: auto;
                padding: 8px 16px;
            }
        }
    }
    
    .input-hint {
        margin-top: 4px;
        font-size: 11px;
        color: #999;
        text-align: center;
    }
}

// 响应式设计
@media (max-width: 768px) {
    .chat-interface {
        .chat-sidebar {
            position: fixed;
            z-index: 1000;
            height: 100%;
        }
        
        .reference-panel {
            display: none;
        }
        
        .message-item {
            .message-bubble {
                max-width: 90%;
                margin-left: 40px !important;
                margin-right: 8px !important;
            }
        }
    }
}
```

这个前端设计方案提供了完整的React组件架构、状态管理、WebSocket集成和样式设计，为用户提供现代化的聊天体验。


