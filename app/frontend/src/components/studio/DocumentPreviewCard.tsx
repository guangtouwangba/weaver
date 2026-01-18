'use client';

import React from 'react';
import { ProjectDocument } from '@/lib/api';
import { DeleteIcon, DownloadIcon } from '@/components/ui/icons';
import { fileRegistry } from '@/lib/registry/FileRegistry';

interface DocumentPreviewCardProps {
  document: ProjectDocument;
  isActive: boolean;
  isDeleting?: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
  onDragStart?: (e: React.DragEvent) => void;
}

const formatFileSize = (bytes: number | undefined): string => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const PdfIcon = ({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"
      fill="currentColor"
    />
    <path d="M14 2V8H20" fill="currentColor" fillOpacity="0.5" />
    <text
      x="50%"
      y="15"
      fontFamily="sans-serif"
      fontSize="6"
      fill="white"
      fontWeight="bold"
      textAnchor="middle"
    >
      PDF
    </text>
  </svg>
);

export default function DocumentPreviewCard({
  document: doc,
  isActive,
  isDeleting = false,
  onSelect,
  onDelete,
  onDragStart,
}: DocumentPreviewCardProps) {
  const config = fileRegistry.getConfig(doc.filename);
  const Icon = config.icon;

  // Enable drag for all supported types in registry that aren't 'unknown' (or even unknown if we want)
  // For now, let's allow dragging for everything, Canvas will decide what to do.
  const isDraggable = true;

  // Pass generic drag data
  const handleDragStart = (e: React.DragEvent) => {
    const dragData = {
      type: 'document', // Generic type
      documentId: doc.id,
      title: doc.filename,
      thumbnailUrl: doc.thumbnail_url,
      pageCount: doc.page_count,
      fileType: config.type, // 'pdf', 'text', 'video', etc.
      mimeType: doc.mime_type, // Also pass mime_type if available
    };
    console.log('[DEBUG] DragStart:', dragData);
    e.dataTransfer.setData('application/json', JSON.stringify(dragData));
    e.dataTransfer.effectAllowed = 'copy';

    // Optimize drag image? (Optional: could set a custom drag image here)

    onDragStart?.(e);
  };

  if (isDeleting) {
    return (
      <div className="w-full h-16 bg-white rounded-xl border border-gray-200 flex items-center justify-center relative overflow-hidden">
        <span className="text-gray-500 font-medium text-sm">Deleting...</span>
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-indigo-50">
          <div
            className="h-full bg-indigo-500"
            style={{
              width: '100%',
              animation: 'progress 1.5s infinite linear',
            }}
          />
        </div>
        <style>{`
                    @keyframes progress {
                        0% { transform: translateX(-100%); }
                        100% { transform: translateX(100%); }
                    }
                `}</style>
      </div>
    );
  }

  return (
    <div
      draggable={isDraggable}
      onDragStart={isDraggable ? handleDragStart : undefined}
      onClick={onSelect}
      className={`
                group relative w-full p-3 rounded-xl border transition-all duration-200 flex items-center gap-3
                ${isActive ? 'bg-indigo-50/50 border-indigo-200 ring-1 ring-indigo-500/20' : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'}
                ${isDraggable ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer'}
            `}
      style={
        isActive
          ? {
              backgroundColor: 'transparent',
              borderColor: 'transparent',
            }
          : undefined
      }
    >
      {/* Icon - Dynamic color based on file type */}
      <div
        className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 transition-colors`}
        style={{
          backgroundColor: isActive ? 'transparent' : config.bgColor,
          color: isActive ? '#7C3AED' : config.color,
        }}
      >
        <Icon size={24} className="currentColor" />
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div
          className={`text-sm font-medium truncate transition-colors`}
          title={doc.filename}
          style={{
            color: isActive ? '#7C3AED' : '#111827', // Violet-500 active, or Gray-900 default
          }}
        >
          {doc.filename}
        </div>
        <div className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
          <span>{formatFileSize(doc.file_size)}</span>
          {doc.page_count > 0 && (
            <>
              <span className="w-0.5 h-0.5 rounded-full bg-gray-300" />
              <span>{doc.page_count}p</span>
            </>
          )}
        </div>
      </div>

      {/* Hover Actions */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation(); /* Download logic */
          }}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          title="Download"
        >
          <DownloadIcon size={16} />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(e);
          }}
          className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
          title="Delete"
        >
          <DeleteIcon size={16} />
        </button>
      </div>

      {/* Selection Indicator - Removed for ghost style, or kept very subtle */}
      {/* User requested "just icon color change", so no heavy background/border */}
    </div>
  );
}
