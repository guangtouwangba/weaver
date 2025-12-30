export interface TextSelection {
  text: string;
  rects: DOMRect[];
  pageNumber: number;
}

export interface DragData {
  sourceType: 'pdf';
  sourceId: string;
  sourceTitle: string;
  pageNumber: number;
  content: string;
}

export type AnnotationType = 'highlight' | 'underline' | 'strike' | 'pen' | 'note' | 'comment' | 'image' | 'diagram';

export type ToolMode = 'cursor' | 'hand' | AnnotationType;

export type AnnotationColor = 'yellow' | 'green' | 'blue' | 'pink' | 'red' | 'orange' | 'purple' | 'black';

export interface BaseAnnotation {
  id: string;
  documentId: string;
  pageNumber: number;
  type: AnnotationType;
  color?: AnnotationColor;
  createdAt?: string;
  updatedAt?: string;
  userId?: string;
}

export interface TextAnnotation extends BaseAnnotation {
  type: 'highlight' | 'underline' | 'strike';
  rects: { left: number; top: number; width: number; height: number }[]; // Serializable rects
  text?: string;
  note?: string;
}

export interface DrawingAnnotation extends BaseAnnotation {
  type: 'pen';
  paths: { x: number; y: number }[][];
  strokeWidth: number;
}

export interface CommentAnnotation extends BaseAnnotation {
  type: 'comment';
  text: string;
  position: { x: number; y: number };
  threadId?: string;
}

// Keep legacy Highlight for backward compatibility if needed, or alias it
export type HighlightColor = AnnotationColor;

// Re-export old Highlight as TextAnnotation for now, or just keep it separate to avoid breaking existing code
export interface Highlight {
  id: string;
  documentId: string;
  pageNumber: number;
  startOffset?: number;
  endOffset?: number;
  color: HighlightColor;
  type?: AnnotationType;
  textContent?: string;
  note?: string;
  createdAt?: string;
  updatedAt?: string;
  rects?: DOMRect[];
}
