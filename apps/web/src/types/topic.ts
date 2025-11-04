/**
 * TypeScript type definitions for Topic management
 */

export enum GoalType {
  THEORY = 'theory',
  PRACTICE = 'practice',
  QUICK = 'quick',
}

export enum TopicStatus {
  LEARNING = 'learning',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  ARCHIVED = 'archived',
}

export interface Topic {
  id: string;  // UUID as string from API
  name: string;
  goal_type: GoalType;
  description?: string;
  status: TopicStatus;
  completion_progress: number;  // 0-100
  total_contents: number;
  understood_contents: number;
  practiced_contents: number;
  created_at: string;  // ISO datetime string
  updated_at: string;  // ISO datetime string
}

export interface TopicCreate {
  name: string;
  goal_type: GoalType;
  description?: string;
}

export interface TopicUpdate {
  name?: string;
  goal_type?: GoalType;
  description?: string;
  status?: TopicStatus;
}

export interface TopicProgressUpdate {
  total_contents: number;
  understood_contents: number;
  practiced_contents: number;
}

export interface TopicListResponse {
  total: number;
  topics: Topic[];
}

export interface TopicStatistics {
  total: number;
  learning: number;
  completed: number;
  paused: number;
  archived: number;
}

// UI Helper types
export interface TopicFormData {
  name: string;
  goal_type: GoalType;
  description?: string;
}

// Goal type labels for display
export const GOAL_TYPE_LABELS: Record<GoalType, string> = {
  [GoalType.THEORY]: '理论研究型',
  [GoalType.PRACTICE]: '实践应用型',
  [GoalType.QUICK]: '快速了解型',
};

// Status labels for display
export const STATUS_LABELS: Record<TopicStatus, string> = {
  [TopicStatus.LEARNING]: '学习中',
  [TopicStatus.PAUSED]: '已暂停',
  [TopicStatus.COMPLETED]: '已完成',
  [TopicStatus.ARCHIVED]: '已归档',
};

// Status colors for Ant Design tags
export const STATUS_COLORS: Record<TopicStatus, string> = {
  [TopicStatus.LEARNING]: 'blue',
  [TopicStatus.PAUSED]: 'orange',
  [TopicStatus.COMPLETED]: 'green',
  [TopicStatus.ARCHIVED]: 'default',
};

