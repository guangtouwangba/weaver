import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Tag, Progress, Space, Typography, Button, Tooltip } from 'antd';
import { EditOutlined, DeleteOutlined, BookOutlined, ExperimentOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Topic, GoalType, GOAL_TYPE_LABELS, STATUS_LABELS, STATUS_COLORS } from '../types/topic';

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
      style={{ height: '100%', cursor: 'pointer' }}
      onClick={handleViewDetail}
      actions={[
        <Tooltip title="查看详情">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={handleViewDetail}
          >
            详情
          </Button>
        </Tooltip>,
        <Tooltip title="编辑">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={handleEdit}
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
          >
            删除
          </Button>
        </Tooltip>,
      ]}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* Title and Status */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Text strong style={{ fontSize: '18px', flex: 1 }}>
            {topic.name}
          </Text>
          <Tag color={STATUS_COLORS[topic.status]}>
            {STATUS_LABELS[topic.status]}
          </Tag>
        </div>

        {/* Goal Type */}
        <div>
          <Tag icon={GOAL_TYPE_ICONS[topic.goal_type]} color="blue">
            {GOAL_TYPE_LABELS[topic.goal_type]}
          </Tag>
        </div>

        {/* Description */}
        {topic.description && (
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ marginBottom: 0, color: '#666' }}
          >
            {topic.description}
          </Paragraph>
        )}

        {/* Progress */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <Text type="secondary">学习进度</Text>
            <Text strong>{topic.completion_progress.toFixed(1)}%</Text>
          </div>
          <Progress
            percent={topic.completion_progress}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            showInfo={false}
          />
        </div>

        {/* Statistics */}
        <div style={{ display: 'flex', justifyContent: 'space-around', padding: '12px 0', background: '#fafafa', borderRadius: '4px' }}>
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block' }}>
              总内容
            </Text>
            <Text strong style={{ fontSize: '20px' }}>
              {topic.total_contents}
            </Text>
          </div>
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: '12px', display: 'block' }}>
              已理解
            </Text>
            <Text strong style={{ fontSize: '20px', color: '#52c41a' }}>
              {topic.understood_contents}
            </Text>
          </div>
          {topic.goal_type === GoalType.PRACTICE && (
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: '12px', display: 'block' }}>
                已实践
              </Text>
              <Text strong style={{ fontSize: '20px', color: '#1890ff' }}>
                {topic.practiced_contents}
              </Text>
            </div>
          )}
        </div>

        {/* Timestamps */}
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            创建: {dayjs(topic.created_at).format('YYYY-MM-DD')}
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            更新: {dayjs(topic.updated_at).format('YYYY-MM-DD')}
          </Text>
        </div>
      </Space>
    </Card>
  );
};

export default TopicCard;

