/**
 * ErrorBoundary - Catch and handle React component errors
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Card, Space } from 'antd';
import { BugOutlined, ReloadOutlined, HomeOutlined } from '@ant-design/icons';

const { Paragraph, Text } = Typography;

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Update state with error info
    this.setState({
      error,
      errorInfo,
    });

    // Call optional error handler
    this.props.onError?.(error, errorInfo);

    // TODO: Send error to error reporting service (e.g., Sentry)
  }

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      const { error, errorInfo } = this.state;
      const isDevelopment = import.meta.env.DEV;

      return (
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f0f2f5',
            padding: '24px',
          }}
        >
          <Card style={{ maxWidth: '800px', width: '100%' }}>
            <Result
              status="error"
              icon={<BugOutlined style={{ color: '#ff4d4f' }} />}
              title="抱歉，页面出现了错误"
              subTitle="应用遇到了意外错误，请尝试刷新页面或返回首页"
              extra={[
                <Button
                  type="primary"
                  key="reload"
                  icon={<ReloadOutlined />}
                  onClick={this.handleReload}
                >
                  刷新页面
                </Button>,
                <Button
                  key="home"
                  icon={<HomeOutlined />}
                  onClick={this.handleGoHome}
                >
                  返回首页
                </Button>,
                isDevelopment && (
                  <Button key="reset" onClick={this.handleReset}>
                    重置错误状态
                  </Button>
                ),
              ].filter(Boolean)}
            />

            {/* Error Details (Development Only) */}
            {isDevelopment && error && (
              <Card
                size="small"
                title="错误详情 (仅开发环境显示)"
                style={{ marginTop: '24px', background: '#fafafa' }}
              >
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <div>
                    <Text strong>错误消息：</Text>
                    <Paragraph
                      code
                      copyable
                      style={{
                        background: '#fff',
                        padding: '8px',
                        marginTop: '8px',
                        marginBottom: 0,
                      }}
                    >
                      {error.toString()}
                    </Paragraph>
                  </div>

                  {errorInfo && (
                    <div>
                      <Text strong>组件堆栈：</Text>
                      <Paragraph
                        code
                        copyable
                        style={{
                          background: '#fff',
                          padding: '8px',
                          marginTop: '8px',
                          marginBottom: 0,
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          maxHeight: '300px',
                          overflow: 'auto',
                        }}
                      >
                        {errorInfo.componentStack}
                      </Paragraph>
                    </div>
                  )}

                  {error.stack && (
                    <div>
                      <Text strong>错误堆栈：</Text>
                      <Paragraph
                        code
                        copyable
                        style={{
                          background: '#fff',
                          padding: '8px',
                          marginTop: '8px',
                          marginBottom: 0,
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          maxHeight: '300px',
                          overflow: 'auto',
                          fontSize: '12px',
                        }}
                      >
                        {error.stack}
                      </Paragraph>
                    </div>
                  )}
                </Space>
              </Card>
            )}

            {/* Help Text */}
            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                💡 如果问题持续出现，请联系技术支持或提交问题报告
              </Text>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

