import React from 'react';
import { Card } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { TopicStatistics } from '../types/topic';
import { STATUS_LABELS } from '../types/topic';

interface TopicProgressChartProps {
  statistics: TopicStatistics;
}

const STATUS_COLORS = {
  learning: '#1890ff',
  completed: '#52c41a',
  paused: '#faad14',
  archived: '#d9d9d9',
};

const TopicProgressChart: React.FC<TopicProgressChartProps> = ({ statistics }) => {
  // Prepare data for bar chart
  const barData = [
    { name: STATUS_LABELS.learning, value: statistics.learning, fill: STATUS_COLORS.learning },
    { name: STATUS_LABELS.completed, value: statistics.completed, fill: STATUS_COLORS.completed },
    { name: STATUS_LABELS.paused, value: statistics.paused, fill: STATUS_COLORS.paused },
    { name: STATUS_LABELS.archived, value: statistics.archived, fill: STATUS_COLORS.archived },
  ];

  // Prepare data for pie chart (exclude archived and zero values)
  const pieData = barData
    .filter((item) => item.value > 0 && item.name !== STATUS_LABELS.archived)
    .map((item) => ({
      name: item.name,
      value: item.value,
    }));

  const RADIAN = Math.PI / 180;
  const renderCustomizedLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: any) => {
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        style={{ fontSize: '14px', fontWeight: 'bold' }}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' }}>
      {/* Bar Chart */}
      <Card title="📊 主题状态分布" bordered={false}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" name="数量" radius={[8, 8, 0, 0]}>
              {barData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Pie Chart */}
      {pieData.length > 0 && (
        <Card title="🥧 学习进度占比" bordered={false}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.name === STATUS_LABELS.learning
                        ? STATUS_COLORS.learning
                        : entry.name === STATUS_LABELS.completed
                        ? STATUS_COLORS.completed
                        : STATUS_COLORS.paused
                    }
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
};

export default TopicProgressChart;

