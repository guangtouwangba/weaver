/**
 * Conversation API client
 */

import axios from 'axios';

const API_BASE_URL = '/api/v1';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds for conversation operations
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Conversation API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface Conversation {
  id: string;
  topic_id: string;
  title: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: string[] | null;
  created_at: string;
}

export interface ConversationListResponse {
  total: number;
  conversations: Conversation[];
}

export interface MessageListResponse {
  total: number;
  messages: Message[];
}

export interface CreateConversationRequest {
  topic_id: string;
  title?: string;
}

export interface UpdateConversationRequest {
  title?: string;
}

/**
 * Conversation API
 */
export const conversationApi = {
  /**
   * Create a new conversation
   */
  async create(data: CreateConversationRequest): Promise<Conversation> {
    const response = await apiClient.post<Conversation>('/conversations/', data);
    return response.data;
  },

  /**
   * Get a conversation by ID
   */
  async get(conversationId: string): Promise<Conversation> {
    const response = await apiClient.get<Conversation>(`/conversations/${conversationId}`);
    return response.data;
  },

  /**
   * Update a conversation
   */
  async update(conversationId: string, data: UpdateConversationRequest): Promise<Conversation> {
    const response = await apiClient.put<Conversation>(`/conversations/${conversationId}`, data);
    return response.data;
  },

  /**
   * Delete a conversation
   */
  async delete(conversationId: string): Promise<void> {
    await apiClient.delete(`/conversations/${conversationId}`);
  },

  /**
   * List conversations for a topic
   */
  async listByTopic(topicId: string, skip = 0, limit = 20): Promise<ConversationListResponse> {
    const response = await apiClient.get<ConversationListResponse>(
      `/conversations/topics/${topicId}/conversations`,
      {
        params: { skip, limit },
      }
    );
    return response.data;
  },
};

/**
 * Message API
 */
export const messageApi = {
  /**
   * Get a message by ID
   */
  async get(messageId: string): Promise<Message> {
    const response = await apiClient.get<Message>(`/messages/${messageId}`);
    return response.data;
  },

  /**
   * Delete a message
   */
  async delete(messageId: string): Promise<void> {
    await apiClient.delete(`/messages/${messageId}`);
  },

  /**
   * List messages for a conversation
   */
  async listByConversation(
    conversationId: string,
    skip = 0,
    limit = 50
  ): Promise<MessageListResponse> {
    const response = await apiClient.get<MessageListResponse>(
      `/messages/conversations/${conversationId}/messages`,
      {
        params: { skip, limit },
      }
    );
    return response.data;
  },
};

