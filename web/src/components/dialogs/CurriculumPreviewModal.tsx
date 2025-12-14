'use client';

import React, { useState, useCallback, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  CircularProgress,
  Alert,
  Fade,
  Paper,
  Chip,
} from '@mui/material';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  X,
  Trash2,
  Plus,
  FileText,
  Video,
  GripVertical,
  Clock,
  Sparkles,
  RotateCcw,
} from 'lucide-react';
import { CurriculumStep } from '@/lib/api';

interface CurriculumPreviewModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (steps: CurriculumStep[]) => void;
  projectId?: string; // Optional for now
}

// Sortable Item Component
function SortableItem(props: { 
  step: CurriculumStep; 
  index: number; 
  onRemove: (id: string) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: props.step.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 1 : 0,
    position: 'relative' as const,
  };

  return (
    <Paper
      ref={setNodeRef}
      style={style}
      elevation={isDragging ? 4 : 0}
      sx={{
        p: 2,
        mb: 1.5,
        borderRadius: 2,
        border: '1px solid',
        borderColor: isDragging ? 'primary.main' : 'divider',
        bgcolor: 'background.paper',
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        transition: 'box-shadow 0.2s, border-color 0.2s',
        '&:hover': {
          borderColor: 'primary.main',
          '& .delete-btn': { opacity: 1 },
        },
      }}
    >
      {/* Drag Handle */}
      <Box
        {...attributes}
        {...listeners}
        sx={{
          cursor: 'grab',
          color: 'text.disabled',
          display: 'flex',
          alignItems: 'center',
          '&:hover': { color: 'text.primary' },
          '&:active': { cursor: 'grabbing' },
        }}
      >
        <GripVertical size={20} />
      </Box>

      {/* Index */}
      <Typography
        variant="body2"
        fontWeight="600"
        color="text.secondary"
        sx={{ minWidth: 24 }}
      >
        {props.index + 1}.
      </Typography>

      {/* Content */}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <Typography variant="body1" fontWeight="500" noWrap>
            {props.step.title}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          {/* Source */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'text.secondary' }}>
            {props.step.sourceType === 'video' ? (
              <Video size={14} />
            ) : (
              <FileText size={14} />
            )}
            <Typography variant="caption" noWrap sx={{ maxWidth: 200 }}>
              {props.step.source} 
              {props.step.pageRange && (
                <Box component="span" sx={{ opacity: 0.7, ml: 0.5 }}>
                  ({props.step.pageRange})
                </Box>
              )}
            </Typography>
          </Box>

          {/* Duration */}
          <Chip
            icon={<Clock size={12} />}
            label={`${props.step.duration} min`}
            size="small"
            sx={{ 
              height: 20, 
              fontSize: '0.7rem',
              bgcolor: 'action.hover',
              '& .MuiChip-icon': { ml: 0.5, width: 12, height: 12 }
            }}
          />
        </Box>
      </Box>

      {/* Delete Button */}
      <IconButton
        className="delete-btn"
        size="small"
        onClick={() => props.onRemove(props.step.id)}
        sx={{
          opacity: 0,
          color: 'error.main',
          transition: 'opacity 0.2s',
          '&:hover': { bgcolor: 'error.50' },
        }}
      >
        <Trash2 size={18} />
      </IconButton>
    </Paper>
  );
}

