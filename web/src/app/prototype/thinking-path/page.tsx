'use client';

import { useState } from 'react';
import GlobalLayout from '@/components/layout/GlobalLayout';
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Chip,
  Button,
  Collapse,
  TextField,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  ChevronRight,
  ChevronDown,
  Plus,
  ParkingCircle,
  Lightbulb,
  CheckCircle2,
  HelpCircle,
  FileText,
  GitBranch,
  ArrowRight,
  Trash2,
  Eye,
  Route,
} from 'lucide-react';

// ============ Type Definitions ============
interface Branch {
  id: string;
  type: 'alternative' | 'question' | 'counterargument';
  content: string;
}

interface ThinkingStep {
  id: string;
  stepNumber: number;
  claim: string;
  reason: string;
  evidence: string;
  uncertainty: string;
  decision: string;
  branches: Branch[];
  isExpanded: boolean;
}

interface ParkingItem {
  id: string;
  content: string;
  fromStepId: string;
  createdAt: Date;
}

// ============ Mock Data ============
const INITIAL_STEPS: ThinkingStep[] = [
  {
    id: '1',
    stepNumber: 1,
    claim: 'Problem Definition',
    reason: 'Deep thinking requires focused attention, but chat interfaces scatter thoughts',
    evidence: 'Research on cognitive load shows context-switching reduces deep work quality',
    uncertainty: 'Is this true for all types of deep thinkers?',
    decision: 'Design for "single active thread" pattern',
    branches: [
      { id: 'b1', type: 'alternative', content: 'Could use multiple parallel threads instead' },
    ],
    isExpanded: true,
  },
  {
    id: '2',
    stepNumber: 2,
    claim: 'Main Thread Design',
    reason: 'A linear breadcrumb keeps momentum and prevents branching chaos',
    evidence: 'GTD methodology emphasizes single next-action focus',
    uncertainty: 'How to handle genuinely parallel concerns?',
    decision: 'One active thread + collapsible side branches',
    branches: [
      { id: 'b2', type: 'question', content: 'What about mind-mapping style layouts?' },
      { id: 'b3', type: 'counterargument', content: 'Some users prefer free-form exploration' },
    ],
    isExpanded: true,
  },
  {
    id: '3',
    stepNumber: 3,
    claim: 'Parking Lot Pattern',
    reason: 'Deep thinkers fear losing ideas, so they chase tangents',
    evidence: 'Zeigarnik effect: unfinished tasks occupy mental bandwidth',
    uncertainty: 'Will users actually use the parking lot?',
    decision: 'Implement a visible "Park for Later" sidebar',
    branches: [],
    isExpanded: true,
  },
];

const INITIAL_PARKING: ParkingItem[] = [
  { id: 'p1', content: 'Explore voice input for capturing fleeting thoughts', fromStepId: '1', createdAt: new Date() },
  { id: 'p2', content: 'Research spaced repetition for revisiting parked ideas', fromStepId: '2', createdAt: new Date() },
];

