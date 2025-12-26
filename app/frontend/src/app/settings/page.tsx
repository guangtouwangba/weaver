'use client';

import { useState, useEffect, useCallback } from 'react';
import GlobalLayout from '@/components/layout/GlobalLayout';
import StrategyTooltip, { StrategyOption } from '@/components/settings/StrategyTooltip';
import StrategyCard from '@/components/settings/StrategyCard';
import { settingsApi, SettingMetadata } from '@/lib/api';
import { 
  Box, 
  Typography, 
  Paper, 
  Avatar, 
  Divider, 
  List, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText,
  TextField,
  Button,
  Chip,
  InputAdornment,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Snackbar,
  Slider,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Switch,
  Box as MuiBox,
} from '@mui/material';
import { 
  AutoAwesomeIcon, 
  CheckIcon, 
  CloseIcon, 
  SearchIcon, 
  TuneIcon,
  DescriptionIcon,
} from '@/components/ui/icons';
import PersonMui from '@mui/icons-material/Person';
import MemoryMui from '@mui/icons-material/Memory';
import StorageMui from '@mui/icons-material/Storage';
import PaletteMui from '@mui/icons-material/Palette';
import LogoutMui from '@mui/icons-material/Logout';
import VisibilityMui from '@mui/icons-material/Visibility';
import VisibilityOffMui from '@mui/icons-material/VisibilityOff';
import VpnKeyMui from '@mui/icons-material/VpnKey';

// Mock user data (will be replaced with auth)
const MOCK_USER = {
  name: "Alex Li",
  email: "alex@weaver.ai",
  avatar: "AL"
};

interface SettingsState {
  // API Keys
  openrouter_api_key: string;
  // Models
  llm_model: string;
  embedding_model: string;
  // RAG Strategy
  rag_mode: string;
  long_context_safety_ratio: number;
  fast_upload_mode: boolean;
  retrieval_strategy: string;
  retrieval_top_k: number;
  retrieval_min_similarity: number;
  citation_format: string;
  // Document Processing
  document_processing_mode: string;
  // Advanced
  intent_classification_enabled: boolean;
}

