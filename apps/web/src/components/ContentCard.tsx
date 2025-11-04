/**
 * Content card component
 */

import React from 'react';
import { Card, Tag, Space, Typography, Button, Slider, Tooltip, message } from 'antd';
import { FileTextOutlined, LinkOutlined, BookOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { TopicContent, ContentStatus, CONTENT_STATUS_LABELS, CONTENT_STATUS_COLORS, ContentSource, CONTENT_SOURCE_LABELS, ProcessingStatus, PROCESSING_STATUS_LABELS, PROCESSING_STATUS_COLORS } from '../types/content';
import { contentApi } from '../api/content';

const { Text, Paragraph } = Typography;

interface ContentCardProps {
  content: TopicContent;
  topicId: string;
  onUpdate: () => void;
  onDelete: () => void;
}

const ContentCard: React.FC<ContentCardProps> = ({ content, topicId, onUpdate, onDelete }) => {
  const [updating, setUpdating] = React.useState(false);

  const handleStatusChange = async (newStatus: ContentStatus) => {
    try {
      setUpdating(true);
      await contentApi.update(topicId, content.id, { status: newStatus });
      message.success('状态已更新');
      onUpdate();
    } catch (error) {
      message.error('更新状态失败');
      console.error('Failed to update status:', error);
    } finally {
      setUpdating(false);
    }
  };

  const handleUnderstandingChange = async (value: number) => {
    try {
      await contentApi.update(topicId, content.id, { understanding_level: value });
      onUpdate();
    } catch (error) {
      message.error('更新理解度失败');
      console.error('Failed to update understanding:', error);
    }
  };

  const getSourceIcon = () => {
    switch (content.source_type) {
      case ContentSource.FILE_UPLOAD:
        return <FileTextOutlined />;
      case ContentSource.URL:
        return <LinkOutlined />;
      case ContentSource.EXISTING_DOC:
        return <BookOutlined />;
      default:
        return <FileTextOutlined />;
    }
  };

  const statusOptions = [
    { value: ContentStatus.PENDING, label: CONTENT_STATUS_LABELS[ContentStatus.PENDING] },
    { value: ContentStatus.READING, label: CONTENT_STATUS_LABELS[ContentStatus.READING] },
    { value: ContentStatus.UNDERSTOOD, label: CONTENT_STATUS_LABELS[ContentStatus.UNDERSTOOD] },
    { value: ContentStatus.QUESTIONED, label: CONTENT_STATUS_LABELS[ContentStatus.QUESTIONED] },
    { value: ContentStatus.PRACTICED, label: CONTENT_STATUS_LABELS[ContentStatus.PRACTICED] },
  ];

  return (
    <Card
      size="small"
      style={{ marginBottom: 16 }}
      actions={[
        <Tooltip title="编辑">
          <Button type="text" icon={<EditOutlined />} size="small">
            编辑
          </Button>
        </Tooltip>,
        <Tooltip title="删除">
          <Button type="text" danger icon={<DeleteOutlined />} size="small" onClick={onDelete}>
            删除
          </Button>
        </Tooltip>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {/* Title and Source */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Space>
            {getSourceIcon()}
            <Text strong>{content.title}</Text>
          </Space>
          <Space>
            <Tag color={PROCESSING_STATUS_COLORS[content.processing_status]}>
              {PROCESSING_STATUS_LABELS[content.processing_status]}
            </Tag>
            <Tag color={CONTENT_STATUS_COLORS[content.status]}>
              {CONTENT_STATUS_LABELS[content.status]}
            </Tag>
          </Space>
        </div>
        
        {/* Processing Error (if any) */}
        {content.processing_status === ProcessingStatus.FAILED && content.processing_error && (
          <div style={{ padding: '8px', backgroundColor: '#fff1f0', border: '1px solid #ffccc7', borderRadius: '4px' }}>
            <Text type="danger" style={{ fontSize: 12 }}>
              处理失败: {content.processing_error}
            </Text>
          </div>
        )}

        {/* Description */}
        {content.description && (
          <Paragraph type="secondary" ellipsis={{ rows: 2 }} style={{ marginBottom: 8 }}>
            {content.description}
          </Paragraph>
        )}

        {/* Metadata */}
        <Space size="small" wrap>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {dayjs(content.added_at).format('YYYY-MM-DD HH:mm')}
          </Text>
          {content.author && (
            <Tag color="default" style={{ fontSize: 11 }}>
              {content.author}
            </Tag>
          )}
          {content.tags.map((tag) => (
            <Tag key={tag} color="blue" style={{ fontSize: 11 }}>
              {tag}
            </Tag>
          ))}
        </Space>

        {/* Understanding Level Slider */}
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            理解程度: {content.understanding_level}%
          </Text>
          <Slider
            value={content.understanding_level}
            onChange={handleUnderstandingChange}
            tooltip={{ formatter: (value) => `${value}%` }}
            marks={{
              0: '0%',
              50: '50%',
              100: '100%',
            }}
          />
        </div>

        {/* Status Buttons */}
        <Space wrap size="small">
          {statusOptions.map((option) => (
            <Button
              key={option.value}
              size="small"
              type={content.status === option.value ? 'primary' : 'default'}
              loading={updating}
              onClick={() => handleStatusChange(option.value)}
              icon={content.status === option.value ? <CheckCircleOutlined /> : null}
            >
              {option.label}
            </Button>
          ))}
        </Space>
      </Space>
    </Card>
  );
};

export default ContentCard;

