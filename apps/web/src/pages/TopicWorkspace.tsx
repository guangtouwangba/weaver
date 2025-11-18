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
import { colors, spacing, radius, shadows, typography, chipVariants } from '../theme/tokens';

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
      <Layout style={{ minHeight: '100vh', background: colors.surface.page }}>
        <Content style={{ 
          padding: `${spacing.lg}px`, 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center' 
        }}>
          <Spin size="large" tip="加载中..." />
        </Content>
      </Layout>
    );
  }

  if (!topic) {
    return null;
  }

  return (
    <Layout style={{ minHeight: '100vh', background: colors.surface.page }}>
      <Content style={{ padding: `${spacing.lg}px` }}>
        {/* 顶部导航栏 */}
        <div
          style={{
            marginBottom: `${spacing.lg}px`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/')}
            style={{
              borderRadius: radius.pill,
              height: 36,
            }}
          >
            返回列表
          </Button>

          <Space size={spacing.xs}>
            <Tooltip title="知识图谱">
              <Button
                icon={<ApartmentOutlined />}
                onClick={() => setDrawerType('knowledge-graph')}
                style={{
                  borderRadius: radius.pill,
                  height: 36,
                }}
              />
            </Tooltip>
            <Tooltip title="智能笔记">
              <Button
                icon={<FileTextOutlined />}
                onClick={() => setDrawerType('notes')}
                style={{
                  borderRadius: radius.pill,
                  height: 36,
                }}
              />
            </Tooltip>
            <Tooltip title="引用溯源">
              <Button
                icon={<LinkOutlined />}
                onClick={() => setDrawerType('citations')}
                style={{
                  borderRadius: radius.pill,
                  height: 36,
                }}
              />
            </Tooltip>
            <Tooltip title="学习设置">
              <Button
                icon={<SettingOutlined />}
                onClick={() => setDrawerType('settings')}
                style={{
                  borderRadius: radius.pill,
                  height: 36,
                }}
              />
            </Tooltip>
          </Space>
        </div>

        {/* 精简主题标题栏 */}
        <div 
          style={{ 
            marginBottom: `${spacing.md}px`,
            padding: `${spacing.sm}px ${spacing.md}px`,
            background: colors.surface.card,
            borderRadius: `${radius.sm}px`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: shadows.soft,
            border: `1px solid ${colors.border.subtle}`,
          }}
        >
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: `${spacing.md}px` }}>
            <Title level={4} style={{ 
              margin: 0,
              fontSize: `${typography.title.size}px`,
              fontWeight: typography.title.weight,
              color: colors.text.primary,
            }}>
              {topic.name}
            </Title>
            <Space size="small">
              <span
                style={{
                  padding: `2px ${spacing.xs}px`,
                  background: STATUS_COLORS[topic.status] === 'green' ? chipVariants.success.background : chipVariants.active.background,
                  color: STATUS_COLORS[topic.status] === 'green' ? chipVariants.success.color : chipVariants.active.color,
                  borderRadius: `${radius.pill}px`,
                  fontSize: `${typography.label.size}px`,
                  fontWeight: typography.label.weight,
                }}
              >
                {STATUS_LABELS[topic.status]}
              </span>
              <span
                style={{
                  padding: `2px ${spacing.xs}px`,
                  background: chipVariants.info.background,
                  color: chipVariants.info.color,
                  borderRadius: `${radius.pill}px`,
                  fontSize: `${typography.label.size}px`,
                  fontWeight: typography.label.weight,
                }}
              >
                {GOAL_TYPE_LABELS[topic.goal_type]}
              </span>
              <Text type="secondary" style={{ fontSize: `${typography.caption.size}px`, color: colors.text.muted }}>
                •
              </Text>
              <Text type="secondary" style={{ fontSize: `${typography.caption.size}px`, color: colors.text.secondary }}>
                {topic.total_contents}个内容
              </Text>
              <Text type="secondary" style={{ fontSize: `${typography.caption.size}px`, color: colors.text.muted }}>
                •
              </Text>
              <Text type="secondary" style={{ fontSize: `${typography.caption.size}px`, color: colors.text.secondary }}>
                完成度 {topic.completion_progress.toFixed(0)}%
              </Text>
            </Space>
          </div>
          <Space size="small">
            <Button 
              size="small" 
              icon={<EditOutlined />} 
              onClick={() => setIsEditModalVisible(true)}
              style={{
                borderRadius: radius.pill,
                height: 28,
              }}
            >
              编辑
            </Button>
            <Button 
              size="small" 
              danger 
              icon={<DeleteOutlined />} 
              onClick={handleDelete}
              style={{
                borderRadius: radius.pill,
                height: 28,
              }}
            >
              删除
            </Button>
          </Space>
        </div>

        {/* Tab切换布局 */}
        <Card 
          style={{ 
            height: 'calc(100vh - 220px)', 
            display: 'flex', 
            flexDirection: 'column',
            borderRadius: radius.lg,
            boxShadow: shadows.soft,
            border: `1px solid ${colors.border.subtle}`,
          }}
          bodyStyle={{ flex: 1, padding: 0, display: 'flex', flexDirection: 'column' }}
        >
          <Tabs
            defaultActiveKey="chat"
            size="large"
            style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
            tabBarStyle={{ 
              margin: `0 ${spacing.md}px`, 
              paddingTop: `${spacing.xs}px`,
            }}
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
              <div style={{ 
                height: 'calc(100vh - 300px)', 
                display: 'flex', 
                gap: `${spacing.sm}px`, 
                padding: `0 ${spacing.md}px ${spacing.md}px` 
              }}>
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
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: `${spacing.sm}px`, minWidth: 0 }}>
                  {/* 文档范围选择 - 极简版 */}
                  <div 
                    style={{ 
                      flexShrink: 0,
                      padding: `${spacing.xs}px ${spacing.sm}px`,
                      background: colors.surface.subtle,
                      borderRadius: `${radius.xs}px`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      border: `1px solid ${colors.border.subtle}`,
                    }}
                  >
                    <Space size="small">
                      <Text style={{ 
                        fontSize: `${typography.caption.size + 1}px`, 
                        color: colors.text.secondary 
                      }}>
                        🎯 对话范围：
                      </Text>
                      {contents.filter(c => c.document_id).length === 0 ? (
                        <Text type="secondary" style={{ 
                          fontSize: `${typography.caption.size + 1}px`,
                          color: colors.text.muted,
                        }}>
                          暂无可用文档
                        </Text>
                      ) : (
                        <Text style={{ 
                          fontSize: `${typography.caption.size + 1}px`,
                          color: colors.text.primary,
                        }}>
                          {selectedDocIds.length} / {contents.filter(c => c.document_id).length} 个文档
                        </Text>
                      )}
                    </Space>
                    {contents.filter(c => c.document_id).length > 0 && (
                      <Button 
                        type="link" 
                        size="small"
                        style={{ 
                          fontSize: `${typography.caption.size}px`, 
                          padding: `0 ${spacing.xs}px`,
                          height: 'auto',
                        }}
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
              <div style={{ height: 'calc(100vh - 300px)', padding: `0 ${spacing.md}px ${spacing.md}px` }}>
                <Card
                  title="📚 关联内容"
                  extra={
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={() => setIsUploadModalVisible(true)}
                      style={{
                        borderRadius: radius.pill,
                        height: 36,
                        fontWeight: typography.bodyBold.weight,
                      }}
                    >
                      添加内容
                    </Button>
                  }
                  style={{ 
                    height: '100%',
                    borderRadius: radius.md,
                    boxShadow: shadows.soft,
                    border: `1px solid ${colors.border.subtle}`,
                  }}
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

