/**
 * API client for Research Agent RAG backend
 */

// Cache the API URL after first detection
let _cachedApiUrl: string | null = null;

// Get API URL - supports both build-time and runtime configuration
function getApiBaseUrl(): string {
  // Return cached value if available
  if (_cachedApiUrl) {
    return _cachedApiUrl;
  }
  
  // For browser environments, detect based on current page URL first
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol; // 'https:' or 'http:'
    console.log('[API] Detecting API URL for hostname:', hostname, 'protocol:', protocol);
    
    // If running on Zeabur public domain, auto-detect the API URL
    if (hostname.includes('zeabur.app')) {
      // Replace 'web' or 'frontend' with 'api' in the hostname
      const apiHostname = hostname
        .replace('-web-', '-api-')
        .replace('-frontend-', '-api-')
        .replace('research-agent-rag-web', 'research-agent-rag-api')
        .replace('research-agent-rag-frontend', 'research-agent-rag-api');
      // Always use HTTPS for public Zeabur domains
      _cachedApiUrl = `https://${apiHostname}`;
      console.log('[API] Auto-detected Zeabur API URL:', _cachedApiUrl);
      return _cachedApiUrl;
    }
  }
  
  // Check build-time env var (Next.js replaces this at build time)
  // Skip internal URLs that would cause mixed content issues
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl && envUrl !== 'undefined' && !envUrl.includes('.internal')) {
    // If page is HTTPS but env URL is HTTP, try to upgrade
    if (typeof window !== 'undefined' && window.location.protocol === 'https:' && envUrl.startsWith('http://')) {
      console.log('[API] Upgrading HTTP env URL to HTTPS');
      _cachedApiUrl = envUrl.replace('http://', 'https://');
    } else {
      _cachedApiUrl = envUrl;
    }
    console.log('[API] Using env URL:', _cachedApiUrl);
    return _cachedApiUrl;
  }
  
  // Check runtime window config (can be injected via script tag)
  if (typeof window !== 'undefined' && (window as any).__API_URL__) {
    _cachedApiUrl = (window as any).__API_URL__;
    console.log('[API] Using window config URL:', _cachedApiUrl);
    return _cachedApiUrl;
  }
  
  // Default to localhost for development (only on client-side)
  // On server-side (SSR), return empty string to avoid issues
  if (typeof window === 'undefined') {
    return ''; // SSR - will be replaced on client
  }
  
  _cachedApiUrl = 'http://localhost:8000';
  console.log('[API] Using default localhost URL');
  return _cachedApiUrl;
}

// Getter function - always call this to get the URL
const getApiUrl = () => getApiBaseUrl();

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

export interface ChatHistoryResponse {
  messages: Array<{
    id: string;
    role: 'user' | 'ai';
    content: string;
    sources?: Array<{
      document_id: string;
      page_number: number;
      snippet: string;
      similarity: number;
    }>;
    created_at: string;
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
  const url = `${getApiUrl()}${endpoint}`;
  
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
    `${getApiUrl()}/api/v1/documents/${documentId}/file`,
  
  upload: async (projectId: string, file: File): Promise<ProjectDocument> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `${getApiUrl()}/api/v1/projects/${projectId}/documents`,
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
  getHistory: (projectId: string) =>
    fetchApi<ChatHistoryResponse>(`/api/v1/projects/${projectId}/chat/history`),

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
      `${getApiUrl()}/api/v1/projects/${projectId}/chat/stream`,
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

