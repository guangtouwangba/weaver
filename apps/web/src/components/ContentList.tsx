/**
 * List of topic contents
 */

import React, { useEffect, useState } from 'react';
import { Button, Space, Select, Empty, Spin, message } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { TopicContent, ContentStatus, CONTENT_STATUS_LABELS } from '../types/content';
import { contentApi } from '../api/content';
import ContentCard from './ContentCard';
import ContentUploadModal from './ContentUploadModal';

interface ContentListProps {
  topicId: string;
}

const ContentList: React.FC<ContentListProps> = ({ topicId }) => {
  const [contents, setContents] = useState<TopicContent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploadModalVisible, setUploadModalVisible] = useState<boolean>(false);
  const [statusFilter, setStatusFilter] = useState<ContentStatus | undefined>(undefined);

  useEffect(() => {
    fetchContents();
  }, [topicId, statusFilter]);

  const fetchContents = async () => {
    setLoading(true);
    try {
      const response = await contentApi.list(topicId, statusFilter);
      setContents(response.contents);
    } catch (error) {
      message.error('加载内容失败');
      console.error('Failed to fetch contents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (contentId: string) => {
    if (window.confirm('确定要删除这个内容吗？')) {
      try {
        await contentApi.delete(topicId, contentId);
        message.success('内容已删除');
        fetchContents();
      } catch (error) {
        message.error('删除失败');
        console.error('Failed to delete content:', error);
      }
    }
  };

  return (
    <div>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setUploadModalVisible(true)}
          >
            添加内容
          </Button>
          <Button icon={<ReloadOutlined />} onClick={fetchContents}>
            刷新
          </Button>
        </Space>
        <Select
          placeholder="筛选状态"
          allowClear
          style={{ width: 150 }}
          value={statusFilter}
          onChange={(value) => setStatusFilter(value)}
          options={[
            { value: ContentStatus.PENDING, label: CONTENT_STATUS_LABELS[ContentStatus.PENDING] },
            { value: ContentStatus.READING, label: CONTENT_STATUS_LABELS[ContentStatus.READING] },
            { value: ContentStatus.UNDERSTOOD, label: CONTENT_STATUS_LABELS[ContentStatus.UNDERSTOOD] },
            { value: ContentStatus.QUESTIONED, label: CONTENT_STATUS_LABELS[ContentStatus.QUESTIONED] },
            { value: ContentStatus.PRACTICED, label: CONTENT_STATUS_LABELS[ContentStatus.PRACTICED] },
          ]}
        />
      </Space>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" tip="加载中..." />
        </div>
      ) : contents.length === 0 ? (
        <Empty
          description="暂无关联内容"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          style={{ padding: '40px 0' }}
        >
          <Button type="primary" onClick={() => setUploadModalVisible(true)}>
            添加第一个内容
          </Button>
        </Empty>
      ) : (
        contents.map((content) => (
          <ContentCard
            key={content.id}
            content={content}
            topicId={topicId}
            onUpdate={fetchContents}
            onDelete={() => handleDelete(content.id)}
          />
        ))
      )}

      <ContentUploadModal
        visible={uploadModalVisible}
        topicId={topicId}
        onCancel={() => setUploadModalVisible(false)}
        onSuccess={() => {
          setUploadModalVisible(false);
          fetchContents();
        }}
      />
    </div>
  );
};

export default ContentList;

