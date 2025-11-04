import React, { useState, useEffect } from 'react';
import { Card, message as antdMessage } from 'antd';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import QuickQuestions from './QuickQuestions';
import type { Message, SourceDocument } from './MessageItem';
import { chatApi } from '../api/chat';
import { v4 as uuidv4 } from 'uuid';

interface ChatPanelProps {
  topicId: string;
  selectedDocIds: string[];
  onSourceClick?: (source: SourceDocument) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ topicId, selectedDocIds, onSourceClick }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  // 欢迎消息
  useEffect(() => {
    const welcomeMessage: Message = {
      id: uuidv4(),
      role: 'assistant',
      content: `你好！👋 我是你的智能学习助手。

我可以帮你：
- 📚 总结文档的核心内容
- 💡 解释关键概念
- 🔍 查找特定信息
- 🎯 提供学习建议

请选择左侧的文档范围，然后向我提问吧！`,
      timestamp: new Date().toISOString(),
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleSendMessage = async (content: string) => {
    // 检查是否选择了文档
    if (selectedDocIds.length === 0) {
      antdMessage.warning('请先选择要对话的文档范围');
      return;
    }

    // 添加用户消息
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      // 调用后端API
      console.log('Sending query with document IDs:', selectedDocIds);
      const response = await chatApi.ask(content, selectedDocIds);

      // 添加AI回复
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources.map((doc) => ({
          content: doc.content,  // 修改：使用 content 字段
          metadata: doc.metadata || {},  // 修改：处理可能的 null
        })),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);
      
      // 错误消息
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: `抱歉，处理您的问题时出现了错误：\n\n${
          error.response?.data?.detail || error.message || '未知错误'
        }\n\n请稍后重试。`,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      antdMessage.error('发送消息失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuestion = (question: string) => {
    handleSendMessage(question);
  };

  return (
    <Card
      title="💬 智能助手"
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      bodyStyle={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: 0,
        overflow: 'hidden',
      }}
    >
      <MessageList
        messages={messages}
        loading={loading}
        onSourceClick={onSourceClick}
      />

      <QuickQuestions
        onQuestionClick={handleQuickQuestion}
        disabled={loading || selectedDocIds.length === 0}
      />

      <ChatInput
        onSend={handleSendMessage}
        loading={loading}
        placeholder={
          selectedDocIds.length === 0
            ? '请先选择文档范围...'
            : '请输入问题...'
        }
      />
    </Card>
  );
};

export default ChatPanel;

