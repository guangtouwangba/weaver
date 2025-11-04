/**
 * SourceDetailModal - Display detailed information about a source document
 */

import React from 'react';
import { Modal, Typography, Space, Tag, Divider } from 'antd';
import { FileTextOutlined, NumberOutlined, FolderOpenOutlined } from '@ant-design/icons';
import type { SourceDocument } from './MessageItem';

const { Title, Paragraph, Text } = Typography;

interface SourceDetailModalProps {
  visible: boolean;
  source: SourceDocument | null;
  onClose: () => void;
}

const SourceDetailModal: React.FC<SourceDetailModalProps> = ({
  visible,
  source,
  onClose,
}) => {
  if (!source) {
    return null;
  }

  const { content, metadata } = source;
  const { source: sourceName, page, document_id, filename } = metadata || {};

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      title={
        <Space>
          <FileTextOutlined style={{ color: '#1890ff' }} />
          <span>源文档引用</span>
        </Space>
      }
    >
      {/* Metadata Section */}
      <Space direction="vertical" size={12} style={{ width: '100%', marginBottom: 16 }}>
        {(sourceName || filename) && (
          <div>
            <Space size={8}>
              <FolderOpenOutlined style={{ color: '#8c8c8c' }} />
              <Text strong>文件名：</Text>
              <Tag color="blue">{sourceName || filename}</Tag>
            </Space>
          </div>
        )}

        {page !== undefined && (
          <div>
            <Space size={8}>
              <NumberOutlined style={{ color: '#8c8c8c' }} />
              <Text strong>页码：</Text>
              <Tag color="green">第 {page} 页</Tag>
            </Space>
          </div>
        )}

        {document_id && (
          <div>
            <Space size={8}>
              <Text strong>文档ID：</Text>
              <Text code copyable style={{ fontSize: 12 }}>
                {document_id}
              </Text>
            </Space>
          </div>
        )}
      </Space>

      <Divider style={{ margin: '12px 0' }} />

      {/* Content Section */}
      <div>
        <Title level={5} style={{ marginBottom: 12 }}>
          引用内容
        </Title>
        <div
          style={{
            background: '#fafafa',
            padding: '16px',
            borderRadius: '8px',
            maxHeight: '400px',
            overflowY: 'auto',
            border: '1px solid #e8e8e8',
          }}
        >
          <Paragraph
            style={{
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              lineHeight: '1.8',
            }}
          >
            {content}
          </Paragraph>
        </div>
        
        <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
          💡 此内容是AI回答的参考来源
        </Text>
      </div>
    </Modal>
  );
};

export default SourceDetailModal;

