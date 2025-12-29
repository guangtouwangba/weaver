'use client';

import React, { useState } from 'react';
import { Box, Typography, Paper, InputBase, IconButton, Avatar } from '@mui/material';
import { Send, User, Bot } from 'lucide-react';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
}

export default function NodeChat({ nodeName }: { nodeName: string }) {
    const [messages, setMessages] = useState<Message[]>([
        { id: '1', role: 'assistant', content: `Hello! I'm your AI assistant for "${nodeName}". How can I help you understand this better?` }
    ]);
    const [inputValue, setInputValue] = useState('');

    const handleSend = () => {
        if (!inputValue.trim()) return;
        
        const userMsg: Message = { id: Date.now().toString(), role: 'user', content: inputValue };
        setMessages(prev => [...prev, userMsg]);
        setInputValue('');

        // Simulate AI response
        setTimeout(() => {
            const aiMsg: Message = { 
                id: (Date.now() + 1).toString(), 
                role: 'assistant', 
                content: `Based on the context of "${nodeName}", this is a very interesting point. Let me analyze that for you...` 
            };
            setMessages(prev => [...prev, aiMsg]);
        }, 1000);
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: '#F8FAFC' }}>
            <Box sx={{ p: 2, borderBottom: '1px solid rgba(0,0,0,0.05)', bgcolor: 'white' }}>
                <Typography variant="subtitle2" fontWeight={700}>Chatting with Node</Typography>
                <Typography variant="caption" color="text.secondary">{nodeName}</Typography>
            </Box>

            <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                {messages.map((msg) => (
                    <Box 
                        key={msg.id} 
                        sx={{ 
                            display: 'flex', 
                            gap: 1.5, 
                            flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                            alignItems: 'flex-start'
                        }}
                    >
                        <Avatar sx={{ width: 24, height: 24, bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.800' }}>
                            {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                        </Avatar>
                        <Paper 
                            elevation={0} 
                            sx={{ 
                                p: 1.5, 
                                borderRadius: 2, 
                                maxWidth: '80%',
                                bgcolor: msg.role === 'user' ? 'primary.main' : 'white',
                                color: msg.role === 'user' ? 'white' : 'text.primary',
                                border: msg.role === 'user' ? 'none' : '1px solid rgba(0,0,0,0.05)'
                            }}
                        >
                            <Typography variant="body2" sx={{ lineHeight: 1.5 }}>{msg.content}</Typography>
                        </Paper>
                    </Box>
                ))}
            </Box>

            <Box sx={{ p: 2, bgcolor: 'white', borderTop: '1px solid rgba(0,0,0,0.05)' }}>
                <Paper
                    elevation={0}
                    sx={{
                        p: '4px 8px',
                        display: 'flex',
                        alignItems: 'center',
                        borderRadius: '12px',
                        bgcolor: 'grey.50',
                        border: '1px solid rgba(0,0,0,0.08)'
                    }}
                >
                    <InputBase
                        sx={{ ml: 1, flex: 1, fontSize: '0.85rem' }}
                        placeholder="Ask about this node..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    />
                    <IconButton size="small" onClick={handleSend} color="primary">
                        <Send size={18} />
                    </IconButton>
                </Paper>
            </Box>
        </Box>
    );
}