// ============ Step Card Component ============
function ThinkingStepCard({
  step,
  isActive,
  onToggleExpand,
  onParkIdea,
  onAddBranch,
}: {
  step: ThinkingStep;
  isActive: boolean;
  onToggleExpand: () => void;
  onParkIdea: (content: string) => void;
  onAddBranch: (type: Branch['type']) => void;
}) {
  const [showBranches, setShowBranches] = useState(false);

  const branchTypeIcon = {
    alternative: <Lightbulb size={14} className="text-amber-500" />,
    question: <HelpCircle size={14} className="text-blue-500" />,
    counterargument: <GitBranch size={14} className="text-red-400" />,
  };

  return (
    <Paper
      elevation={isActive ? 3 : 1}
      sx={{
        p: 0,
        borderRadius: 3,
        border: '1px solid',
        borderColor: isActive ? 'primary.main' : 'divider',
        bgcolor: 'background.paper',
        transition: 'all 0.2s ease',
        overflow: 'hidden',
      }}
    >
      {/* Card Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          p: 2,
          bgcolor: isActive ? 'primary.50' : 'grey.50',
          borderBottom: '1px solid',
          borderColor: 'divider',
          cursor: 'pointer',
        }}
        onClick={onToggleExpand}
      >
        <Box
          sx={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            bgcolor: isActive ? 'primary.main' : 'grey.400',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          {step.stepNumber}
        </Box>
        <Typography variant="subtitle1" fontWeight={600} sx={{ flex: 1 }}>
          {step.claim}
        </Typography>
        <IconButton size="small">
          {step.isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
        </IconButton>
      </Box>

      {/* Card Body */}
      <Collapse in={step.isExpanded}>
        <Box sx={{ p: 2.5 }}>
          {/* Structured Fields */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ display: 'block', mb: 0.5 }}>
                REASON
              </Typography>
              <Typography variant="body2" color="text.primary">
                {step.reason}
              </Typography>
            </Box>

            <Box>
              <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ display: 'block', mb: 0.5 }}>
                EVIDENCE
              </Typography>
              <Typography variant="body2" color="text.primary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <FileText size={14} className="text-green-500" />
                {step.evidence}
              </Typography>
            </Box>

            <Box>
              <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ display: 'block', mb: 0.5 }}>
                UNCERTAINTY
              </Typography>
              <Typography variant="body2" color="text.secondary" fontStyle="italic">
                {step.uncertainty}
              </Typography>
            </Box>

            <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: 'success.50', border: '1px solid', borderColor: 'success.200' }}>
              <Typography variant="caption" color="success.dark" fontWeight={600} sx={{ display: 'block', mb: 0.5 }}>
                DECISION
              </Typography>
              <Typography variant="body2" color="success.dark" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <CheckCircle2 size={14} />
                {step.decision}
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Branches Section */}
          <Box>
            <Box
              sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', mb: 1 }}
              onClick={() => setShowBranches(!showBranches)}
            >
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                SIDE BRANCHES ({step.branches.length})
              </Typography>
              <IconButton size="small">
                {showBranches ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </IconButton>
            </Box>

            <Collapse in={showBranches}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 1.5 }}>
                {step.branches.map((branch) => (
                  <Box
                    key={branch.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 1,
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: 'grey.50',
                      border: '1px dashed',
                      borderColor: 'grey.300',
                    }}
                  >
                    {branchTypeIcon[branch.type]}
                    <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
                      {branch.content}
                    </Typography>
                    <Tooltip title="Park this idea">
                      <IconButton size="small" onClick={() => onParkIdea(branch.content)}>
                        <ParkingCircle size={14} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                ))}
              </Box>

              {/* Add Branch Buttons */}
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  icon={<Lightbulb size={12} />}
                  label="Alternative"
                  size="small"
                  variant="outlined"
                  onClick={() => onAddBranch('alternative')}
                  sx={{ cursor: 'pointer', fontSize: 11 }}
                />
                <Chip
                  icon={<HelpCircle size={12} />}
                  label="Question"
                  size="small"
                  variant="outlined"
                  onClick={() => onAddBranch('question')}
                  sx={{ cursor: 'pointer', fontSize: 11 }}
                />
                <Chip
                  icon={<GitBranch size={12} />}
                  label="Counterargument"
                  size="small"
                  variant="outlined"
                  onClick={() => onAddBranch('counterargument')}
                  sx={{ cursor: 'pointer', fontSize: 11 }}
                />
              </Box>
            </Collapse>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
}

// ============ Parking Lot Component ============
function ParkingLot({
  items,
  onRemove,
}: {
  items: ParkingItem[];
  onRemove: (id: string) => void;
}) {
  return (
    <Paper
      elevation={0}
      sx={{
        width: 280,
        height: '100%',
        borderLeft: '1px solid',
        borderColor: 'divider',
        bgcolor: 'grey.50',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ParkingCircle size={18} className="text-purple-500" />
          <Typography variant="subtitle2" fontWeight={600}>
            Parking Lot
          </Typography>
          <Chip label={items.length} size="small" sx={{ height: 20, fontSize: 11 }} />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Ideas to explore later
        </Typography>
      </Box>

      {/* Items */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 1.5 }}>
        {items.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4, color: 'text.disabled' }}>
            <ParkingCircle size={32} style={{ opacity: 0.3 }} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              No parked ideas yet
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {items.map((item) => (
              <Paper
                key={item.id}
                elevation={0}
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  bgcolor: 'background.paper',
                  border: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Typography variant="body2" sx={{ mb: 1 }}>
                  {item.content}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="text.disabled">
                    from Step {item.fromStepId}
                  </Typography>
                  <IconButton size="small" onClick={() => onRemove(item.id)}>
                    <Trash2 size={14} />
                  </IconButton>
                </Box>
              </Paper>
            ))}
          </Box>
        )}
      </Box>
    </Paper>
  );
}

