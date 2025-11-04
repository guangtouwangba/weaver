/**
 * API client for Topic management endpoints
 */

import axios, { AxiosResponse } from 'axios';
import type {
  Topic,
  TopicCreate,
  TopicUpdate,
  TopicListResponse,
  TopicStatistics,
  TopicProgressUpdate,
  TopicStatus,
} from '../types/topic';

const API_BASE_URL = '/api/v1';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Topics API client
 */
export const topicsApi = {
  /**
   * List all topics with optional filtering
   */
  list: async (params?: {
    status?: TopicStatus;
    skip?: number;
    limit?: number;
  }): Promise<TopicListResponse> => {
    const response: AxiosResponse<TopicListResponse> = await apiClient.get('/topics', {
      params,
    });
    return response.data;
  },

  /**
   * Get a single topic by ID
   */
  get: async (id: string): Promise<Topic> => {
    const response: AxiosResponse<Topic> = await apiClient.get(`/topics/${id}`);
    return response.data;
  },

  /**
   * Create a new topic
   */
  create: async (data: TopicCreate): Promise<Topic> => {
    const response: AxiosResponse<Topic> = await apiClient.post('/topics/', data);
    return response.data;
  },

  /**
   * Update an existing topic
   */
  update: async (id: string, data: TopicUpdate): Promise<Topic> => {
    const response: AxiosResponse<Topic> = await apiClient.put(`/topics/${id}`, data);
    return response.data;
  },

  /**
   * Delete a topic
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/topics/${id}`);
  },

  /**
   * Update topic progress statistics
   */
  updateProgress: async (id: string, data: TopicProgressUpdate): Promise<Topic> => {
    const response: AxiosResponse<Topic> = await apiClient.put(
      `/topics/${id}/progress`,
      data
    );
    return response.data;
  },

  /**
   * Get topic statistics
   */
  getStatistics: async (): Promise<TopicStatistics> => {
    const response: AxiosResponse<TopicStatistics> = await apiClient.get('/topics/statistics');
    return response.data;
  },

  /**
   * Search topics by query string
   */
  search: async (query: string, limit = 10): Promise<Topic[]> => {
    const response: AxiosResponse<Topic[]> = await apiClient.get('/topics/search', {
      params: { q: query, limit },
    });
    return response.data;
  },
};

export default topicsApi;

