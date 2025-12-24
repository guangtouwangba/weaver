'use client';

import React, { useState } from 'react';
import { Paper, InputBase, IconButton, Box, Tooltip } from '@mui/material';
import { ArrowUp, Sparkles } from 'lucide-react';

const GLOBAL_SIDEBAR_WIDTH = 72;

interface ChatInputProps {
    isConnectionMode?: boolean;
    onToggleConnectionMode?: (active: boolean) => void;
    onChatSubmit?: (value: string) => void;
}

export default function ChatInput({ isConnectionMode, onToggleConnectionMode, onChatSubmit }: ChatInputProps) {
    const [value, setValue] = useState('');
    const [isFocused, setIsFocused] = useState(false);

    const handleSubmit = () => {
        if (!value.trim()) return;
        onChatSubmit?.(value);
        setValue('');
    };

    return (
        <Box
            sx={{
                position: 'fixed',
                bottom: 40,
                left: `calc(50% + ${GLOBAL_SIDEBAR_WIDTH / 2}px)`,
                transform: 'translateX(-50%)',
                width: '100%',
                maxWidth: 640,
                px: 2,
                zIndex: 1200,
            }}
        >
            <Paper
                elevation={isFocused ? 8 : 4}
                sx={{
                    p: '6px 8px 6px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    borderRadius: '28px',
                    backgroundColor: 'white',
                    border: isFocused ? '1px solid #6366F1' : '1px solid rgba(0, 0, 0, 0.08)',
                    boxShadow: isFocused 
                        ? '0 8px 32px rgba(99, 102, 241, 0.15), 0 4px 12px rgba(0, 0, 0, 0.08)'
                        : '0 4px 20px rgba(0, 0, 0, 0.08)',
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
            >
                {/* AI Icon */}
                <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    mr: 1.5,
                    color: '#6366F1'
                }}>
                    <Sparkles size={18} />
                </Box>

                <InputBase
                    sx={{ 
                        flex: 1, 
                        fontSize: '0.95rem',
                        '& input::placeholder': {
                            color: 'text.secondary',
                            opacity: 0.7
                        }
                    }}
                    placeholder="Ask Weaver to regroup or summarize these insights..."
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit();
                        }
                    }}
                    multiline
                    maxRows={4}
                />

                {/* Send Button */}
                <Tooltip title="Send message" placement="top">
                    <IconButton
                        onClick={handleSubmit}
                        disabled={!value.trim()}
                        sx={{
                            width: 36,
                            height: 36,
                            bgcolor: value.trim() ? '#6366F1' : 'grey.100',
                            color: value.trim() ? 'white' : 'grey.400',
                            borderRadius: '50%',
                            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                            '&:hover': {
                                bgcolor: value.trim() ? '#4F46E5' : 'grey.100',
                                transform: value.trim() ? 'scale(1.05)' : 'none'
                            },
                            '&:disabled': {
                                bgcolor: 'grey.100',
                                color: 'grey.400'
                            }
                        }}
                    >
                        <ArrowUp size={18} strokeWidth={2.5} />
                    </IconButton>
                </Tooltip>
            </Paper>
        </Box>
    );
}
