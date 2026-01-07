'use client';

/**
 * Super Card Modal Components
 * 
 * Modal dialogs for viewing and editing Super Card content:
 * - DocumentCardModal: Rich text editor for article content
 * - TicketCardModal: Action item management (CRUD, drag-to-reorder)
 */

import React, { useState, useCallback } from 'react';
import { Dialog } from '@/components/ui/composites';
import { Button, Stack, Text, Surface, IconButton } from '@/components/ui';
import { CloseIcon, EditIcon, DeleteIcon, AddIcon, CheckIcon, SaveIcon } from '@/components/ui/icons';
import { ArticleData, ActionListData, ActionItem, ArticleSection } from '@/lib/api';
import { colors, shadows } from '@/components/ui/tokens';

// ============================================================================
// Document Card Modal (Article Viewer/Editor)
// ============================================================================

interface DocumentCardModalProps {
  open: boolean;
  onClose: () => void;
  data: ArticleData;
  onSave?: (data: ArticleData) => void;
}

export const DocumentCardModal: React.FC<DocumentCardModalProps> = ({
  open,
  onClose,
  data,
  onSave,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState<ArticleData>(data);
  
  const handleSave = useCallback(() => {
    onSave?.(editedData);
    setIsEditing(false);
  }, [editedData, onSave]);
  
  const handleSectionChange = useCallback((index: number, field: 'heading' | 'content', value: string) => {
    setEditedData(prev => ({
      ...prev,
      sections: prev.sections.map((s, i) => 
        i === index ? { ...s, [field]: value } : s
      ),
    }));
  }, []);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={
        <Stack direction="row" align="center" justify="between" style={{ width: '100%' }}>
          <Stack direction="row" align="center" gap={2}>
            <span style={{ fontSize: 24 }}>📄</span>
            <Text variant="h3">{data.title}</Text>
          </Stack>
          <Stack direction="row" gap={1}>
            {isEditing ? (
              <>
                <Button variant="ghost" size="sm" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
                <Button variant="default" size="sm" onClick={handleSave}>
                  <SaveIcon size={16} />
                  <span style={{ marginLeft: 4 }}>Save</span>
                </Button>
              </>
            ) : (
              <IconButton size="sm" variant="ghost" onClick={() => setIsEditing(true)}>
                <EditIcon size={18} />
              </IconButton>
            )}
          </Stack>
        </Stack>
      }
      maxWidth={720}
    >
      <div style={{ maxHeight: '70vh', overflowY: 'auto', padding: '16px 0' }}>
        {editedData.sections.map((section, index) => (
          <div key={index} style={{ marginBottom: 24 }}>
            {isEditing ? (
              <>
                <input
                  type="text"
                  value={section.heading}
                  onChange={(e) => handleSectionChange(index, 'heading', e.target.value)}
                  style={{
                    width: '100%',
                    fontSize: 18,
                    fontWeight: 600,
                    border: 'none',
                    borderBottom: `2px solid ${colors.primary.main}`,
                    padding: '8px 0',
                    marginBottom: 12,
                    outline: 'none',
                    background: 'transparent',
                  }}
                />
                <textarea
                  value={section.content}
                  onChange={(e) => handleSectionChange(index, 'content', e.target.value)}
                  rows={6}
                  style={{
                    width: '100%',
                    fontSize: 14,
                    lineHeight: 1.7,
                    border: `1px solid ${colors.border.light}`,
                    borderRadius: 8,
                    padding: 12,
                    resize: 'vertical',
                    fontFamily: 'inherit',
                    outline: 'none',
                  }}
                />
              </>
            ) : (
              <>
                <Text variant="h4" style={{ marginBottom: 12, color: colors.primary.main }}>
                  {section.heading}
                </Text>
                <Text
                  variant="body1"
                  style={{
                    lineHeight: 1.8,
                    color: colors.text.primary,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {section.content}
                </Text>
              </>
            )}
          </div>
        ))}
        
        {/* Source References */}
        {data.sourceRefs && data.sourceRefs.length > 0 && (
          <Surface
            elevation={0}
            bordered
            radius="md"
            style={{ padding: 16, marginTop: 24, background: colors.background.subtle }}
          >
            <Text variant="caption" color="secondary" style={{ marginBottom: 8, display: 'block' }}>
              SOURCES ({data.sourceRefs.length})
            </Text>
            {data.sourceRefs.map((ref, index) => (
              <Text
                key={index}
                variant="body2"
                color="secondary"
                style={{ marginBottom: 4, fontStyle: 'italic' }}
              >
                • {ref.quote}
              </Text>
            ))}
          </Surface>
        )}
      </div>
    </Dialog>
  );
};

// ============================================================================
// Ticket Card Modal (Action List Manager)
// ============================================================================

interface TicketCardModalProps {
  open: boolean;
  onClose: () => void;
  data: ActionListData;
  onSave?: (data: ActionListData) => void;
}

export const TicketCardModal: React.FC<TicketCardModalProps> = ({
  open,
  onClose,
  data,
  onSave,
}) => {
  const [items, setItems] = useState<ActionItem[]>(data.items);
  const [newItemText, setNewItemText] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  
  const handleToggle = useCallback((id: string) => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, done: !item.done } : item
    ));
  }, []);
  
  const handleDelete = useCallback((id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  }, []);
  
  const handleAdd = useCallback(() => {
    if (!newItemText.trim()) return;
    
    const newItem: ActionItem = {
      id: `item-${Date.now()}`,
      text: newItemText.trim(),
      done: false,
      priority: 'medium',
    };
    
    setItems(prev => [...prev, newItem]);
    setNewItemText('');
  }, [newItemText]);
  
  const handleStartEdit = useCallback((item: ActionItem) => {
    setEditingId(item.id);
    setEditText(item.text);
  }, []);
  
  const handleSaveEdit = useCallback(() => {
    if (!editingId || !editText.trim()) return;
    
    setItems(prev => prev.map(item =>
      item.id === editingId ? { ...item, text: editText.trim() } : item
    ));
    setEditingId(null);
    setEditText('');
  }, [editingId, editText]);
  
  const handlePriorityChange = useCallback((id: string, priority: 'high' | 'medium' | 'low') => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, priority } : item
    ));
  }, []);
  
  const handleSave = useCallback(() => {
    onSave?.({ ...data, items });
    onClose();
  }, [data, items, onSave, onClose]);
  
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };
  
  const completedCount = items.filter(item => item.done).length;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={
        <Stack direction="row" align="center" justify="between" style={{ width: '100%' }}>
          <Stack direction="row" align="center" gap={2}>
            <span style={{ fontSize: 24 }}>✅</span>
            <Text variant="h3">{data.title}</Text>
            <Text variant="caption" color="secondary">
              ({completedCount}/{items.length} completed)
            </Text>
          </Stack>
          <Button variant="default" size="sm" onClick={handleSave}>
            <SaveIcon size={16} />
            <span style={{ marginLeft: 4 }}>Save</span>
          </Button>
        </Stack>
      }
      maxWidth={560}
    >
      <div style={{ maxHeight: '70vh', overflowY: 'auto', padding: '16px 0' }}>
        {/* Add new item */}
        <Stack direction="row" gap={2} style={{ marginBottom: 20 }}>
          <input
            type="text"
            value={newItemText}
            onChange={(e) => setNewItemText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            placeholder="Add new action item..."
            style={{
              flex: 1,
              padding: '10px 14px',
              border: `1px solid ${colors.border.light}`,
              borderRadius: 8,
              fontSize: 14,
              outline: 'none',
            }}
          />
          <Button variant="default" size="sm" onClick={handleAdd} disabled={!newItemText.trim()}>
            <AddIcon size={16} />
          </Button>
        </Stack>
        
        {/* Items list */}
        <Stack direction="column" gap={1}>
          {items.map((item) => (
            <Surface
              key={item.id}
              elevation={0}
              bordered
              radius="md"
              style={{
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                opacity: item.done ? 0.6 : 1,
                background: item.done ? colors.background.subtle : '#FFFFFF',
              }}
            >
              {/* Checkbox */}
              <button
                onClick={() => handleToggle(item.id)}
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: 4,
                  border: `2px solid ${item.done ? '#10B981' : colors.border.main}`,
                  background: item.done ? '#10B981' : 'transparent',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {item.done && <CheckIcon size={14} style={{ color: '#FFFFFF' }} />}
              </button>
              
              {/* Priority selector */}
              <select
                value={item.priority}
                onChange={(e) => handlePriorityChange(item.id, e.target.value as 'high' | 'medium' | 'low')}
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: '50%',
                  border: 'none',
                  background: getPriorityColor(item.priority),
                  cursor: 'pointer',
                  appearance: 'none',
                  WebkitAppearance: 'none',
                  flexShrink: 0,
                }}
                title={`Priority: ${item.priority}`}
              >
                <option value="high">🔴</option>
                <option value="medium">🟡</option>
                <option value="low">🟢</option>
              </select>
              
              {/* Text (editable) */}
              {editingId === item.id ? (
                <input
                  type="text"
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  onBlur={handleSaveEdit}
                  onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                  autoFocus
                  style={{
                    flex: 1,
                    border: 'none',
                    borderBottom: `1px solid ${colors.primary.main}`,
                    fontSize: 14,
                    padding: '4px 0',
                    outline: 'none',
                    background: 'transparent',
                  }}
                />
              ) : (
                <Text
                  variant="body2"
                  style={{
                    flex: 1,
                    textDecoration: item.done ? 'line-through' : 'none',
                    cursor: 'text',
                  }}
                  onClick={() => handleStartEdit(item)}
                >
                  {item.text}
                </Text>
              )}
              
              {/* Delete button */}
              <IconButton
                size="sm"
                variant="ghost"
                onClick={() => handleDelete(item.id)}
                style={{ flexShrink: 0 }}
              >
                <DeleteIcon size={16} />
              </IconButton>
            </Surface>
          ))}
        </Stack>
        
        {items.length === 0 && (
          <Text variant="body2" color="secondary" style={{ textAlign: 'center', padding: 32 }}>
            No action items yet. Add one above!
          </Text>
        )}
      </div>
    </Dialog>
  );
};

