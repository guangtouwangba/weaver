import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Descriptions,
  Progress,
  Tag,
  Button,
  Space,
  Spin,
  message,
  Statistic,
  Row,
  Col,
  Typography,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  BookOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { topicsApi } from '../api/topics';
import TopicForm from '../components/TopicForm';
import ContentList from '../components/ContentList';
import type { Topic, TopicUpdate } from '../types/topic';
import { GOAL_TYPE_LABELS, STATUS_LABELS, STATUS_COLORS, GoalType } from '../types/topic';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

const TopicDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [topic, setTopic] = useState<Topic | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);

  // Load topic details
  const loadTopic = async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const data = await topicsApi.get(id);
      setTopic(data);
    } catch (error) {
      message.error('加载主题详情失败');
      console.error('Failed to load topic:', error);
      // Navigate back if topic not found
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTopic();
  }, [id]);

  // Handle update
  const handleUpdate = async (values: TopicUpdate) => {
    if (!id) return;
    
    try {
      await topicsApi.update(id, values);
      message.success('更新成功');
      setIsEditModalVisible(false);
      loadTopic();
    } catch (error) {
      message.error('更新失败');
      console.error('Failed to update topic:', error);
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!id) return;
    
    if (!window.confirm(`确定要删除主题"${topic?.name}"吗？`)) {
      return;
    }
    
    try {
      await topicsApi.delete(id);
      message.success('删除成功');
      navigate('/');
    } catch (error) {
      message.error('删除失败');
      console.error('Failed to delete topic:', error);
    }
  };

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
        <Content style={{ padding: '24px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Spin size="large" tip="加载中..." />
        </Content>
      </Layout>
    );
  }

  if (!topic) {
    return null;
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            style={{ marginBottom: '16px' }}
          >
            返回列表
          </Button>
          
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Title level={2} style={{ margin: 0 }}>
                      {topic.name}
                    </Title>
                    <Tag color={STATUS_COLORS[topic.status]} style={{ fontSize: '14px' }}>
                      {STATUS_LABELS[topic.status]}
                    </Tag>
                  </div>
                  
                  <Space>
                    <Tag color="blue">
                      {GOAL_TYPE_LABELS[topic.goal_type]}
                    </Tag>
                  </Space>
                  
                  {topic.description && (
                    <Paragraph style={{ marginTop: '12px', marginBottom: 0, color: '#666' }}>
                      {topic.description}
                    </Paragraph>
                  )}
                </Space>
              </div>
              
              <Space>
                <Button
                  icon={<EditOutlined />}
                  onClick={() => setIsEditModalVisible(true)}
                >
                  编辑
                </Button>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={handleDelete}
                >
                  删除
                </Button>
              </Space>
            </div>
          </Card>
        </div>

        {/* Progress Overview */}
        <Card title="📊 学习进度" style={{ marginBottom: '24px' }}>
          <Row gutter={24}>
            <Col span={24} style={{ marginBottom: '24px' }}>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={Number(topic.completion_progress.toFixed(1))}
                  size={180}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                  format={(percent) => (
                    <div>
                      <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{percent}%</div>
                      <div style={{ fontSize: '14px', color: '#666', marginTop: '8px' }}>完成度</div>
                    </div>
                  )}
                />
              </div>
            </Col>
            
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="总内容数"
                  value={topic.total_contents}
                  prefix={<BookOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="已理解"
                  value={topic.understood_contents}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                  suffix={<Text type="secondary">/ {topic.total_contents}</Text>}
                />
              </Card>
            </Col>
            
            {topic.goal_type === GoalType.PRACTICE && (
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="已实践"
                    value={topic.practiced_contents}
                    prefix={<ClockCircleOutlined />}
                    valueStyle={{ color: '#fa8c16' }}
                    suffix={<Text type="secondary">/ {topic.total_contents}</Text>}
                  />
                </Card>
              </Col>
            )}
          </Row>
        </Card>

        {/* Details */}
        <Card title="📝 详细信息">
          <Descriptions column={2} bordered>
            <Descriptions.Item label="主题ID">
              <Text code copyable>
                {topic.id}
              </Text>
            </Descriptions.Item>
            
            <Descriptions.Item label="学习目标类型">
              <Tag color="blue">{GOAL_TYPE_LABELS[topic.goal_type]}</Tag>
            </Descriptions.Item>
            
            <Descriptions.Item label="当前状态">
              <Tag color={STATUS_COLORS[topic.status]}>
                {STATUS_LABELS[topic.status]}
              </Tag>
            </Descriptions.Item>
            
            <Descriptions.Item label="完成进度">
              <Progress
                percent={Number(topic.completion_progress.toFixed(1))}
                size="small"
                style={{ maxWidth: '200px' }}
              />
            </Descriptions.Item>
            
            <Descriptions.Item label="创建时间">
              {dayjs(topic.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            
            <Descriptions.Item label="最后更新">
              {dayjs(topic.updated_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
            
            <Descriptions.Item label="学习时长" span={2}>
              <Text type="secondary">
                已持续 {dayjs(topic.updated_at).diff(dayjs(topic.created_at), 'day')} 天
              </Text>
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {/* Content Management */}
        <Card 
          title="📚 关联内容" 
          style={{ marginTop: '24px' }}
        >
          <ContentList topicId={id!} />
        </Card>

        {/* Edit Modal */}
        <TopicForm
          visible={isEditModalVisible}
          topic={topic}
          onSubmit={handleUpdate}
          onCancel={() => setIsEditModalVisible(false)}
        />
      </Content>
    </Layout>
  );
};

export default TopicDetail;

