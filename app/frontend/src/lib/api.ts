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
  thumbnail_url?: string;  // URL for PDF thumbnail image
  thumbnail_status?: 'pending' | 'processing' | 'ready' | 'error' | null;  // Thumbnail generation status
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
  context_node_ids?: string[];  // Optional: explicit context from canvas nodes (for DB lookup)
  context_nodes?: Array<{  // Optional: explicit context content from canvas nodes (direct)
    id: string;
    title: string;
    content: string;
  }>;
  context_url_ids?: string[];  // Optional: URL content IDs for video/article context
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
    context_refs?: {
      url_ids?: string[];
      urls?: Array<{ id: string; title: string; platform?: string; url?: string }>;
      node_ids?: string[];
      nodes?: Array<{ id: string; title: string }>;
    };
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
  generation?: number;  // Generation ID for async clear support
  createdAt?: string;
  updatedAt?: string;
  // New fields for thinking path / message linking
  messageIds?: string[];  // Linked chat message IDs
  analysisStatus?: 'pending' | 'analyzed' | 'error';
  isDuplicate?: boolean;
  duplicateOf?: string;  // Node ID if this is a duplicate
  isUserModified?: boolean;  // True if user has manually edited this node
  // Phase 1: Source Node support (The Portal)
  subType?: 'source' | 'note' | 'insight';  // Distinguishes source files from regular notes
  fileMetadata?: {
    fileType: 'pdf' | 'markdown' | 'web' | 'text' | 'youtube' | 'video' | 'bilibili' | 'douyin';
    pageCount?: number;
    author?: string;
    lastModified?: string;
    thumbnailUrl?: string;  // PDF first page thumbnail or video thumbnail
    // Video-specific metadata
    videoId?: string;
    duration?: number;
    channelName?: string;
    viewCount?: string;
    publishedAt?: string;
    sourceUrl?: string;
  };
  // === Thinking Graph Fields (Dynamic Mind Map) ===
  thinkingStepIndex?: number;  // Step number in the thinking sequence
  thinkingFields?: {
    claim: string;      // Main point or question
    reason: string;     // Why this matters
    evidence: string;   // Supporting information
    uncertainty: string; // What's unclear
    decision: string;   // Conclusion or next step
  };
  branchType?: 'alternative' | 'question' | 'counterargument';  // For branch nodes
  depth?: number;       // Tree depth for layout (0 for root)
  parentStepId?: string;  // ID of parent thinking step
  isDraft?: boolean;    // True while waiting for AI response (optimistic UI)
  topicId?: string;     // Topic context this node belongs to
  relatedConcepts?: string[];  // Extracted concepts for linking
  suggestedBranches?: Array<{
    type: 'question' | 'alternative' | 'counterargument';
    content: string;
  }>;
  
  // === Unified Node Model: Generation Output Fields ===
  // For nodes created from generation outputs (mindmap, summary, etc.)
  outputId?: string;        // Backend output ID for persistence
  outputData?: Record<string, unknown>;  // SummaryData | MindmapData | ArticleData | etc.
  generatedFrom?: {
    documentIds?: string[];
    nodeIds?: string[];      // Source nodes for Magic Cursor generation
    snapshotContext?: { x: number; y: number; width: number; height: number };
  };
}

export interface CanvasEdge {
  id?: string;
  source: string;
  target: string;
  generation?: number;  // Generation ID for async clear support

  // Edge label (AI-generated or user-defined)
  label?: string;

