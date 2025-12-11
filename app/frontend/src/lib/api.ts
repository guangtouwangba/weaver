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
  graph_status?: 'pending' | 'processing' | 'ready' | 'error';
  summary?: string;  // Document summary (generated during processing)
  task_id?: string;  // Async task ID for tracking processing status
  created_at: string;
}

// Citation from Mega-Prompt RAG mode
export interface Citation {
  doc_id: string;        // Mega-prompt doc ID (doc_01, doc_02, etc.)
  document_id: string;   // Actual document UUID
  filename?: string;     // Document filename
  quote: string;         // Original text quoted from document
  conclusion?: string;   // LLM's conclusion/statement
  char_start?: number;   // Character start position in original document
  char_end?: number;     // Character end position
  page_number?: number;  // Page number (calculated from page_map)
  match_score?: number;  // Fuzzy match score (0-100)
}

export interface ChatMessage {
  message: string;
  document_id?: string;
  session_id?: string;  // Chat session ID
}

export interface ChatResponse {
  answer: string;
  sources: Array<{
    document_id: string;
    page_number: number;
    snippet: string;
    similarity: number;
  }>;
  session_id?: string;  // Session this message belongs to
  citations?: Citation[];  // Mega-Prompt mode citations
}

export interface ChatHistoryResponse {
  messages: Array<{
    id: string;
    role: 'user' | 'ai';
    content: string;
    session_id?: string;
    sources?: Array<{
      document_id: string;
      page_number: number;
      snippet: string;
      similarity: number;
    }>;
    created_at: string;
  }>;
}

// Chat Session types
export interface ChatSession {
  id: string;
  project_id: string;
  title: string;
  is_shared: boolean;  // true = shared (cross-device), false = private (device-only)
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
}

export interface ChatSessionListResponse {
  items: ChatSession[];
  total: number;
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
  // New fields for view system
  viewType: 'free' | 'thinking';
  sectionId?: string;
  promotedFrom?: string;
  createdAt?: string;
  updatedAt?: string;
  // New fields for thinking path / message linking
  messageIds?: string[];  // Linked chat message IDs
  analysisStatus?: 'pending' | 'analyzed' | 'error';
  isDuplicate?: boolean;
  duplicateOf?: string;  // Node ID if this is a duplicate
  isUserModified?: boolean;  // True if user has manually edited this node
}

export interface CanvasEdge {
  id?: string;
  source: string;
  target: string;
}

