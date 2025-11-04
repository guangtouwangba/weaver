import React from 'react';
import { Space, Button, Typography } from 'antd';
import {
  BulbOutlined,
  FileSearchOutlined,
  QuestionCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface QuickQuestionsProps {
  onQuestionClick: (question: string) => void;
  disabled?: boolean;
}

const QuickQuestions: React.FC<QuickQuestionsProps> = ({ onQuestionClick, disabled = false }) => {
  const quickQuestions = [
    {
      icon: <FileSearchOutlined />,
      label: '总结核心观点',
      question: '请总结这些文档的核心观点和主要内容',
    },
    {
      icon: <QuestionCircleOutlined />,
      label: '解释关键概念',
      question: '请解释文档中的关键概念和术语',
    },
    {
      icon: <ThunderboltOutlined />,
      label: '应用示例',
      question: '请提供一些实际应用的例子',
    },
    {
      icon: <BulbOutlined />,
      label: '学习建议',
      question: '基于这些内容，你有什么学习建议？',
    },
  ];

  return (
    <div style={{ padding: '12px 16px', background: '#fafafa', borderRadius: '8px' }}>
      <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginBottom: '8px' }}>
        💡 快捷提问：
      </Text>
      <Space size={[8, 8]} wrap>
        {quickQuestions.map((item, index) => (
          <Button
            key={index}
            size="small"
            icon={item.icon}
            onClick={() => onQuestionClick(item.question)}
            disabled={disabled}
            style={{
              fontSize: '12px',
              height: '28px',
              borderRadius: '14px',
            }}
          >
            {item.label}
          </Button>
        ))}
      </Space>
    </div>
  );
};

export default QuickQuestions;

