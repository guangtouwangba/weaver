/**
 * API client for TopicContent endpoints
 */

import axios, { AxiosResponse } from 'axios';
import type {
  TopicContent,
  TopicContentCreate,
  TopicContentUpdate,
  TopicContentStats,
  ContentStatus,
} from '../types/content';

// Use proxy in development (configured in vite.config.ts)
// In production, use relative path
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,  // 30 seconds for file uploads
});

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Content API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * TopicContent API client
 */
export const contentApi = {
  /**
   * Upload a file to a topic
   */
  uploadFile: async (topicId: string, file: File, description?: string, tags?: string[]): Promise<TopicContent> => {
    console.log('=== uploadFile START ===');
    console.log('uploadFile called with:', { 
      topicId, 
      fileName: file?.name, 
      fileType: file?.type, 
      fileSize: file?.size,
      description, 
      tags 
    });
    
    if (!file) {
      console.error('File is null or undefined!');
      throw new Error('File is required');
    }
    
    const formData = new FormData();
    formData.append('file', file, file.name);
    
    if (description) {
      formData.append('description', description);
    }
    
    if (tags && tags.length > 0) {
      formData.append('tags', tags.join(','));
    }
    
    console.log('FormData entries:', Array.from(formData.entries()));

    const url = `${API_BASE_URL}/topics/${topicId}/contents/upload`;
    console.log('Uploading to URL:', url);
    console.log('API_BASE_URL:', API_BASE_URL);

    try {
      console.log('Making POST request...');
      const response: AxiosResponse<TopicContent> = await axios.post(
        url,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 90000,  // 90 seconds - for uploading large files (streaming on backend)
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              console.log(`Upload progress: ${percentCompleted}%`);
            }
          },
        }
      );
      
      console.log('Upload response status:', response.status);
      console.log('Upload response data:', response.data);
      console.log('=== uploadFile SUCCESS ===');
      return response.data;
    } catch (error: any) {
      console.error('=== uploadFile ERROR ===');
      console.error('Error in axios.post:', error);
      console.error('Error message:', error.message);
      console.error('Error response:', error.response);
      console.error('Error request:', error.request);
      console.error('Error config:', error.config);
      throw error;
    }
  },

  /**
   * Add content to topic (for URL or existing doc)
   */
  create: async (topicId: string, data: TopicContentCreate): Promise<TopicContent> => {
    const response: AxiosResponse<TopicContent> = await apiClient.post(
      `/topics/${topicId}/contents/`,
      data
    );
    return response.data;
  },

  /**
   * List contents for a topic
   */
  list: async (topicId: string, status?: ContentStatus, skip = 0, limit = 100): Promise<{ total: number; contents: TopicContent[] }> => {
    const params: any = { skip, limit };
    if (status) {
      params.status = status;
    }
    
    const response: AxiosResponse<{ total: number; contents: TopicContent[] }> = await apiClient.get(
      `/topics/${topicId}/contents/`,
      { params }
    );
    return response.data;
  },

  /**
   * Get content statistics
   */
  getStats: async (topicId: string): Promise<TopicContentStats> => {
    const response: AxiosResponse<TopicContentStats> = await apiClient.get(
      `/topics/${topicId}/contents/stats`
    );
    return response.data;
  },

  /**
   * Get a single content
   */
  get: async (topicId: string, contentId: string): Promise<TopicContent> => {
    const response: AxiosResponse<TopicContent> = await apiClient.get(
      `/topics/${topicId}/contents/${contentId}`
    );
    return response.data;
  },

  /**
   * Update content
   */
  update: async (topicId: string, contentId: string, data: TopicContentUpdate): Promise<TopicContent> => {
    const response: AxiosResponse<TopicContent> = await apiClient.put(
      `/topics/${topicId}/contents/${contentId}`,
      data
    );
    return response.data;
  },

  /**
   * Delete content
   */
  delete: async (topicId: string, contentId: string): Promise<void> => {
    await apiClient.delete(`/topics/${topicId}/contents/${contentId}`);
  },
};

export default contentApi;