// ============ Convergence View Component ============
function ConvergenceView({ steps }: { steps: ThinkingStep[] }) {
  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', py: 4 }}>
      <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h6" fontWeight={600} sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Eye size={20} />
          Convergence Summary
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            CURRENT BEST ANSWER
          </Typography>
          <Typography variant="body1" sx={{ mt: 0.5, p: 2, bgcolor: 'success.50', borderRadius: 2, border: '1px solid', borderColor: 'success.200' }}>
            Design a &quot;single active thread&quot; interface with collapsible branches and a parking lot for off-topic ideas. This balances focus with idea preservation.
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            KEY DECISIONS
          </Typography>
          <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
            {steps.map((step) => (
              <Box key={step.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircle2 size={16} className="text-green-500" />
                <Typography variant="body2">{step.decision}</Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            OPEN RISKS
          </Typography>
          <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
            {steps.filter(s => s.uncertainty).map((step) => (
              <Box key={step.id} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <HelpCircle size={16} className="text-amber-500" style={{ marginTop: 2 }} />
                <Typography variant="body2" color="text.secondary">{step.uncertainty}</Typography>
              </Box>
            ))}
          </Box>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            NEXT ACTION
          </Typography>
          <Box sx={{ mt: 1, p: 2, bgcolor: 'primary.50', borderRadius: 2, border: '1px solid', borderColor: 'primary.200' }}>
            <Typography variant="body2" color="primary.dark" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ArrowRight size={16} />
              Implement prototype and test with real deep-thinking scenarios
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}

// ============ Main Page Component ============
export default function ThinkingPathPage() {
  const [steps, setSteps] = useState<ThinkingStep[]>(INITIAL_STEPS);
  const [parkingItems, setParkingItems] = useState<ParkingItem[]>(INITIAL_PARKING);
  const [activeStepId, setActiveStepId] = useState<string>('3');
  const [viewMode, setViewMode] = useState<'path' | 'convergence'>('path');

  const handleToggleExpand = (stepId: string) => {
    setSteps((prev) =>
      prev.map((s) => (s.id === stepId ? { ...s, isExpanded: !s.isExpanded } : s))
    );
    setActiveStepId(stepId);
  };

  const handleParkIdea = (stepId: string, content: string) => {
    const newItem: ParkingItem = {
      id: `p${Date.now()}`,
      content,
      fromStepId: stepId,
      createdAt: new Date(),
    };
    setParkingItems((prev) => [newItem, ...prev]);
  };

  const handleRemoveParkingItem = (id: string) => {
    setParkingItems((prev) => prev.filter((item) => item.id !== id));
  };

  const handleAddBranch = (stepId: string, type: Branch['type']) => {
    const content = prompt(`Enter ${type}:`);
    if (!content) return;

    setSteps((prev) =>
      prev.map((s) =>
        s.id === stepId
          ? { ...s, branches: [...s.branches, { id: `b${Date.now()}`, type, content }] }
          : s
      )
    );
  };

  const handleAddStep = () => {
    const newStep: ThinkingStep = {
      id: `${Date.now()}`,
      stepNumber: steps.length + 1,
      claim: 'New Step',
      reason: '',
      evidence: '',
      uncertainty: '',
      decision: '',
      branches: [],
      isExpanded: true,
    };
    setSteps((prev) => [...prev, newStep]);
    setActiveStepId(newStep.id);
  };

  return (
    <GlobalLayout>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
        {/* Top Bar */}
        <Box
          sx={{
            px: 3,
            py: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Route size={24} className="text-purple-600" />
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Thinking Path
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Deep Thinker Interface Design
              </Typography>
            </Box>
          </Box>

          {/* View Toggle */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant={viewMode === 'path' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setViewMode('path')}
              sx={{ textTransform: 'none' }}
            >
              Path View
            </Button>
            <Button
              variant={viewMode === 'convergence' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setViewMode('convergence')}
              sx={{ textTransform: 'none' }}
            >
              Convergence View
            </Button>
          </Box>
        </Box>

        {/* Main Content */}
        <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {viewMode === 'path' ? (
            <>
              {/* Main Thread */}
              <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
                {/* Breadcrumb Timeline */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3, flexWrap: 'wrap' }}>
                  {steps.map((step, idx) => (
                    <Box key={step.id} sx={{ display: 'flex', alignItems: 'center' }}>
                      <Chip
                        label={step.claim}
                        size="small"
                        onClick={() => setActiveStepId(step.id)}
                        sx={{
                          bgcolor: activeStepId === step.id ? 'primary.main' : 'grey.200',
                          color: activeStepId === step.id ? 'white' : 'text.primary',
                          fontWeight: activeStepId === step.id ? 600 : 400,
                          cursor: 'pointer',
                          '&:hover': { bgcolor: activeStepId === step.id ? 'primary.dark' : 'grey.300' },
                        }}
                      />
                      {idx < steps.length - 1 && (
                        <ArrowRight size={16} style={{ margin: '0 4px', color: '#9CA3AF' }} />
                      )}
                    </Box>
                  ))}
                </Box>

                {/* Step Cards */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxWidth: 700 }}>
                  {steps.map((step) => (
                    <ThinkingStepCard
                      key={step.id}
                      step={step}
                      isActive={activeStepId === step.id}
                      onToggleExpand={() => handleToggleExpand(step.id)}
                      onParkIdea={(content) => handleParkIdea(step.id, content)}
                      onAddBranch={(type) => handleAddBranch(step.id, type)}
                    />
                  ))}

                  {/* Add Step Button */}
                  <Button
                    variant="outlined"
                    startIcon={<Plus size={18} />}
                    onClick={handleAddStep}
                    sx={{
                      textTransform: 'none',
                      borderStyle: 'dashed',
                      color: 'text.secondary',
                      borderColor: 'grey.300',
                      '&:hover': { borderColor: 'primary.main', color: 'primary.main' },
                    }}
                  >
                    Add Next Step
                  </Button>
                </Box>
              </Box>

              {/* Parking Lot Sidebar */}
              <ParkingLot items={parkingItems} onRemove={handleRemoveParkingItem} />
            </>
          ) : (
            <ConvergenceView steps={steps} />
          )}
        </Box>
      </Box>
    </GlobalLayout>
  );
}












