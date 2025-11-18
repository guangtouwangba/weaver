import React, { useEffect } from 'react';
import { Modal, Form, Input, Radio, Select } from 'antd';
import { Topic, TopicCreate, TopicUpdate, GoalType, TopicStatus, GOAL_TYPE_LABELS, STATUS_LABELS } from '../types/topic';
import { colors, spacing, radius, shadows, typography } from '../theme/tokens';

const { TextArea } = Input;

interface TopicFormProps {
  visible: boolean;
  topic: Topic | null;
  onSubmit: (values: TopicCreate | TopicUpdate) => Promise<void>;
  onCancel: () => void;
}

const TopicForm: React.FC<TopicFormProps> = ({ visible, topic, onSubmit, onCancel }) => {
  const [form] = Form.useForm();
  const isEdit = !!topic;

  useEffect(() => {
    if (visible) {
      if (topic) {
        form.setFieldsValue({
          name: topic.name,
          goal_type: topic.goal_type,
          description: topic.description,
          status: topic.status,
        });
      } else {
        form.resetFields();
      }
    }
  }, [visible, topic, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await onSubmit(values);
      form.resetFields();
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title={isEdit ? '编辑主题' : '新建主题'}
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      width={600}
      okText="确定"
      cancelText="取消"
      styles={{
        header: {
          fontSize: `${typography.title.size}px`,
          fontWeight: typography.title.weight,
          color: colors.text.primary,
        },
        body: {
          padding: `${spacing.lg}px`,
        },
      }}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          goal_type: GoalType.THEORY,
          status: TopicStatus.LEARNING,
        }}
      >
        <Form.Item
          name="name"
          label="主题名称"
          rules={[
            { required: true, message: '请输入主题名称' },
            { max: 200, message: '名称不能超过200个字符' },
          ]}
        >
          <Input placeholder="例如：量价关系" />
        </Form.Item>

        <Form.Item
          name="goal_type"
          label="学习目标类型"
          rules={[{ required: true, message: '请选择学习目标类型' }]}
        >
          <Radio.Group>
            {Object.entries(GOAL_TYPE_LABELS).map(([key, label]) => (
              <Radio.Button key={key} value={key}>
                {label}
              </Radio.Button>
            ))}
          </Radio.Group>
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
          help="简要描述这个主题的学习目标和范围"
        >
          <TextArea
            rows={4}
            placeholder="例如：深入学习量价关系的理论基础和实战应用，包括价涨量增、价涨量缩等经典形态"
          />
        </Form.Item>

        {isEdit && (
          <Form.Item
            name="status"
            label="状态"
          >
            <Select>
              {Object.entries(STATUS_LABELS).map(([key, label]) => (
                <Select.Option key={key} value={key}>
                  {label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        )}
      </Form>
    </Modal>
  );
};

export default TopicForm;

