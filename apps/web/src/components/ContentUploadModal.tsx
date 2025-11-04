/**
 * Modal for uploading content to a topic
 */

import React, { useState } from 'react';
import { Modal, Form, Input, Upload, Tag, message, Space } from 'antd';
import { InboxOutlined, FileTextOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import { contentApi } from '../api/content';

const { Dragger } = Upload;
const { TextArea } = Input;

interface ContentUploadModalProps {
  visible: boolean;
  topicId: string;
  onCancel: () => void;
  onSuccess: () => void;
}

const ContentUploadModal: React.FC<ContentUploadModalProps> = ({
  visible,
  topicId,
  onCancel,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [uploading, setUploading] = useState<boolean>(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [inputTag, setInputTag] = useState<string>('');

  const handleUpload = async () => {
    try {
      await form.validateFields();
      
      if (fileList.length === 0) {
        message.warning('请选择要上传的文件');
        return;
      }

      const values = form.getFieldsValue();
      
      // Get the actual File object
      const uploadFile = fileList[0];
      const file = uploadFile.originFileObj || uploadFile as any;
      
      if (!file) {
        message.error('无法获取文件对象，请重新选择文件');
        setUploading(false);
        return;
      }

      // Show loading message
      const hideLoading = message.loading('📤 正在上传文件...', 0);
      setUploading(true);
      
      console.log('Uploading file:', file.name, file.type, file.size);
      
      try {
        console.log('Starting upload...');
        
        const result = await contentApi.uploadFile(topicId, file, values.description, tags);
        console.log('Upload successful, result:', result);
        
        hideLoading();
        
        message.success({
          content: '✅ 文档已上传！系统正在后台处理中，请稍候刷新查看进度。',
          duration: 5,
        });
        
        form.resetFields();
        setFileList([]);
        setTags([]);
        onSuccess();
      } catch (uploadError: any) {
        console.error('Upload error caught:', uploadError);
        console.error('Error details:', {
          message: uploadError.message,
          response: uploadError.response,
          status: uploadError.response?.status,
          data: uploadError.response?.data,
        });
        hideLoading();
        throw uploadError;
      }
    } catch (error: any) {
      console.error('Outer catch - Upload error:', error);
      console.error('Error object:', error);
      
      let errorMessage = '上传失败，请重试';
      if (error.response) {
        // 服务器返回错误
        errorMessage = error.response.data?.detail || `服务器错误 (${error.response.status})`;
      } else if (error.request) {
        // 请求发出但没有收到响应
        errorMessage = '网络错误，请检查服务器是否运行';
      } else {
        // 其他错误
        errorMessage = error.message || '未知错误';
      }
      
      message.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleAddTag = () => {
    if (inputTag && !tags.includes(inputTag)) {
      setTags([...tags, inputTag]);
      setInputTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const uploadProps = {
    onRemove: (file: UploadFile) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file: File) => {
      console.log('File selected:', file.name, file.type, file.size);
      // Create UploadFile object with the File
      const uploadFile: UploadFile = {
        uid: Date.now().toString(),
        name: file.name,
        status: 'done',
        originFileObj: file as any,
      };
      setFileList([uploadFile]);
      return false;  // Prevent automatic upload
    },
    fileList,
    maxCount: 1,
  };

  return (
    <Modal
      title="📤 添加学习内容"
      open={visible}
      onCancel={() => {
        if (!uploading) {
          onCancel();
        }
      }}
      onOk={handleUpload}
      confirmLoading={uploading}
      okText={uploading ? "上传中..." : "上传并分析"}
      cancelText="取消"
      width={600}
      maskClosable={!uploading}
      closable={!uploading}
    >
      <Form form={form} layout="vertical">
        <Form.Item label="选择文件" required>
          <Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
            <p className="ant-upload-hint">
              支持：PDF, Word, TXT, MD, 图片等格式
            </p>
          </Dragger>
        </Form.Item>

        <Form.Item label="描述（可选）" name="description">
          <TextArea
            rows={3}
            placeholder="简要描述这个内容的主要信息..."
          />
        </Form.Item>

        <Form.Item label="标签">
          <Space style={{ marginBottom: 8 }}>
            <Input
              placeholder="添加标签"
              value={inputTag}
              onChange={(e) => setInputTag(e.target.value)}
              onPressEnter={handleAddTag}
              style={{ width: 200 }}
            />
            <Tag
              color="blue"
              style={{ cursor: 'pointer' }}
              onClick={handleAddTag}
            >
              + 添加
            </Tag>
          </Space>
          <div>
            {tags.map((tag) => (
              <Tag
                key={tag}
                closable
                onClose={() => handleRemoveTag(tag)}
                color="processing"
              >
                {tag}
              </Tag>
            ))}
          </div>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ContentUploadModal;

