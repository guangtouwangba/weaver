/**
 * API client for Research Agent RAG backend
 */

// Get API URL - supports both build-time and runtime configuration
function getApiBaseUrl(): string {
  // 1. Check build-time env var (Next.js replaces this at build time)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // 2. Check runtime window config (can be injected via script tag)
  if (typeof window !== 'undefined' && (window as any).__API_URL__) {
    return (window as any).__API_URL__;
  }
  
  // 3. Auto-detect based on current hostname for Zeabur deployments
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // If running on Zeabur, try to guess the API URL
    if (hostname.includes('zeabur.app')) {
      // Replace 'web' or 'frontend' with 'api' in the hostname
      const apiHostname = hostname
        .replace('-web-', '-api-')
        .replace('-frontend-', '-api-')
        .replace('research-agent-rag-web', 'research-agent-rag-api')
        .replace('research-agent-rag-frontend', 'research-agent-rag-api');
      return `https://${apiHostname}`;
    }
  }
  
  // 4. Default to localhost for development
  return 'http://localhost:8000';
}

const API_BASE_URL = getApiBaseUrl();

// Log the API URL for debugging (only in browser)
if (typeof window !== 'undefined') {
  console.log('[API] Using API URL:', API_BASE_URL);
}

// Types
export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectDocument {
  id: string;
  project_id: string;
  filename: string;
  file_size: number;
  page_count: number;
  status: 'pending' | 'processing' | 'ready' | 'error';
  created_at: string;
}

export interface ChatMessage {
  message: string;
  document_id?: string;
}

export interface ChatResponse {
  answer: string;
  sources: Array<{
    document_id: string;
    page_number: number;
    snippet: string;
    similarity: number;
  }>;
}

export interface CanvasNode {
  id: string;
  type: string;
  title: string;
  content: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  tags: string[];
  sourceId?: string;
  sourcePage?: number;
}

export interface CanvasEdge {
  id?: string;
  source: string;
  target: string;
}

export interface CanvasData {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  viewport: {
    x: number;
    y: number;
    scale: number;
  };
  updated_at?: string;
}

// API Error
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new ApiError(response.status, error.detail || 'Request failed');
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Projects API
export const projectsApi = {
  list: () => fetchApi<{ items: Project[]; total: number }>('/api/v1/projects'),
  
  create: (name: string, description?: string) =>
    fetchApi<Project>('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    }),
  
  get: (id: string) => fetchApi<Project>(`/api/v1/projects/${id}`),
  
  delete: (id: string) =>
    fetchApi<void>(`/api/v1/projects/${id}`, { method: 'DELETE' }),
};

// Documents API
export const documentsApi = {
  list: (projectId: string) =>
    fetchApi<{ items: ProjectDocument[]; total: number }>(
      `/api/v1/projects/${projectId}/documents`
    ),
  
  get: (documentId: string) =>
    fetchApi<ProjectDocument>(`/api/v1/documents/${documentId}`),
  
  // Get PDF file URL for viewing
  getFileUrl: (documentId: string) =>
    `${API_BASE_URL}/api/v1/documents/${documentId}/file`,
  
  upload: async (projectId: string, file: File): Promise<ProjectDocument> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/documents`,
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new ApiError(response.status, error.detail);
    }

    return response.json();
  },
  
  delete: (documentId: string) =>
    fetchApi<void>(`/api/v1/documents/${documentId}`, { method: 'DELETE' }),
};

// Chat API
export const chatApi = {
  send: (projectId: string, message: ChatMessage) =>
    fetchApi<ChatResponse>(`/api/v1/projects/${projectId}/chat`, {
      method: 'POST',
      body: JSON.stringify(message),
    }),
  
  // Streaming chat
  stream: async function* (
    projectId: string,
    message: ChatMessage
  ): AsyncGenerator<{ type: string; content?: string; sources?: ChatResponse['sources'] }> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/projects/${projectId}/chat/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message),
      }
    );

    if (!response.ok) {
      throw new ApiError(response.status, 'Stream request failed');
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          yield data;
        }
      }
    }
  },
};

// Canvas API
export const canvasApi = {
  get: (projectId: string) =>
    fetchApi<CanvasData>(`/api/v1/projects/${projectId}/canvas`),
  
  save: (projectId: string, data: Omit<CanvasData, 'updated_at'>) =>
    fetchApi<{ success: boolean; updated_at: string }>(
      `/api/v1/projects/${projectId}/canvas`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    ),
};

// Health check
export const healthApi = {
  check: () => fetchApi<{ status: string; environment: string; version: string }>('/health'),
};

