'use client';

import React, { useState } from 'react';
import { Box, Paper, Typography, IconButton, Tooltip, CircularProgress } from '@mui/material';
import { Zap, Network, Plus, Mic, Layout, HelpCircle, Sparkles } from 'lucide-react';
import { useStudio } from '@/contexts/StudioContext';
import SummaryCard from './SummaryCard';
import { useCanvasActions } from '@/hooks/useCanvasActions';
import { outputsApi, SummaryData } from '@/lib/api';

// Helper function to wait
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export default function InspirationDock() {
  const { documents, projectId } = useStudio();
  const { handleGenerateContent } = useCanvasActions();
  
  const [showMoreActions, setShowMoreActions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null);
  const [summaryTitle, setSummaryTitle] = useState('');
  const [error, setError] = useState<string | null>(null);

  const projectColor = '#0096FF'; // Default project color

  const handleAction = async (actionType: 'summarize' | 'map' | 'podcast' | 'quiz' | 'timeline' | 'compare') => {
    if (documents.length === 0) return;

    if (actionType === 'summarize') {
      if (!projectId) {
        console.error('No project ID available');
        return;
      }
      
      setIsLoading(true);
      setError(null);
      setShowSummary(false);
      setSummaryData(null);
      
      try {
        // 1. Call generate API
        const documentIds = documents.map(d => d.id);
        const firstDocName = documents[0]?.filename || 'Document';
        const { output_id } = await outputsApi.generate(
          projectId,
          'summary',
          documentIds,
          `Summary: ${firstDocName}`
        );
        
        // 2. Poll for completion (max 60 seconds)
        const maxAttempts = 60;
        let attempts = 0;
        let output = await outputsApi.get(projectId, output_id);
        
        while (output.status === 'generating' && attempts < maxAttempts) {
          await sleep(1000);
          output = await outputsApi.get(projectId, output_id);
          attempts++;
        }
        
        // 3. Handle result
        if (output.status === 'complete' && output.data) {
          setSummaryData(output.data as SummaryData);
          setSummaryTitle(output.title || firstDocName);
          setShowSummary(true);
        } else if (output.status === 'error') {
          setError(output.error_message || 'Summary generation failed');
          console.error('Summary generation error:', output.error_message);
        } else if (attempts >= maxAttempts) {
          setError('Summary generation timed out. Please try again.');
          console.error('Summary generation timed out');
        }
      } catch (err) {
        console.error('Failed to generate summary:', err);
        setError('Failed to generate summary. Please try again.');
      } finally {
        setIsLoading(false);
      }
      return;
    }
    
    // For other actions, just call the hook
    const hookActionType = actionType === 'map' ? 'mindmap' : actionType;
    await handleGenerateContent(hookActionType as Parameters<typeof handleGenerateContent>[0]);
  };

  const handleCloseSummary = () => {
    setShowSummary(false);
    setSummaryData(null);
  };

  return (
    <Box
      sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        pointerEvents: 'none' // Allow click-through to canvas, but enable on children
      }}
    >
      {/* Summary Card Overlay */}
      {showSummary && summaryData && (
        <Box sx={{ pointerEvents: 'auto' }}>
          <SummaryCard 
            title={summaryTitle}
            summary={summaryData.summary}
            keyFindings={summaryData.keyFindings}
            onClose={handleCloseSummary}
            onDock={() => console.log('Dock to board')}
            onFullScreen={() => console.log('Full screen')}
            onShare={() => console.log('Share')}
            onCopy={() => {
              if (summaryData?.summary) {
                navigator.clipboard.writeText(summaryData.summary);
                console.log('Copied to clipboard');
              }
            }}
          />
        </Box>
      )}
      
      {/* Error display */}
      {error && !isLoading && (
        <Box sx={{ 
          pointerEvents: 'auto',
          position: 'absolute',
          top: -60,
          bgcolor: 'error.light',
          color: 'error.contrastText',
          px: 2,
          py: 1,
          borderRadius: 2,
          fontSize: '0.875rem'
        }}>
          {error}
        </Box>
      )}

      {/* Dock UI - Only visible when summary is not shown */}
      {!showSummary && (
        <Box sx={{ 
          pointerEvents: 'auto', 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          gap: 3,
          animation: 'fadeIn 0.5s ease-out',
          '@keyframes fadeIn': {
            from: { opacity: 0, transform: 'translateY(20px)' },
            to: { opacity: 1, transform: 'translateY(0)' }
          }
        }}>
          <Box sx={{ position: 'relative' }}>
            {/* Mini App Launcher Popover */}
            {showMoreActions && !isLoading && (
              <Paper
                elevation={8}
                sx={{
                  position: 'absolute',
                  bottom: '120%', // Appear above the dock
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: 340,
                  p: 2,
                  borderRadius: '24px',
                  bgcolor: 'rgba(255,255,255,0.95)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(0,0,0,0.08)',
                  animation: 'floatUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 1.5,
                  zIndex: 10,
                  '@keyframes floatUp': {
                    from: { opacity: 0, transform: 'translateX(-50%) translateY(10px) scale(0.95)' },
                    to: { opacity: 1, transform: 'translateX(-50%) translateY(0) scale(1)' }
                  }
                }}
              >
                {[
                  { id: 'podcast', label: 'Podcast', desc: 'Audio overview', icon: <Mic size={20} color="#8B5CF6" />, color: '#8B5CF6' },
                  { id: 'quiz', label: 'Quiz', desc: 'Test knowledge', icon: <HelpCircle size={20} color="#F59E0B" />, color: '#F59E0B' },
                  { id: 'timeline', label: 'Timeline', desc: 'Chronology', icon: <Sparkles size={20} color="#EC4899" />, color: '#EC4899' },
                  { id: 'compare', label: 'Compare', desc: 'Diff analysis', icon: <Layout size={20} color="#10B981" />, color: '#10B981' }
                ].map((action) => (
                  <Box
                    key={action.id}
                    onClick={() => {
                      handleAction(action.id as 'podcast' | 'quiz' | 'timeline' | 'compare');
                      setShowMoreActions(false);
                    }}
                    sx={{
                      p: 1.5,
                      borderRadius: '16px',
                      border: '1px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      '&:hover': {
                        bgcolor: `${action.color}11`,
                        borderColor: `${action.color}33`,
                        transform: 'scale(1.02)'
                      },
                      '&:active': { transform: 'scale(0.98)' }
                    }}
                  >
                    <Box sx={{ 
                      p: 1, 
                      borderRadius: '12px', 
                      bgcolor: 'white',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      {action.icon}
                    </Box>
                    <Box>
                      <Typography variant="body2" fontWeight={700} sx={{ color: 'text.primary', lineHeight: 1.2 }}>{action.label}</Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>{action.desc}</Typography>
                    </Box>
                  </Box>
                ))}
              </Paper>
            )}

            <Paper
              elevation={6}
              sx={{
                p: 1.5,
                borderRadius: '24px', // Capsule shape
                bgcolor: 'rgba(255,255,255,0.9)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(0,0,0,0.08)',
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                transition: 'all 0.3s ease'
              }}
            >
              {isLoading ? (
                <Box sx={{ px: 4, py: 1.5, display: 'flex', alignItems: 'center', gap: 2 }}>
                  <CircularProgress size={24} sx={{ color: projectColor }} />
                  <Typography variant="body2" color="text.secondary" fontWeight={500}>
                    Generating insights...
                  </Typography>
                </Box>
              ) : documents.length === 0 ? (
                <Box sx={{ px: 2, py: 1, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Typography variant="body2" color="text.secondary" fontWeight={500}>
                    Upload a document to start
                  </Typography>
                </Box>
              ) : (
                <>
                  {/* Action 1: Summary */}
                  <Tooltip title="Generate Executive Summary" placement="top" arrow>
                    <IconButton 
                      onClick={() => handleAction('summarize')}
                      sx={{ 
                        width: 64, 
                        height: 64, 
                        borderRadius: '16px',
                        bgcolor: 'grey.50',
                        border: '1px solid',
                        borderColor: 'divider',
                        flexDirection: 'column',
                        gap: 0.5,
                        transition: 'all 0.2s',
                        '&:hover': { 
                          bgcolor: `${projectColor}11`, 
                          borderColor: projectColor,
                          transform: 'translateY(-2px)' 
                        }
                      }}
                    >
                      <Zap size={24} color={projectColor} />
                      <Typography variant="caption" sx={{ fontSize: '0.65rem', fontWeight: 600, color: 'text.secondary' }}>Summary</Typography>
                    </IconButton>
                  </Tooltip>

                  {/* Action 2: Concept Map */}
                  <Tooltip title="Extract Concept Map" placement="top" arrow>
                    <IconButton 
                      onClick={() => handleAction('map')}
                      sx={{ 
                        width: 64, 
                        height: 64, 
                        borderRadius: '16px',
                        bgcolor: 'grey.50',
                        border: '1px solid',
                        borderColor: 'divider',
                        flexDirection: 'column',
                        gap: 0.5,
                        transition: 'all 0.2s',
                        '&:hover': { 
                          bgcolor: '#10B98111', 
                          borderColor: '#10B981',
                          transform: 'translateY(-2px)' 
                        }
                      }}
                    >
                      <Network size={24} color="#10B981" />
                      <Typography variant="caption" sx={{ fontSize: '0.65rem', fontWeight: 600, color: 'text.secondary' }}>Map</Typography>
                    </IconButton>
                  </Tooltip>

                  {/* Action 3: More / Close */}
                  <Tooltip title={showMoreActions ? "Close" : "More Actions"} placement="top" arrow>
                    <IconButton 
                      onClick={() => setShowMoreActions(!showMoreActions)}
                      sx={{ 
                        width: 64, 
                        height: 64, 
                        borderRadius: '16px',
                        border: '1px dashed',
                        borderColor: showMoreActions ? projectColor : 'divider',
                        bgcolor: showMoreActions ? `${projectColor}11` : 'transparent',
                        color: showMoreActions ? projectColor : 'text.secondary',
                        transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                        transform: showMoreActions ? 'rotate(45deg)' : 'rotate(0deg)',
                        '&:hover': {
                          borderColor: projectColor,
                          color: projectColor,
                          bgcolor: `${projectColor}08`
                        }
                      }}
                    >
                      <Plus size={24} />
                    </IconButton>
                  </Tooltip>
                </>
              )}
            </Paper>
          </Box>
        </Box>
      )}
    </Box>
  );
}

