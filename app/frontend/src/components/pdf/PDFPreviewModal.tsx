'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useStudio } from '@/contexts/StudioContext';
import { PDFViewer } from './PDFViewer';
import PageThumbnailSidebar from './PageThumbnailSidebar';
import AnnotationToolbar from './AnnotationToolbar';
import AnnotationsPanel from './AnnotationsPanel';
import CommentsPanel from './CommentsPanel';
import { ToolMode, AnnotationColor, Highlight } from './types';
import { highlightsApi } from '@/lib/api';
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Search, MoreVertical, LayoutGrid, List } from 'lucide-react'; // Assuming we have generic icons or I'll use text if not

export default function PDFPreviewModal() {
    const {
        isPreviewModalOpen,
        closeDocumentPreview,
        previewDocumentId,
        documents,
        projectId,
        addNodeToCanvas,
        viewport
    } = useStudio();

    const [pageNumber, setPageNumber] = useState(1);
    const [numPages, setNumPages] = useState(0);
    const [scale, setScale] = useState(1.0);
    const [activeRightTab, setActiveRightTab] = useState<'tools' | 'comments'>('tools');
    const [sidebarMode, setSidebarMode] = useState<'list' | 'grid'>('list');

    // Tool State
    const [toolMode, setToolMode] = useState<ToolMode>('cursor');
    const [activeColor, setActiveColor] = useState<AnnotationColor>('yellow');

    // Data State
    const [highlights, setHighlights] = useState<Highlight[]>([]);
    const [selectedSnippet, setSelectedSnippet] = useState<{
        text: string;
        pageNumber: number;
        color?: string;
    } | null>(null);
    const [isLoadingHighlights, setIsLoadingHighlights] = useState(false);
    const [highlightsError, setHighlightsError] = useState<string | null>(null);

    // Reset state when opening a new document
    useEffect(() => {
        if (isPreviewModalOpen) {
            setPageNumber(1);
            setScale(1.0);
            // Highlights will be loaded by the specific effect below
        }
    }, [isPreviewModalOpen, previewDocumentId]);

    // Keyboard shortcuts
    useEffect(() => {
        if (!isPreviewModalOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            // Escape to close
            if (e.key === 'Escape') {
                closeDocumentPreview();
            }
            // Arrow keys for page navigation
            if (e.key === 'ArrowLeft' && pageNumber > 1) {
                setPageNumber(prev => prev - 1);
            }
            if (e.key === 'ArrowRight' && pageNumber < numPages) {
                setPageNumber(prev => prev + 1);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isPreviewModalOpen, closeDocumentPreview, pageNumber, numPages]);

    const activeDocument = useMemo(() =>
        documents.find(d => d.id === previewDocumentId),
        [documents, previewDocumentId]);

    // Load Highlights
    useEffect(() => {
        if (!activeDocument?.id) {
            setHighlights([]);
            setHighlightsError(null);
            return;
        }

        const loadHighlights = async () => {
            setIsLoadingHighlights(true);
            setHighlightsError(null);
            try {
                const list = await highlightsApi.list(activeDocument.id);
                const processed = list.map(h => ({
                    ...h,
                    rects: h.rects ? h.rects.map((r: any) => new DOMRect(r.left, r.top, r.width, r.height)) : []
                }));
                setHighlights(processed);
            } catch (e) {
                console.error("Failed to load highlights", e);
                setHighlightsError("Failed to load annotations");
            } finally {
                setIsLoadingHighlights(false);
            }
        };
        loadHighlights();
    }, [activeDocument?.id]);

    // Handlers
    const handleHighlightCreate = (h: Highlight) => {
        setHighlights(prev => [...prev, h]);
    };

    const handleHighlightUpdate = (h: Highlight) => {
        setHighlights(prev => prev.map(cur => cur.id === h.id ? h : cur));
    };

    const handleHighlightDelete = (id: string) => {
        setHighlights(prev => prev.filter(h => h.id !== id));
    };

    // Handle Add to Whiteboard
    const handleAddToWhiteboard = useCallback(() => {
        // Use selected snippet if available, otherwise use a default message
        const snippetText = selectedSnippet?.text || 'PDF Excerpt';
        const snippetPage = selectedSnippet?.pageNumber || pageNumber;

        // Calculate position at viewport center
        const centerX = viewport ? (-viewport.x + 400) / viewport.scale : 200;
        const centerY = viewport ? (-viewport.y + 300) / viewport.scale : 200;

        // Create snippet node
        addNodeToCanvas({
            type: 'knowledge',
            title: `Snippet from ${activeDocument?.filename || 'PDF'}`,
            content: snippetText,
            x: centerX,
            y: centerY,
            width: 280,
            height: 180,
            color: selectedSnippet?.color || '#FEF3C7', // Light yellow default
            tags: ['snippet', 'pdf-excerpt'],
            sourceId: activeDocument?.id,
            sourcePage: snippetPage,
            viewType: 'free',
            subType: 'note',
        });

        // Close modal
        closeDocumentPreview();
        setSelectedSnippet(null);
    }, [selectedSnippet, pageNumber, viewport, addNodeToCanvas, activeDocument, closeDocumentPreview]);

    if (!isPreviewModalOpen || !activeDocument) return null;

    // -- Handlers --

    const handlePageChange = (newPage: number) => {
        setPageNumber(Math.max(1, Math.min(newPage, numPages)));
    };

    const handleDocumentLoad = (total: number) => {
        setNumPages(total);
    };

    const handleZoomIn = () => setScale(s => Math.min(s + 0.1, 3.0));
    const handleZoomOut = () => setScale(s => Math.max(s - 0.1, 0.5));

    // Construct file URL since it's not in the ProjectDocument interface
    // Backend endpoint is /api/v1/documents/{documentId}/file (no project prefix)
    const fileUrl = activeDocument ? `/api/v1/documents/${activeDocument.id}/file` : null;

    return (
        <div className="fixed inset-0 z-[1301] flex flex-col bg-white animate-in fade-in slide-in-from-bottom-4 duration-200">
            {/* Top Bar / Header */}
            <div className="h-14 border-b border-gray-200 flex items-center justify-between px-4 bg-white shadow-sm z-10">
                {/* Left: Back & Title */}
                <div className="flex items-center gap-4 w-1/4">
                    <button
                        onClick={closeDocumentPreview}
                        className="flex items-center text-gray-600 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-100 transition-colors"
                    >
                        {/* Fallback chevron if lucide not avail, but assuming standard build */}
                        <span className="mr-2">←</span> Back
                    </button>
                    <div className="flex flex-col overflow-hidden">
                        <span className="font-medium text-gray-900 truncate" title={activeDocument.filename}>
                            {activeDocument.filename}
                        </span>
                        <span className="text-xs text-gray-500">
                            Updated {new Date(activeDocument.updated_at || Date.now()).toLocaleDateString()}
                        </span>
                    </div>
                </div>

                {/* Center: Zoom & Navigation */}
                <div className="flex items-center gap-2">
                    <div className="flex items-center bg-gray-100 rounded-lg p-1">
                        <button onClick={handleZoomOut} className="p-1 hover:bg-white rounded shadow-sm disabled:opacity-50">
                            -
                        </button>
                        <span className="px-3 text-xs font-mono w-16 text-center">{Math.round(scale * 100)}%</span>
                        <button onClick={handleZoomIn} className="p-1 hover:bg-white rounded shadow-sm disabled:opacity-50">
                            +
                        </button>
                    </div>
                    <div className="w-px h-6 bg-gray-300 mx-2" />
                    <div className="flex items-center bg-gray-100 rounded-lg p-1">
                        <button
                            onClick={() => handlePageChange(pageNumber - 1)}
                            disabled={pageNumber <= 1}
                            className="p-1 hover:bg-white rounded shadow-sm disabled:opacity-50"
                        >
                            {'<'}
                        </button>
                        <span className="px-3 text-xs font-mono">
                            {pageNumber} / {numPages || '-'}
                        </span>
                        <button
                            onClick={() => handlePageChange(pageNumber + 1)}
                            disabled={pageNumber >= numPages}
                            className="p-1 hover:bg-white rounded shadow-sm disabled:opacity-50"
                        >
                            {'>'}
                        </button>
                    </div>
                </div>

                {/* Right: Search & Actions */}
                <div className="flex items-center justify-end gap-3 w-1/4">
                    <div className="relative">
                        <input
                            type="text"
                            placeholder="Find in document..."
                            className="bg-gray-100 border-none rounded-lg py-1.5 pl-9 pr-3 text-sm w-48 focus:ring-2 focus:ring-blue-500 outline-none"
                        />
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
                    </div>
                    <button className="p-2 hover:bg-gray-100 rounded-full text-gray-600">
                        ⋮
                    </button>
                </div>
            </div>

            {/* Main Content Area: 3-Panel Layout */}
            <div className="flex-1 flex overflow-hidden">

                {/* Left Panel: Thumbnails */}
                <div className="w-64 border-r border-gray-200 bg-gray-50 flex flex-col">
                    <div className="h-10 border-b border-gray-200 flex items-center justify-between px-3 bg-white">
                        <span className="text-xs font-semibold text-gray-500 uppercase">Pages</span>
                        <div className="flex bg-gray-100 rounded p-0.5">
                            <button
                                onClick={() => setSidebarMode('grid')}
                                className={`p-1 rounded ${sidebarMode === 'grid' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-400'}`}
                            >
                                ⊞
                            </button>
                            <button
                                onClick={() => setSidebarMode('list')}
                                className={`p-1 rounded ${sidebarMode === 'list' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-400'}`}
                            >
                                ≣
                            </button>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        <PageThumbnailSidebar
                            fileUrl={fileUrl}
                            numPages={numPages}
                            currentPage={pageNumber}
                            onPageClick={handlePageChange}
                        />
                    </div>
                </div>

                {/* Center Panel: Content */}
                <div className="flex-1 bg-gray-100 relative items-center justify-center overflow-auto flex">
                    {/* 
                The PDFViewer handles its own scrolling internally usually, 
                but we need to make sure it expands to fill this container.
             */}
                    <div className="h-full w-full">
                        {fileUrl ? (
                            <PDFViewer
                                documentId={activeDocument.id}
                                fileUrl={fileUrl}
                                pageNumber={pageNumber}
                                onPageChange={setPageNumber}
                                onDocumentLoad={handleDocumentLoad}
                                activeTool={toolMode}
                                activeColor={activeColor}
                                highlights={highlights}
                                onHighlightCreate={handleHighlightCreate}
                                onHighlightUpdate={handleHighlightUpdate}
                                onHighlightDelete={handleHighlightDelete}
                            />
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-400">
                                Document URL not available
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel: Tools & Comments */}
                <div className="w-80 border-l border-gray-200 bg-white flex flex-col shadow-xl z-20">
                    {/* Tabs */}
                    <div className="flex border-b border-gray-200">
                        <button
                            onClick={() => setActiveRightTab('tools')}
                            className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${activeRightTab === 'tools'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            Tools
                        </button>
                        <button
                            onClick={() => setActiveRightTab('comments')}
                            className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${activeRightTab === 'comments'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            Comments
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-6">
                        {activeRightTab === 'tools' ? (
                            <>
                                <AnnotationToolbar
                                    activeTool={toolMode}
                                    onToolChange={setToolMode}
                                    activeColor={activeColor}
                                    onColorChange={setActiveColor}
                                />
                                <hr className="border-gray-100" />
                                <AnnotationsPanel
                                    highlights={highlights}
                                    onNavigate={(page) => setPageNumber(page)}
                                    onDelete={handleHighlightDelete}
                                    isLoading={isLoadingHighlights}
                                    error={highlightsError}
                                />
                            </>
                        ) : (
                            <CommentsPanel documentId={activeDocument.id} />
                        )}
                    </div>

                    {/* Footer Action */}
                    {activeRightTab === 'tools' && (
                        <div className="p-4 border-t border-gray-200 bg-gray-50">
                            <button
                                onClick={handleAddToWhiteboard}
                                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm transition-colors flex items-center justify-center gap-2"
                            >
                                <span>+</span> Add to Whiteboard
                            </button>
                            <p className="text-center text-[10px] text-gray-400 mt-2">
                                {selectedSnippet ? `"${selectedSnippet.text.slice(0, 40)}..."` : 'Select text to add as snippet'}
                            </p>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
}
