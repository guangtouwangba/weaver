/**
 * ConversationList - Display and manage conversations for a topic
 */

import React, { useState, useEffect } from 'react';
import { List, Card, Button, Empty, Tag, Typography, Space, Spin, message as antdMessage, Popconfirm, Input } from 'antd';
import { PlusOutlined, MessageOutlined, DeleteOutlined, ClockCircleOutlined, EditOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { conversationApi, type Conversation } from '../api/conversation';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import { colors, spacing, radius, shadows, typography } from '../theme/tokens';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const { Text } = Typography;

interface ConversationListProps {
  topicId: string;
  selectedConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onNewConversation: () => void;
}

const ConversationList: React.FC<ConversationListProps> = ({
  topicId,
  selectedConversationId,
  onConversationSelect,
  onNewConversation,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const loadConversations = async () => {
    setLoading(true);
    try {
      const response = await conversationApi.listByTopic(topicId);
      setConversations(response.conversations);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to load conversations:', error);
      antdMessage.error('加载对话列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [topicId]);

  const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();  // Prevent triggering the parent click event
    
    try {
      await conversationApi.delete(conversationId);
      antdMessage.success('对话已删除');
      loadConversations();
      
      // If deleted conversation was selected, trigger new conversation
      if (conversationId === selectedConversationId) {
        onNewConversation();
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      antdMessage.error('删除对话失败');
    }
  };

  const handleStartEdit = (conversation: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conversation.id);
    setEditingTitle(conversation.title || '');
  };

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
    setEditingTitle('');
  };

  const handleSaveEdit = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!editingTitle.trim()) {
      antdMessage.warning('对话标题不能为空');
      return;
    }

    try {
      await conversationApi.update(conversationId, { title: editingTitle.trim() });
      antdMessage.success('对话标题已更新');
      setEditingId(null);
      setEditingTitle('');
      loadConversations();
    } catch (error) {
      console.error('Failed to update conversation:', error);
      antdMessage.error('更新对话标题失败');
    }
  };

  const formatTime = (timestamp: string | null) => {
    if (!timestamp) return '';
    return dayjs(timestamp).fromNow();
  };

  return (
    <Card
      title={
        <Space>
          <MessageOutlined />
          <span>对话历史</span>
          <Tag color="blue">{total}</Tag>
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={onNewConversation}
          size="small"
        >
          新对话
        </Button>
      }
      bodyStyle={{ padding: 0 }}
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin tip="加载中..." />
          </div>
        ) : conversations.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="还没有对话记录"
            style={{ marginTop: 50 }}
          >
            <Button type="primary" icon={<PlusOutlined />} onClick={onNewConversation}>
              开始第一个对话
            </Button>
          </Empty>
        ) : (
          <List
            dataSource={conversations}
            renderItem={(conversation) => {
              const isSelected = conversation.id === selectedConversationId;
              
              return (
                <List.Item
                  key={conversation.id}
                  onClick={() => onConversationSelect(conversation.id)}
                  style={{
                    cursor: 'pointer',
                    padding: '12px 16px',
                    backgroundColor: isSelected ? '#e6f7ff' : 'transparent',
                    borderLeft: isSelected ? '3px solid #1890ff' : '3px solid transparent',
                    transition: 'all 0.3s',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.backgroundColor = '#fafafa';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  <List.Item.Meta
                    title={
                      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                        {editingId === conversation.id ? (
                          // Editing mode
                          <Input
                            size="small"
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onClick={(e) => e.stopPropagation()}
                            onPressEnter={(e) => handleSaveEdit(conversation.id, e as any)}
                            autoFocus
                            style={{ flex: 1, marginRight: 4 }}
                          />
                        ) : (
                          // Display mode
                          <Text
                            strong={isSelected}
                            ellipsis
                            style={{
                              maxWidth: '150px',
                              color: isSelected ? '#1890ff' : undefined,
                            }}
                          >
                            {conversation.title || '未命名对话'}
                          </Text>
                        )}
                        
                        <Space size={0}>
                          {editingId === conversation.id ? (
                            <>
                              <Button
                                type="text"
                                icon={<CheckOutlined />}
                                size="small"
                                onClick={(e) => handleSaveEdit(conversation.id, e)}
                                style={{ color: '#52c41a' }}
                              />
                              <Button
                                type="text"
                                icon={<CloseOutlined />}
                                size="small"
                                onClick={handleCancelEdit}
                              />
                            </>
                          ) : (
                            <>
                              <Button
                                type="text"
                                icon={<EditOutlined />}
                                size="small"
                                onClick={(e) => handleStartEdit(conversation, e)}
                              />
                              <Popconfirm
                                title="确定要删除这个对话吗？"
                                description="此操作将删除所有对话消息，且无法恢复。"
                                onConfirm={(e) => handleDelete(conversation.id, e as any)}
                                onCancel={(e) => e?.stopPropagation()}
                                okText="删除"
                                cancelText="取消"
                                okType="danger"
                              >
                                <Button
                                  type="text"
                                  icon={<DeleteOutlined />}
                                  size="small"
                                  danger
                                  onClick={(e) => e.stopPropagation()}
                                />
                              </Popconfirm>
                            </>
                          )}
                        </Space>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size={0} style={{ width: '100%' }}>
                        <Space size="small">
                          <MessageOutlined style={{ fontSize: 12 }} />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {conversation.message_count} 条消息
                          </Text>
                        </Space>
                        {conversation.last_message_at && (
                          <Space size="small">
                            <ClockCircleOutlined style={{ fontSize: 12 }} />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {formatTime(conversation.last_message_at)}
                            </Text>
                          </Space>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              );
            }}
          />
        )}
      </div>
    </Card>
  );
};

export default ConversationList;

