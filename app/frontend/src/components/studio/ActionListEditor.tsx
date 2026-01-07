'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { colors, radii, shadows, fontSize, fontWeight, spacing } from '@/components/ui/tokens';

export interface ActionItem {
  id: string;
  text: string;
  done: boolean;
  priority?: 'high' | 'medium' | 'low';
}

export interface ActionListData {
  title: string;
  items: ActionItem[];
  sourceRefs?: Array<{
    source_id: string;
    source_type: string;
    location?: string;
    quote?: string;
  }>;
}

interface ActionListEditorProps {
  nodeId: string;
  initialData: ActionListData;
  onSave: (nodeId: string, data: ActionListData) => void;
  onCancel: () => void;
}

/**
 * ActionListEditor - A modal for viewing/editing generated action lists.
 */
export default function ActionListEditor({
  nodeId,
  initialData,
  onSave,
  onCancel,
}: ActionListEditorProps) {
  const [title, setTitle] = useState(initialData.title || '');
  const [items, setItems] = useState<ActionItem[]>(initialData.items || []);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [newItemText, setNewItemText] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);
  const newItemInputRef = useRef<HTMLInputElement>(null);

  const handleSave = useCallback(() => {
    onSave(nodeId, {
      title,
      items,
      sourceRefs: initialData.sourceRefs,
    });
  }, [nodeId, title, items, initialData.sourceRefs, onSave]);

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

  const handleToggleItem = (itemId: string) => {
    setItems(prev => prev.map(item =>
      item.id === itemId ? { ...item, done: !item.done } : item
    ));
  };

  const handleItemTextChange = (itemId: string, text: string) => {
    setItems(prev => prev.map(item =>
      item.id === itemId ? { ...item, text } : item
    ));
  };

  const handleAddItem = () => {
    if (!newItemText.trim()) return;
    
    const newItem: ActionItem = {
      id: `item-${Date.now()}`,
      text: newItemText.trim(),
      done: false,
    };
    setItems(prev => [...prev, newItem]);
    setNewItemText('');
    newItemInputRef.current?.focus();
  };

  const handleDeleteItem = (itemId: string) => {
    setItems(prev => prev.filter(item => item.id !== itemId));
    setEditingItemId(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddItem();
    }
  };

  const completedCount = items.filter(item => item.done).length;
  const totalCount = items.length;
  const progressPercent = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

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
          maxWidth: 560,
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
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: spacing[3], marginBottom: spacing[2] }}>
            <span style={{ fontSize: '24px' }}>✅</span>
            <span style={{ 
              fontSize: fontSize.sm, 
              fontWeight: fontWeight.medium,
              color: 'rgba(255,255,255,0.9)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}>
              Action List
            </span>
          </div>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="List Title"
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
          
          {/* Progress Bar */}
          <div style={{ marginTop: spacing[3] }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: spacing[1],
            }}>
              <span style={{ fontSize: fontSize.sm, color: 'rgba(255,255,255,0.9)' }}>
                Progress
              </span>
              <span style={{ fontSize: fontSize.sm, color: 'rgba(255,255,255,0.9)' }}>
                {completedCount}/{totalCount}
              </span>
            </div>
            <div style={{
              height: 6,
              backgroundColor: 'rgba(255,255,255,0.3)',
              borderRadius: radii.full,
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${progressPercent}%`,
                backgroundColor: '#FFFFFF',
                borderRadius: radii.full,
                transition: 'width 0.3s ease',
              }} />
            </div>
          </div>
        </div>

        {/* Content - Scrollable Items */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: spacing[4],
          }}
        >
          {items.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: spacing[8], 
              color: colors.text.secondary 
            }}>
              <p>No items yet. Add your first action item below.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: spacing[2] }}>
              {items.map((item) => (
                <div
                  key={item.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: spacing[3],
                    padding: spacing[3],
                    backgroundColor: editingItemId === item.id ? colors.neutral[50] : 'transparent',
                    borderRadius: radii.lg,
                    border: `1px solid ${editingItemId === item.id ? colors.warning[200] : 'transparent'}`,
                    transition: 'all 0.2s ease',
                  }}
                  onClick={() => setEditingItemId(item.id)}
                >
                  {/* Checkbox */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleItem(item.id);
                    }}
                    style={{
                      width: 22,
                      height: 22,
                      minWidth: 22,
                      borderRadius: radii.md,
                      border: `2px solid ${item.done ? colors.success[500] : colors.neutral[300]}`,
                      backgroundColor: item.done ? colors.success[500] : 'transparent',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {item.done && (
                      <span style={{ color: '#FFFFFF', fontSize: '14px', fontWeight: 'bold' }}>✓</span>
                    )}
                  </button>

                  {/* Item Content */}
                  <div style={{ flex: 1 }}>
                    {editingItemId === item.id ? (
                      <input
                        type="text"
                        value={item.text}
                        onChange={(e) => handleItemTextChange(item.id, e.target.value)}
                        style={{
                          width: '100%',
                          border: 'none',
                          outline: 'none',
                          fontSize: fontSize.base,
                          color: colors.text.primary,
                          backgroundColor: 'transparent',
                        }}
                        autoFocus
                      />
                    ) : (
                      <span style={{
                        fontSize: fontSize.base,
                        color: item.done ? colors.text.secondary : colors.text.primary,
                        textDecoration: item.done ? 'line-through' : 'none',
                      }}>
                        {item.text}
                      </span>
                    )}

                    {/* Delete Button */}
                    {editingItemId === item.id && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteItem(item.id);
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
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add Item Input */}
        <div
          style={{
            padding: spacing[4],
            borderTop: `1px solid ${colors.border.default}`,
            backgroundColor: colors.neutral[50],
          }}
        >
          <div style={{ display: 'flex', gap: spacing[2] }}>
            <input
              ref={newItemInputRef}
              type="text"
              value={newItemText}
              onChange={(e) => setNewItemText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Add a new action item..."
              style={{
                flex: 1,
                padding: `${spacing[2]} ${spacing[3]}`,
                fontSize: fontSize.sm,
                border: `1px solid ${colors.border.default}`,
                borderRadius: radii.md,
                outline: 'none',
              }}
            />
            <button
              onClick={handleAddItem}
              disabled={!newItemText.trim()}
              style={{
                padding: `${spacing[2]} ${spacing[4]}`,
                fontSize: fontSize.sm,
                fontWeight: fontWeight.medium,
                color: newItemText.trim() ? '#FFFFFF' : colors.text.secondary,
                backgroundColor: newItemText.trim() ? colors.warning[500] : colors.neutral[200],
                border: 'none',
                borderRadius: radii.md,
                cursor: newItemText.trim() ? 'pointer' : 'not-allowed',
              }}
            >
              Add
            </button>
          </div>
          
          <div style={{ marginTop: spacing[2], textAlign: 'right' }}>
            <span style={{ fontSize: fontSize.xs, color: colors.text.secondary }}>
              Click outside to save • Press Enter to add
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

