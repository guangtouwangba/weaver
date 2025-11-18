import React, { useEffect, useState } from 'react';
import { Layout, Card, Row, Col, Button, Space, Spin, message, Statistic, Tabs } from 'antd';
import { PlusOutlined, BookOutlined, CheckCircleOutlined, PauseCircleOutlined, BarChartOutlined } from '@ant-design/icons';
import TopicList from '../components/TopicList';
import TopicForm from '../components/TopicForm';
import TopicProgressChart from '../components/TopicProgressChart';
import { topicsApi } from '../api/topics';
import type { Topic, TopicStatistics, TopicCreate, TopicUpdate } from '../types/topic';
import { colors, spacing, radius, shadows, typography } from '../theme/tokens';

const { Header, Content } = Layout;

const Topics: React.FC = () => {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [statistics, setStatistics] = useState<TopicStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingTopic, setEditingTopic] = useState<Topic | null>(null);

  // Load topics and statistics
  const loadData = async () => {
    setLoading(true);
    try {
      const [topicsResponse, statsResponse] = await Promise.all([
        topicsApi.list(),
        topicsApi.getStatistics(),
      ]);
      setTopics(topicsResponse.topics);
      setStatistics(statsResponse);
    } catch (error) {
      message.error('加载数据失败');
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Handle create topic
  const handleCreate = async (values: TopicCreate) => {
    try {
      await topicsApi.create(values);
      message.success('创建成功');
      setIsModalVisible(false);
      loadData();
    } catch (error) {
      message.error('创建失败');
      console.error('Failed to create topic:', error);
    }
  };

  // Handle update topic
  const handleUpdate = async (id: string, values: TopicUpdate) => {
    try {
      await topicsApi.update(id, values);
      message.success('更新成功');
      setIsModalVisible(false);
      setEditingTopic(null);
      loadData();
    } catch (error) {
      message.error('更新失败');
      console.error('Failed to update topic:', error);
    }
  };

  // Handle delete topic
  const handleDelete = async (id: string) => {
    try {
      await topicsApi.delete(id);
      message.success('删除成功');
      loadData();
    } catch (error) {
      message.error('删除失败');
      console.error('Failed to delete topic:', error);
    }
  };

  // Open modal for creating new topic
  const handleOpenCreate = () => {
    setEditingTopic(null);
    setIsModalVisible(true);
  };

  // Open modal for editing topic
  const handleOpenEdit = (topic: Topic) => {
    setEditingTopic(topic);
    setIsModalVisible(true);
  };

  // Close modal
  const handleCloseModal = () => {
    setIsModalVisible(false);
    setEditingTopic(null);
  };

  return (
    <Layout style={{ minHeight: '100vh', background: colors.surface.page }}>
      <Header style={{ 
        background: colors.surface.card, 
        padding: `0 ${spacing.lg}px`, 
        boxShadow: shadows.soft,
        borderBottom: `1px solid ${colors.border.subtle}`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ 
            margin: 0, 
            fontSize: `${typography.displayMd.size}px`,
            fontWeight: typography.displayMd.weight,
            color: colors.text.primary,
          }}>
            📚 知识主题管理
          </h1>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleOpenCreate}
            size="large"
            style={{
              height: 40,
              borderRadius: radius.pill,
              fontWeight: typography.bodyBold.weight,
            }}
          >
            新建主题
          </Button>
        </div>
      </Header>

      <Content style={{ padding: `${spacing.lg}px` }}>
        {/* Statistics Cards */}
        <Row gutter={spacing.md} style={{ marginBottom: `${spacing.lg}px` }}>
          <Col xs={24} sm={12} md={6}>
            <Card style={{ 
              borderRadius: radius.lg, 
              boxShadow: shadows.soft,
              border: `1px solid ${colors.border.subtle}`,
            }}>
              <Statistic
                title="总主题数"
                value={statistics?.total || 0}
                prefix={<BookOutlined />}
                valueStyle={{ 
                  fontSize: `${typography.displayMd.size}px`,
                  fontWeight: typography.displayMd.weight,
                  color: colors.text.primary,
                }}
                titleStyle={{
                  fontSize: `${typography.body.size}px`,
                  color: colors.text.secondary,
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{ 
              borderRadius: radius.lg, 
              boxShadow: shadows.soft,
              border: `1px solid ${colors.border.subtle}`,
            }}>
              <Statistic
                title="学习中"
                value={statistics?.learning || 0}
                valueStyle={{ 
                  color: colors.primary.strong,
                  fontSize: `${typography.displayMd.size}px`,
                  fontWeight: typography.displayMd.weight,
                }}
                titleStyle={{
                  fontSize: `${typography.body.size}px`,
                  color: colors.text.secondary,
                }}
                prefix={<BookOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{ 
              borderRadius: radius.lg, 
              boxShadow: shadows.soft,
              border: `1px solid ${colors.border.subtle}`,
            }}>
              <Statistic
                title="已完成"
                value={statistics?.completed || 0}
                valueStyle={{ 
                  color: colors.emerald.strong,
                  fontSize: `${typography.displayMd.size}px`,
                  fontWeight: typography.displayMd.weight,
                }}
                titleStyle={{
                  fontSize: `${typography.body.size}px`,
                  color: colors.text.secondary,
                }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card style={{ 
              borderRadius: radius.lg, 
              boxShadow: shadows.soft,
              border: `1px solid ${colors.border.subtle}`,
            }}>
              <Statistic
                title="已暂停"
                value={statistics?.paused || 0}
                valueStyle={{ 
                  color: colors.yellow.strong,
                  fontSize: `${typography.displayMd.size}px`,
                  fontWeight: typography.displayMd.weight,
                }}
                titleStyle={{
                  fontSize: `${typography.body.size}px`,
                  color: colors.text.secondary,
                }}
                prefix={<PauseCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Visualization Charts */}
        {statistics && statistics.total > 0 && (
          <div style={{ marginBottom: `${spacing.lg}px` }}>
            <TopicProgressChart statistics={statistics} />
          </div>
        )}

        {/* Topic List with Tabs */}
        <Card style={{
          borderRadius: radius.lg,
          boxShadow: shadows.soft,
          border: `1px solid ${colors.border.subtle}`,
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: `${spacing.xxl * 2}px 0` }}>
              <Spin size="large" tip="加载中..." />
            </div>
          ) : (
            <TopicList
              topics={topics}
              onEdit={handleOpenEdit}
              onDelete={handleDelete}
              loading={loading}
            />
          )}
        </Card>

        {/* Topic Form Modal */}
        <TopicForm
          visible={isModalVisible}
          topic={editingTopic}
          onSubmit={editingTopic ? (values) => handleUpdate(editingTopic.id, values) : handleCreate}
          onCancel={handleCloseModal}
        />
      </Content>
    </Layout>
  );
};

export default Topics;

