import React, { useState } from 'react';
import { TextField } from '@/components/ui/composites';
import { Surface, Text as UiText, IconButton } from '@/components/ui/primitives';
import { CloseIcon } from '@/components/ui/icons';

export interface LinkTypeDialogProps {
    position: { x: number; y: number };
    onSelect: (type: string, label?: string) => void;
    onCancel: () => void;
}

export default function LinkTypeDialog({ position, onSelect, onCancel }: LinkTypeDialogProps) {
    const [customLabel, setCustomLabel] = useState('');

    const relationTypes = [
        { type: 'supports', label: 'Support', color: '#059669', description: 'Supports the idea' },
        { type: 'contradicts', label: 'Contradict', color: '#DC2626', description: 'Contradicts the idea' },
        { type: 'correlates', label: 'Correlates', color: '#3B82F6', description: 'Related linearly' },
        { type: 'causes', label: 'Causes', color: '#D97706', description: 'Causal link' },
    ];

    return (
        <Surface
            elevation={4}
            radius="md"
            style={{
                position: 'absolute',
                left: position.x,
                top: position.y,
                transform: 'translate(-50%, -50%)',
                padding: 16,
                minWidth: 280,
                zIndex: 1100,
                backgroundColor: 'white',
                display: 'flex',
                flexDirection: 'column',
                gap: 12
            }}
            role="dialog"
        >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <UiText variant="h6" style={{ fontWeight: 600 }}>Logic Link</UiText>
                <IconButton size="sm" variant="ghost" onClick={onCancel}>
                    <CloseIcon size={16} />
                </IconButton>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {relationTypes.map((rt) => (
                    <div
                        key={rt.type}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            padding: '8px 12px',
                            borderRadius: 8,
                            cursor: 'pointer',
                            border: '1px solid #E5E7EB',
                            transition: 'all 0.2s',
                        }}
                        onClick={() => onSelect(rt.type, rt.label)}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#F3F4F6';
                            e.currentTarget.style.borderColor = rt.color;
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                            e.currentTarget.style.borderColor = '#E5E7EB';
                        }}
                    >
                        <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: rt.color, marginRight: 12 }} />
                        <div style={{ flex: 1 }}>
                            <UiText style={{ fontWeight: 500 }}>{rt.label}</UiText>
                            <UiText variant="caption" style={{ color: '#6B7280' }}>{rt.description}</UiText>
                        </div>
                    </div>
                ))}
            </div>

            <div style={{ marginTop: 8 }}>
                <TextField
                    placeholder="Or type custom label..."
                    value={customLabel}
                    onChange={(e) => setCustomLabel(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && customLabel) {
                            onSelect('custom', customLabel);
                        }
                    }}
                />
            </div>
        </Surface>
    );
}
