'use client';

import { useState, useEffect, useCallback } from 'react';
import GlobalLayout from '@/components/layout/GlobalLayout';
import { StrategyOption } from '@/components/settings/StrategyTooltip';
import StrategyCard from '@/components/settings/StrategyCard';
import { settingsApi, SettingMetadata } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import {
  Stack,
  Text,
  Button,
  Surface,
  Spinner,
  Chip,
  IconButton,
  Avatar,
  Switch,
  Slider,
} from '@/components/ui/primitives';
import { TextField } from '@/components/ui/composites';
import { colors } from '@/components/ui/tokens';
import {
  AutoAwesomeIcon,
  CheckIcon,
  CloseIcon,
  SearchIcon,
  TuneIcon,
  DescriptionIcon,
  PersonIcon,
  BrainIcon,
  StorageIcon,
  PaletteIcon,
  LogoutIcon,
  VisibilityIcon,
  VisibilityOffIcon,
  KeyIcon,
  InfoIcon,
} from '@/components/ui/icons';

// Get user display info
const getUserDisplayInfo = (
  user: {
    id: string;
    email?: string;
    user_metadata?: { full_name?: string; name?: string };
  } | null
) => {
  if (!user) return { name: 'User', email: '', avatar: 'U' };
  const name =
    user.user_metadata?.full_name ||
    user.user_metadata?.name ||
    user.email?.split('@')[0] ||
    'User';
  const email = user.email || '';
  const avatar =
    name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'U';
  return { name, email, avatar };
};

