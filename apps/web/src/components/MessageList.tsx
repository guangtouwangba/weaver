import React, { useEffect, useRef } from 'react';
import { Empty, Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import MessageItem, { Message, SourceDocument } from './MessageItem';

interface MessageListProps {
  messages: Message[];
  loading?: boolean;
  onSourceClick?: (source: SourceDocument) => void;
}

const MessageList: React.FC<MessageListProps> = ({ messages, loading, onSourceClick }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        background: '#fff',
      }}
    >
      {messages.length === 0 && !loading ? (
        <div
          style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Empty
            description="开始对话，向AI提问吧！"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageItem
              key={message.id}
              message={message}
              onSourceClick={onSourceClick}
            />
          ))}

          {/* Loading indicator */}
          {loading && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '16px',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: '#1890ff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginRight: '8px',
                }}
              >
                <LoadingOutlined style={{ color: '#fff', fontSize: '18px' }} />
              </div>
              <div
                style={{
                  padding: '12px 16px',
                  background: '#f5f5f5',
                  borderRadius: '12px',
                }}
              >
                <Spin size="small" /> <span style={{ marginLeft: '8px' }}>AI思考中...</span>
              </div>
            </div>
          )}

          {/* 滚动锚点 */}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
};

export default MessageList;