  // Semantic relationship type for Thinking Path
  relationType?:
  // Core Q&A relationships
  | 'answers'           // Q→A: Question gets answered
  | 'prompts_question'  // A→Q': Answer leads to follow-up question
  | 'derives'           // A→Insight: Answer derives insight
  // Logical relationships
  | 'causes'            // A→B: Causal relationship (因果)
  | 'compares'          // A↔B: Comparison/contrast (对比)
  | 'supports'          // Evidence supporting a claim
  | 'contradicts'       // Evidence contradicting a claim
  // Evolution relationships
  | 'revises'           // A→A': Correction/update (修正)
  | 'extends'           // Building on previous point
  // Organization
  | 'parks'             // Main→Parking: Temporarily set aside (暂存)
  | 'groups'            // Grouping relationship
  | 'belongs_to'        // Legacy: belongs to group
  | 'related'           // Legacy: generic relation
  | 'correlates'        // Strong thematic connection
  // User-defined
  | 'custom';

  // Edge direction hint (for bidirectional relations like 'compares')
  direction?: 'forward' | 'backward' | 'bidirectional';

  // Thinking Path edge types (for styling compatibility)
  type?: 'branch' | 'progression';

  // === Connection Anchor & Routing (P0) ===
  // Anchor points: N(top), S(bottom), E(right), W(left), auto(calculated)
  sourceAnchor?: 'N' | 'S' | 'E' | 'W' | 'auto';
  targetAnchor?: 'N' | 'S' | 'E' | 'W' | 'auto';
  // Routing algorithm for edge path
  routingType?: 'straight' | 'bezier' | 'orthogonal';

  // === Visual Customization (P1) ===
  color?: string;           // Override color
  strokeWidth?: number;     // Override thickness
  strokeDash?: number[];    // Custom dash pattern e.g. [5, 5]
  markerStart?: 'arrow' | 'circle' | 'none';
  markerEnd?: 'arrow' | 'circle' | 'none';
}

export interface CanvasSection {
  id: string;
  title: string;
  viewType: 'free' | 'thinking';
  isCollapsed: boolean;
  nodeIds: string[];
  x: number;
  y: number;
  generation?: number;  // Generation ID for async clear support
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
    step?: string;  // For status events: rewriting, memory, analyzing, retrieving, ranking, generating
    message?: string;  // Human-readable status message
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

  deleteNode: (projectId: string, nodeId: string) =>
    fetchApi<{ success: boolean; updated_at: string; version: number }>(
      `/api/v1/projects/${projectId}/canvas/nodes/${nodeId}`,
      {
        method: 'DELETE',
      }
    ),

  clear: (projectId: string, viewType?: 'free' | 'thinking') =>
    fetchApi<{ success: boolean; updated_at: string; version: number }>(
      `/api/v1/projects/${projectId}/canvas${viewType ? `?view_type=${viewType}` : ''}`,
      {
        method: 'DELETE',
      }
    ),

