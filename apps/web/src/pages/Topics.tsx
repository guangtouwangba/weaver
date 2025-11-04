import React, { useEffect, useState } from 'react';
import { Layout, Card, Row, Col, Button, Space, Spin, message, Statistic, Tabs } from 'antd';
import { PlusOutlined, BookOutlined, CheckCircleOutlined, PauseCircleOutlined, BarChartOutlined } from '@ant-design/icons';
import TopicList from '../components/TopicList';
import TopicForm from '../components/TopicForm';
import TopicProgressChart from '../components/TopicProgressChart';
import { topicsApi } from '../api/topics';
import type { Topic, TopicStatistics, TopicCreate, TopicUpdate } from '../types/topic';

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
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header style={{ background: '#fff', padding: '0 24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>📚 知识主题管理</h1>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleOpenCreate}
            size="large"
          >
            新建主题
          </Button>
        </div>
      </Header>

      <Content style={{ padding: '24px' }}>
        {/* Statistics Cards */}
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="总主题数"
                value={statistics?.total || 0}
                prefix={<BookOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="学习中"
                value={statistics?.learning || 0}
                valueStyle={{ color: '#1890ff' }}
                prefix={<BookOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="已完成"
                value={statistics?.completed || 0}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="已暂停"
                value={statistics?.paused || 0}
                valueStyle={{ color: '#faad14' }}
                prefix={<PauseCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Visualization Charts */}
        {statistics && statistics.total > 0 && (
          <div style={{ marginBottom: '24px' }}>
            <TopicProgressChart statistics={statistics} />
          </div>
        )}

        {/* Topic List with Tabs */}
        <Card>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
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