export default function CurriculumPreviewModal({
  open,
  onClose,
  onConfirm,
}: CurriculumPreviewModalProps) {
  const [steps, setSteps] = useState<CurriculumStep[]>([]);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setSteps((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const handleGenerate = useCallback(async () => {
    setGenerating(true);
    setError(null);
    
    try {
      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 2000));
      
      // Mock data
      const mockSteps: CurriculumStep[] = [
        {
          id: '1',
          title: 'Introduction to Transformers',
          source: 'attention.pdf',
          sourceType: 'document',
          pageRange: 'p.1-10',
          duration: 15,
        },
        {
          id: '2',
          title: 'Attention Mechanism Explained',
          source: 'video.mp4',
          sourceType: 'video',
          pageRange: '0:00-5:30',
          duration: 6,
        },
        {
          id: '3',
          title: 'Self-Attention Deep Dive',
          source: 'attention.pdf',
          sourceType: 'document',
          pageRange: 'p.11-15',
          duration: 12,
        },
        {
          id: '4',
          title: 'Multi-Head Attention',
          source: 'transformer_architecture.pdf',
          sourceType: 'document',
          pageRange: 'p.3-5',
          duration: 10,
        },
      ];
      
      setSteps(mockSteps);
    } catch (err) {
      setError('Failed to generate curriculum. Please try again.');
    } finally {
      setGenerating(false);
    }
  }, []);

  const handleAddStep = () => {
    const newStep: CurriculumStep = {
      id: `custom-${Date.now()}`,
      title: 'New Custom Step',
      source: 'Custom Source',
      sourceType: 'document',
      duration: 10,
    };
    setSteps([...steps, newStep]);
  };

  const handleRemoveStep = (id: string) => {
    setSteps(steps.filter((s) => s.id !== id));
  };

  const handleConfirm = async () => {
    setSaving(true);
    try {
      // Simulate save
      await new Promise(resolve => setTimeout(resolve, 1000));
      onConfirm(steps);
    } catch (err) {
      setError('Failed to save curriculum');
    } finally {
      setSaving(false);
    }
  };

  const totalDuration = steps.reduce((acc, step) => acc + step.duration, 0);

  // Auto-generate on first open if empty (optional, but good UX)
  // useEffect(() => {
  //   if (open && steps.length === 0 && !generating) {
  //     handleGenerate();
  //   }
  // }, [open]); 
  // Commented out to let user click "Generate" as per requirement

  return (
    <Dialog
      open={open}
      onClose={() => !saving && onClose()}
      maxWidth="md"
      fullWidth
      TransitionComponent={Fade}
      PaperProps={{
        sx: {
          borderRadius: 3,
          height: '80vh',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid',
          borderColor: 'divider',
          py: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              p: 1,
              borderRadius: 1.5,
              bgcolor: 'primary.50',
              color: 'primary.main',
            }}
          >
            <Sparkles size={20} />
          </Box>
          <Box>
            <Typography variant="h6" fontWeight="600">
              AI-Generated Learning Path
            </Typography>
            {steps.length > 0 && (
              <Typography variant="caption" color="text.secondary">
                Total Duration: {Math.floor(totalDuration / 60)}h {totalDuration % 60}m
              </Typography>
            )}
          </Box>
        </Box>
        <IconButton onClick={onClose} disabled={saving}>
          <X size={20} />
        </IconButton>
      </DialogTitle>

      <DialogContent 
        sx={{ 
          p: 3, 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          bgcolor: 'background.default' 
        }}
      >
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {generating ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
            }}
          >
            <CircularProgress size={40} thickness={4} />
            <Typography variant="body1" color="text.secondary" fontWeight="500">
              Analyzing documents...
            </Typography>
            <Typography variant="caption" color="text.disabled">
              This usually takes 15-30 seconds
            </Typography>
          </Box>
        ) : steps.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 2,
              py: 8,
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                bgcolor: 'action.hover',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'text.disabled',
                mb: 1,
              }}
            >
              <Sparkles size={40} />
            </Box>
            <Typography variant="h6" color="text.secondary">
              No Curriculum Generated Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center" sx={{ maxWidth: 400 }}>
              Click the button below to let AI analyze your documents and generate a personalized learning path for you.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Sparkles size={18} />}
              onClick={handleGenerate}
              sx={{ mt: 2, px: 4, py: 1.5, borderRadius: 2 }}
            >
              Generate Learning Path
            </Button>
          </Box>
        ) : (
          <Box sx={{ flex: 1, overflowY: 'auto', px: 1 }}>
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={steps.map((s) => s.id)}
                strategy={verticalListSortingStrategy}
              >
                {steps.map((step, index) => (
                  <SortableItem
                    key={step.id}
                    step={step}
                    index={index}
                    onRemove={handleRemoveStep}
                  />
                ))}
              </SortableContext>
            </DndContext>

            <Button
              fullWidth
              startIcon={<Plus size={18} />}
              onClick={handleAddStep}
              sx={{
                mt: 2,
                py: 1.5,
                border: '1px dashed',
                borderColor: 'divider',
                color: 'text.secondary',
                borderRadius: 2,
                '&:hover': {
                  borderColor: 'primary.main',
                  color: 'primary.main',
                  bgcolor: 'primary.50',
                },
              }}
            >
              Add Custom Step
            </Button>
          </Box>
        )}
      </DialogContent>

      <DialogActions
        sx={{
          p: 2.5,
          borderTop: '1px solid',
          borderColor: 'divider',
          justifyContent: 'space-between',
        }}
      >
        {steps.length > 0 && !generating && (
          <Button
            startIcon={<RotateCcw size={16} />}
            color="inherit"
            onClick={handleGenerate}
            disabled={saving}
          >
            Regenerate
          </Button>
        )}
        <Box sx={{ display: 'flex', gap: 1.5, ml: 'auto' }}>
          <Button onClick={onClose} disabled={saving} color="inherit">
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleConfirm}
            disabled={generating || saving || steps.length === 0}
            startIcon={saving ? <CircularProgress size={16} color="inherit" /> : undefined}
            sx={{ px: 3, borderRadius: 2 }}
          >
            {saving ? 'Saving...' : 'Confirm & Start'}
          </Button>
        </Box>
      </DialogActions>
    </Dialog>
  );
}