const NotificationToast = ({
  open,
  message,
  severity,
  onClose,
}: {
  open: boolean;
  message: string;
  severity: 'success' | 'error';
  onClose: () => void;
}) => {
  if (!open) return null;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 2000,
        animation: 'slideUp 0.3s ease-out',
      }}
    >
      <Surface
        elevation={2}
        radius="lg"
        style={{
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          backgroundColor:
            severity === 'error' ? colors.error[50] : colors.success[50],
          border: '1px solid',
          borderColor:
            severity === 'error' ? colors.error[200] : colors.success[200],
          color: severity === 'error' ? colors.error[700] : colors.success[700],
        }}
      >
        {severity === 'error' ? (
          <InfoIcon size={18} style={{ color: colors.error[500] }} />
        ) : (
          <CheckIcon size={18} style={{ color: colors.success[500] }} />
        )}
        <Text variant="bodySmall" fontWeight="500" color="inherit">
          {message}
        </Text>
        <IconButton
          size="sm"
          onClick={onClose}
          style={{
            marginLeft: 8,
            color:
              severity === 'error' ? colors.error[500] : colors.success[500],
          }}
        >
          <CloseIcon size={16} />
        </IconButton>
      </Surface>
    </div>
  );
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
  llm_model: 'google/gemini-2.5-flash',
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
  const [validatingKey, setValidatingKey] = useState(false);
  const [keyValidation, setKeyValidation] = useState<{
    valid: boolean;
    message: string;
  } | null>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // Get real user ID from auth context
  const { user } = useAuth();
  const userId = user?.id;

  const menuItems = [
    {
      id: 'profile',
      label: 'Profile & Account',
      icon: <PersonIcon size={20} />,
    },
    { id: 'ai', label: 'AI & Models', icon: <BrainIcon size={20} /> },
    { id: 'rag', label: 'RAG Strategy', icon: <SearchIcon size={20} /> },
    { id: 'advanced', label: 'Advanced', icon: <TuneIcon size={20} /> },
    { id: 'appearance', label: 'Appearance', icon: <PaletteIcon size={20} /> },
  ];

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      if (!userId) {
        // Wait for auth to be ready
        return;
      }
      try {
        setLoading(true);
        const [settingsRes, metadataRes] = await Promise.all([
          settingsApi.getUserSettings(userId),
          settingsApi.getMetadata(),
        ]);

        // Merge with defaults
        setSettings({
          ...defaultSettings,
          ...(settingsRes.settings as Partial<SettingsState>),
        });
        setMetadata(metadataRes.settings);
      } catch (error) {
        console.error('Failed to load settings:', error);
        setSnackbar({
          open: true,
          message: 'Failed to load settings',
          severity: 'error',
        });
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, [userId]);

  // Save setting with debounce
  const saveSetting = useCallback(
    async (key: string, value: unknown) => {
      if (!userId) return;
      try {
        await settingsApi.updateUserSetting(key, value, userId);
        setSnackbar({
          open: true,
          message: 'Setting saved',
          severity: 'success',
        });
      } catch (error) {
        console.error('Failed to save setting:', error);
        setSnackbar({
          open: true,
          message: 'Failed to save setting',
          severity: 'error',
        });
      }
    },
    [userId]
  );

  // Handle direct selection (for cards)
  const handleSelection = (key: keyof SettingsState, value: string) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    saveSetting(key, value);
  };

  // Handle setting change
  const handleChange =
    (key: keyof SettingsState) =>
    (
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

      setSettings((prev) => ({ ...prev, [key]: value }));
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
      const result = await settingsApi.validateApiKey(
        settings.openrouter_api_key
      );
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

  if (loading || !userId) {
    return (
      <GlobalLayout>
        <Stack align="center" justify="center" style={{ minHeight: '100vh' }}>
          <Spinner />
        </Stack>
      </GlobalLayout>
    );
  }

  return (
    <GlobalLayout>
      <div
        style={{
          padding: 32,
          maxWidth: 1200,
          margin: '0 auto',
          minHeight: '100vh',
        }}
      >
        <Text variant="h4" fontWeight="800" style={{ marginBottom: 32 }}>
          Settings
        </Text>

        <div
          style={{
            display: 'flex',
            gap: 32,
            flexWrap: 'wrap',
            alignItems: 'flex-start',
          }}
        >
          {/* Sidebar */}
          <Surface
            elevation={0}
            style={{
              width: 280,
              height: 'fit-content',
              borderRadius: 16,
              border: `1px solid ${colors.border.default}`,
              overflow: 'hidden',
              flexShrink: 0,
            }}
          >
            {/* User Identity */}
            <Stack
              align="center"
              style={{
                padding: 24,
                backgroundColor: colors.background.default,
              }}
            >
              <Avatar
                style={{
                  width: 72,
                  height: 72,
                  backgroundColor: colors.primary[500],
                  fontSize: '1.75rem',
                  fontWeight: 600,
                  marginBottom: 16,
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                }}
              >
                {getUserDisplayInfo(user).avatar}
              </Avatar>
              <Text variant="h6" fontWeight="700">
                {getUserDisplayInfo(user).name}
              </Text>
              <Text variant="bodySmall" color="secondary">
                {getUserDisplayInfo(user).email}
              </Text>
              <Chip
                label="Pro Plan"
                size="sm"
                variant="outlined"
                style={{ marginTop: 12, height: 24, fontWeight: 600 }}
              />
            </Stack>

            <div style={{ height: 1, backgroundColor: '#E5E7EB', margin: 0 }} />

            {/* Navigation Menu */}
            <Stack gap={4} style={{ padding: 8 }}>
              {menuItems.map((item) => (
                <Surface
                  key={item.id}
                  elevation={0}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    padding: 12,
                    cursor: 'pointer',
                    backgroundColor:
                      activeTab === item.id
                        ? colors.primary[50]
                        : 'transparent',
                    color:
                      activeTab === item.id
                        ? colors.primary[500]
                        : colors.text.secondary,
                    borderRadius: 8,
                    transition: 'all 0.2s',
                  }}
                >
                  <Stack direction="row" align="center" gap={16}>
                    <div style={{ display: 'flex' }}>{item.icon}</div>
                    <Text
                      fontWeight={activeTab === item.id ? 600 : 500}
                      color={activeTab === item.id ? 'primary' : 'secondary'}
                    >
                      {item.label}
                    </Text>
                  </Stack>
                </Surface>
              ))}
            </Stack>

            <div
              style={{ height: 1, backgroundColor: '#E5E7EB', margin: '8px 0' }}
            />

            <Stack style={{ padding: 8 }}>
              <Surface
                elevation={0}
                style={{
                  padding: 12,
                  borderRadius: 8,
                  color: colors.error[500],
                  cursor: 'pointer',
                }}
              >
                <Stack direction="row" align="center" gap={16}>
                  <div style={{ display: 'flex' }}>
                    <LogoutIcon size={20} />
                  </div>
                  <Text fontWeight={500} color="error">
                    Sign Out
                  </Text>
                </Stack>
              </Surface>
            </Stack>
          </Surface>

          {/* Content */}
          <div
            style={{
              flex: 1,
              minWidth: 300,
              display: 'flex',
              flexDirection: 'column',
              gap: 24,
            }}
          >
            {/* Panels */}
            {activeTab === 'ai' && (
              <div
                style={{ display: 'flex', flexDirection: 'column', gap: 24 }}
              >
                {/* API Key */}
                <Surface
                  elevation={0}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    border: `1px solid ${colors.border.default}`,
                  }}
                >
                  {/* Header */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      marginBottom: 24,
                    }}
                  >
                    <div
                      style={{
                        padding: 8,
                        borderRadius: 8,
                        backgroundColor: colors.primary[50],
                        color: colors.primary[500],
                      }}
                    >
                      <KeyIcon size={24} />
                    </div>
                    <div>
                      <Text variant="h6" fontWeight="700">
                        API Configuration
                      </Text>
                      <Text variant="bodySmall" color="secondary">
                        Configure your LLM provider
                      </Text>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 20,
                    }}
                  >
                    <TextField
                      label="API Key (OpenRouter / OpenAI)"
                      type={showKey ? 'text' : 'password'}
                      fullWidth
                      value={settings.openrouter_api_key}
                      onChange={handleChange('openrouter_api_key')}
                      endAdornment={
                        <IconButton
                          onClick={() => setShowKey(!showKey)}
                          size="sm"
                        >
                          {showKey ? (
                            <VisibilityOffIcon size={20} />
                          ) : (
                            <VisibilityIcon size={20} />
                          )}
                        </IconButton>
                      }
                      helperText="Your key is encrypted and stored securely."
                    />

                    <div
                      style={{ display: 'flex', gap: 16, alignItems: 'center' }}
                    >
                      <Button
                        variant="outline"
                        onClick={handleValidateApiKey}
                        disabled={validatingKey}
                        startIcon={validatingKey ? <Spinner size="sm" /> : null}
                      >
                        {validatingKey
                          ? 'Validating...'
                          : 'Validate & Save Key'}
                      </Button>

                      {keyValidation && (
                        <Chip
                          icon={
                            keyValidation.valid ? (
                              <CheckIcon size={16} />
                            ) : (
                              <CloseIcon size={16} />
                            )
                          }
                          label={keyValidation.message}
                          color={keyValidation.valid ? 'success' : 'error'}
                          size="sm"
                        />
                      )}
                    </div>
                  </div>
                </Surface>

                {/* Model Selection */}
                <Surface
                  elevation={0}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    border: `1px solid ${colors.border.default}`,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      marginBottom: 24,
                    }}
                  >
                    <div
                      style={{
                        padding: 8,
                        borderRadius: 8,
                        backgroundColor: colors.primary[50],
                        color: colors.primary[500],
                      }}
                    >
                      <AutoAwesomeIcon size={24} />
                    </div>
                    <div>
                      <Text variant="h6" fontWeight="700">
                        Model Selection
                      </Text>
                      <Text variant="bodySmall" color="secondary">
                        Choose your AI models
                      </Text>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 24,
                    }}
                  >
                    <div style={{ width: '100%' }}>
                      <Text style={{ marginBottom: 16, fontWeight: 600 }}>
                        LLM Model
                      </Text>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns:
                            'repeat(auto-fit, minmax(280px, 1fr))',
                          gap: 16,
                        }}
                      >
                        {getOptions('llm_model').map((opt) => (
                          <StrategyCard
                            key={opt.value}
                            option={opt}
                            selected={settings.llm_model === opt.value}
                            onClick={() =>
                              handleSelection('llm_model', opt.value)
                            }
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </Surface>
              </div>
            )}

            {/* RAG Strategy Section */}
            {activeTab === 'rag' && (
              <div
                style={{ display: 'flex', flexDirection: 'column', gap: 24 }}
              >
                {/* RAG Mode */}
                <Surface
                  elevation={0}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    border: `1px solid ${colors.border.default}`,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      marginBottom: 24,
                    }}
                  >
                    <div
                      style={{
                        padding: 8,
                        borderRadius: 8,
                        backgroundColor: colors.info[50],
                        color: colors.info[500],
                      }}
                    >
                      <StorageIcon size={24} />
                    </div>
                    <div>
                      <Text variant="h6" fontWeight="700">
                        RAG Mode
                      </Text>
                      <Text variant="bodySmall" color="secondary">
                        How documents are processed for answering questions
                      </Text>
                    </div>
                  </div>

                  <div style={{ width: '100%' }}>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns:
                          'repeat(auto-fit, minmax(280px, 1fr))',
                        gap: 16,
                      }}
                    >
                      {getOptions('rag_mode').map((opt) => (
                        <StrategyCard
                          key={opt.value}
                          option={opt}
                          selected={settings.rag_mode === opt.value}
                          onClick={() => handleSelection('rag_mode', opt.value)}
                        />
                      ))}
                    </div>
                  </div>
                </Surface>

                {/* Document Processing Mode */}
                <Surface
                  elevation={0}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    border: `1px solid ${colors.border.default}`,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      marginBottom: 24,
                    }}
                  >
                    <div
                      style={{
                        padding: 8,
                        borderRadius: 8,
                        backgroundColor: colors.success[50],
                        color: colors.success[500],
                      }}
                    >
                      <DescriptionIcon size={24} />
                    </div>
                    <div>
                      <Text variant="h6" fontWeight="700">
                        Document Processing
                      </Text>
                      <Text variant="bodySmall" color="secondary">
                        How documents are parsed and text is extracted
                      </Text>
                    </div>
                  </div>

                  <div style={{ width: '100%' }}>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns:
                          'repeat(auto-fit, minmax(280px, 1fr))',
                        gap: 16,
                      }}
                    >
                      {getOptions('document_processing_mode').map((opt) => (
                        <StrategyCard
                          key={opt.value}
                          option={opt}
                          selected={
                            settings.document_processing_mode === opt.value
                          }
                          onClick={() =>
                            handleSelection(
                              'document_processing_mode',
                              opt.value
                            )
                          }
                        />
                      ))}
                    </div>
                  </div>
                </Surface>

                {/* Retrieval Strategy */}
                {settings.rag_mode === 'traditional' && (
                  <>
                    <Surface
                      elevation={0}
                      style={{
                        padding: 24,
                        borderRadius: 16,
                        border: `1px solid ${colors.border.default}`,
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 12,
                          marginBottom: 24,
                        }}
                      >
                        <div
                          style={{
                            padding: 8,
                            borderRadius: 8,
                            backgroundColor: colors.warning[50],
                            color: colors.warning[500],
                          }}
                        >
                          <SearchIcon size={24} />
                        </div>
                        <div>
                          <Text variant="h6" fontWeight="700">
                            Retrieval Strategy
                          </Text>
                          <Text variant="bodySmall" color="secondary">
                            How relevant content is found in your documents
                          </Text>
                        </div>
                      </div>

                      <div style={{ width: '100%' }}>
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns:
                              'repeat(auto-fit, minmax(280px, 1fr))',
                            gap: 16,
                          }}
                        >
                          {getOptions('retrieval_strategy').map((opt) => (
                            <StrategyCard
                              key={opt.value}
                              option={opt}
                              selected={
                                settings.retrieval_strategy === opt.value
                              }
                              onClick={() =>
                                handleSelection('retrieval_strategy', opt.value)
                              }
                            />
                          ))}
                        </div>
                      </div>
                    </Surface>

                    {/* Retrieval Parameters */}
                    <Surface
                      elevation={0}
                      style={{
                        padding: 24,
                        borderRadius: 16,
                        border: `1px solid ${colors.border.default}`,
                      }}
                    >
                      <Text
                        variant="h6"
                        fontWeight="700"
                        style={{ marginBottom: 16 }}
                      >
                        Retrieval Parameters
                      </Text>

                      <div style={{ marginTop: 24 }}>
                        <Text variant="bodySmall" style={{ marginBottom: 4 }}>
                          Top-K Documents: {settings.retrieval_top_k}
                        </Text>
                        <Text
                          variant="caption"
                          color="secondary"
                          style={{ display: 'block', marginBottom: 8 }}
                        >
                          Number of document chunks to retrieve for each query
                        </Text>
                        <Slider
                          value={settings.retrieval_top_k}
                          onChange={(val) =>
                            setSettings((prev) => ({
                              ...prev,
                              retrieval_top_k: val,
                            }))
                          }
                          onCommit={(val) =>
                            saveSetting('retrieval_top_k', val)
                          }
                          min={1}
                          max={20}
                          step={1}
                        />
                      </div>

                      <div style={{ marginTop: 32 }}>
                        <Text variant="bodySmall" style={{ marginBottom: 4 }}>
                          Minimum Similarity:{' '}
                          {(settings.retrieval_min_similarity * 100).toFixed(0)}
                          %
                        </Text>
                        <Text
                          variant="caption"
                          color="secondary"
                          style={{ display: 'block', marginBottom: 8 }}
                        >
                          Minimum similarity threshold for retrieved documents
                        </Text>
                        <Slider
                          value={settings.retrieval_min_similarity}
                          onChange={(val) =>
                            setSettings((prev) => ({
                              ...prev,
                              retrieval_min_similarity: val,
                            }))
                          }
                          onCommit={(val) =>
                            saveSetting('retrieval_min_similarity', val)
                          }
                          min={0}
                          max={1}
                          step={0.05}
                        />
                      </div>
                    </Surface>
                  </>
                )}

                {/* Long Context Mode Settings */}
                {settings.rag_mode === 'long_context' && (
                  <Surface
                    elevation={0}
                    style={{
                      padding: 24,
                      borderRadius: 16,
                      border: `1px solid ${colors.border.default}`,
                    }}
                  >
                    <Text
                      variant="h6"
                      fontWeight="700"
                      style={{ marginBottom: 16 }}
                    >
                      Context Window Settings
                    </Text>
                    <Text
                      variant="bodySmall"
                      color="secondary"
                      style={{ marginBottom: 24 }}
                    >
                      Control how much of the model&apos;s context window is
                      used for document content. Documents exceeding this limit
                      will use chunked retrieval instead.
                    </Text>

                    <div style={{ marginTop: 24 }}>
                      <Text variant="bodySmall" style={{ marginBottom: 4 }}>
                        Context Usage Ratio:{' '}
                        {(settings.long_context_safety_ratio * 100).toFixed(0)}%
                      </Text>
                      <Text
                        variant="caption"
                        color="secondary"
                        style={{ display: 'block', marginBottom: 8 }}
                      >
                        Higher values allow more document content but leave less
                        space for responses.
                      </Text>
                      <Slider
                        value={settings.long_context_safety_ratio}
                        onChange={(val) =>
                          setSettings((prev) => ({
                            ...prev,
                            long_context_safety_ratio: val,
                          }))
                        }
                        onCommit={(val) =>
                          saveSetting('long_context_safety_ratio', val)
                        }
                        min={0.3}
                        max={0.9}
                        step={0.05}
                      />
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          marginTop: 8,
                        }}
                      >
                        <Text variant="caption" color="secondary">
                          Conservative (more response space)
                        </Text>
                        <Text variant="caption" color="secondary">
                          Aggressive (more document content)
                        </Text>
                      </div>
                    </div>

                    {/* Fast Upload Mode Switch */}
                    <div
                      style={{
                        marginTop: 32,
                        paddingTop: 24,
                        borderTop: `1px solid ${colors.border.default}`,
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'flex-start',
                        }}
                      >
                        <div>
                          <Text fontWeight="600">Fast Upload Mode</Text>
                          <Text
                            variant="caption"
                            color="secondary"
                            style={{ display: 'block', marginTop: 4 }}
                          >
                            Skip summary generation and embeddings to speed up
                            document processing. Documents will be ready for
                            querying immediately after upload.
                          </Text>
                        </div>
                        <Switch
                          checked={settings.fast_upload_mode}
                          onChange={(checked) => {
                            setSettings((prev) => ({
                              ...prev,
                              fast_upload_mode: checked,
                            }));
                            saveSetting('fast_upload_mode', checked);
                          }}
                        />
                      </div>
                    </div>
                  </Surface>
                )}
              </div>
            )}

            {/* Advanced Section */}
            {activeTab === 'advanced' && (
              <div
                style={{ display: 'flex', flexDirection: 'column', gap: 24 }}
              >
                <Surface
                  elevation={0}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    border: `1px solid ${colors.border.default}`,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      marginBottom: 24,
                    }}
                  >
                    <div
                      style={{
                        padding: 8,
                        borderRadius: 8,
                        backgroundColor: colors.neutral[100],
                        color: colors.neutral[700],
                      }}
                    >
                      <TuneIcon size={24} />
                    </div>
                    <div>
                      <Text variant="h6" fontWeight="700">
                        Advanced Settings
                      </Text>
                      <Text variant="bodySmall" color="secondary">
                        Fine-tune your experience
                      </Text>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 16,
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <Text fontWeight="600">Intent Classification</Text>
                        <Text variant="caption" color="secondary">
                          Smartly determine if query needs RAG or not
                        </Text>
                      </div>
                      <Switch
                        checked={settings.intent_classification_enabled}
                        onChange={(checked) => {
                          setSettings((prev) => ({
                            ...prev,
                            intent_classification_enabled: checked,
                          }));
                          saveSetting('intent_classification_enabled', checked);
                        }}
                      />
                    </div>
                  </div>
                </Surface>

                <Surface
                  elevation={0}
                  style={{
                    padding: 24,
                    borderRadius: 16,
                    border: `1px solid ${colors.border.default}`,
                  }}
                >
                  <Text
                    variant="h6"
                    fontWeight="700"
                    style={{ marginBottom: 16 }}
                  >
                    Citation Format
                  </Text>
                  <div style={{ width: '100%' }}>
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns:
                          'repeat(auto-fit, minmax(280px, 1fr))',
                        gap: 16,
                      }}
                    >
                      {getOptions('citation_format').map((opt) => (
                        <StrategyCard
                          key={opt.value}
                          option={opt}
                          selected={settings.citation_format === opt.value}
                          onClick={() =>
                            handleSelection('citation_format', opt.value)
                          }
                        />
                      ))}
                    </div>
                  </div>
                </Surface>
              </div>
            )}

            {/* Profile Section */}
            {activeTab === 'profile' && (
              <Surface
                elevation={0}
                style={{
                  padding: 24,
                  borderRadius: 16,
                  border: `1px solid ${colors.border.default}`,
                }}
              >
                <Text
                  variant="h6"
                  fontWeight="700"
                  style={{ marginBottom: 24 }}
                >
                  Personal Information
                </Text>
                <div
                  style={{ display: 'flex', flexDirection: 'column', gap: 24 }}
                >
                  <TextField
                    label="Display Name"
                    defaultValue={getUserDisplayInfo(user).name}
                    fullWidth
                  />
                  <TextField
                    label="Email Address"
                    defaultValue={getUserDisplayInfo(user).email}
                    disabled
                    fullWidth
                  />
                  <div>
                    <Button style={{ backgroundColor: '#000', color: '#fff' }}>
                      Save Changes
                    </Button>
                  </div>
                </div>
              </Surface>
            )}

            {activeTab === 'appearance' && (
              <Surface
                elevation={0}
                style={{
                  padding: 32,
                  borderRadius: 16,
                  border: `1px dashed ${colors.border.default}`,
                  textAlign: 'center',
                }}
              >
                <Text color="secondary">Appearance settings coming soon.</Text>
              </Surface>
            )}
          </div>
        </div>
      </div>

      <NotificationToast
        open={snackbar.open}
        message={snackbar.message}
        severity={snackbar.severity}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
      />
    </GlobalLayout>
  );
}
