import React, { useState, KeyboardEvent } from 'react';
import { Input, Button, Space, Tooltip } from 'antd';
import { SendOutlined, PaperClipOutlined, AudioOutlined } from '@ant-design/icons';

const { TextArea } = Input;

interface ChatInputProps {
  onSend: (message: string) => void;
  loading?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  loading = false,
  placeholder = '请输入问题...',
}) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !loading) {
      onSend(trimmedMessage);
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter 或 Cmd+Enter 发送
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        padding: '16px',
        background: '#fff',
        borderTop: '1px solid #f0f0f0',
      }}
    >
      <Space.Compact style={{ width: '100%' }} direction="vertical" size={8}>
        <TextArea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoSize={{ minRows: 2, maxRows: 6 }}
          disabled={loading}
          style={{ resize: 'none' }}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space size={8}>
            <Tooltip title="上传文件（即将推出）">
              <Button
                type="text"
                icon={<PaperClipOutlined />}
                disabled
                size="small"
              />
            </Tooltip>
            <Tooltip title="语音输入（即将推出）">
              <Button
                type="text"
                icon={<AudioOutlined />}
                disabled
                size="small"
              />
            </Tooltip>
          </Space>

          <Space size={8}>
            <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
              Ctrl+Enter 发送
            </span>
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
              disabled={!message.trim() || loading}
            >
              发送
            </Button>
          </Space>
        </div>
      </Space.Compact>
    </div>
  );
};

export default ChatInput;

