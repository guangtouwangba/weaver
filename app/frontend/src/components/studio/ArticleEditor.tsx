'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { colors, radii, shadows, fontSize, fontWeight, spacing } from '@/components/ui/tokens';

export interface ArticleSection {
  heading: string;
  content: string;
}

export interface ArticleData {
  title: string;
  sections: ArticleSection[];
  sourceRefs?: Array<{
    source_id: string;
    source_type: string;
    location?: string;
    quote?: string;
  }>;
}

interface ArticleEditorProps {
  nodeId: string;
  initialData: ArticleData;
  onSave: (nodeId: string, data: ArticleData) => void;
  onCancel: () => void;
}

/**
 * ArticleEditor - A modal for viewing/editing generated articles.
 */
export default function ArticleEditor({
  nodeId,
  initialData,
  onSave,
  onCancel,
}: ArticleEditorProps) {
  const [title, setTitle] = useState(initialData.title || '');
  const [sections, setSections] = useState<ArticleSection[]>(initialData.sections || []);
  const [editingSectionIndex, setEditingSectionIndex] = useState<number | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const handleSave = useCallback(() => {
    onSave(nodeId, {
      title,
      sections,
      sourceRefs: initialData.sourceRefs,
    });
  }, [nodeId, title, sections, initialData.sourceRefs, onSave]);

  // Handle backdrop click (auto-save on blur)
  const handleBackdropClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleSave();
    }
  }, [handleSave]);

  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleSave();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleSave]);

  const handleSectionChange = (index: number, field: 'heading' | 'content', value: string) => {
    setSections(prev => prev.map((s, i) => 
      i === index ? { ...s, [field]: value } : s
    ));
  };

  const handleAddSection = () => {
    setSections(prev => [...prev, { heading: 'New Section', content: '' }]);
    setEditingSectionIndex(sections.length);
  };

  const handleDeleteSection = (index: number) => {
    setSections(prev => prev.filter((_, i) => i !== index));
    setEditingSectionIndex(null);
  };

  return (
    <div
      onClick={handleBackdropClick}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1400,
      }}
    >
      <div
        ref={modalRef}
        style={{
          width: '100%',
          maxWidth: 720,
          maxHeight: '85vh',
          backgroundColor: colors.background.paper,
          borderRadius: radii.xl,
          boxShadow: shadows.xl,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: spacing[5],
            borderBottom: `1px solid ${colors.border.default}`,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: spacing[3], marginBottom: spacing[2] }}>
            <span style={{ fontSize: '24px' }}>📄</span>
            <span style={{ 
              fontSize: fontSize.sm, 
              fontWeight: fontWeight.medium,
              color: 'rgba(255,255,255,0.8)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              Generated Article
            </span>
          </div>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Article Title"
            style={{
              width: '100%',
              border: 'none',
              outline: 'none',
              fontSize: fontSize['2xl'],
              fontWeight: fontWeight.bold,
              color: '#FFFFFF',
              backgroundColor: 'transparent',
            }}
          />
        </div>

        {/* Content - Scrollable Sections */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: spacing[5],
          }}
        >
          {sections.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: spacing[8], 
              color: colors.text.secondary 
            }}>
              <p>No sections yet. Click &quot;Add Section&quot; to get started.</p>
            </div>
          ) : (
            sections.map((section, index) => (
              <div
                key={index}
                style={{
                  marginBottom: spacing[6],
                  padding: spacing[4],
                  backgroundColor: editingSectionIndex === index ? colors.neutral[50] : 'transparent',
                  borderRadius: radii.lg,
                  border: `1px solid ${editingSectionIndex === index ? colors.primary[200] : 'transparent'}`,
                  transition: 'all 0.2s ease',
                }}
                onClick={() => setEditingSectionIndex(index)}
              >
                {/* Section Heading */}
                {editingSectionIndex === index ? (
                  <input
                    type="text"
                    value={section.heading}
                    onChange={(e) => handleSectionChange(index, 'heading', e.target.value)}
                    style={{
                      width: '100%',
                      border: 'none',
                      outline: 'none',
                      fontSize: fontSize.lg,
                      fontWeight: fontWeight.semibold,
                      color: colors.text.primary,
                      backgroundColor: 'transparent',
                      marginBottom: spacing[2],
                    }}
                    autoFocus
                  />
                ) : (
                  <h3 style={{
                    fontSize: fontSize.lg,
                    fontWeight: fontWeight.semibold,
                    color: colors.text.primary,
                    marginBottom: spacing[2],
                  }}>
                    {section.heading}
                  </h3>
                )}

                {/* Section Content */}
                {editingSectionIndex === index ? (
                  <textarea
                    value={section.content}
                    onChange={(e) => handleSectionChange(index, 'content', e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: 120,
                      border: 'none',
                      outline: 'none',
                      resize: 'vertical',
                      fontSize: fontSize.base,
                      lineHeight: 1.7,
                      color: colors.text.primary,
                      backgroundColor: 'transparent',
                      fontFamily: 'inherit',
                    }}
                  />
                ) : (
                  <p style={{
                    fontSize: fontSize.base,
                    lineHeight: 1.7,
                    color: colors.text.secondary,
                    whiteSpace: 'pre-wrap',
                  }}>
                    {section.content}
                  </p>
                )}

                {/* Delete Button */}
                {editingSectionIndex === index && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSection(index);
                    }}
                    style={{
                      marginTop: spacing[2],
                      padding: `${spacing[1]} ${spacing[3]}`,
                      fontSize: fontSize.xs,
                      color: colors.error[600],
                      backgroundColor: colors.error[50],
                      border: 'none',
                      borderRadius: radii.md,
                      cursor: 'pointer',
                    }}
                  >
                    Delete Section
                  </button>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: spacing[4],
            borderTop: `1px solid ${colors.border.default}`,
            backgroundColor: colors.neutral[50],
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <button
            onClick={handleAddSection}
            style={{
              padding: `${spacing[2]} ${spacing[4]}`,
              fontSize: fontSize.sm,
              fontWeight: fontWeight.medium,
              color: colors.primary[600],
              backgroundColor: colors.primary[50],
              border: 'none',
              borderRadius: radii.md,
              cursor: 'pointer',
            }}
          >
            + Add Section
          </button>
          
          <span style={{ fontSize: fontSize.xs, color: colors.text.secondary }}>
            {sections.length} section{sections.length !== 1 ? 's' : ''} • Click outside to save
          </span>
        </div>
      </div>
    </div>
  );
}

