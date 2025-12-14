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

export type HighlightColor = 'yellow' | 'green' | 'blue' | 'pink';

export interface Highlight {
  id: string;
  documentId: string;
  pageNumber: number;
  startOffset?: number; // Optional as we are using rects primarily for now
  endOffset?: number;
  color: HighlightColor;
  note?: string;
  createdAt?: string;
  updatedAt?: string;
  rects?: DOMRect[];
}
