import React, { useState } from 'react';
import { Row, Col, Empty, Input, Select, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import TopicCard from './TopicCard';
import { Topic, TopicStatus, STATUS_LABELS } from '../types/topic';

const { Search } = Input;

interface TopicListProps {
  topics: Topic[];
  onEdit: (topic: Topic) => void;
  onDelete: (id: string) => void;
  loading?: boolean;
}

const TopicList: React.FC<TopicListProps> = ({ topics, onEdit, onDelete, loading }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<TopicStatus | 'all'>('all');

  // Filter topics
  const filteredTopics = topics.filter((topic) => {
    // Status filter
    if (statusFilter !== 'all' && topic.status !== statusFilter) {
      return false;
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        topic.name.toLowerCase().includes(query) ||
        (topic.description && topic.description.toLowerCase().includes(query))
      );
    }

    return true;
  });

  return (
    <div>
      {/* Filters */}
      <Space style={{ marginBottom: '24px', width: '100%', justifyContent: 'space-between' }}>
        <Search
          placeholder="搜索主题名称或描述"
          allowClear
          prefix={<SearchOutlined />}
          style={{ width: 300 }}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <Select
          value={statusFilter}
          onChange={setStatusFilter}
          style={{ width: 150 }}
        >
          <Select.Option value="all">全部状态</Select.Option>
          {Object.entries(STATUS_LABELS).map(([key, label]) => (
            <Select.Option key={key} value={key}>
              {label}
            </Select.Option>
          ))}
        </Select>
      </Space>

      {/* Topic Cards Grid */}
      {filteredTopics.length === 0 ? (
        <Empty
          description={
            searchQuery || statusFilter !== 'all'
              ? '没有找到符合条件的主题'
              : '还没有创建任何主题，点击上方"新建主题"按钮开始'
          }
          style={{ padding: '60px 0' }}
        />
      ) : (
        <Row gutter={[16, 16]}>
          {filteredTopics.map((topic) => (
            <Col xs={24} sm={12} lg={8} xl={6} key={topic.id}>
              <TopicCard
                topic={topic}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default TopicList;

