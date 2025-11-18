import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Tag, Progress, Space, Typography, Button, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, BookOutlined, ExperimentOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Topic, GoalType, GOAL_TYPE_LABELS, STATUS_LABELS, STATUS_COLORS } from '../types/topic';
import { colors, spacing, radius, shadows, typography, chipVariants } from '../theme/tokens';

const { Text, Paragraph } = Typography;

interface TopicCardProps {
  topic: Topic;
  onEdit: (topic: Topic) => void;
  onDelete: (id: string) => void;
}

const GOAL_TYPE_ICONS: Record<GoalType, React.ReactNode> = {
  [GoalType.THEORY]: <BookOutlined />,
  [GoalType.PRACTICE]: <ExperimentOutlined />,
  [GoalType.QUICK]: <ThunderboltOutlined />,
};

const TopicCard: React.FC<TopicCardProps> = ({ topic, onEdit, onDelete }) => {
  const navigate = useNavigate();

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    if (window.confirm(`确定要删除主题"${topic.name}"吗？`)) {
      onDelete(topic.id);
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    onEdit(topic);
  };

  const handleViewDetail = () => {
    navigate(`/topics/${topic.id}`);
  };

  return (
    <Card
      hoverable
      style={{ 
        height: '100%', 
        cursor: 'pointer',
        borderRadius: radius.lg,
        boxShadow: shadows.soft,
        border: `1px solid ${colors.border.subtle}`,
        transition: `all ${180}ms cubic-bezier(0.2, 0.8, 0.2, 1)`,
      }}
      bodyStyle={{ padding: spacing.lg }}
      onClick={handleViewDetail}
      actions={[
        <Tooltip title="查看详情">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={handleViewDetail}
            style={{
              borderRadius: radius.pill,
            }}
          >
            详情
          </Button>
        </Tooltip>,
        <Tooltip title="编辑">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={handleEdit}
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
            onClick={handleDelete}
            style={{
              borderRadius: radius.pill,
            }}
          >
            删除
          </Button>
        </Tooltip>,
      ]}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* Title and Status */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: `${spacing.sm}px` }}>
          <Text strong style={{ 
            fontSize: `${typography.subtitle.size}px`,
            fontWeight: typography.subtitle.weight, 
            flex: 1,
            color: colors.text.primary,
          }}>
            {topic.name}
          </Text>
          <span style={{
            padding: `${spacing.xxs}px ${spacing.xs}px`,
            background: STATUS_COLORS[topic.status] === 'green' ? chipVariants.success.background : chipVariants.active.background,
            color: STATUS_COLORS[topic.status] === 'green' ? chipVariants.success.color : chipVariants.active.color,
            borderRadius: `${radius.pill}px`,
            fontSize: `${typography.label.size}px`,
            fontWeight: typography.label.weight,
            whiteSpace: 'nowrap',
          }}>
            {STATUS_LABELS[topic.status]}
          </span>
        </div>

        {/* Goal Type */}
        <div>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: `${spacing.xxs}px`,
            padding: `${spacing.xxs}px ${spacing.xs}px`,
            background: chipVariants.info.background,
            color: chipVariants.info.color,
            borderRadius: `${radius.pill}px`,
            fontSize: `${typography.label.size}px`,
            fontWeight: typography.label.weight,
          }}>
            {GOAL_TYPE_ICONS[topic.goal_type]}
            {GOAL_TYPE_LABELS[topic.goal_type]}
          </span>
        </div>

        {/* Description */}
        {topic.description && (
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ 
              marginBottom: 0, 
              color: colors.text.secondary,
              fontSize: `${typography.body.size}px`,
              lineHeight: typography.body.lineHeight,
            }}
          >
            {topic.description}
          </Paragraph>
        )}

        {/* Progress */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: `${spacing.xs}px` }}>
            <Text type="secondary" style={{ 
              fontSize: `${typography.body.size}px`,
              color: colors.text.secondary,
            }}>
              学习进度
            </Text>
            <Text strong style={{ 
              fontSize: `${typography.body.size}px`,
              fontWeight: typography.bodyBold.weight,
              color: colors.text.primary,
            }}>
              {topic.completion_progress.toFixed(1)}%
            </Text>
          </div>
          <Progress
            percent={topic.completion_progress}
            strokeColor={{
              '0%': colors.primary.strong,
              '100%': colors.emerald.strong,
            }}
            trailColor={colors.surface.subtle}
            showInfo={false}
            strokeLinecap="round"
            style={{
              height: 6,
            }}
          />
        </div>

        {/* Statistics */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-around', 
          padding: `${spacing.sm}px 0`, 
          background: colors.surface.subtle, 
          borderRadius: `${radius.xs}px`,
          border: `1px solid ${colors.border.subtle}`,
        }}>
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary" style={{ 
              fontSize: `${typography.caption.size}px`, 
              display: 'block',
              color: colors.text.secondary,
              marginBottom: `${spacing.xxs}px`,
            }}>
              总内容
            </Text>
            <Text strong style={{ 
              fontSize: `${typography.title.size}px`,
              fontWeight: typography.title.weight,
              color: colors.text.primary,
            }}>
              {topic.total_contents}
            </Text>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary" style={{ 
              fontSize: `${typography.caption.size}px`, 
              display: 'block',
              color: colors.text.secondary,
              marginBottom: `${spacing.xxs}px`,
            }}>
              已理解
            </Text>
            <Text strong style={{ 
              fontSize: `${typography.title.size}px`,
              fontWeight: typography.title.weight, 
              color: colors.emerald.strong 
            }}>
              {topic.understood_contents}
            </Text>
          </div>
          {topic.goal_type === GoalType.PRACTICE && (
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ 
                fontSize: `${typography.caption.size}px`, 
                display: 'block',
                color: colors.text.secondary,
                marginBottom: `${spacing.xxs}px`,
              }}>
                已实践
              </Text>
              <Text strong style={{ 
                fontSize: `${typography.title.size}px`,
                fontWeight: typography.title.weight, 
                color: colors.primary.strong 
              }}>
                {topic.practiced_contents}
              </Text>
            </div>
          )}
        </div>

        {/* Timestamps */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text type="secondary" style={{ 
            fontSize: `${typography.caption.size}px`,
            color: colors.text.muted,
          }}>
            创建: {dayjs(topic.created_at).format('YYYY-MM-DD')}
          </Text>
          <Text type="secondary" style={{ 
            fontSize: `${typography.caption.size}px`,
            color: colors.text.muted,
          }}>
            更新: {dayjs(topic.updated_at).format('YYYY-MM-DD')}
          </Text>
        </div>
      </Space>
    </Card>
  );
};

export default TopicCard;

