'use client';

import { useState } from 'react';
import GlobalLayout from '@/components/layout/GlobalLayout';
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
  Switch,
  FormControlLabel,
  Chip,
  InputAdornment,
  IconButton
} from '@mui/material';
import { 
  User, 
  Cpu, 
  Database, 
  Shield, 
  Palette, 
  LogOut,
  Eye,
  EyeOff,
  Key,
  Sparkles
} from 'lucide-react';

// Mock user data
const MOCK_USER = {
  name: "Alex Li",
  email: "alex@weaver.ai",
  avatar: "AL"
};

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('ai'); // Default to AI settings to emphasize product positioning
  const [showKey, setShowKey] = useState(false);

  const menuItems = [
    { id: 'profile', label: 'Profile & Account', icon: <User size={20} /> },
    { id: 'ai', label: 'AI & Models', icon: <Cpu size={20} /> },
    { id: 'knowledge', label: 'Knowledge Base', icon: <Database size={20} /> },
    { id: 'appearance', label: 'Appearance', icon: <Palette size={20} /> },
  ];

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
                      '& .lucide': { color: 'primary.main' }
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
                  <LogOut size={20} />
                </ListItemIcon>
                <ListItemText primary="Sign Out" primaryTypographyProps={{ fontWeight: 500 }} />
              </ListItemButton>
            </Box>
          </Paper>

          {/* RIGHT CONTENT: Configuration Panels */}
          <Box sx={{ flex: 1 }}>
            
            {/* AI & Models Section (The "Brain" of Weaver) */}
            {activeTab === 'ai' && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Box sx={{ p: 1, borderRadius: 2, bgcolor: 'primary.50', color: 'primary.main' }}>
                      <Key size={24} />
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="700">LLM Provider</Typography>
                      <Typography variant="body2" color="text.secondary">Configure the brain behind your research agent</Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                    <TextField
                      label="API Key (OpenRouter / OpenAI)"
                      type={showKey ? 'text' : 'password'}
                      fullWidth
                      defaultValue="sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton onClick={() => setShowKey(!showKey)} edge="end">
                              {showKey ? <EyeOff size={20} /> : <Eye size={20} />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                      helperText="Your key is stored locally and never shared."
                    />
                    
                    <TextField
                      label="Base URL (Optional)"
                      placeholder="https://openrouter.ai/api/v1"
                      fullWidth
                    />
                  </Box>
                </Paper>

                <Paper elevation={0} sx={{ p: 3, borderRadius: 4, border: '1px solid', borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Box sx={{ p: 1, borderRadius: 2, bgcolor: 'secondary.50', color: 'secondary.main' }}>
                      <Sparkles size={24} />
                    </Box>
                    <Box>
                      <Typography variant="h6" fontWeight="700">Model Strategy</Typography>
                      <Typography variant="body2" color="text.secondary">Define how Weaver processes your documents</Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <Box>
                      <Typography variant="subtitle2" fontWeight="600" gutterBottom>Reasoning Model (Slow & Deep)</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        Used for complex analysis, report generation, and connecting dots.
                      </Typography>
                      <TextField select SelectProps={{ native: true }} fullWidth defaultValue="openai/gpt-4o">
                        <option value="openai/gpt-4o">GPT-4o (Recommended)</option>
                        <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                        <option value="openai/o1-preview">o1-preview (Advanced)</option>
                      </TextField>
                    </Box>

                    <Box>
                      <Typography variant="subtitle2" fontWeight="600" gutterBottom>Chat Model (Fast)</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                        Used for quick Q&A and UI interactions.
                      </Typography>
                      <TextField select SelectProps={{ native: true }} fullWidth defaultValue="openai/gpt-4o-mini">
                        <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                        <option value="meta-llama/llama-3-70b">Llama 3 70B</option>
                      </TextField>
                    </Box>
                  </Box>
                </Paper>
              </Box>
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

            {/* Placeholder for other tabs */}
            {['knowledge', 'appearance'].includes(activeTab) && (
              <Paper elevation={0} sx={{ p: 4, borderRadius: 4, border: '1px dashed', borderColor: 'divider', textAlign: 'center' }}>
                <Typography color="text.secondary">This section is under construction.</Typography>
              </Paper>
            )}

          </Box>
        </Box>
      </Box>
    </GlobalLayout>
  );
}
