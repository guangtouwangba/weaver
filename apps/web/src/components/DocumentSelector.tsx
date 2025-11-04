import React from 'react';
import { Card, Checkbox, Space, Typography, Tag } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import type { TopicContent } from '../types/content';
import { CONTENT_STATUS_LABELS, CONTENT_STATUS_COLORS } from '../types/content';

const { Text } = Typography;

interface DocumentSelectorProps {
  contents: TopicContent[];
  selectedDocIds: string[];
  onSelectionChange: (docIds: string[]) => void;
}

const DocumentSelector: React.FC<DocumentSelectorProps> = ({
  contents,
  selectedDocIds,
  onSelectionChange,
}) => {
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allDocIds = contents
        .filter((content) => content.document_id)
        .map((content) => content.document_id!);
      onSelectionChange(allDocIds);
    } else {
      onSelectionChange([]);
    }
  };

  const handleSelectOne = (docId: string, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedDocIds, docId]);
    } else {
      onSelectionChange(selectedDocIds.filter((id) => id !== docId));
    }
  };

  const availableContents = contents.filter((content) => content.document_id);
  const allSelected = availableContents.length > 0 && selectedDocIds.length === availableContents.length;
  const indeterminate = selectedDocIds.length > 0 && selectedDocIds.length < availableContents.length;

  return (
    <Card
      title="🎯 文档范围选择"
      size="small"
      style={{ marginBottom: '16px' }}
      bodyStyle={{ padding: '12px' }}
    >
      <Space direction="vertical" size={8} style={{ width: '100%' }}>
        {/* 全选选项 */}
        <Checkbox
          checked={allSelected}
          indeterminate={indeterminate}
          onChange={(e) => handleSelectAll(e.target.checked)}
          disabled={availableContents.length === 0}
        >
          <Text strong>全部文档 ({availableContents.length})</Text>
        </Checkbox>

        {/* 文档列表 */}
        {availableContents.length === 0 ? (
          <Text type="secondary" style={{ fontSize: '12px', display: 'block', paddingLeft: '24px' }}>
            暂无可用文档，请先上传并处理文档
          </Text>
        ) : (
          <div style={{ paddingLeft: '24px' }}>
            <Space direction="vertical" size={4} style={{ width: '100%' }}>
              {availableContents.map((content) => (
                <Checkbox
                  key={content.id}
                  checked={selectedDocIds.includes(content.document_id!)}
                  onChange={(e) => handleSelectOne(content.document_id!, e.target.checked)}
                >
                  <Space size={4}>
                    <FileTextOutlined style={{ fontSize: '12px', color: '#8c8c8c' }} />
                    <Text
                      ellipsis
                      style={{ fontSize: '13px', maxWidth: '150px' }}
                      title={content.title}
                    >
                      {content.title}
                    </Text>
                    <Tag
                      color={CONTENT_STATUS_COLORS[content.status]}
                      style={{ fontSize: '11px', padding: '0 4px', margin: 0 }}
                    >
                      {CONTENT_STATUS_LABELS[content.status]}
                    </Tag>
                  </Space>
                </Checkbox>
              ))}
            </Space>
          </div>
        )}
      </Space>
    </Card>
  );
};

export default DocumentSelector;

