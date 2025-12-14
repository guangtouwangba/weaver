'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Stack,
} from '@mui/material';
import {
  healthApi,
  projectsApi,
  documentsApi,
  chatApi,
  canvasApi,
  Project,
  ProjectDocument,
} from '@/lib/api';

export default function ApiTestPage() {
  const [health, setHealth] = useState<string>('');
  const [loading, setLoading] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  // Projects
  const [projects, setProjects] = useState<Project[]>([]);
  const [newProjectName, setNewProjectName] = useState('');
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Documents
  const [documents, setDocuments] = useState<ProjectDocument[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<ProjectDocument | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string>('');

  // Chat
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState('');

  // Canvas
  const [canvasData, setCanvasData] = useState<string>('');

  // Health Check
  const checkHealth = async () => {
    setLoading('health');
    setError('');
    try {
      const result = await healthApi.check();
      setHealth(JSON.stringify(result, null, 2));
      setSuccess('Health check passed!');
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // Load Projects
  const loadProjects = async () => {
    setLoading('projects');
    setError('');
    try {
      const result = await projectsApi.list();
      setProjects(result.items);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // Create Project
  const createProject = async () => {
    if (!newProjectName) return;
    setLoading('createProject');
    setError('');
    try {
      const project = await projectsApi.create(newProjectName);
      setSuccess(`Project "${project.name}" created!`);
      setNewProjectName('');
      loadProjects();
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // Delete Project
  const deleteProject = async (id: string) => {
    setLoading('deleteProject');
    setError('');
    try {
      await projectsApi.delete(id);
      setSuccess('Project deleted!');
      if (selectedProject?.id === id) {
        setSelectedProject(null);
        setDocuments([]);
      }
      loadProjects();
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // Load Documents
  const loadDocuments = async (projectId: string) => {
    setLoading('documents');
    setError('');
    try {
      const result = await documentsApi.list(projectId);
      setDocuments(result.items);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // Upload Document
  const uploadDocument = async () => {
    if (!selectedProject || !selectedFile) return;
    setLoading('upload');
    setError('');
    try {
      const doc = await documentsApi.upload(selectedProject.id, selectedFile);
      setSuccess(`Document "${doc.filename}" uploaded! Status: ${doc.status}`);
      setSelectedFile(null);
      loadDocuments(selectedProject.id);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // View PDF
  const viewPdf = (doc: ProjectDocument) => {
    setSelectedDocument(doc);
    setPdfUrl(documentsApi.getFileUrl(doc.id));
  };

  // Send Chat
  const sendChat = async () => {
    if (!selectedProject || !chatMessage) return;
    setLoading('chat');
    setError('');
    setChatResponse('');
    try {
      const result = await chatApi.send(selectedProject.id, { message: chatMessage });
      setChatResponse(result.answer);
      setSuccess('Chat response received!');
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // Load Canvas
  const loadCanvas = async () => {
    if (!selectedProject) return;
    setLoading('canvas');
    setError('');
    try {
      const result = await canvasApi.get(selectedProject.id);
      setCanvasData(JSON.stringify(result, null, 2));
    } catch (e: any) {
      setError(e.message);
    }
    setLoading('');
  };

  // Select Project
  const selectProject = (project: Project) => {
    setSelectedProject(project);
    loadDocuments(project.id);
    setCanvasData('');
    setChatResponse('');
  };

  useEffect(() => {
    checkHealth();
    loadProjects();
  }, []);

  return (
    <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        API Integration Test
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Health Check */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            1. Health Check
          </Typography>
          <Button
            variant="contained"
            onClick={checkHealth}
            disabled={loading === 'health'}
          >
            {loading === 'health' ? <CircularProgress size={20} /> : 'Check Health'}
          </Button>
          {health && (
            <Box
              component="pre"
              sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1, overflow: 'auto' }}
            >
              {health}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Projects */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            2. Projects
          </Typography>

          <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
            <TextField
              size="small"
              placeholder="Project name"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
            />
            <Button
              variant="contained"
              onClick={createProject}
              disabled={loading === 'createProject' || !newProjectName}
            >
              Create Project
            </Button>
            <Button variant="outlined" onClick={loadProjects}>
              Refresh
            </Button>
          </Stack>

          <List dense>
            {projects.map((project) => (
              <ListItem
                key={project.id}
                secondaryAction={
                  <Button
                    size="small"
                    color="error"
                    onClick={() => deleteProject(project.id)}
                  >
                    Delete
                  </Button>
                }
                sx={{
                  bgcolor: selectedProject?.id === project.id ? 'action.selected' : 'transparent',
                  cursor: 'pointer',
                }}
                onClick={() => selectProject(project)}
              >
                <ListItemText
                  primary={project.name}
                  secondary={`ID: ${project.id.slice(0, 8)}...`}
                />
              </ListItem>
            ))}
            {projects.length === 0 && (
              <Typography color="text.secondary">No projects yet</Typography>
            )}
          </List>
        </CardContent>
      </Card>

      {/* Documents */}
      {selectedProject && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              3. Documents (Project: {selectedProject.name})
            </Typography>

            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <Button
                variant="contained"
                onClick={uploadDocument}
                disabled={loading === 'upload' || !selectedFile}
              >
                {loading === 'upload' ? <CircularProgress size={20} /> : 'Upload PDF'}
              </Button>
            </Stack>

            <List dense>
              {documents.map((doc) => (
                <ListItem
                  key={doc.id}
                  secondaryAction={
                    <Stack direction="row" spacing={1}>
                      <Chip
                        label={doc.status}
                        color={doc.status === 'ready' ? 'success' : 'default'}
                        size="small"
                      />
                      {doc.status === 'ready' && (
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => viewPdf(doc)}
                        >
                          View PDF
                        </Button>
                      )}
                    </Stack>
                  }
                >
                  <ListItemText
                    primary={doc.filename}
                    secondary={`Pages: ${doc.page_count} | ID: ${doc.id.slice(0, 8)}...`}
                  />
                </ListItem>
              ))}
              {documents.length === 0 && (
                <Typography color="text.secondary">No documents yet</Typography>
              )}
            </List>

            {/* PDF Viewer */}
            {selectedDocument && pdfUrl && (
              <Box sx={{ mt: 3 }}>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  PDF Preview: {selectedDocument.filename}
                </Typography>
                <Box
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    overflow: 'hidden',
                    height: 600,
                  }}
                >
                  <iframe
                    src={pdfUrl}
                    width="100%"
                    height="100%"
                    style={{ border: 'none' }}
                    title="PDF Preview"
                  />
                </Box>
                <Button
                  sx={{ mt: 1 }}
                  onClick={() => {
                    setSelectedDocument(null);
                    setPdfUrl('');
                  }}
                >
                  Close Preview
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Chat */}
      {selectedProject && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              4. RAG Chat (Project: {selectedProject.name})
            </Typography>

            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <TextField
                fullWidth
                size="small"
                placeholder="Ask a question about your documents..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
              />
              <Button
                variant="contained"
                onClick={sendChat}
                disabled={loading === 'chat' || !chatMessage}
              >
                {loading === 'chat' ? <CircularProgress size={20} /> : 'Send'}
              </Button>
            </Stack>

            {chatResponse && (
              <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" color="primary">
                  AI Response:
                </Typography>
                <Typography>{chatResponse}</Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Canvas */}
      {selectedProject && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              5. Canvas (Project: {selectedProject.name})
            </Typography>

            <Button variant="outlined" onClick={loadCanvas} sx={{ mb: 2 }}>
              Load Canvas Data
            </Button>

            {canvasData && (
              <Box
                component="pre"
                sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1, overflow: 'auto', maxHeight: 300 }}
              >
                {canvasData}
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

