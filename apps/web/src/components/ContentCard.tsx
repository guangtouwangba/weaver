/**
 * Content card component
 */

import React from 'react';
import { Card, Tag, Space, Typography, Button, Slider, Tooltip, message } from 'antd';
import { FileTextOutlined, LinkOutlined, BookOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { TopicContent, ContentStatus, CONTENT_STATUS_LABELS, CONTENT_STATUS_COLORS, ContentSource, CONTENT_SOURCE_LABELS, ProcessingStatus, PROCESSING_STATUS_LABELS, PROCESSING_STATUS_COLORS } from '../types/content';
import { contentApi } from '../api/content';
import { colors, spacing, radius, shadows, typography, chipVariants } from '../theme/tokens';

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
      style={{ 
        marginBottom: spacing.md,
        borderRadius: radius.md,
        boxShadow: shadows.soft,
        border: `1px solid ${colors.border.subtle}`,
      }}
      bodyStyle={{ padding: spacing.md }}
      actions={[
        <Tooltip title="编辑">
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            size="small"
            style={{
              borderRadius: radius.pill,
            }}
          >
            编辑
          </Button>
        </Tooltip>,
        <Tooltip title="删除">
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />} 
            size="small" 
            onClick={onDelete}
            style={{
              borderRadius: radius.pill,
            }}
          >
            删除
          </Button>
        </Tooltip>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {/* Title and Source */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: `${spacing.sm}px` }}>
          <Space>
            {getSourceIcon()}
            <Text strong style={{
              fontSize: `${typography.body.size}px`,
              fontWeight: typography.bodyBold.weight,
              color: colors.text.primary,
            }}>
              {content.title}
            </Text>
          </Space>
          <Space size={spacing.xxs}>
            <span style={{
              padding: `${spacing.xxs}px ${spacing.xs}px`,
              background: PROCESSING_STATUS_COLORS[content.processing_status] === 'green' ? chipVariants.success.background : 
                         PROCESSING_STATUS_COLORS[content.processing_status] === 'red' ? chipVariants.error.background :
                         PROCESSING_STATUS_COLORS[content.processing_status] === 'orange' ? chipVariants.warning.background : chipVariants.info.background,
              color: PROCESSING_STATUS_COLORS[content.processing_status] === 'green' ? chipVariants.success.color : 
                     PROCESSING_STATUS_COLORS[content.processing_status] === 'red' ? chipVariants.error.color :
                     PROCESSING_STATUS_COLORS[content.processing_status] === 'orange' ? colors.text.onWarning : chipVariants.info.color,
              borderRadius: `${radius.pill}px`,
              fontSize: `${typography.label.size}px`,
              fontWeight: typography.label.weight,
              whiteSpace: 'nowrap',
            }}>
              {PROCESSING_STATUS_LABELS[content.processing_status]}
            </span>
            <span style={{
              padding: `${spacing.xxs}px ${spacing.xs}px`,
              background: CONTENT_STATUS_COLORS[content.status] === 'green' ? chipVariants.success.background : chipVariants.active.background,
              color: CONTENT_STATUS_COLORS[content.status] === 'green' ? chipVariants.success.color : chipVariants.active.color,
              borderRadius: `${radius.pill}px`,
              fontSize: `${typography.label.size}px`,
              fontWeight: typography.label.weight,
              whiteSpace: 'nowrap',
            }}>
              {CONTENT_STATUS_LABELS[content.status]}
            </span>
          </Space>
        </div>
        
        {/* Processing Error (if any) */}
        {content.processing_status === ProcessingStatus.FAILED && content.processing_error && (
          <div style={{ 
            padding: `${spacing.xs}px`, 
            backgroundColor: chipVariants.error.background, 
            border: `1px solid ${colors.red.strong}`, 
            borderRadius: `${radius.xs}px`,
          }}>
            <Text type="danger" style={{ 
              fontSize: `${typography.caption.size}px`,
              color: colors.red.strong,
            }}>
              处理失败: {content.processing_error}
            </Text>
          </div>
        )}

        {/* Description */}
        {content.description && (
          <Paragraph 
            type="secondary" 
            ellipsis={{ rows: 2 }} 
            style={{ 
              marginBottom: `${spacing.xs}px`,
              fontSize: `${typography.body.size}px`,
              color: colors.text.secondary,
            }}
          >
            {content.description}
          </Paragraph>
        )}

        {/* Metadata */}
        <Space size="small" wrap>
          <Text type="secondary" style={{ 
            fontSize: `${typography.caption.size}px`,
            color: colors.text.muted,
          }}>
            {dayjs(content.added_at).format('YYYY-MM-DD HH:mm')}
          </Text>
          {content.author && (
            <span style={{
              padding: `${spacing.xxs}px ${spacing.xs}px`,
              background: colors.surface.subtle,
              color: colors.text.secondary,
              borderRadius: `${radius.pill}px`,
              fontSize: `${typography.label.size}px`,
            }}>
              {content.author}
            </span>
          )}
          {content.tags.map((tag) => (
            <span 
              key={tag}
              style={{
                padding: `${spacing.xxs}px ${spacing.xs}px`,
                background: chipVariants.info.background,
                color: chipVariants.info.color,
                borderRadius: `${radius.pill}px`,
                fontSize: `${typography.label.size}px`,
              }}
            >
              {tag}
            </span>
          ))}
        </Space>

        {/* Understanding Level Slider */}
        <div>
          <Text type="secondary" style={{ 
            fontSize: `${typography.caption.size}px`,
            color: colors.text.secondary,
          }}>
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
            styles={{
              track: {
                backgroundColor: colors.primary.strong,
              },
              rail: {
                backgroundColor: colors.surface.subtle,
              },
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
              style={{
                borderRadius: radius.pill,
                height: 28,
              }}
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

