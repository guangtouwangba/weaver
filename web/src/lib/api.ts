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
export interface CanvasNode {
  id: string;
  type: string;
  title: string;
  content: string;
  x: number;
  y: number;
  width?: number;
  height?: number;
  color?: string;
  tags?: string[];
  sourceId?: string;
  sourcePage?: number;
  isSimplified?: boolean;
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

// Canvas API
export const canvasApi = {
  simplifyNode: (projectId: string, nodeId: string) =>
    fetchApi<{ simplified_content: string }>(
      `/api/v1/projects/${projectId}/canvas/nodes/${nodeId}/simplify`,
      {
        method: 'POST',
      }
    ),

  critiqueNode: (projectId: string, nodeId: string) =>
    fetchApi<{ critique_node: CanvasNode }>(
      `/api/v1/projects/${projectId}/canvas/nodes/${nodeId}/critique`,
      {
        method: 'POST',
      }
    ),

  fuseNodes: (projectId: string, nodeId1: string, nodeId2: string) =>
    fetchApi<{ fusion_node: CanvasNode }>(
      `/api/v1/projects/${projectId}/canvas/nodes/fuse`,
      {
        method: 'POST',
        body: JSON.stringify({ node1_id: nodeId1, node2_id: nodeId2 }),
      }
    ),
};

// Curriculum Types
export interface CurriculumStep {
  id: string;
  title: string;
  source: string;
  sourceType: 'document' | 'video';
  pageRange?: string;
  duration: number; // in minutes
}

export interface Curriculum {
  id: string;
  projectId: string;
  steps: CurriculumStep[];
  totalDuration: number;
  createdAt: string;
}

export const curriculumApi = {
  generate: (projectId: string) => 
    fetchApi<Curriculum>(`/api/v1/projects/${projectId}/curriculum/generate`, {
      method: 'POST'
    }),
    
  save: (projectId: string, steps: CurriculumStep[]) =>
    fetchApi<Curriculum>(`/api/v1/projects/${projectId}/curriculum`, {
      method: 'PUT',
      body: JSON.stringify({ steps })
    })
};

// Highlight Types
export interface HighlightCreateRequest {
  pageNumber: number;
  startOffset: number;
  endOffset: number;
  color: 'yellow' | 'green' | 'blue' | 'pink';
  note?: string;
  rects?: Array<{
    left: number;
    top: number;
    width: number;
    height: number;
    right: number;
    bottom: number;
  }>;
}

export interface HighlightUpdateRequest {
  color?: 'yellow' | 'green' | 'blue' | 'pink';
  note?: string;
}

export interface HighlightResponse {
  id: string;
  documentId: string;
  pageNumber: number;
  startOffset: number;
  endOffset: number;
  color: 'yellow' | 'green' | 'blue' | 'pink';
  note?: string;
  createdAt: string;
  updatedAt: string;
}

// Highlights API
export const highlightsApi = {
  list: (documentId: string) =>
    fetchApi<HighlightResponse[]>(`/api/v1/documents/${documentId}/highlights`),

  create: (documentId: string, data: HighlightCreateRequest) =>
    fetchApi<HighlightResponse>(`/api/v1/documents/${documentId}/highlights`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (documentId: string, highlightId: string, data: HighlightUpdateRequest) =>
    fetchApi<HighlightResponse>(`/api/v1/documents/${documentId}/highlights/${highlightId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (documentId: string, highlightId: string) =>
    fetchApi<void>(`/api/v1/documents/${documentId}/highlights/${highlightId}`, {
      method: 'DELETE',
    }),
};
