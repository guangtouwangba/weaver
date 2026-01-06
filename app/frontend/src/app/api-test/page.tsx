'use client';

import React, { useState, useEffect } from 'react';
import {
  Stack,
  Text,
  Button,
  Surface,
  Spinner,
  Chip
} from '@/components/ui/primitives';
import { Card, TextField } from '@/components/ui/composites';
import { colors } from '@/components/ui/tokens';
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
    <div style={{ padding: 32, maxWidth: 1200, margin: '0 auto' }}>
      <Text variant="h4" gutterBottom>
        API Integration Test
      </Text>

      {error && (
        <Surface sx={{ mb: 2, p: 2, bgcolor: '#FEE2E2', color: '#B91C1C' }}>
          <Stack direction="row" align="center" justify="between">
             <Text>{error}</Text>
             <Button size="sm" variant="ghost" onClick={() => setError('')}>Close</Button>
          </Stack>
        </Surface>
      )}
      {success && (
        <Surface sx={{ mb: 2, p: 2, bgcolor: '#DCFCE7', color: '#15803D' }}>
           <Stack direction="row" align="center" justify="between">
             <Text>{success}</Text>
             <Button size="sm" variant="ghost" onClick={() => setSuccess('')}>Close</Button>
          </Stack>
        </Surface>
      )}

      {/* Health Check */}
      <Card sx={{ mb: 3 }}>
        <Stack gap={2}>
          <Text variant="h6">
            1. Health Check
          </Text>
          <Button
            variant="primary"
            onClick={checkHealth}
            disabled={loading === 'health'}
            sx={{ alignSelf: 'flex-start' }}
          >
            {loading === 'health' ? <Spinner size="sm" /> : 'Check Health'}
          </Button>
          {health && (
            <div
              style={{ marginTop: 16, padding: 16, backgroundColor: colors.neutral[100], borderRadius: 4, overflow: 'auto', fontFamily: 'monospace' }}
            >
              {health}
            </div>
          )}
        </Stack>
      </Card>

      {/* Projects */}
      <Card sx={{ mb: 3 }}>
        <Stack gap={2}>
          <Text variant="h6">
            2. Projects
          </Text>

          <Stack direction="row" gap={2} sx={{ mb: 2 }}>
            <TextField
              size="sm"
              placeholder="Project name"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
            />
            <Button
              variant="primary"
              onClick={createProject}
              disabled={loading === 'createProject' || !newProjectName}
            >
              Create Project
            </Button>
            <Button variant="outline" onClick={loadProjects}>
              Refresh
            </Button>
          </Stack>

          <Stack gap={1}>
            {projects.map((project) => (
              <Surface
                key={project.id}
                elevation={0}
                sx={{
                  p: 1,
                  bgcolor: selectedProject?.id === project.id ? 'action.selected' : 'transparent',
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover' }
                }}
                onClick={() => selectProject(project)}
              >
                <Stack direction="row" justify="between" align="center">
                    <Stack>
                        <Text>{project.name}</Text>
                        <Text variant="caption" color="secondary">ID: {project.id.slice(0, 8)}...</Text>
                    </Stack>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={(e) => {
                        e.stopPropagation();
                        deleteProject(project.id);
                    }}
                  >
                    Delete
                  </Button>
                </Stack>
              </Surface>
            ))}
            {projects.length === 0 && (
              <Text color="secondary">No projects yet</Text>
            )}
          </Stack>
        </Stack>
      </Card>

      {/* Documents */}
      {selectedProject && (
        <Card sx={{ mb: 3 }}>
          <Stack gap={2}>
            <Text variant="h6">
              3. Documents (Project: {selectedProject.name})
            </Text>

            <Stack direction="row" gap={2} sx={{ mb: 2 }}>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <Button
                variant="primary"
                onClick={uploadDocument}
                disabled={loading === 'upload' || !selectedFile}
              >
                {loading === 'upload' ? <Spinner size="sm" /> : 'Upload PDF'}
              </Button>
            </Stack>

            <Stack gap={1}>
              {documents.map((doc) => (
                <Surface
                  key={doc.id}
                   elevation={0}
                   sx={{ p: 1 }}
                >
                    <Stack direction="row" justify="between" align="center">
                        <Stack>
                            <Text>{doc.filename}</Text>
                            <Text variant="caption" color="secondary">Pages: {doc.page_count} | ID: {doc.id.slice(0, 8)}...</Text>
                        </Stack>
                        <Stack direction="row" gap={1}>
                        <Chip
                            label={doc.status}
                            color={doc.status === 'ready' ? 'success' : 'default'}
                            size="sm"
                        />
                        {doc.status === 'ready' && (
                            <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewPdf(doc)}
                            >
                            View PDF
                            </Button>
                        )}
                        </Stack>
                    </Stack>
                </Surface>
              ))}
              {documents.length === 0 && (
                <Text color="secondary">No documents yet</Text>
              )}
            </Stack>

            {/* PDF Viewer */}
            {selectedDocument && pdfUrl && (
              <div style={{ marginTop: 24 }}>
                <div style={{ borderBottom: `1px solid ${colors.border.default}`, marginBottom: 16 }} />
                <Text variant="h6" gutterBottom>
                  PDF Preview: {selectedDocument.filename}
                </Text>
                <div
                  style={{
                    border: `1px solid ${colors.border.default}`,
                    borderRadius: 4,
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
                </div>
                <Button
                  sx={{ mt: 1 }}
                  onClick={() => {
                    setSelectedDocument(null);
                    setPdfUrl('');
                  }}
                >
                  Close Preview
                </Button>
              </div>
            )}
          </Stack>
        </Card>
      )}

      {/* Chat */}
      {selectedProject && (
        <Card sx={{ mb: 3 }}>
          <Stack gap={2}>
            <Text variant="h6">
              4. RAG Chat (Project: {selectedProject.name})
            </Text>

            <Stack direction="row" gap={2} sx={{ mb: 2 }}>
              <TextField
                fullWidth
                size="sm"
                placeholder="Ask a question about your documents..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
              />
              <Button
                variant="primary"
                onClick={sendChat}
                disabled={loading === 'chat' || !chatMessage}
              >
                {loading === 'chat' ? <Spinner size="sm" /> : 'Send'}
              </Button>
            </Stack>

            {chatResponse && (
              <div style={{ padding: 16, backgroundColor: colors.neutral[50], borderRadius: 4 }}>
                <Text variant="h6" color="primary">
                  AI Response:
                </Text>
                <Text>{chatResponse}</Text>
              </div>
            )}
          </Stack>
        </Card>
      )}

      {/* Canvas */}
      {selectedProject && (
        <Card sx={{ mb: 3 }}>
          <Stack gap={2}>
            <Text variant="h6">
              5. Canvas (Project: {selectedProject.name})
            </Text>

            <Button variant="outline" onClick={loadCanvas} sx={{ alignSelf: 'flex-start', mb: 2 }}>
              Load Canvas Data
            </Button>

            {canvasData && (
              <div
                style={{ padding: 16, backgroundColor: colors.neutral[100], borderRadius: 4, overflow: 'auto', maxHeight: 300, fontFamily: 'monospace' }}
              >
                {canvasData}
              </div>
            )}
          </Stack>
        </Card>
      )}
    </div>
  );
}