  verifyRelation: (
    sourceContent: string,
    targetContent: string,
    relationType: string
  ) =>
    fetchApi<{ valid: boolean; reasoning: string; confidence: number }>(
      `/api/v1/canvas/verify-relation`,
      {
        method: 'POST',
        body: JSON.stringify({
          source_content: sourceContent,
          target_content: targetContent,
          relation_type: relationType,
        }),
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

// Document WebSocket Event Types
export type DocumentEventType = 'document_status';

export interface DocumentWebSocketEvent {
  type: DocumentEventType;
  document_id: string;
  status: 'pending' | 'processing' | 'ready' | 'error';
  summary?: string;
  page_count?: number;
  graph_status?: 'pending' | 'processing' | 'ready' | 'error';
  error_message?: string;
}

// Output WebSocket Event Types (for mindmap, summary generation, etc.)
export type OutputEventType =
  | 'generation_started'
  | 'generation_progress'
  | 'generation_complete'
  | 'generation_error'
  | 'node_generating'
  | 'node_added'
  | 'node_updated'
  | 'edge_added'
  | 'level_complete'
  | 'token';

export interface OutputWebSocketEvent {
  type: OutputEventType;
  taskId?: string;
  timestamp?: string;
  // Generation lifecycle
  outputType?: string;
  outputId?: string;  // ID of the generated output (for generation_complete)
  message?: string;
  progress?: number;
  errorMessage?: string;
  // Mindmap node/edge events
  nodeId?: string;
  nodeData?: Partial<MindmapNode>;
  edgeId?: string;
  edgeData?: Partial<MindmapEdge>;
  // Level progress
  currentLevel?: number;
  totalLevels?: number;
  // Token streaming
  token?: string;
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
  type?: string; // highlight, underline, strike, etc.
  textContent?: string;
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
  type?: string;
  textContent?: string;
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

// Comment Types
export interface CommentCreateRequest {
  content: string;
  parent_id?: string;
  page_number?: number;
  highlight_id?: string;
  author_name?: string;
}

export interface CommentResponse {
  id: string;
  document_id: string;
  parent_id?: string;
  page_number?: number;
  highlight_id?: string;
  content: string;
  author_name: string;
  created_at: string;
  updated_at: string;
  reply_count: number;
}

export interface CommentListResponse {
  comments: CommentResponse[];
  total: number;
}

// Comments API
export const commentsApi = {
  list: (documentId: string) =>
    fetchApi<CommentListResponse>(`/api/v1/documents/${documentId}/comments`),

  create: (documentId: string, data: CommentCreateRequest) =>
    fetchApi<CommentResponse>(`/api/v1/documents/${documentId}/comments`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  listReplies: (documentId: string, commentId: string) =>
    fetchApi<CommentResponse[]>(`/api/v1/documents/${documentId}/comments/${commentId}/replies`),

  update: (documentId: string, commentId: string, content: string) =>
    fetchApi<CommentResponse>(`/api/v1/documents/${documentId}/comments/${commentId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    }),

  delete: (documentId: string, commentId: string) =>
    fetchApi<void>(`/api/v1/documents/${documentId}/comments/${commentId}`, {
      method: 'DELETE',
    }),
};

// Output Generation Types
export interface KeyFinding {
  label: string;
  content: string;
}

export interface SummaryData {
  summary: string;
  keyFindings: KeyFinding[];
  documentTitle: string;
}

/**
 * Reference to source content for traceability and drilldown.
 * Supports multiple source types for future extensibility:
 * - document: PDF, markdown, etc. (location = page number)
 * - video/audio: Media files (location = timestamp in seconds)
 * - web: URLs (location = URL with optional text fragment)
 * - node: Canvas nodes (location = node ID)
 */
export interface SourceRef {
  sourceId: string;       // ID of the source entity (document_id, node_id, etc.)
  sourceType: 'document' | 'node' | 'video' | 'audio' | 'web';
  location?: string;      // Page number, timestamp, URL fragment, etc.
  quote: string;          // Exact quoted text or transcript segment
}

export interface MindmapNode {
  id: string;
  label: string;
  content: string;
  depth: number;
  parentId?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  status: 'generating' | 'complete' | 'error';
  sourceRefs?: SourceRef[];  // Source references for drilldown
}

export interface MindmapEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export interface MindmapData {
  nodes: MindmapNode[];
  edges: MindmapEdge[];
  rootId?: string;
}

// Article Data (Magic Cursor: Draft Article)
export interface ArticleSection {
  heading: string;
  content: string;
}

export interface ArticleData {
  title: string;
  sections: ArticleSection[];
  sourceRefs: SourceRef[];
  snapshotContext?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

// Action List Data (Magic Cursor: Action List)
export interface ActionItem {
  id: string;
  text: string;
  done: boolean;
  priority: 'high' | 'medium' | 'low';
}

export interface ActionListData {
  title: string;
  items: ActionItem[];
  sourceRefs: SourceRef[];
  snapshotContext?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export type OutputType = 'mindmap' | 'summary' | 'flashcards' | 'custom' | 'article' | 'action_list';

export interface OutputResponse {
  id: string;
  project_id: string;
  output_type: OutputType;
  document_ids: string[];
  status: 'generating' | 'complete' | 'error' | 'cancelled';
  title?: string;
  data?: SummaryData | MindmapData | ArticleData | ActionListData | Record<string, unknown>;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface GenerateOutputResponse {
  task_id: string;
  output_id: string;
  status: string;
  websocket_channel: string;
}

export interface OutputListResponse {
  outputs: OutputResponse[];
  total: number;
}

// Outputs API
export const outputsApi = {
  generate: (
    projectId: string,
    outputType: OutputType,
    documentIds: string[],
    title?: string,
    options?: Record<string, unknown>,
    urlContentIds?: string[]
  ) =>
    fetchApi<GenerateOutputResponse>(`/api/v1/projects/${projectId}/outputs/generate`, {
      method: 'POST',
      body: JSON.stringify({
        output_type: outputType,
        document_ids: documentIds,
        url_content_ids: urlContentIds || [],
        title,
        options,
      }),
    }),

  get: (projectId: string, outputId: string) =>
    fetchApi<OutputResponse>(`/api/v1/projects/${projectId}/outputs/${outputId}`),

  list: (
    projectId: string,
    outputType?: string,
    limit: number = 20,
    offset: number = 0
  ) =>
    fetchApi<OutputListResponse>(
      `/api/v1/projects/${projectId}/outputs?${new URLSearchParams({
        ...(outputType && { output_type: outputType }),
        limit: limit.toString(),
        offset: offset.toString(),
      })}`
    ),

  delete: (projectId: string, outputId: string) =>
    fetchApi<void>(`/api/v1/projects/${projectId}/outputs/${outputId}`, {
      method: 'DELETE',
    }),

  cancelTask: (projectId: string, taskId: string) =>
    fetchApi<void>(`/api/v1/projects/${projectId}/outputs/tasks/${taskId}/cancel`, {
      method: 'POST',
    }),

  update: (
    projectId: string,
    outputId: string,
    updates: { title?: string; data?: Record<string, unknown> }
  ) =>
    fetchApi<OutputResponse>(`/api/v1/projects/${projectId}/outputs/${outputId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),

  synthesize: (
    projectId: string,
    outputId: string,
    nodeIds: string[],
    mode: 'connect' | 'inspire' | 'debate' = 'connect',
    nodeData?: Array<{ id: string; title: string; content: string }>
  ) =>
    fetchApi<{ task_id: string; action: string }>(
      `/api/v1/projects/${projectId}/outputs/${outputId}/synthesize`,
      {
        method: 'POST',
        body: JSON.stringify({ node_ids: nodeIds, mode, node_data: nodeData }),
      }
    ),
};

// =============================================================================
// Inbox Types & API
// =============================================================================

export interface InboxTag {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface InboxItem {
  id: string;
  title: string | null;
  type: 'article' | 'video' | 'note' | 'pdf' | 'link';
  source_url: string | null;
  content: string | null;
  thumbnail_url: string | null;
  source_type: string; // 'extension', 'manual', 'upload'
  meta_data: Record<string, unknown>;
  collected_at: string;
  is_read: boolean;
  is_processed: boolean;
  tags: InboxTag[];
}

export interface InboxItemListResponse {
  items: InboxItem[];
  total: number;
}

export interface InboxItemCreate {
  title?: string;
  type: string;
  source_url?: string;
  content?: string;
  thumbnail_url?: string;
  source_type: string;
  meta_data?: Record<string, unknown>;
  is_read?: boolean;
  is_processed?: boolean;
  tag_ids?: string[];
}

// Inbox API
export const inboxApi = {
  list: (params?: {
    skip?: number;
    limit?: number;
    is_processed?: boolean;
    type?: string;
    tag_id?: string;
    q?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.set('skip', params.skip.toString());
    if (params?.limit !== undefined) searchParams.set('limit', params.limit.toString());
    if (params?.is_processed !== undefined) searchParams.set('is_processed', params.is_processed.toString());
    if (params?.type) searchParams.set('type', params.type);
    if (params?.tag_id) searchParams.set('tag_id', params.tag_id);
    if (params?.q) searchParams.set('q', params.q);

    const query = searchParams.toString();
    return fetchApi<InboxItemListResponse>(`/api/v1/inbox/items${query ? `?${query}` : ''}`);
  },

  get: (itemId: string) =>
    fetchApi<InboxItem>(`/api/v1/inbox/items/${itemId}`),

  delete: (itemId: string) =>
    fetchApi<void>(`/api/v1/inbox/items/${itemId}`, { method: 'DELETE' }),

  assignToProject: (itemId: string, projectId: string) =>
    fetchApi<void>(`/api/v1/inbox/items/${itemId}/assign/${projectId}`, { method: 'POST' }),

  // For internal use (manual item creation)
  create: (item: InboxItemCreate) =>
    fetchApi<InboxItem>('/api/v1/inbox/items', {
      method: 'POST',
      body: JSON.stringify(item),
    }),
};

// Tags API
export const tagsApi = {
  list: () =>
    fetchApi<{ items: InboxTag[] }>('/api/v1/tags'),

  create: (name: string, color: string = 'blue') =>
    fetchApi<InboxTag>('/api/v1/tags', {
      method: 'POST',
      body: JSON.stringify({ name, color }),
    }),

  delete: (tagId: string) =>
    fetchApi<void>(`/api/v1/tags/${tagId}`, { method: 'DELETE' }),
};

// =============================================================================
// URL Content Extraction API
// =============================================================================

export interface UrlContent {
  id: string;
  url: string;
  normalized_url: string;
  platform: 'youtube' | 'bilibili' | 'douyin' | 'web';
  content_type: 'video' | 'article' | 'link';
  title: string | null;
  content: string | null;
  thumbnail_url: string | null;
  meta_data: Record<string, unknown>;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  updated_at: string;
  extracted_at: string | null;
  project_id: string | null;
}

export interface UrlContentListResponse {
  items: UrlContent[];
  total: number;
}

export interface UrlContentStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  title: string | null;
  thumbnail_url: string | null;
}

export const urlApi = {
  /**
   * Extract content from a URL.
   * Returns immediately with status="pending".
   * Use getStatus() to poll for completion.
   */
  extract: (url: string, options: { force?: boolean; projectId?: string } = {}) =>
    fetchApi<UrlContent>('/api/v1/url/extract', {
      method: 'POST',
      body: JSON.stringify({ 
        url, 
        force: options.force ?? false,
        project_id: options.projectId,
      }),
    }),

  /**
   * List all URL contents for a project.
   */
  listByProject: (projectId: string) =>
    fetchApi<UrlContentListResponse>(`/api/v1/url/projects/${projectId}/contents`),

  /**
   * Delete a URL content record.
   */
  delete: (id: string) =>
    fetchApi<void>(`/api/v1/url/extract/${id}`, {
      method: 'DELETE',
    }),

  /**
   * Get full URL content by ID.
   */
  get: (id: string) =>
    fetchApi<UrlContent>(`/api/v1/url/extract/${id}`),

  /**
   * Get lightweight status for polling.
   */
  getStatus: (id: string) =>
    fetchApi<UrlContentStatus>(`/api/v1/url/extract/${id}/status`),

  /**
   * Poll for extraction completion with retry.
   * @param id URL content ID
   * @param options Polling options
   * @returns Full URL content when completed
   */
  waitForCompletion: async (
    id: string,
    options: {
      maxAttempts?: number;
      intervalMs?: number;
      onStatusChange?: (status: UrlContentStatus) => void;
    } = {}
  ): Promise<UrlContent> => {
    const { maxAttempts = 60, intervalMs = 1000, onStatusChange } = options;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await urlApi.getStatus(id);
      
      if (onStatusChange) {
        onStatusChange(status);
      }

      if (status.status === 'completed') {
        return urlApi.get(id);
      }

      if (status.status === 'failed') {
        throw new Error(status.error_message || 'URL extraction failed');
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }

    throw new Error('URL extraction timed out');
  },
};

