'use client';

import React, { useState } from 'react';
import { Box, Typography, Paper, IconButton, Chip, Button } from '@mui/material';
import { ChevronLeft, ChevronRight, RotateCcw, CheckCircle2, HelpCircle } from 'lucide-react';

interface FlashCard {
    question: string;
    answer: string;
    category: string;
}

const MOCK_CARDS: FlashCard[] = [
    {
        question: "What is the primary innovation of the Transformer architecture?",
        answer: "The replacement of recurrent and convolutional layers with self-attention mechanisms, allowing for massive parallelization.",
        category: "Architecture"
    },
    {
        question: "What does 'multi-head attention' achieve?",
        answer: "It allows the model to simultaneously attend to information from different representation subspaces at different positions.",
        category: "Mechanism"
    },
    {
        question: "Why is positional encoding necessary in Transformers?",
        answer: "Since the model contains no recurrence or convolution, it has no inherent sense of the relative or absolute positions of tokens in a sequence.",
        category: "Preprocessing"
    }
];

export default function FlashCardView() {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const [score, setScore] = useState({ correct: 0, total: 0 });

    const currentCard = MOCK_CARDS[currentIndex];

    const handleNext = () => {
        setIsFlipped(false);
        setCurrentIndex((prev) => (prev + 1) % MOCK_CARDS.length);
    };

    const handlePrev = () => {
        setIsFlipped(false);
        setCurrentIndex((prev) => (prev - 1 + MOCK_CARDS.length) % MOCK_CARDS.length);
    };

    const handleResult = (isCorrect: boolean) => {
        setScore(prev => ({ correct: prev.correct + (isCorrect ? 1 : 0), total: prev.total + 1 }));
        handleNext();
    };

    return (
        <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#F8FAFC' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="subtitle2" fontWeight={700} color="text.secondary">
                    FLASH CARDS • {currentIndex + 1} / {MOCK_CARDS.length}
                </Typography>
                <Chip 
                    label={`Score: ${score.correct}/${score.total}`} 
                    size="small" 
                    color="primary" 
                    variant="outlined" 
                    sx={{ fontWeight: 600 }}
                />
            </Box>

            <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', perspective: '1000px' }}>
                <Box
                    onClick={() => setIsFlipped(!isFlipped)}
                    sx={{
                        width: '100%',
                        height: 320,
                        position: 'relative',
                        transition: 'transform 0.6s',
                        transformStyle: 'preserve-3d',
                        transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                        cursor: 'pointer'
                    }}
                >
                    {/* Front Side */}
                    <Paper
                        elevation={4}
                        sx={{
                            position: 'absolute',
                            width: '100%',
                            height: '100%',
                            backfaceVisibility: 'hidden',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            p: 4,
                            borderRadius: 4,
                            bgcolor: 'white',
                            textAlign: 'center'
                        }}
                    >
                        <Chip label={currentCard.category} size="small" sx={{ mb: 2, bgcolor: 'primary.50', color: 'primary.main', fontWeight: 600 }} />
                        <Typography variant="h6" fontWeight={600} sx={{ lineHeight: 1.4 }}>
                            {currentCard.question}
                        </Typography>
                        <Typography variant="caption" color="text.disabled" sx={{ mt: 4 }}>
                            Click to flip
                        </Typography>
                    </Paper>

                    {/* Back Side */}
                    <Paper
                        elevation={4}
                        sx={{
                            position: 'absolute',
                            width: '100%',
                            height: '100%',
                            backfaceVisibility: 'hidden',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            p: 4,
                            borderRadius: 4,
                            bgcolor: '#1E293B',
                            color: 'white',
                            textAlign: 'center',
                            transform: 'rotateY(180deg)'
                        }}
                    >
                        <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                            {currentCard.answer}
                        </Typography>
                        <Typography variant="caption" sx={{ mt: 4, opacity: 0.5 }}>
                            Click to flip back
                        </Typography>
                    </Paper>
                </Box>
            </Box>

            <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
                {isFlipped ? (
                    <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button 
                            fullWidth 
                            variant="outlined" 
                            color="error" 
                            startIcon={<HelpCircle size={18} />}
                            onClick={() => handleResult(false)}
                            sx={{ borderRadius: 2, py: 1.5 }}
                        >
                            Need Review
                        </Button>
                        <Button 
                            fullWidth 
                            variant="contained" 
                            color="success" 
                            startIcon={<CheckCircle2 size={18} />}
                            onClick={() => handleResult(true)}
                            sx={{ borderRadius: 2, py: 1.5 }}
                        >
                            Got it
                        </Button>
                    </Box>
                ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', gap: 4 }}>
                        <IconButton onClick={handlePrev}><ChevronLeft size={24} /></IconButton>
                        <IconButton onClick={() => { setIsFlipped(false); setScore({ correct: 0, total: 0 }); setCurrentIndex(0); }}>
                            <RotateCcw size={20} />
                        </IconButton>
                        <IconButton onClick={handleNext}><ChevronRight size={24} /></IconButton>
                    </Box>
                )}
            </Box>
        </Box>
    );
}





