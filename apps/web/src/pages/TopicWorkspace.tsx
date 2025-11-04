import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Progress,
  Button,
  Space,
  Spin,
  message,
  Statistic,
  Row,
  Col,
  Typography,
  Divider,
  Tooltip,
  Tabs,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  BookOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  ApartmentOutlined,
  FileTextOutlined,
  LinkOutlined,
  SettingOutlined,
  MessageOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { topicsApi } from '../api/topics';
import { contentApi } from '../api/content';
import TopicForm from '../components/TopicForm';
import ContentUploadModal from '../components/ContentUploadModal';
import ContentList from '../components/ContentList';
import DocumentSelector from '../components/DocumentSelector';
import ChatPanel from '../components/ChatPanel';
import ConversationList from '../components/ConversationList';
import FunctionDrawer, { DrawerType } from '../components/FunctionDrawer';
import type { Topic, TopicUpdate, GoalType } from '../types/topic';
import type { TopicContent } from '../types/content';
import { GOAL_TYPE_LABELS, STATUS_LABELS, STATUS_COLORS } from '../types/topic';

const { Content } = Layout;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

const TopicWorkspace: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [topic, setTopic] = useState<Topic | null>(null);
  const [contents, setContents] = useState<TopicContent[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [isUploadModalVisible, setIsUploadModalVisible] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(false);
  
  // Chat状态
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(undefined);
  
  // 功能抽屉状态
  const [drawerType, setDrawerType] = useState<DrawerType>(null);

  // 加载主题和内容
  const loadData = async () => {
    if (!id) return;

    setLoading(true);
    try {
      const [topicData, contentsData] = await Promise.all([
        topicsApi.get(id),
        contentApi.list(id),
      ]);
      setTopic(topicData);
      setContents(contentsData.contents);
      
      // 自动选择所有已入库的文档
      const availableDocIds = contentsData.contents
        .filter((c) => c.document_id)
        .map((c) => c.document_id!);
      setSelectedDocIds(availableDocIds);
    } catch (error) {
      message.error('加载数据失败');
      console.error('Failed to load data:', error);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  // 更新主题
  const handleUpdate = async (values: TopicUpdate) => {
    if (!id) return;

    try {
      await topicsApi.update(id, values);
      message.success('更新成功');
      setIsEditModalVisible(false);
      loadData();
    } catch (error) {
      message.error('更新失败');
      console.error('Failed to update topic:', error);
    }
  };

  // 删除主题
  const handleDelete = async () => {
    if (!id || !topic) return;

    if (!window.confirm(`确定要删除主题"${topic.name}"吗？`)) {
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

  // 上传成功回调
  const handleUploadSuccess = () => {
    setIsUploadModalVisible(false);
    setRefreshTrigger((prev) => !prev);
    // 立即重新加载数据
    loadData();
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
      <Content style={{ padding: '24px' }}>
        {/* 顶部导航栏 */}
        <div
          style={{
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
            返回列表
          </Button>

          <Space size={8}>
            <Tooltip title="知识图谱">
              <Button
                icon={<ApartmentOutlined />}
                onClick={() => setDrawerType('knowledge-graph')}
              />
            </Tooltip>
            <Tooltip title="智能笔记">
              <Button
                icon={<FileTextOutlined />}
                onClick={() => setDrawerType('notes')}
              />
            </Tooltip>
            <Tooltip title="引用溯源">
              <Button
                icon={<LinkOutlined />}
                onClick={() => setDrawerType('citations')}
              />
            </Tooltip>
            <Tooltip title="学习设置">
              <Button
                icon={<SettingOutlined />}
                onClick={() => setDrawerType('settings')}
              />
            </Tooltip>
          </Space>
        </div>

        {/* 精简主题标题栏 */}
        <div 
          style={{ 
            marginBottom: '16px',
            padding: '12px 16px',
            background: '#fff',
            borderRadius: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
          }}
        >
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Title level={4} style={{ margin: 0 }}>
              {topic.name}
            </Title>
            <Space size="small">
              <span
                style={{
                  padding: '2px 8px',
                  background: STATUS_COLORS[topic.status] === 'green' ? '#f6ffed' : '#e6f7ff',
                  color: STATUS_COLORS[topic.status] === 'green' ? '#52c41a' : '#1890ff',
                  borderRadius: '4px',
                  fontSize: '12px',
                }}
              >
                {STATUS_LABELS[topic.status]}
              </span>
              <span
                style={{
                  padding: '2px 8px',
                  background: '#f0f5ff',
                  color: '#2f54eb',
                  borderRadius: '4px',
                  fontSize: '12px',
                }}
              >
                {GOAL_TYPE_LABELS[topic.goal_type]}
              </span>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                •
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {topic.total_contents}个内容
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                •
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                完成度 {topic.completion_progress.toFixed(0)}%
              </Text>
            </Space>
          </div>
          <Space size="small">
            <Button size="small" icon={<EditOutlined />} onClick={() => setIsEditModalVisible(true)}>
              编辑
            </Button>
            <Button size="small" danger icon={<DeleteOutlined />} onClick={handleDelete}>
              删除
            </Button>
          </Space>
        </div>

        {/* Tab切换布局 */}
        <Card 
          style={{ height: 'calc(100vh - 220px)', display: 'flex', flexDirection: 'column' }}
          bodyStyle={{ flex: 1, padding: 0, display: 'flex', flexDirection: 'column' }}
        >
          <Tabs
            defaultActiveKey="chat"
            size="large"
            style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
            tabBarStyle={{ margin: '0 16px', paddingTop: '8px' }}
          >
            {/* Tab 1: 智能对话 */}
            <TabPane
              tab={
                <span>
                  <MessageOutlined />
                  智能对话
                </span>
              }
              key="chat"
              style={{ height: '100%' }}
            >
              <div style={{ height: 'calc(100vh - 300px)', display: 'flex', gap: '12px', padding: '0 16px 16px' }}>
                {/* 左侧：对话列表 */}
                <div style={{ width: '280px', flexShrink: 0 }}>
                  <ConversationList
                    topicId={id!}
                    selectedConversationId={currentConversationId}
                    onConversationSelect={(conversationId) => {
                      console.log('📝 选择对话:', conversationId);
                      setCurrentConversationId(conversationId);
                    }}
                    onNewConversation={() => {
                      console.log('🆕 开始新对话');
                      setCurrentConversationId(undefined);
                    }}
                  />
                </div>

                {/* 右侧：文档选择 + Chat */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px', minWidth: 0 }}>
                  {/* 文档范围选择 - 极简版 */}
                  <div 
                    style={{ 
                      flexShrink: 0,
                      padding: '8px 12px',
                      background: '#fafafa',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Space size="small">
                      <Text style={{ fontSize: '13px', color: '#666' }}>🎯 对话范围：</Text>
                      {contents.filter(c => c.document_id).length === 0 ? (
                        <Text type="secondary" style={{ fontSize: '13px' }}>
                          暂无可用文档
                        </Text>
                      ) : (
                        <Text style={{ fontSize: '13px' }}>
                          {selectedDocIds.length} / {contents.filter(c => c.document_id).length} 个文档
                        </Text>
                      )}
                    </Space>
                    {contents.filter(c => c.document_id).length > 0 && (
                      <Button 
                        type="link" 
                        size="small"
                        style={{ fontSize: '12px', padding: '0 8px' }}
                        onClick={() => {
                          const allDocIds = contents.filter(c => c.document_id).map(c => c.document_id!);
                          if (selectedDocIds.length === allDocIds.length) {
                            setSelectedDocIds([]);
                          } else {
                            setSelectedDocIds(allDocIds);
                          }
                        }}
                      >
                        {selectedDocIds.length === contents.filter(c => c.document_id).length ? '取消全选' : '全选'}
                      </Button>
                    )}
                  </div>

                  {/* Chat面板 - 占据主要空间 */}
                  <div style={{ flex: 1, minHeight: 0 }}>
                    <ChatPanel
                      topicId={id!}
                      selectedDocIds={selectedDocIds}
                      conversationId={currentConversationId}
                      onConversationChange={(conversationId) => {
                        console.log('💬 对话ID更新:', conversationId);
                        setCurrentConversationId(conversationId);
                      }}
                    />
                  </div>
                </div>
              </div>
            </TabPane>

            {/* Tab 2: 文档管理 */}
            <TabPane
              tab={
                <span>
                  <FolderOpenOutlined />
                  文档管理
                </span>
              }
              key="documents"
              style={{ height: '100%' }}
            >
              <div style={{ height: 'calc(100vh - 300px)', padding: '0 16px 16px' }}>
                <Card
                  title="📚 关联内容"
                  extra={
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setIsUploadModalVisible(true)}
                    >
                      添加内容
                    </Button>
                  }
                  style={{ height: '100%' }}
                  bodyStyle={{ height: 'calc(100% - 57px)', overflowY: 'auto' }}
                >
                  <ContentList topicId={id!} refreshTrigger={refreshTrigger} />
                </Card>
              </div>
            </TabPane>
          </Tabs>
        </Card>

        {/* 编辑模态框 */}
        <TopicForm
          visible={isEditModalVisible}
          topic={topic}
          onSubmit={handleUpdate}
          onCancel={() => setIsEditModalVisible(false)}
        />

        {/* 上传模态框 */}
        {id && (
          <ContentUploadModal
            visible={isUploadModalVisible}
            onCancel={() => setIsUploadModalVisible(false)}
            onSuccess={handleUploadSuccess}
            topicId={id}
          />
        )}

        {/* 功能抽屉 */}
        <FunctionDrawer
          type={drawerType}
          open={drawerType !== null}
          onClose={() => setDrawerType(null)}
        />
      </Content>
    </Layout>
  );
};

export default TopicWorkspace;

