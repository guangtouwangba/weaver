'use client';

import React, { useState } from 'react';
import { Box, Typography, Paper, Grid, IconButton, Divider, Chip, Avatar } from "@mui/material";
import { ChevronLeft, ChevronRight, Maximize2, FileText, Download, Share2 } from "lucide-react";

interface Slide {
    id: number;
    title: string;
    content: string[];
    sources: string[];
}

const MOCK_SLIDES: Slide[] = [
    {
        id: 1,
        title: "Executive Synthesis: Parallel Processing",
        content: [
            "Market demand for high-concurrency workflows is increasing (Source A).",
            "Current bottlenecks are predominantly in data-privacy-preserving latency (Source B).",
            "Technical roadmap supports 4x scaling by Q4 (Source C)."
        ],
        sources: ["Attention_Paper.pdf", "User_Interviews.mp4", "Tech_Roadmap.pdf"]
    },
    {
        id: 2,
        title: "Conflict Analysis: Speed vs. Privacy",
        content: [
            "Source A advocates for 'Maximum Parallelization' at the cost of transient cache data.",
            "Source B highlights critical user refusal to allow shared cache state.",
            "Synthesis: A hybrid 'Private Parallelization' layer is required."
        ],
        sources: ["Attention_Paper.pdf", "User_Interviews.mp4"]
    },
    {
        id: 3,
        title: "Strategic Recommendations",
        content: [
            "Implement multi-head attention with isolated context windows.",
            "Phased rollout of the new architecture starting October.",
            "Secondary validation with focus groups on privacy concerns."
        ],
        sources: ["Tech_Roadmap.pdf", "User_Interviews.mp4"]
    }
];

export default function PPTSynthesisView({ fileName, sourceNames = [] }: { fileName: string, sourceNames?: string[] }) {
    const [currentSlide, setCurrentSlide] = useState(0);

    const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % MOCK_SLIDES.length);
    const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + MOCK_SLIDES.length) % MOCK_SLIDES.length);

    const slide = MOCK_SLIDES[currentSlide];

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: '#f4f4f4' }}>
            {/* Header */}
            <Paper elevation={0} sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', justifyContent: 'space-between', bgcolor: '#fff' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="PPT SYNTHESIS" size="small" color="primary" sx={{ fontWeight: 800, fontSize: '10px' }} />
                    <Typography variant="subtitle2" fontWeight="bold">{fileName}</Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <IconButton size="small"><Download size={18} /></IconButton>
                    <IconButton size="small"><Share2 size={18} /></IconButton>
                </Box>
            </Paper>

            {/* Slide Viewer */}
            <Box sx={{ flex: 1, p: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                <Paper
                    elevation={10}
                    sx={{
                        width: '100%',
                        aspectRatio: '16/9',
                        bgcolor: 'white',
                        p: 6,
                        display: 'flex',
                        flexDirection: 'column',
                        position: 'relative',
                        borderRadius: 2,
                        overflow: 'hidden',
                        border: '1px solid rgba(0,0,0,0.1)'
                    }}
                >
                    {/* Slide Content */}
                    <Typography variant="h4" fontWeight={800} sx={{ mb: 4, color: 'primary.main', borderBottom: '4px solid', borderColor: 'primary.light', pb: 1, display: 'inline-block' }}>
                        {slide.title}
                    </Typography>

                    <Box sx={{ flex: 1 }}>
                        <ul style={{ paddingLeft: '1.5rem' }}>
                            {slide.content.map((item, i) => (
                                <li key={i} style={{ marginBottom: '1.5rem' }}>
                                    <Typography variant="h6" sx={{ lineHeight: 1.4, color: '#374151' }}>
                                        {item}
                                    </Typography>
                                </li>
                            ))}
                        </ul>
                    </Box>

                    {/* Footer / Attribution */}
                    <Box sx={{ mt: 'auto', pt: 2, borderTop: '1px solid #eee', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <Typography variant="caption" sx={{ fontWeight: 700, color: 'text.disabled' }}>SOURCES:</Typography>
                            {slide.sources.map((s, i) => (
                                <Chip key={i} label={s} size="small" sx={{ fontSize: '9px', height: 20 }} />
                            ))}
                        </Box>
                        <Typography variant="caption" color="text.disabled">Slide {slide.id} of {MOCK_SLIDES.length}</Typography>
                    </Box>
                </Paper>

                {/* Navigation Controls */}
                <IconButton 
                    onClick={prevSlide}
                    sx={{ position: 'absolute', left: 10, bgcolor: 'white', '&:hover': { bgcolor: 'grey.100' }, boxShadow: 2 }}
                >
                    <ChevronLeft size={24} />
                </IconButton>
                <IconButton 
                    onClick={nextSlide}
                    sx={{ position: 'absolute', right: 10, bgcolor: 'white', '&:hover': { bgcolor: 'grey.100' }, boxShadow: 2 }}
                >
                    <ChevronRight size={24} />
                </IconButton>
            </Box>

            {/* Thumbnail Sorter */}
            <Box sx={{ px: 4, pb: 4, display: 'flex', gap: 2, overflowX: 'auto' }}>
                {MOCK_SLIDES.map((s, i) => (
                    <Paper
                        key={s.id}
                        onClick={() => setCurrentSlide(i)}
                        sx={{
                            minWidth: 120,
                            aspectRatio: '16/9',
                            cursor: 'pointer',
                            border: currentSlide === i ? '3px solid' : '1px solid',
                            borderColor: currentSlide === i ? 'primary.main' : 'divider',
                            p: 1,
                            opacity: currentSlide === i ? 1 : 0.7,
                            transition: 'all 0.2s',
                            '&:hover': { opacity: 1 }
                        }}
                    >
                        <Typography sx={{ fontSize: '8px', fontWeight: 800, mb: 0.5, noWrap: true }}>{s.title}</Typography>
                        <Box sx={{ height: 2, width: '40%', bgcolor: 'primary.light', mb: 0.5 }} />
                        <Box sx={{ height: 1, width: '80%', bgcolor: 'grey.200', mb: 0.2 }} />
                        <Box sx={{ height: 1, width: '70%', bgcolor: 'grey.200', mb: 0.2 }} />
                        <Box sx={{ height: 1, width: '90%', bgcolor: 'grey.200' }} />
                    </Paper>
                ))}
            </Box>
        </Box>
    );
}







