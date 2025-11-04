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
}

/**
 * Chat API client
 */
export const chatApi = {
  /**
   * Send a question and get an answer
   */
  ask: async (query: string, documentIds?: string[], topK: number = 4): Promise<QAResponse> => {
    console.log('Chat API - Sending question:', { query, documentIds, topK });
    
    const payload: QARequest = {
      question: query,  // 修改：使用 question 字段
      top_k: topK,
    };

    if (documentIds && documentIds.length > 0) {
      payload.document_ids = documentIds;
    }

    const response: AxiosResponse<QAResponse> = await apiClient.post('/qa/', payload);  // 修改：添加斜杠
    
    console.log('Chat API - Response received:', response.data);
    return response.data;
  },
};

export default chatApi;

