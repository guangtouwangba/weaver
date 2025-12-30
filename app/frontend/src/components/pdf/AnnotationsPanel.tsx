import React, { useMemo } from 'react';
import { Highlight } from './types';
import { Trash2, MessageSquare, StickyNote, Loader2 } from 'lucide-react';

interface AnnotationsPanelProps {
    highlights?: Highlight[];
    onNavigate?: (page: number) => void;
    onDelete?: (id: string) => void;
    isLoading?: boolean;
    error?: string | null;
}

export default function AnnotationsPanel({
    highlights = [],
    onNavigate,
    onDelete,
    isLoading = false,
    error = null
}: AnnotationsPanelProps) {

    // Group by page and sort by date descending
    const groupedHighlights = useMemo(() => {
        const sorted = [...highlights].sort((a, b) => {
            return (new Date(b.createdAt || 0).getTime()) - (new Date(a.createdAt || 0).getTime());
        });

        // Group
        const groups: Record<number, Highlight[]> = {};
        sorted.forEach(h => {
            if (!groups[h.pageNumber]) groups[h.pageNumber] = [];
            groups[h.pageNumber].push(h);
        });

        return groups;
    }, [highlights]);

    const pageNumbers = Object.keys(groupedHighlights).map(Number).sort((a, b) => a - b);

    return (
        <div className="flex-1 overflow-y-auto min-h-0 pb-4">
            {isLoading ? (
                <div className="flex items-center justify-center py-8 text-gray-400">
                    <Loader2 size={24} className="animate-spin mr-2" />
                    <span className="text-sm">Loading annotations...</span>
                </div>
            ) : error ? (
                <div className="text-center text-red-500 text-sm py-8">
                    {error}
                </div>
            ) : highlights.length === 0 ? (
                <div className="text-center text-gray-400 text-sm py-8">
                    No annotations yet.
                    <br />Select text to highlight.
                </div>
            ) : (
                <div className="space-y-6">
                    {pageNumbers.map(page => (
                        <div key={page}>
                            <div
                                className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 sticky top-0 bg-white py-1 cursor-pointer hover:text-blue-600"
                                onClick={() => onNavigate?.(page)}
                            >
                                Page {page}
                            </div>
                            <div className="space-y-2">
                                {groupedHighlights[page].map(highlight => (
                                    <div
                                        key={highlight.id}
                                        className="group bg-white p-3 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow relative"
                                    >
                                        {/* Action Buttons */}
                                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 bg-white pl-2">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onDelete?.(highlight.id);
                                                }}
                                                className="p-1 hover:bg-red-50 text-gray-400 hover:text-red-500 rounded"
                                                title="Delete"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>

                                        {/* Content Click to Navigate */}
                                        <div
                                            onClick={() => onNavigate?.(highlight.pageNumber)}
                                            className="cursor-pointer"
                                        >
                                            <div className="flex items-center gap-2 mb-1">
                                                <div
                                                    className={`w-3 h-3 rounded-full border border-gray-300 opacity-80`}
                                                    style={{
                                                        backgroundColor: highlight.color === 'yellow' ? '#FFEB3B' :
                                                            highlight.color === 'green' ? '#4CAF50' :
                                                                highlight.color === 'blue' ? '#2196F3' : '#E91E63'
                                                    }}
                                                />
                                                <span className="text-xs text-gray-400">
                                                    {new Date(highlight.createdAt || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                            </div>

                                            {highlight.note ? (
                                                <div className="flex items-start gap-2 mt-2 bg-yellow-50 p-2 rounded text-xs text-gray-700">
                                                    <StickyNote size={12} className="mt-0.5 text-yellow-600 flex-shrink-0" />
                                                    <span className="line-clamp-3">{highlight.note}</span>
                                                </div>
                                            ) : (
                                                <div className="text-sm text-gray-600 italic">
                                                    Highlight
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