const defaultSettings: SettingsState = {
  openrouter_api_key: '',
  llm_model: 'openai/gpt-4o-mini',
  embedding_model: 'openai/text-embedding-3-small',
  rag_mode: 'traditional',
  long_context_safety_ratio: 0.55,
  fast_upload_mode: true,
  retrieval_strategy: 'vector',
  retrieval_top_k: 5,
  retrieval_min_similarity: 0,
  citation_format: 'both',
  document_processing_mode: 'standard',
  intent_classification_enabled: true,
};

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('ai');
  const [showKey, setShowKey] = useState(false);
  const [settings, setSettings] = useState<SettingsState>(defaultSettings);
  const [metadata, setMetadata] = useState<Record<string, SettingMetadata>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [validatingKey, setValidatingKey] = useState(false);
  const [keyValidation, setKeyValidation] = useState<{ valid: boolean; message: string } | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const menuItems = [
    { id: 'profile', label: 'Profile & Account', icon: <PersonMui sx={{ fontSize: 20 }} /> },
    { id: 'ai', label: 'AI & Models', icon: <MemoryMui sx={{ fontSize: 20 }} /> },
    { id: 'rag', label: 'RAG Strategy', icon: <SearchIcon size="md" /> },
    { id: 'advanced', label: 'Advanced', icon: <TuneIcon size="md" /> },
    { id: 'appearance', label: 'Appearance', icon: <PaletteMui sx={{ fontSize: 20 }} /> },
  ];

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        const [settingsRes, metadataRes] = await Promise.all([
          settingsApi.getUserSettings(),
          settingsApi.getMetadata(),
        ]);
        
        // Merge with defaults
        setSettings({
          ...defaultSettings,
          ...settingsRes.settings as Partial<SettingsState>,
        });
        setMetadata(metadataRes.settings);
      } catch (error) {
        console.error('Failed to load settings:', error);
        setSnackbar({ open: true, message: 'Failed to load settings', severity: 'error' });
      } finally {
        setLoading(false);
      }
    };
    
    loadSettings();
  }, []);

  // Save setting with debounce
  const saveSetting = useCallback(async (key: string, value: unknown) => {
    try {
      setSaving(true);
      await settingsApi.updateUserSetting(key, value);
      setSnackbar({ open: true, message: 'Setting saved', severity: 'success' });
    } catch (error) {
      console.error('Failed to save setting:', error);
      setSnackbar({ open: true, message: 'Failed to save setting', severity: 'error' });
    } finally {
      setSaving(false);
    }
  }, []);

  // Handle direct selection (for cards)
  const handleSelection = (key: keyof SettingsState, value: string) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    saveSetting(key, value);
  };

  // Handle setting change
  const handleChange = (key: keyof SettingsState) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | Event,
    newValue?: number | boolean
  ) => {
    let value: string | number | boolean;
    
    if (typeof newValue !== 'undefined') {
      value = newValue;
    } else if ('target' in event && event.target) {
      const target = event.target as HTMLInputElement;
      value = target.type === 'checkbox' ? target.checked : target.value;
    } else {
      return;
    }
    
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  // Save on blur (for text fields)
  const handleBlur = (key: keyof SettingsState) => () => {
    saveSetting(key, settings[key]);
  };

  // Validate API key
  const handleValidateApiKey = async () => {
    if (!settings.openrouter_api_key) {
      setKeyValidation({ valid: false, message: 'Please enter an API key' });
      return;
    }

    try {
      setValidatingKey(true);
      setKeyValidation(null);
      const result = await settingsApi.validateApiKey(settings.openrouter_api_key);
      setKeyValidation(result);
      
      if (result.valid) {
        await saveSetting('openrouter_api_key', settings.openrouter_api_key);
      }
    } catch (error) {
      setKeyValidation({ valid: false, message: 'Validation failed' });
    } finally {
      setValidatingKey(false);
    }
  };

  // Get options for a setting from metadata
  const getOptions = (key: string): StrategyOption[] => {
    return (metadata[key]?.options as StrategyOption[]) || [];
  };

  if (loading) {
    return (
      <GlobalLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
          <CircularProgress />
        </Box>
      </GlobalLayout>
    );
  }

  return (
    <GlobalLayout>
      <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto', minHeight: '100vh' }}>
        <Typography variant="h4" fontWeight="800" gutterBottom sx={{ mb: 4 }}>
          Settings
        </Typography>

        <Box sx={{ display: 'flex', gap: 4, flexDirection: { xs: 'column', md: 'row' } }}>
          
          {/* LEFT SIDEBAR: Navigation & Identity */}
          <Paper 
            elevation={0}
            sx={{ 
              width: { xs: '100%', md: 280 }, 
              height: 'fit-content',
              borderRadius: 4,
              border: '1px solid',
              borderColor: 'divider',
              overflow: 'hidden'
            }}
          >
            {/* User Identity Card */}
            <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', bgcolor: 'background.default' }}>
              <Avatar 
                sx={{ 
                  width: 72, 
                  height: 72, 
                  bgcolor: 'primary.main', 
                  fontSize: '1.75rem',
                  fontWeight: 600,
                  mb: 2,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                }}
              >
                {MOCK_USER.avatar}
              </Avatar>
              <Typography variant="h6" fontWeight="700">{MOCK_USER.name}</Typography>
              <Typography variant="body2" color="text.secondary">{MOCK_USER.email}</Typography>
              <Chip 
                label="Pro Plan" 
                size="small" 
                color="primary" 
                variant="outlined" 
                sx={{ mt: 1.5, height: 24, fontWeight: 600 }} 
              />
            </Box>
            
            <Divider />

            {/* Navigation Menu */}
            <List sx={{ p: 1 }}>
              {menuItems.map((item) => (
                <ListItemButton
                  key={item.id}
                  selected={activeTab === item.id}
                  onClick={() => setActiveTab(item.id)}
                  sx={{
                    borderRadius: 2,
                    mb: 0.5,
                    '&.Mui-selected': {
                      bgcolor: 'primary.50',
                      color: 'primary.main',
                    },
                    '&:hover': {
                      bgcolor: 'action.hover'
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40, color: activeTab === item.id ? 'primary.main' : 'text.secondary' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.label} 
                    primaryTypographyProps={{ fontWeight: activeTab === item.id ? 600 : 500 }}
                  />
                </ListItemButton>
              ))}
            </List>
            
            <Divider sx={{ my: 1 }} />
            
            <Box sx={{ p: 1 }}>
              <ListItemButton sx={{ borderRadius: 2, color: 'error.main' }}>
                <ListItemIcon sx={{ minWidth: 40, color: 'error.main' }}>
                  <LogoutMui sx={{ fontSize: 20 }} />
                </ListItemIcon>
                <ListItemText primary="Sign Out" primaryTypographyProps={{ fontWeight: 500 }} />
              </ListItemButton>
            </Box>
          </Paper>

          {/* RIGHT CONTENT: Configuration Panels */}
          <Box sx={{ flex: 1 }}>
            
            {/* AI & Models Section */}
            {activeTab === 'ai' && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* API Key Section */}
                <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Box sx={{ p: 1, borderRadius: 2, bgcolor: 'primary.50', color: 'primary.main' }}>
                      <VpnKeyMui sx={{ fontSize: 24 }} />
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="700">API Configuration</Typography>
                      <Typography variant="body2" color="text.secondary">Configure your LLM provider</Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                    <TextField
                      label="API Key (OpenRouter / OpenAI)"
                      type={showKey ? 'text' : 'password'}
                      fullWidth
                      value={settings.openrouter_api_key}
                      onChange={handleChange('openrouter_api_key')}
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton onClick={() => setShowKey(!showKey)} edge="end">
                              {showKey ? <VisibilityOffMui sx={{ fontSize: 20 }} /> : <VisibilityMui sx={{ fontSize: 20 }} />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                      helperText="Your key is encrypted and stored securely."
                    />
                    
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                      <Button 
                        variant="outlined" 
                        onClick={handleValidateApiKey}
                        disabled={validatingKey}
                        startIcon={validatingKey ? <CircularProgress size={16} /> : null}
                      >
                        {validatingKey ? 'Validating...' : 'Validate & Save Key'}
                      </Button>
                      
                      {keyValidation && (
                        <Chip
                          icon={keyValidation.valid ? <Check size={16} /> : <X size={16} />}
                          label={keyValidation.message}
                          color={keyValidation.valid ? 'success' : 'error'}
                          size="small"
                        />
                      )}
                    </Box>
                  </Box>
                </Paper>

                {/* Model Selection */}
                <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Box sx={{ p: 1, borderRadius: 2, bgcolor: 'secondary.50', color: 'secondary.main' }}>
                      <AutoAwesomeMui sx={{ fontSize: 24 }} />
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="700">Model Selection</Typography>
                      <Typography variant="body2" color="text.secondary">Choose your AI models</Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <FormControl fullWidth>
                      <FormLabel sx={{ mb: 2, fontWeight: 600, color: 'text.primary' }}>LLM Model</FormLabel>
                      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2 }}>
                        {getOptions('llm_model').map((opt) => (
                          <StrategyCard 
                            key={opt.value}
                            option={opt}
                            selected={settings.llm_model === opt.value}
                            onClick={() => handleSelection('llm_model', opt.value)}
                          />
                        ))}
                      </Box>
                    </FormControl>
                  </Box>
                </Paper>
              </Box>
            )}

            {/* RAG Strategy Section */}
            {activeTab === 'rag' && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* RAG Mode */}
                <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Box sx={{ p: 1, borderRadius: 2, bgcolor: 'info.50', color: 'info.main' }}>
                      <StorageMui sx={{ fontSize: 24 }} />
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="700">RAG Mode</Typography>
                      <Typography variant="body2" color="text.secondary">How documents are processed for answering questions</Typography>
                    </Box>
                  </Box>

                  <FormControl fullWidth>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2 }}>
                      {getOptions('rag_mode').map((opt) => (
                        <StrategyCard 
                          key={opt.value}
                          option={opt}
                          selected={settings.rag_mode === opt.value}
                          onClick={() => handleSelection('rag_mode', opt.value)}
                        />
                      ))}
                    </Box>
                  </FormControl>
                </Paper>

                {/* Document Processing Mode */}
                <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Box sx={{ p: 1, borderRadius: 2, bgcolor: 'success.50', color: 'success.main' }}>
                      <DescriptionMui sx={{ fontSize: 24 }} />
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="700">Document Processing</Typography>
                      <Typography variant="body2" color="text.secondary">How documents are parsed and text is extracted</Typography>
                    </Box>
                  </Box>

                  <FormControl fullWidth>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2 }}>
                      {getOptions('document_processing_mode').map((opt) => (
                        <StrategyCard 
                          key={opt.value}
                          option={opt}
                          selected={settings.document_processing_mode === opt.value}
                          onClick={() => handleSelection('document_processing_mode', opt.value)}
                        />
                      ))}
                    </Box>
                  </FormControl>
                </Paper>

                {/* Retrieval Strategy - Only show for Traditional (chunk-based) mode */}
                {settings.rag_mode === 'traditional' && (
                  <>
                    <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                        <Box sx={{ p: 1, borderRadius: 2, bgcolor: 'warning.50', color: 'warning.main' }}>
                          <SearchIcon size="lg" />
                        </Box>
                        <Box>
                          <Typography variant="h6" fontWeight="700">Retrieval Strategy</Typography>
                          <Typography variant="body2" color="text.secondary">How relevant content is found in your documents</Typography>
                        </Box>
                      </Box>

                      <FormControl fullWidth>
                        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2 }}>
                          {getOptions('retrieval_strategy').map((opt) => (
                            <StrategyCard 
                              key={opt.value}
                              option={opt}
                              selected={settings.retrieval_strategy === opt.value}
                              onClick={() => handleSelection('retrieval_strategy', opt.value)}
                            />
                          ))}
                        </Box>
                      </FormControl>
                    </Paper>

                    {/* Retrieval Parameters */}
                    <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="h6" fontWeight="700" gutterBottom>Retrieval Parameters</Typography>
                      
                      <Box sx={{ mt: 3 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Top-K Documents: {settings.retrieval_top_k}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                          Number of document chunks to retrieve for each query
                        </Typography>
                        <Slider
                          value={settings.retrieval_top_k}
                          onChange={handleChange('retrieval_top_k')}
                          onChangeCommitted={(_, value) => saveSetting('retrieval_top_k', value)}
                          min={1}
                          max={20}
                          marks={[
                            { value: 1, label: '1' },
                            { value: 5, label: '5' },
                            { value: 10, label: '10' },
                            { value: 20, label: '20' },
                          ]}
                          valueLabelDisplay="auto"
                        />
                      </Box>

                      <Box sx={{ mt: 4 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Min Similarity: {(settings.retrieval_min_similarity * 100).toFixed(0)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                          Minimum similarity threshold for retrieved documents
                        </Typography>
                        <Slider
                          value={settings.retrieval_min_similarity}
                          onChange={handleChange('retrieval_min_similarity')}
                          onChangeCommitted={(_, value) => saveSetting('retrieval_min_similarity', value)}
                          min={0}
                          max={1}
                          step={0.05}
                          marks={[
                            { value: 0, label: '0%' },
                            { value: 0.5, label: '50%' },
                            { value: 1, label: '100%' },
                          ]}
                          valueLabelDisplay="auto"
                          valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                        />
                      </Box>
                    </Paper>
                  </>
                )}

                {/* Long Context Mode Settings */}
                {settings.rag_mode === 'long_context' && (
                  <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="h6" fontWeight="700" gutterBottom>Context Window Settings</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      Control how much of the model&apos;s context window is used for document content. 
                      Documents exceeding this limit will use chunked retrieval instead.
                    </Typography>
                    
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Context Usage Ratio: {(settings.long_context_safety_ratio * 100).toFixed(0)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        Higher values allow more document content but leave less space for responses.
                      </Typography>
                      <Slider
                        value={settings.long_context_safety_ratio}
                        onChange={handleChange('long_context_safety_ratio')}
                        onChangeCommitted={(_, value) => saveSetting('long_context_safety_ratio', value)}
                        min={0.3}
                        max={0.9}
                        step={0.05}
                        marks={[
                          { value: 0.4, label: '40%' },
                          { value: 0.55, label: '55%' },
                          { value: 0.7, label: '70%' },
                          { value: 0.85, label: '85%' },
                        ]}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                      />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          Conservative (more response space)
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Aggressive (more document content)
                        </Typography>
                      </Box>
                    </Box>

                    {/* Fast Upload Mode Switch */}
                    <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={settings.fast_upload_mode}
                            onChange={(e) => {
                              handleChange('fast_upload_mode')(e, e.target.checked);
                              saveSetting('fast_upload_mode', e.target.checked);
                            }}
                            color="primary"
                          />
                        }
                        label={
                          <Box>
                            <Typography variant="subtitle2" fontWeight="600">
                              Fast Upload Mode
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                              Skip summary generation and embeddings to speed up document processing. 
                              Documents will be ready for querying immediately after upload.
                            </Typography>
                          </Box>
                        }
                        sx={{ alignItems: 'flex-start' }}
                      />
                    </Box>
                  </Paper>
                )}
              </Box>
            )}

            {/* Advanced Section */}
            {activeTab === 'advanced' && (
              <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="h6" fontWeight="700" gutterBottom>Advanced Settings</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Fine-tune the behavior of your research assistant
                </Typography>

                <FormControl fullWidth>
                  <FormLabel sx={{ mb: 2, fontWeight: 600 }}>Citation Format</FormLabel>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2 }}>
                    {getOptions('citation_format').map((opt) => (
                      <StrategyCard 
                        key={opt.value}
                        option={opt}
                        selected={settings.citation_format === opt.value}
                        onClick={() => handleSelection('citation_format', opt.value)}
                      />
                    ))}
                  </Box>
                </FormControl>
              </Paper>
            )}

            {/* Profile Section */}
            {activeTab === 'profile' && (
              <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="h6" fontWeight="700" gutterBottom>Personal Information</Typography>
                <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <TextField label="Display Name" defaultValue={MOCK_USER.name} fullWidth />
                  <TextField label="Email Address" defaultValue={MOCK_USER.email} disabled fullWidth />
                  <Box>
                    <Button variant="contained" sx={{ bgcolor: 'black', '&:hover': { bgcolor: '#333' } }}>
                      Save Changes
                    </Button>
                  </Box>
                </Box>
              </Paper>
            )}

            {/* Placeholder for appearance tab */}
            {activeTab === 'appearance' && (
              <Paper elevation={0} sx={{ p: 4, borderRadius: 4, border: '1px dashed', borderColor: 'divider', textAlign: 'center' }}>
                <Typography color="text.secondary">Appearance settings coming soon.</Typography>
              </Paper>
            )}

          </Box>
        </Box>
      </Box>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))} 
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </GlobalLayout>
  );
}
