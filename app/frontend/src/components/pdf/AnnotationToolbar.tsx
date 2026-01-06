import React from 'react';
import {
    Highlighter,
    Underline,
    Strikethrough,
    PenTool,
    StickyNote,
    MessageSquarePlus,
    Image as ImageIcon,
    Shapes,
    MousePointer2
} from 'lucide-react';
import { ToolMode, AnnotationColor } from './types';

interface AnnotationToolbarProps {
    activeTool: ToolMode;
    onToolChange: (tool: ToolMode) => void;
    activeColor: AnnotationColor;
    onColorChange: (color: AnnotationColor) => void;
}

const TOOLS = [
    { id: 'highlight', icon: Highlighter, label: 'Highlight' },
    { id: 'underline', icon: Underline, label: 'Underline' },
    { id: 'strike', icon: Strikethrough, label: 'Strikethrough' },
    { id: 'pen', icon: PenTool, label: 'Pen' },
    { id: 'note', icon: StickyNote, label: 'Note' },
    { id: 'comment', icon: MessageSquarePlus, label: 'Comment' },
    { id: 'image', icon: ImageIcon, label: 'Image' },
    { id: 'diagram', icon: Shapes, label: 'Diagram' },
] as const;

const COLORS: { id: AnnotationColor; class: string; border: string }[] = [
    { id: 'yellow', class: 'bg-yellow-300', border: 'border-yellow-400' },
    { id: 'green', class: 'bg-green-300', border: 'border-green-400' },
    { id: 'blue', class: 'bg-blue-300', border: 'border-blue-400' },
    { id: 'pink', class: 'bg-pink-300', border: 'border-pink-400' },
    { id: 'red', class: 'bg-red-500', border: 'border-red-600' },
    { id: 'orange', class: 'bg-orange-400', border: 'border-orange-500' },
    { id: 'purple', class: 'bg-purple-400', border: 'border-purple-500' },
    { id: 'black', class: 'bg-stone-900', border: 'border-stone-700' },
];

export default function AnnotationToolbar({
    activeTool,
    onToolChange,
    activeColor,
    onColorChange
}: AnnotationToolbarProps) {

    const handleToolClick = (toolId: ToolMode) => {
        // Toggle off if already active
        if (activeTool === toolId) {
            onToolChange('cursor');
        } else {
            onToolChange(toolId);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header with Cursor Reset */}
            <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
                    Annotation Tools
                </span>
                <button
                    onClick={() => onToolChange('cursor')}
                    className={`p-1.5 rounded-lg transition-colors ${activeTool === 'cursor' || activeTool === 'hand'
                        ? 'bg-teal-50 text-teal-600'
                        : 'text-stone-400 hover:text-stone-600'
                        }`}
                    title="Select / Cursor Mode"
                >
                    <MousePointer2 size={16} />
                </button>
            </div>

            {/* Tools Grid (2 rows x 4 columns) */}
            <div className="grid grid-cols-4 gap-3">
                {TOOLS.map((tool) => {
                    const isActive = activeTool === tool.id;
                    const Icon = tool.icon;

                    return (
                        <button
                            key={tool.id}
                            onClick={() => handleToolClick(tool.id as ToolMode)}
                            className={`
                aspect-square flex flex-col items-center justify-center rounded-xl transition-all duration-200
                ${isActive
                                    ? 'bg-teal-50 text-teal-600 ring-2 ring-teal-500 ring-offset-2 shadow-sm'
                                    : 'bg-stone-50 text-stone-500 hover:bg-stone-100 hover:text-stone-800'
                                }
              `}
                            title={tool.label}
                        >
                            <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                        </button>
                    );
                })}
            </div>

            {/* Color Selection (Only show if tool supports color) */}
            {(['highlight', 'underline', 'strike', 'pen', 'note'].includes(activeTool as string)) && (
                <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                    <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider block">
                        Color
                    </span>
                    <div className="flex flex-wrap gap-2">
                        {COLORS.map((color) => (
                            <button
                                key={color.id}
                                onClick={() => onColorChange(color.id)}
                                className={`
                   w-8 h-8 rounded-full border-2 transition-transform duration-200 
                   ${color.class} 
                   ${color.border}
                   ${activeColor === color.id ? 'scale-110 ring-2 ring-offset-2 ring-stone-300' : 'hover:scale-105 opacity-80 hover:opacity-100'}
                 `}
                                title={color.id}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
