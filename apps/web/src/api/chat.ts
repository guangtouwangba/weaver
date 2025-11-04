import axios, { AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds for QA
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Chat API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * QA Request payload
 */
export interface QARequest {
  question: string;  // 修改：后端期望 question 不是 query
  document_ids?: string[];
  top_k?: number;
  conversation_id?: string;  // Continue existing conversation
  topic_id?: string;         // Create new conversation in this topic
}

/**
 * Source document in QA response (SearchHit)
 */
export interface SourceDocument {
  content: string;  // 修改：后端返回 content 不是 page_content
  score?: number | null;
  metadata?: {
    source?: string;
    page?: number;
    document_id?: string;
    [key: string]: any;
  } | null;
}

/**
 * QA Response
 */
export interface QAResponse {
  question: string;  // 修改：后端返回 question 不是 query
  answer: string;
  sources: SourceDocument[];  // 修改：后端返回 sources 不是 source_documents
  conversation_id?: string;  // Conversation ID (created or existing)
}

/**
 * Streaming event types
 */
export interface StreamEvent {
  type: 'progress' | 'sources' | 'answer_chunk' | 'done' | 'error';
  message?: string;
  stage?: string;
  sources?: SourceDocument[];
  count?: number;
  chunk?: string;
  conversation_id?: string;
}

export interface StreamCallbacks {
  onProgress?: (message: string, stage: string) => void;
  onSources?: (sources: SourceDocument[], count: number) => void;
  onChunk?: (chunk: string) => void;
  onDone?: (conversationId?: string) => void;
  onError?: (error: string) => void;
}

/**
 * Chat API client
 */
export const chatApi = {
  /**
   * Send a question and get an answer
   */
  ask: async (
    query: string,
    documentIds?: string[],
    topK: number = 4,
    conversationId?: string,
    topicId?: string
  ): Promise<QAResponse> => {
    console.log('Chat API - Sending question:', { query, documentIds, topK, conversationId, topicId });
    
    const payload: QARequest = {
      question: query,  // 修改：使用 question 字段
      top_k: topK,
    };

    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }

    if (conversationId) {
      payload.conversation_id = conversationId;
    }

    if (topicId) {
      payload.topic_id = topicId;
    }

    const response: AxiosResponse<QAResponse> = await apiClient.post('/qa/', payload);  // 修改：添加斜杠
    
    console.log('Chat API - Response received:', response.data);
    return response.data;
  },

  /**
   * Send a question with streaming response
   */
  askStream: async (
    query: string,
    documentIds?: string[],
    topK: number = 4,
    conversationId?: string,
    topicId?: string,
    callbacks: StreamCallbacks = {}
  ): Promise<void> => {
    console.log('Chat API - Sending streaming question:', { query, documentIds, topK, conversationId, topicId });
    
    const payload: QARequest = {
      question: query,
      top_k: topK,
    };

    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }

    if (conversationId) {
      payload.conversation_id = conversationId;
    }

    if (topicId) {
      payload.topic_id = topicId;
    }

    // Use fetch for SSE streaming
    const response = await fetch(`${API_BASE_URL}/qa/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is null');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        // Decode the chunk
        const chunk = decoder.decode(value, { stream: true });
        
        // Process each line (SSE format)
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6)) as StreamEvent;
              
              switch (data.type) {
                case 'progress':
                  callbacks.onProgress?.(data.message || '', data.stage || '');
                  break;
                case 'sources':
                  callbacks.onSources?.(data.sources || [], data.count || 0);
                  break;
                case 'answer_chunk':
                  callbacks.onChunk?.(data.chunk || '');
                  break;
                case 'done':
                  callbacks.onDone?.(data.conversation_id);
                  break;
                case 'error':
                  callbacks.onError?.(data.message || 'Unknown error');
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', line, e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },
};

export default chatApi;