export interface CanvasSection {
  id: string;
  title: string;
  viewType: 'free' | 'thinking';
  isCollapsed: boolean;
  nodeIds: string[];
  x: number;
  y: number;
  width?: number;
  height?: number;
  conversationId?: string;
  question?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface CanvasViewState {
  viewType: 'free' | 'thinking';
  viewport: {
    x: number;
    y: number;
    scale: number;
  };
  selectedNodeIds: string[];
  collapsedSectionIds: string[];
}

export interface CanvasData {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  sections?: CanvasSection[];
  viewport: {
    x: number;
    y: number;
    scale: number;
  };
  viewStates?: {
    free?: CanvasViewState;
    thinking?: CanvasViewState;
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

// Presigned URL response type
interface PresignResponse {
  upload_url: string;
  file_path: string;
  token: string;
  expires_at: string;
}

// Upload progress callback type
type UploadProgressCallback = (progress: number) => void;

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
  
  // Get presigned upload URL (for Supabase Storage direct upload)
  getPresignedUrl: (projectId: string, filename: string, contentType: string = 'application/pdf') =>
    fetchApi<PresignResponse>(`/api/v1/projects/${projectId}/documents/presign`, {
      method: 'POST',
      body: JSON.stringify({ filename, content_type: contentType }),
    }),
  
  // Confirm upload after direct upload to Supabase Storage
  confirmUpload: (
    projectId: string,
    filePath: string,
    filename: string,
    fileSize: number,
    contentType: string = 'application/pdf'
  ) =>
    fetchApi<ProjectDocument>(`/api/v1/projects/${projectId}/documents/confirm`, {
      method: 'POST',
      body: JSON.stringify({
        file_path: filePath,
        filename,
        file_size: fileSize,
        content_type: contentType,
      }),
    }),
  
  // Upload with presigned URL (new method - direct to Supabase Storage)
  uploadWithPresignedUrl: async (
    projectId: string,
    file: File,
    onProgress?: UploadProgressCallback
  ): Promise<ProjectDocument> => {
    // Step 1: Get presigned upload URL
    const presignResponse = await documentsApi.getPresignedUrl(
      projectId,
      file.name,
      file.type || 'application/pdf'
    );
    
    // Step 2: Upload directly to Supabase Storage
    // Supabase signed upload URL expects POST with the file as body
    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });
      
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          console.error('Supabase upload failed:', xhr.status, xhr.responseText);
          reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.responseText}`));
        }
      });
      
      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });
      
      // Supabase Storage uploadToSignedUrl uses PUT with binary body
      // and the token as Authorization header
      // See: https://supabase.com/docs/reference/javascript/storage-from-uploadtosignedurl
      xhr.open('PUT', presignResponse.upload_url);
      xhr.setRequestHeader('Authorization', `Bearer ${presignResponse.token}`);
      xhr.setRequestHeader('Content-Type', file.type || 'application/pdf');
      xhr.send(file);
    });
    
    // Step 3: Confirm upload and process document
    return documentsApi.confirmUpload(
      projectId,
      presignResponse.file_path,
      file.name,
      file.size,
      file.type || 'application/pdf'
    );
  },
  
  // Legacy upload (direct to backend - fallback)
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
  // Session Management
  createSession: (projectId: string, title: string = 'New Conversation', isShared: boolean = true) =>
    fetchApi<ChatSession>(`/api/v1/projects/${projectId}/chat/sessions`, {
      method: 'POST',
      body: JSON.stringify({ title, is_shared: isShared }),
    }),

  listSessions: (projectId: string, includeShared: boolean = true) =>
    fetchApi<ChatSessionListResponse>(
      `/api/v1/projects/${projectId}/chat/sessions?include_shared=${includeShared}`
    ),

  getOrCreateDefaultSession: (projectId: string) =>
    fetchApi<ChatSession>(`/api/v1/projects/${projectId}/chat/sessions/default`),

  updateSession: (projectId: string, sessionId: string, title: string) =>
    fetchApi<ChatSession>(`/api/v1/projects/${projectId}/chat/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),

  deleteSession: (projectId: string, sessionId: string) =>
    fetchApi<{ success: boolean; message: string }>(
      `/api/v1/projects/${projectId}/chat/sessions/${sessionId}`,
      { method: 'DELETE' }
    ),

  // Chat History
  getHistory: (projectId: string, sessionId?: string) =>
    fetchApi<ChatHistoryResponse>(
      `/api/v1/projects/${projectId}/chat/history${sessionId ? `?session_id=${sessionId}` : ''}`
    ),

  send: (projectId: string, message: ChatMessage) =>
    fetchApi<ChatResponse>(`/api/v1/projects/${projectId}/chat`, {
      method: 'POST',
      body: JSON.stringify(message),
    }),
  
  // Streaming chat
  stream: async function* (
    projectId: string,
    message: ChatMessage
  ): AsyncGenerator<{ 
    type: string; 
    content?: string; 
    sources?: ChatResponse['sources'];
    data?: Citation;  // Single citation event
    citations?: Citation[];  // All citations at end
  }> {
    const response = await fetch(
      `${getApiUrl()}/api/v1/projects/${projectId}/chat/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message),
      }
    );

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new ApiError(response.status, `Stream request failed: ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          // Skip empty lines and comments
          if (!trimmed || trimmed.startsWith(':')) continue;
          
          if (trimmed.startsWith('data: ')) {
            try {
              const jsonStr = trimmed.slice(6); // Remove 'data: ' prefix
              if (jsonStr) {
                const data = JSON.parse(jsonStr);
                yield data;
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', trimmed, e);
              // Continue processing other lines
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream reading error:', error);
      throw error;
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

  clear: (projectId: string, viewType?: 'free' | 'thinking') =>
    fetchApi<{ success: boolean; updated_at: string; version: number }>(
      `/api/v1/projects/${projectId}/canvas${viewType ? `?view_type=${viewType}` : ''}`,
      {
        method: 'DELETE',
      }
    ),
};

// Health check
export const healthApi = {
  check: () => fetchApi<{ status: string; environment: string; version: string }>('/health'),
};

// WebSocket URL helper
export function getWebSocketUrl(): string {
  const apiUrl = getApiUrl();
  // Convert HTTP(S) to WS(S)
  return apiUrl
    .replace('https://', 'wss://')
    .replace('http://', 'ws://');
}

// Canvas WebSocket Event Types
export type CanvasEventType =
  | 'node_added'
  | 'node_updated'
  | 'node_deleted'
  | 'edge_added'
  | 'edge_deleted'
  | 'section_added'
  | 'section_updated'
  | 'section_deleted'
  | 'thinking_path_analyzing'
  | 'thinking_path_analyzed'
  | 'thinking_path_error'
  | 'canvas_batch_update';

export interface CanvasWebSocketEvent {
  type: CanvasEventType;
  timestamp: string;
  node_id?: string;
  node_data?: Partial<CanvasNode>;
  message_ids?: string[];
  analysis_status?: 'pending' | 'analyzed' | 'error';
  edge_id?: string;
  source_id?: string;
  target_id?: string;
  nodes?: CanvasNode[];
  edges?: CanvasEdge[];
  sections?: CanvasSection[];
  message_id?: string;
  error_message?: string;
  duplicate_of?: string;
}

// Thinking Path API
export const thinkingPathApi = {
  analyze: (projectId: string, startIndex: number = 0, maxMessages: number = 20) =>
    fetchApi<{
      nodes_created: number;
      edges_created: number;
      duplicate_count: number;
      error?: string;
    }>(`/api/v1/projects/${projectId}/thinking-path/analyze`, {
      method: 'POST',
      body: JSON.stringify({ start_index: startIndex, max_messages: maxMessages }),
    }),

  triggerForMessage: (projectId: string, messageId: string) =>
    fetchApi<{ status: string; message_id: string }>(
      `/api/v1/projects/${projectId}/thinking-path/trigger/${messageId}`,
      { method: 'POST' }
    ),

  clearCache: (projectId: string) =>
    fetchApi<{ status: string; project_id: string }>(
      `/api/v1/projects/${projectId}/thinking-path/cache`,
      { method: 'DELETE' }
    ),
};

// Settings Types
export interface SettingOption {
  value: string;
  label: string;
  description: string;
  cost: 'low' | 'medium' | 'high' | 'variable';
  performance: 'slow' | 'medium' | 'fast' | 'variable';
  best_for: string;
}

export interface SettingMetadata {
  category: string;
  description: string;
  default?: string | number | boolean;
  allowed_values?: string[];
  options?: SettingOption[];
  min?: number;
  max?: number;
  encrypted?: boolean;
}

export interface AllSettingsResponse {
  settings: Record<string, unknown>;
  metadata: Record<string, SettingMetadata>;
}

export interface SettingResponse {
  key: string;
  value: unknown;
  category: string;
  description?: string;
  is_encrypted: boolean;
  is_project_override: boolean;
  is_user_override: boolean;
}

export interface ApiKeyValidationResponse {
  valid: boolean;
  message: string;
  data?: Record<string, unknown>;
}

// Default user ID (placeholder until auth is implemented)
const DEFAULT_USER_ID = '00000000-0000-0000-0000-000000000001';

// Settings API
export const settingsApi = {
  // Get all user settings
  getUserSettings: (userId: string = DEFAULT_USER_ID, category?: string) =>
    fetchApi<AllSettingsResponse>(
      `/api/v1/settings/users/${userId}${category ? `?category=${category}` : ''}`
    ),

  // Get a specific user setting
  getUserSetting: (key: string, userId: string = DEFAULT_USER_ID) =>
    fetchApi<SettingResponse>(`/api/v1/settings/users/${userId}/${key}`),

  // Update a user setting
  updateUserSetting: (
    key: string,
    value: unknown,
    userId: string = DEFAULT_USER_ID,
    description?: string
  ) =>
    fetchApi<SettingResponse>(`/api/v1/settings/users/${userId}/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value, description }),
    }),

  // Delete a user setting (reverts to default)
  deleteUserSetting: (key: string, userId: string = DEFAULT_USER_ID) =>
    fetchApi<{ message: string }>(`/api/v1/settings/users/${userId}/${key}`, {
      method: 'DELETE',
    }),

  // Get settings metadata (for UI rendering)
  getMetadata: () =>
    fetchApi<{ settings: Record<string, SettingMetadata> }>('/api/v1/settings/metadata'),

  // Validate API key
  validateApiKey: (apiKey: string, provider: string = 'openrouter') =>
    fetchApi<ApiKeyValidationResponse>('/api/v1/settings/validate-api-key', {
      method: 'POST',
      body: JSON.stringify({ api_key: apiKey, provider }),
    }),

  // Global settings (admin only)
  getGlobalSettings: (category?: string) =>
    fetchApi<AllSettingsResponse>(
      `/api/v1/settings/global${category ? `?category=${category}` : ''}`
    ),

  updateGlobalSetting: (key: string, value: unknown, description?: string) =>
    fetchApi<SettingResponse>(`/api/v1/settings/global/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value, description }),
    }),
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
  rects?: Array<{
    left: number;
    top: number;
    width: number;
    height: number;
    right: number;
    bottom: number;
  }>;
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

