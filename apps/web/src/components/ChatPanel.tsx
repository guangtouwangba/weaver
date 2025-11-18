import React, { useState, useEffect } from 'react';
import { Card, message as antdMessage } from 'antd';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import QuickQuestions from './QuickQuestions';
import SourceDetailModal from './SourceDetailModal';
import type { Message, SourceDocument } from './MessageItem';
import { chatApi } from '../api/chat';
import { messageApi } from '../api/conversation';
import { v4 as uuidv4 } from 'uuid';
import { colors, spacing, radius, shadows, typography } from '../theme/tokens';

interface ChatPanelProps {
  topicId: string;
  selectedDocIds: string[];
  conversationId?: string;  // Optional: continue existing conversation
  onConversationChange?: (conversationId: string) => void;  // Notify parent of conversation ID changes
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  topicId,
  selectedDocIds,
  conversationId: initialConversationId,
  onConversationChange,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(initialConversationId);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [selectedSource, setSelectedSource] = useState<SourceDocument | null>(null);
  const [sourceModalVisible, setSourceModalVisible] = useState(false);

  // Sync conversationId when prop changes (for conversation switching)
  useEffect(() => {
    console.log('🔄 ChatPanel conversationId prop changed:', initialConversationId);
    setConversationId(initialConversationId);
  }, [initialConversationId]);

  // Load conversation history when conversationId changes
  useEffect(() => {
    const loadHistory = async () => {
      if (!conversationId) {
        // No conversation, show welcome message
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
        return;
      }

      // Load history from backend
      setLoadingHistory(true);
      try {
        const response = await messageApi.listByConversation(conversationId);
        const historyMessages: Message[] = response.messages.map((msg) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: msg.created_at,
          sources: msg.sources ? JSON.parse(msg.sources[0] || '[]') : undefined,
        }));
        setMessages(historyMessages);
        console.log(`📚 加载了 ${historyMessages.length} 条历史消息`);
      } catch (error) {
        console.error('Failed to load conversation history:', error);
        antdMessage.error('加载对话历史失败');
      } finally {
        setLoadingHistory(false);
      }
    };

    loadHistory();
  }, [conversationId]);

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

    // 创建一个空的助手消息用于streaming
    const assistantMessageId = uuidv4();
    const streamingMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };
    
    setMessages((prev) => [...prev, streamingMessage]);

    try {
      // 使用streaming API
      console.log('Sending streaming query with:', {
        content,
        documentIds: selectedDocIds,
        conversationId,
        topicId,
      });
      
      let sources: SourceDocument[] = [];
      let fullAnswer = '';
      
      await chatApi.askStream(
        content,
        selectedDocIds,
        4,  // topK
        conversationId,  // Continue existing conversation
        topicId,  // Create new conversation in this topic
        {
          onProgress: (message, stage) => {
            console.log(`📊 Progress [${stage}]: ${message}`);
            // 可以显示进度指示器
          },
          onSources: (receivedSources, count) => {
            console.log(`📚 Received ${count} sources`);
            sources = receivedSources;
            // 更新消息以显示sources
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, sources: sources.map(s => ({ content: s.content, metadata: s.metadata || {} })) }
                  : msg
              )
            );
          },
          onChunk: (chunk) => {
            // 追加文本块
            fullAnswer += chunk;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: fullAnswer }
                  : msg
              )
            );
          },
          onDone: (returnedConversationId) => {
            console.log(`✅ Streaming complete, conversation: ${returnedConversationId}`);
            
            // Update conversation ID if returned (for new conversations)
            if (returnedConversationId && returnedConversationId !== 'new' && returnedConversationId !== conversationId) {
              console.log(`🆕 新对话创建: ${returnedConversationId}`);
              setConversationId(returnedConversationId);
              onConversationChange?.(returnedConversationId);
            }
            
            setLoading(false);
          },
          onError: (error) => {
            console.error('Streaming error:', error);
            
            // 更新为错误消息
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: `抱歉，处理您的问题时出现了错误：\n\n${error}\n\n请稍后重试。` }
                  : msg
              )
            );
            
            antdMessage.error('发送消息失败，请重试');
            setLoading(false);
          },
        }
      );
    } catch (error: any) {
      console.error('Chat error:', error);
      
      // 更新为错误消息
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: `抱歉，处理您的问题时出现了错误：\n\n${error.message || '未知错误'}\n\n请稍后重试。` }
            : msg
        )
      );
      
      antdMessage.error('发送消息失败，请重试');
      setLoading(false);
    }
  };

  const handleQuickQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleSourceClick = (source: SourceDocument) => {
    console.log('Source clicked:', source);
    setSelectedSource(source);
    setSourceModalVisible(true);
  };

  return (
    <>
    <Card
      title="💬 智能助手"
      style={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        borderRadius: radius.md,
        boxShadow: shadows.soft,
        border: `1px solid ${colors.border.subtle}`,
      }}
      headStyle={{
        fontSize: `${typography.subtitle.size}px`,
        fontWeight: typography.subtitle.weight,
        color: colors.text.primary,
      }}
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
        loading={loading || loadingHistory}
        onSourceClick={handleSourceClick}
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

    <SourceDetailModal
      visible={sourceModalVisible}
      source={selectedSource}
      onClose={() => setSourceModalVisible(false)}
    />
    </>
  );
};

export default ChatPanel;

