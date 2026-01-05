'use client';

import React, { useState, useRef } from 'react';
import { Box, Typography, Paper, IconButton, Tooltip } from '@mui/material';
import { FileText, Highlighter, Copy, Share2, Plus, Zap } from 'lucide-react';

interface PDFReviewerProps {
    file: {
        id: string;
        name: string;
        type: string;
    };
    onDragStateChange?: (isDragging: boolean) => void;
}

export default function PDFReviewer({ file, onDragStateChange }: PDFReviewerProps) {
    const [selectedText, setSelectedText] = useState('');
    const [selectionPos, setSelectionPos] = useState({ top: 0, left: 0 });
    const containerRef = useRef<HTMLDivElement>(null);

    const handleMouseUp = (e: React.MouseEvent) => {
        const selection = window.getSelection();
        const text = selection?.toString().trim();
        if (text) {
            setSelectedText(text);
            // Position the float menu near the mouse cursor
            setSelectionPos({ top: e.clientY, left: e.clientX });
        } else {
            setSelectedText('');
        }
    };

    const handleDragStart = (e: React.DragEvent) => {
        if (!selectedText) return;
        
        onDragStateChange?.(true);
        
        const dragData = {
            type: 'insight',
            content: selectedText,
            sourceFileId: file.id,
            sourceFileName: file.name
        };
        
        e.dataTransfer.setData('application/json', JSON.stringify(dragData));
        e.dataTransfer.effectAllowed = 'copy';
        
        // Custom drag image: A small yellow "sticky note" ghost
        const ghost = document.createElement('div');
        ghost.textContent = selectedText.substring(0, 40) + '...';
        ghost.style.width = '120px';
        ghost.style.padding = '12px';
        ghost.style.background = '#FEF9C3'; // Sticky note yellow
        ghost.style.border = '1px solid #EAB308';
        ghost.style.borderRadius = '4px';
        ghost.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)';
        ghost.style.fontSize = '10px';
        ghost.style.color = '#854D0E';
        ghost.style.position = 'absolute';
        ghost.style.top = '-1000px';
        ghost.style.transform = 'rotate(-3deg)';
        document.body.appendChild(ghost);
        e.dataTransfer.setDragImage(ghost, 60, 20);
        setTimeout(() => document.body.removeChild(ghost), 0);
    };

    const handleDragEnd = () => {
        onDragStateChange?.(false);
    };

    return (
        <Box 
            ref={containerRef}
            onMouseUp={handleMouseUp}
            onDragEnd={handleDragEnd}
            sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                height: '100%', 
                bgcolor: '#F3F4F6', 
                p: 4,
                overflowY: 'auto',
                position: 'relative',
                '&::selection': {
                    backgroundColor: 'rgba(0, 150, 255, 0.2)'
                }
            }}
        >
            {/* Simulation of PDF Pages */}
            <Paper
                elevation={2}
                sx={{
                    width: '100%',
                    maxWidth: 800,
                    minHeight: 1100,
                    mx: 'auto',
                    p: 8,
                    bgcolor: 'white',
                    position: 'relative',
                    userSelect: 'text',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
                }}
            >
                <Typography variant="h4" gutterBottom fontWeight={700} sx={{ letterSpacing: '-0.02em' }}>
                    {file.name.replace('.pdf', '').replace(/_/g, ' ')}
                </Typography>
                
                <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: '#374151', fontSize: '1.1rem' }}>
                    The transformer architecture has revolutionized the field of natural language processing. 
                    Unlike previous sequence-to-sequence models that relied on recurrent neural networks (RNNs) 
                    or convolutional neural networks (CNNs), the transformer architecture is based entirely 
                    on attention mechanisms.
                </Typography>

                <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: '#374151', fontSize: '1.1rem' }}>
                    One of the key advantages of the transformer is its ability to parallelize computations, 
                    leading to significantly faster training times on large datasets. This is achieved 
                    through the multi-head attention mechanism, which allows the model to attend to 
                    different parts of the input sequence simultaneously.
                </Typography>

                <Typography 
                    variant="body1" 
                    paragraph 
                    sx={{ 
                        lineHeight: 1.8, 
                        color: '#374151', 
                        bgcolor: '#FEF9C3', 
                        p: 2, 
                        borderRadius: 1, 
                        borderLeft: '4px solid #EAB308',
                        fontSize: '1.1rem'
                    }}
                >
                    "The attention mechanism allows the model to focus on relevant parts of the input 
                    sequence regardless of their distance, effectively solving the vanishing gradient 
                    problem found in traditional RNNs."
                </Typography>

                <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: '#374151', fontSize: '1.1rem' }}>
                    In addition to language modeling, transformers have been successfully applied to 
                    other domains such as computer vision (Vision Transformers) and audio processing. 
                    The scalability of the architecture has paved the way for large-scale pre-trained 
                    models like GPT and BERT, which have set new benchmarks across various tasks.
                </Typography>

                <Typography variant="body1" paragraph sx={{ lineHeight: 1.8, color: '#374151', fontSize: '1.1rem' }}>
                    Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. It has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations.
                </Typography>

                {/* Floating "Peel" Handle near selection */}
                {selectedText && (
                    <Box
                        sx={{
                            position: 'fixed',
                            top: selectionPos.top - 60,
                            left: selectionPos.left,
                            transform: 'translateX(-50%)',
                            zIndex: 2000,
                            animation: 'bounceIn 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                        }}
                    >
                        <Paper
                            elevation={6}
                            draggable
                            onDragStart={handleDragStart}
                            sx={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 0.5,
                                p: 0.5,
                                pr: 1.5,
                                borderRadius: '24px',
                                bgcolor: '#1E293B',
                                color: 'white',
                                cursor: 'grab',
                                '&:active': { cursor: 'grabbing' },
                                border: '1px solid rgba(255,255,255,0.1)',
                                transition: 'transform 0.2s',
                                '&:hover': {
                                    transform: 'scale(1.05)'
                                }
                            }}
                        >
                            <IconButton size="small" sx={{ color: '#FACC15', bgcolor: 'rgba(250, 204, 21, 0.1)', mr: 0.5 }}>
                                <Zap size={18} fill="currentColor" />
                            </IconButton>
                            <Typography variant="caption" fontWeight={600}>
                                Drag Insight
                            </Typography>
                        </Paper>
                    </Box>
                )}
            </Paper>
            
            {/* Page Indicator */}
            <Box 
                sx={{ 
                    position: 'fixed', 
                    bottom: 20, 
                    right: 40, 
                    bgcolor: 'rgba(0,0,0,0.6)', 
                    color: 'white', 
                    px: 2, 
                    py: 0.5, 
                    borderRadius: 1,
                    fontSize: '12px',
                    backdropFilter: 'blur(4px)'
                }}
            >
                Page 1 / 12
            </Box>

            <style jsx global>{`
                @keyframes bounceIn {
                    from { opacity: 0; transform: translateX(-50%) scale(0.5); }
                    to { opacity: 1; transform: translateX(-50%) scale(1); }
                }
            `}</style>
        </Box>
    );
}









