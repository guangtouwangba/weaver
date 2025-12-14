'use client';

import { useState, useEffect } from 'react';
import { Box, Typography, Fade } from '@mui/material';
import { Loader2 } from 'lucide-react';

interface ProjectInitializerProps {
  projectId: string;
  onComplete: () => void;
}

const PROCESSING_STEPS = [
  "Analyzing uploaded documents...",
  "Extracting key concepts...",
  "Generating vector embeddings...",
  "Weaving knowledge graph...",
  "Finalizing project..."
];

export default function ProjectInitializer({ projectId, onComplete }: ProjectInitializerProps) {
  const [step, setStep] = useState(0);
  
  useEffect(() => {
    // Simulate processing steps
    const totalDuration = 4000; // 4 seconds total
    const stepDuration = totalDuration / PROCESSING_STEPS.length;
    
    const interval = setInterval(() => {
      setStep(prev => {
        if (prev < PROCESSING_STEPS.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, stepDuration);

    const timeout = setTimeout(() => {
      clearInterval(interval);
      // Clear the initializing flag
      localStorage.removeItem(`project_initializing_${projectId}`);
      onComplete();
    }, totalDuration);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [projectId, onComplete]);

  return (
    <Fade in timeout={1000}>
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          width: '100%',
          position: 'absolute',
          top: 0,
          left: 0,
          zIndex: 10,
          bgcolor: 'background.default', // Or 'transparent' if you want to see underlying UI vaguely
        }}
      >
        {/* Weaving Animation */}
        <Box sx={{ position: 'relative', width: 120, height: 120, mb: 6 }}>
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              border: '4px solid',
              borderColor: 'primary.main',
              opacity: 0.2,
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%': { transform: 'scale(0.8)', opacity: 0.2 },
                '50%': { transform: 'scale(1.1)', opacity: 0.5 },
                '100%': { transform: 'scale(0.8)', opacity: 0.2 },
              }
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: 'primary.main',
              animation: 'spin 3s linear infinite',
              '@keyframes spin': {
                '0%': { transform: 'translate(-50%, -50%) rotate(0deg)' },
                '100%': { transform: 'translate(-50%, -50%) rotate(360deg)' },
              }
            }}
          >
            <Loader2 size={48} />
          </Box>
          {/* Particle Effects */}
          {[0, 1, 2].map((i) => (
            <Box
              key={i}
              sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: i % 2 === 0 ? 'primary.light' : 'secondary.main',
                animation: `orbit${i} 3s linear infinite`,
                '@keyframes orbit0': {
                  '0%': { transform: 'translate(-50%, -50%) rotate(0deg) translateX(40px)' },
                  '100%': { transform: 'translate(-50%, -50%) rotate(360deg) translateX(40px)' },
                },
                '@keyframes orbit1': {
                  '0%': { transform: 'translate(-50%, -50%) rotate(120deg) translateX(50px)' },
                  '100%': { transform: 'translate(-50%, -50%) rotate(480deg) translateX(50px)' },
                },
                '@keyframes orbit2': {
                  '0%': { transform: 'translate(-50%, -50%) rotate(240deg) translateX(35px)' },
                  '100%': { transform: 'translate(-50%, -50%) rotate(600deg) translateX(35px)' },
                }
              }}
            />
          ))}
        </Box>

        <Typography variant="h5" fontWeight="600" gutterBottom sx={{ color: 'primary.main' }}>
          {PROCESSING_STEPS[step]}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400, textAlign: 'center' }}>
          Weaver is analyzing your materials and constructing the initial knowledge graph...
        </Typography>
      </Box>
    </Fade>
  );
}

