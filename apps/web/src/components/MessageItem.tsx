import React from 'react';
import { Card, Typography, Tag, Space } from 'antd';
import { UserOutlined, RobotOutlined, FileTextOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text, Paragraph } = Typography;

export interface SourceDocument {
  content: string;
  metadata: {
    source?: string;
    page?: number;
    document_id?: string;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: SourceDocument[];
}

interface MessageItemProps {
  message: Message;
  onSourceClick?: (source: SourceDocument) => void;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, onSourceClick }) => {
  const isUser = message.role === 'user';

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
      }}
    >
      <div style={{ maxWidth: '80%' }}>
        <Space align="start" size={8}>
          {!isUser && (
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: '#1890ff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <RobotOutlined style={{ color: '#fff', fontSize: '18px' }} />
            </div>
          )}

          <Card
            size="small"
            style={{
              background: isUser ? '#1890ff' : '#f5f5f5',
              border: 'none',
              borderRadius: '12px',
            }}
            bodyStyle={{ padding: '12px 16px' }}
          >
            <Paragraph
              style={{
                margin: 0,
                color: isUser ? '#fff' : '#000',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {message.content}
            </Paragraph>

            {/* 引用来源 */}
            {!isUser && message.sources && message.sources.length > 0 && (
              <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e8e8e8' }}>
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                  {message.sources.map((source, index) => (
                    <div
                      key={index}
                      onClick={() => onSourceClick?.(source)}
                      style={{
                        cursor: onSourceClick ? 'pointer' : 'default',
                        padding: '4px 8px',
                        background: '#fff',
                        borderRadius: '6px',
                        transition: 'all 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        if (onSourceClick) {
                          e.currentTarget.style.background = '#e6f7ff';
                        }
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#fff';
                      }}
                    >
                      <Space size={4}>
                        <FileTextOutlined style={{ fontSize: '12px', color: '#8c8c8c' }} />
                        <Text style={{ fontSize: '12px', color: '#595959' }}>
                          {source.metadata?.source || source.metadata?.filename || '未知来源'}
                          {source.metadata?.page && ` - 第${source.metadata.page}页`}
                        </Text>
                      </Space>
                    </div>
                  ))}
                </Space>
              </div>
            )}

            {/* 时间戳 */}
            <Text
              type="secondary"
              style={{
                fontSize: '11px',
                display: 'block',
                marginTop: '8px',
                color: isUser ? 'rgba(255,255,255,0.7)' : '#8c8c8c',
              }}
            >
              {dayjs(message.timestamp).format('HH:mm:ss')}
            </Text>
          </Card>

          {isUser && (
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: '#52c41a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              <UserOutlined style={{ color: '#fff', fontSize: '18px' }} />
            </div>
          )}
        </Space>
      </div>
    </div>
  );
};

export default MessageItem;

