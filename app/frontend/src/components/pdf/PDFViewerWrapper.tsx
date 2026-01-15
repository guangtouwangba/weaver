import React, { useEffect, useRef } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { PDFViewer, EventBus, PDFLinkService, PDFFindController } from 'pdfjs-dist/web/pdf_viewer';
import 'pdfjs-dist/web/pdf_viewer.css';
import { TextSelection } from './types';

// Initialize worker
if (typeof window !== 'undefined' && !pdfjsLib.GlobalWorkerOptions.workerSrc) {
  pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;
}

interface PDFViewerWrapperProps {
  fileUrl: string;
  pageNumber: number;
  width: number;
  onPageChange: (page: number) => void;
  onDocumentLoad: (numPages: number) => void;
  onTextSelect?: (selection: TextSelection | null) => void; // Optional if handled externally via SelectionManager
  highlightText?: string;
}

export function PDFViewerWrapper({
  fileUrl,
  pageNumber,
  width, // Currently unused in direct PDFViewer instantiation as it handles its own sizing, but passed for prop compatibility
  onPageChange,
  onDocumentLoad,
  onTextSelect,
  highlightText,
}: PDFViewerWrapperProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const eventBusRef = useRef<EventBus | null>(null);
  const viewerRef = useRef<PDFViewer | null>(null);
  const linkServiceRef = useRef<PDFLinkService | null>(null);
  const findControllerRef = useRef<PDFFindController | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize EventBus and PDFViewer
    const eventBus = new EventBus();
    eventBusRef.current = eventBus;

    const linkService = new PDFLinkService({ eventBus });
    linkServiceRef.current = linkService;

    const findController = new PDFFindController({
      eventBus,
      linkService,
    });
    findControllerRef.current = findController;

    const viewer = new PDFViewer({
      container: containerRef.current,
      eventBus,
      linkService,
      findController,
      textLayerMode: 2, // Enable enhanced text layer
      annotationMode: 2,
    });
    viewerRef.current = viewer;

    linkService.setViewer(viewer);

    // Listen for document load
    eventBus.on('pagesinit', () => {
      viewer.currentScaleValue = 'page-width'; // Scale to page width by default
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    eventBus.on('pagechanging', (evt: any) => {
      if (evt.pageNumber !== pageNumber) {
        onPageChange(evt.pageNumber);
      }
    });

    // Load PDF
    const loadDocument = async () => {
      console.log('[PDFViewerWrapper] Loading PDF:', fileUrl);
      try {
        const loadingTask = pdfjsLib.getDocument(fileUrl);
        const pdf = await loadingTask.promise;
        console.log('[PDFViewerWrapper] PDF loaded, pages:', pdf.numPages);
        viewer.setDocument(pdf);
        linkService.setDocument(pdf);
        onDocumentLoad(pdf.numPages);
      } catch (error) {
        console.error('Error loading PDF:', error);
      }
    };

    loadDocument();

    return () => {
      // Cleanup
      // viewer.cleanup() might be needed but it also clears the container
      // If we unmount, we should probably destroy.
      // pdfjs-dist 4.x structure might differ slightly in cleanup methods
      // viewer.cleanup() mainly clears rendering queues.
    };
  }, [fileUrl]);

  // Handle page jump
  useEffect(() => {
    if (viewerRef.current && pageNumber > 0) {
      // Avoid loop if already on page
      if (viewerRef.current.currentPageNumber !== pageNumber) {
        viewerRef.current.currentPageNumber = pageNumber;
      }
    }
  }, [pageNumber]);

  // Handle highlight text
  useEffect(() => {
    if (viewerRef.current && findControllerRef.current && highlightText) {
      // Try to find and highlight the text
      // If search fails, the page jump will still work (handled by pageNumber effect)
      try {
        findControllerRef.current.executeCommand('find', {
          query: highlightText,
          highlightAll: true,
          phraseSearch: true,
        });
      } catch (error) {
        // Silently fail - page navigation will still work
        console.debug('PDF text search failed:', error);
      }
    }
  }, [highlightText]);

  return (
    <div ref={containerRef} className="pdf-viewer-container" style={{ position: 'absolute', width: '100%', height: '100%', overflow: 'auto' }}>
      <div className="pdfViewer" />
    </div>
  );
}
