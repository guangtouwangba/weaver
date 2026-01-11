'use client';

import React, { useState, useMemo } from 'react';
import { Surface, Stack, Text, IconButton, Tooltip, Spinner } from '@/components/ui';
import { colors, radii, shadows } from '@/components/ui/tokens';
import { BoltIcon, AccountTreeIcon, AddIcon, MicIcon, DashboardIcon, HelpOutlineIcon, AutoAwesomeIcon, CloseIcon, CheckIcon, ErrorIcon } from '@/components/ui/icons';
import { useStudio, GenerationType } from '@/contexts/StudioContext';
import SummaryCard from './SummaryCard';
import MindMapCanvasNode from './canvas-nodes/MindMapCanvasNode';
import { useCanvasActions } from '@/hooks/useCanvasActions';
import { SummaryData, MindmapData } from '@/lib/api';

export default function InspirationDock() {
  const {
    documents,
    urlContents,
    projectId,
    selectedDocumentIds,
    isInspirationDockVisible,
    setInspirationDockVisible,
    // Canvas nodes (unified node model - includes output nodes)
    canvasNodes,
    // Concurrent generation tasks
    generationTasks,
    getActiveGenerationsOfType,
    hasActiveGenerations,
    removeGenerationTask,
    // Legacy overlay states (for backward compatibility with card display)
    summaryResult,
    setSummaryResult,
    showSummaryOverlay,
    setShowSummaryOverlay,
    mindmapResult,
    setMindmapResult,
    showMindmapOverlay,
    setShowMindmapOverlay,
  } = useStudio();

  const { handleGenerateContentConcurrent, getViewportCenterPosition } = useCanvasActions();

  const [showMoreActions, setShowMoreActions] = useState(false);

  const projectColor = '#7C3AED'; // Violet (primary)

  // Get loading states for each action type
  const isGeneratingSummary = useMemo(() =>
    getActiveGenerationsOfType('summary').length > 0,
    [getActiveGenerationsOfType]
  );

  const isGeneratingMindmap = useMemo(() =>
    getActiveGenerationsOfType('mindmap').length > 0,
    [getActiveGenerationsOfType]
  );

  const isGeneratingPodcast = useMemo(() =>
    getActiveGenerationsOfType('podcast').length > 0,
    [getActiveGenerationsOfType]
  );

  const isGeneratingQuiz = useMemo(() =>
    getActiveGenerationsOfType('quiz').length > 0,
    [getActiveGenerationsOfType]
  );

  const isGeneratingTimeline = useMemo(() =>
    getActiveGenerationsOfType('timeline').length > 0,
    [getActiveGenerationsOfType]
  );

  const isGeneratingCompare = useMemo(() =>
    getActiveGenerationsOfType('compare').length > 0,
    [getActiveGenerationsOfType]
  );

  // Get recently completed tasks for showing success feedback
  // With unified node model, check both generationTasks (for backward compat) and canvasNodes
  const recentlyCompleted = useMemo(() => {
    const completed: Record<GenerationType, boolean> = {
      summary: false, mindmap: false, podcast: false,
      quiz: false, timeline: false, compare: false, flashcards: false
    };
    // Check generationTasks (legacy)
    generationTasks.forEach(task => {
      if (task.status === 'complete') {
        completed[task.type] = true;
      }
    });
    // Check canvasNodes (unified node model - outputs are now CanvasNodes)
    canvasNodes.forEach(node => {
      if (node.type === 'mindmap' || node.type === 'summary') {
        completed[node.type as GenerationType] = true;
      }
    });
    return completed;
  }, [generationTasks, canvasNodes]);

  // Get error states
  const hasError = useMemo(() => {
    const errors: Record<GenerationType, string | undefined> = {
      summary: undefined, mindmap: undefined, podcast: undefined,
      quiz: undefined, timeline: undefined, compare: undefined, flashcards: undefined
    };
    generationTasks.forEach(task => {
      if (task.status === 'error') {
        errors[task.type] = task.error;
      }
    });
    return errors;
  }, [generationTasks]);

  if (!isInspirationDockVisible) return null;

  const handleAction = async (actionType: 'summarize' | 'map' | 'podcast' | 'quiz' | 'timeline' | 'compare') => {
    if (documents.length === 0 && urlContents.length === 0) return;

    // Map action type to generation type
    const typeMap: Record<string, GenerationType> = {
      'summarize': 'summary',
      'map': 'mindmap',
      'podcast': 'podcast',
      'quiz': 'quiz',
      'timeline': 'timeline',
      'compare': 'compare'
    };

    const generationType = typeMap[actionType];

    // Capture current viewport position at the moment of click
    const position = getViewportCenterPosition();

    // Add random jitter to prevent perfect stacking (±20px)
    const jitter = {
      x: (Math.random() - 0.5) * 40,
      y: (Math.random() - 0.5) * 40
    };

    const jitteredPosition = {
      x: position.x + jitter.x,
      y: position.y + jitter.y
    };

    // Start concurrent generation (non-blocking)
    handleGenerateContentConcurrent(generationType, jitteredPosition);
  };

  const handleCloseSummary = () => {
    setShowSummaryOverlay(false);
    setSummaryResult(null);
  };

  const handleCloseMindmap = () => {
    setShowMindmapOverlay(false);
    setMindmapResult(null);
  };

  // ActionButton component to properly use hooks
  const ActionButton = ({
    id,
    label,
    icon,
    color,
    isGenerating,
    isComplete,
    error,
    onClick
  }: {
    id: string;
    label: string;
    icon: React.ReactNode;
    color: string;
    isGenerating: boolean;
    isComplete: boolean;
    error: string | undefined;
    onClick: () => void;
  }) => {
    const [isHovered, setIsHovered] = useState(false);

    return (
      <Tooltip
        title={error ? `Error: ${error}` : isGenerating ? `Generating ${label}...` : `Generate ${label}`}
        placement="top"
      >
        <div
          onClick={isGenerating ? undefined : onClick}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          style={{
            width: 64,
            height: 64,
            borderRadius: radii.lg,
            backgroundColor: error ? colors.error[50] : isComplete ? `${color}22` : isHovered ? `${color}11` : colors.neutral[50],
            border: '1px solid',
            borderColor: error ? colors.error[500] : isGenerating || isHovered ? color : colors.border.default,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
            transition: 'all 0.2s',
            position: 'relative',
            cursor: isGenerating ? 'wait' : 'pointer',
            transform: isHovered ? 'translateY(-2px)' : undefined,
          }}
        >
          {isGenerating ? (
            <Spinner size="sm" color="primary" />
          ) : error ? (
            <ErrorIcon size="lg" style={{ color: colors.error[500] }} />
          ) : isComplete ? (
            <CheckIcon size="lg" style={{ color: color }} />
          ) : (
            icon
          )}
          <Text
            variant="caption"
            style={{
              fontSize: '0.65rem',
              fontWeight: 600,
              color: error ? colors.error[500] : colors.text.secondary
            }}
          >
            {label}
          </Text>
        </div>
      </Tooltip>
    );
  };

  return (
    <Stack
      direction="column"
      align="center"
      justify="center"
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 100,
        pointerEvents: 'none' // Allow click-through to canvas, but enable on children
      }}
    >
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes floatUp {
            from { opacity: 0; transform: translateX(-50%) translateY(10px) scale(0.95); }
            to { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
          }
          .more-action-item {
            padding: 12px;
            border-radius: ${radii.lg}px;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.2s;
            opacity: 1;
          }
          .more-action-item:hover {
            background-color: var(--action-bg);
            border-color: var(--action-border);
            transform: scale(1.02);
          }
          .more-action-item:active {
            transform: scale(0.98);
          }
          .more-action-item.generating {
            cursor: wait;
            opacity: 0.7;
          }
          .more-action-item.generating:hover {
            background-color: transparent;
            border-color: transparent;
            transform: none;
          }
          .more-action-item.generating:active {
            transform: none;
          }
        `
      }} />


      {/* Dock UI - Hidden during generation */}
      {!showSummaryOverlay && !showMindmapOverlay && !hasActiveGenerations() && (
        <div
          className="dock-container"
          style={{
            pointerEvents: 'auto',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
          }}
        >
          <div style={{ position: 'relative' }}>
            {/* Mini App Launcher Popover */}
            {showMoreActions && (
              <Surface
                elevation={4}
                radius="xl"
                style={{
                  position: 'absolute',
                  bottom: '120%', // Appear above the dock
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: 340,
                  padding: 16,
                  backgroundColor: 'rgba(255,255,255,0.95)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(0,0,0,0.08)',
                  animation: 'floatUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 12,
                  zIndex: 10,
                }}
              >
                {[
                  { id: 'podcast', label: 'Podcast', desc: 'Audio overview', icon: <MicIcon size="md" style={{ color: '#8B5CF6' }} />, color: '#8B5CF6', isGenerating: isGeneratingPodcast },
                  { id: 'quiz', label: 'Quiz', desc: 'Test knowledge', icon: <HelpOutlineIcon size="md" style={{ color: '#F59E0B' }} />, color: '#F59E0B', isGenerating: isGeneratingQuiz },
                  { id: 'timeline', label: 'Timeline', desc: 'Chronology', icon: <AutoAwesomeIcon size="md" style={{ color: '#EC4899' }} />, color: '#EC4899', isGenerating: isGeneratingTimeline },
                  { id: 'compare', label: 'Compare', desc: 'Diff analysis', icon: <DashboardIcon size="md" style={{ color: '#10B981' }} />, color: '#10B981', isGenerating: isGeneratingCompare }
                ].map((action) => (
                  <Stack
                    key={action.id}
                    direction="row"
                    align="center"
                    gap={1}
                    onClick={() => {
                      if (!action.isGenerating) {
                        handleAction(action.id as 'podcast' | 'quiz' | 'timeline' | 'compare');
                        setShowMoreActions(false);
                      }
                    }}
                    className={`more-action-item ${action.isGenerating ? 'generating' : ''}`}
                    style={{
                      // @ts-ignore
                      '--action-bg': `${action.color}11`,
                      '--action-border': `${action.color}33`,
                    }}
                  >
                    <div
                      style={{
                        padding: 8,
                        borderRadius: radii.md,
                        backgroundColor: 'white',
                        boxShadow: shadows.xs,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {action.isGenerating ? (
                        <Spinner size="xs" color="primary" />
                      ) : (
                        action.icon
                      )}
                    </div>
                    <div>
                      <Text variant="bodySmall" style={{ fontWeight: 700, lineHeight: 1.2 }}>
                        {action.label}
                        {action.isGenerating && '...'}
                      </Text>
                      <Text variant="caption" color="secondary" style={{ fontSize: '0.7rem' }}>
                        {action.isGenerating ? 'Generating' : action.desc}
                      </Text>
                    </div>
                  </Stack>
                ))}
              </Surface>
            )}

            <Surface
              elevation={3}
              radius="xl"
              style={{
                padding: 12,
                backgroundColor: 'rgba(255,255,255,0.9)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(0,0,0,0.08)',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                transition: 'all 0.3s ease'
              }}
            >
              {documents.length === 0 && urlContents.length === 0 ? (
                <Stack direction="row" align="center" gap={1} style={{ paddingLeft: 16, paddingRight: 16, paddingTop: 8, paddingBottom: 8 }}>
                  <Text variant="bodySmall" color="secondary" style={{ fontWeight: 500 }}>
                    Add a source (PDF or Link) to start
                  </Text>
                </Stack>
              ) : (
                <>
                  {/* Action 1: Summary */}
                  <ActionButton
                    id="summary"
                    label="Summary"
                    icon={<BoltIcon size="lg" style={{ color: projectColor }} />}
                    color={projectColor}
                    isGenerating={isGeneratingSummary}
                    isComplete={recentlyCompleted.summary}
                    error={hasError.summary}
                    onClick={() => handleAction('summarize')}
                  />

                  {/* Action 2: Mindmap */}
                  <ActionButton
                    id="mindmap"
                    label="Mindmap"
                    icon={<AccountTreeIcon size="lg" style={{ color: '#10B981' }} />}
                    color="#10B981"
                    isGenerating={isGeneratingMindmap}
                    isComplete={recentlyCompleted.mindmap}
                    error={hasError.mindmap}
                    onClick={() => handleAction('map')}
                  />

                  {/* Action 3: More / Close */}
                  <Tooltip title={showMoreActions ? "Close" : "More Actions"} placement="top">
                    <div
                      onClick={() => setShowMoreActions(!showMoreActions)}
                      style={{
                        width: 64,
                        height: 64,
                        borderRadius: radii.lg,
                        border: '1px dashed',
                        borderColor: showMoreActions ? projectColor : colors.border.default,
                        backgroundColor: showMoreActions ? `${projectColor}11` : 'transparent',
                        color: showMoreActions ? projectColor : colors.text.secondary,
                        transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                        transform: showMoreActions ? 'rotate(45deg)' : 'rotate(0deg)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                      }}
                    >
                      <AddIcon size="lg" />
                    </div>
                  </Tooltip>
                </>
              )}
            </Surface>

            {/* Close Dock Button - Outside the main paper */}
            {(documents.length > 0 || urlContents.length > 0) && (
              <div
                className="close-dock-btn"
                style={{
                  position: 'absolute',
                  top: '50%',
                  right: -40,
                  transform: 'translateY(-50%) translateX(-10px)',
                  opacity: 0,
                  transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                }}
              >
                <Tooltip title="Close Dock" placement="right">
                  <div
                    onClick={() => setInspirationDockVisible(false)}
                    style={{
                      width: 32,
                      height: 32,
                      backgroundColor: 'rgba(255,255,255,0.9)',
                      backdropFilter: 'blur(10px)',
                      border: `1px solid ${colors.border.default}`,
                      color: colors.text.secondary,
                      boxShadow: shadows.sm,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                    }}
                  >
                    <CloseIcon size={18} />
                  </div>
                </Tooltip>
              </div>
            )}
          </div>

          <style>{`
            .dock-container:hover .close-dock-btn {
              opacity: 1 !important;
              transform: translateY(-50%) translateX(0) !important;
            }
            .close-dock-btn:hover {
              background-color: white !important;
              color: #EF4444 !important;
              border-color: #FECACA !important;
              transform: translateY(-50%) scale(1.1) !important;
            }
            @keyframes fadeIn {
              from { opacity: 0; transform: translateY(20px); }
              to { opacity: 1; transform: translateY(0); }
            }
            .dock-container {
              animation: fadeIn 0.5s ease-out;
            }
          `}</style>
        </div>
      )}
    </Stack>
  );
}
