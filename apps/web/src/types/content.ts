/**
 * TypeScript types for TopicContent
 */

export enum ContentSource {
  FILE_UPLOAD = "file_upload",
  URL = "url",
  EXISTING_DOC = "existing_doc",
  TEXT_INPUT = "text_input",
}

export enum ContentStatus {
  PENDING = "pending",
  READING = "reading",
  UNDERSTOOD = "understood",
  QUESTIONED = "questioned",
  PRACTICED = "practiced",
}

export enum ProcessingStatus {
  NOT_STARTED = "not_started",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface TopicContent {
  id: string;
  topic_id: string;
  source_type: ContentSource;
  
  // Content info
  title: string;
  description?: string;
  source_url?: string;
  document_id?: string;
  
  // Processing status
  processing_status: ProcessingStatus;
  processing_error?: string;
  
  // Status
  status: ContentStatus;
  understanding_level: number;  // 0-100
  
  // Metadata
  author?: string;
  publish_date?: string;
  word_count?: number;
  estimated_time?: number;
  
  // User interaction
  notes?: string;
  highlights: string[];
  tags: string[];
  
  // Timestamps
  added_at: string;
  last_viewed_at?: string;
  completed_at?: string;
}

export interface TopicContentCreate {
  title: string;
  description?: string;
  source_type?: ContentSource;
  source_url?: string;
  document_id?: string;
  author?: string;
  tags?: string[];
}

export interface TopicContentUpdate {
  title?: string;
  description?: string;
  status?: ContentStatus;
  understanding_level?: number;
  notes?: string;
  tags?: string[];
}

export interface TopicContentStats {
  total: number;
  pending: number;
  reading: number;
  understood: number;
  questioned: number;
  practiced: number;
  avg_understanding: number;
}

// Display labels
export const CONTENT_STATUS_LABELS: Record<ContentStatus, string> = {
  [ContentStatus.PENDING]: '待消化',
  [ContentStatus.READING]: '阅读中',
  [ContentStatus.UNDERSTOOD]: '已理解',
  [ContentStatus.QUESTIONED]: '有疑问',
  [ContentStatus.PRACTICED]: '已实践',
};

export const CONTENT_STATUS_COLORS: Record<ContentStatus, string> = {
  [ContentStatus.PENDING]: 'default',
  [ContentStatus.READING]: 'blue',
  [ContentStatus.UNDERSTOOD]: 'green',
  [ContentStatus.QUESTIONED]: 'orange',
  [ContentStatus.PRACTICED]: 'purple',
};

export const CONTENT_SOURCE_LABELS: Record<ContentSource, string> = {
  [ContentSource.FILE_UPLOAD]: '📄 文件上传',
  [ContentSource.URL]: '🔗 网页链接',
  [ContentSource.EXISTING_DOC]: '📚 已有文档',
  [ContentSource.TEXT_INPUT]: '✍️ 文本输入',
};

export const PROCESSING_STATUS_LABELS: Record<ProcessingStatus, string> = {
  [ProcessingStatus.NOT_STARTED]: '未开始',
  [ProcessingStatus.PROCESSING]: '处理中...',
  [ProcessingStatus.COMPLETED]: '已完成',
  [ProcessingStatus.FAILED]: '处理失败',
};

export const PROCESSING_STATUS_COLORS: Record<ProcessingStatus, string> = {
  [ProcessingStatus.NOT_STARTED]: 'default',
  [ProcessingStatus.PROCESSING]: 'blue',
  [ProcessingStatus.COMPLETED]: 'success',
  [ProcessingStatus.FAILED]: 'error',
};

