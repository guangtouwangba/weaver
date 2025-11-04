import React from 'react';
import { Drawer } from 'antd';

export type DrawerType = 'knowledge-graph' | 'notes' | 'citations' | 'settings' | null;

interface FunctionDrawerProps {
  type: DrawerType;
  open: boolean;
  onClose: () => void;
  children?: React.ReactNode;
}

const drawerConfig: Record<Exclude<DrawerType, null>, { title: string; width: number | string }> = {
  'knowledge-graph': {
    title: '🧠 知识图谱',
    width: 500,
  },
  'notes': {
    title: '📝 智能笔记',
    width: 500,
  },
  'citations': {
    title: '🔗 引用溯源',
    width: 450,
  },
  'settings': {
    title: '⚙️ 学习设置',
    width: 400,
  },
};

const FunctionDrawer: React.FC<FunctionDrawerProps> = ({ type, open, onClose, children }) => {
  if (!type) return null;

  const config = drawerConfig[type];

  return (
    <Drawer
      title={config.title}
      placement="right"
      onClose={onClose}
      open={open}
      width={config.width}
      styles={{
        body: {
          padding: '16px',
        },
      }}
    >
      {children || (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: '#8c8c8c' }}>
          <p>✨ 此功能即将推出</p>
          <p style={{ fontSize: '12px' }}>敬请期待 Phase 2 更新</p>
        </div>
      )}
    </Drawer>
  );
};

export default FunctionDrawer;

