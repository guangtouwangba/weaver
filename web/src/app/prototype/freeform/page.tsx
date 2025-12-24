'use client';

import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, IconButton, Divider } from '@mui/material';
import { X, Info, MessageCircle, Share2, Highlighter, ChevronLeft } from 'lucide-react';
import GlobalSidebar from '@/components/layout/GlobalSidebar';
import Canvas from '@/components/prototype/freeform/Canvas';
import Sidebar from '@/components/prototype/freeform/Sidebar';
import ChatInput from '@/components/prototype/freeform/ChatInput';
import MediaPreview from '@/components/prototype/freeform/MediaPreview';
import ReviewModal from '@/components/prototype/freeform/ReviewModal';
import CanvasToolbar from '@/components/prototype/freeform/CanvasToolbar';
import ProjectHeader, { Project } from '@/components/prototype/freeform/ProjectHeader';
import FlashCardView from '@/components/prototype/freeform/FlashCardView';
import PodcastView from '@/components/prototype/freeform/PodcastView';
import PPTSynthesisView from '@/components/prototype/freeform/PPTSynthesisView';
import NodeChat from '@/components/prototype/freeform/NodeChat';

const GLOBAL_SIDEBAR_WIDTH = 72;

export interface Node {
    id: string;
    type: 'file' | 'action' | 'insight' | 'entity' | 'note' | 'chat' | 'synthesis' | 'topic' | 'mindmap' | 'podcast' | 'data' | 'brief' | 'flashcard';
    name: string;
    x: number;
    y: number;
    icon?: string;
    content?: string;
    parentId?: string;
    parentIds?: string[];
    category?: string;
    color?: string;
    messages?: { role: 'user' | 'assistant'; content: string }[];
    isThinking?: boolean;
    outputType?: 'podcast' | 'ppt' | 'mindmap' | 'flashcards' | 'quiz' | 'briefing';
    status?: 'analyzing' | 'ready';
    // New card-specific properties
    cardType?: 'topic' | 'mindmap' | 'podcast' | 'data' | 'brief' | 'flashcard';
    subtitle?: string;        // e.g., "High growth sector"
    accentColor?: string;     // Card accent color
    duration?: string;        // For podcasts
    pageCount?: number;       // For briefs
    cardCount?: number;       // For flashcards
    metric?: string;          // For data cards
    isOnCanvas?: boolean;     // For sidebar eye indicator
    iconType?: 'trending' | 'target' | 'zap' | 'lightbulb';
    term?: string;            // For flashcards
    definition?: string;      // For flashcards
}

export interface Edge {
    id: string;
    source: string;
    target: string;
    label?: string;
}

const MOCK_PROJECTS: Project[] = [
    { id: 'p1', name: 'Q1 Research', color: '#3B82F6', description: 'Quarterly market research and analysis' },
    { id: 'p2', name: 'Product Roadmap', color: '#8B5CF6', description: 'Next generation product planning' },
    { id: 'p3', name: 'Dream of Red Mansions', color: '#EF4444', description: 'Analyzing classic Chinese literature' }
];

const PROJECT_FILES: Record<string, any[]> = {
    'p1': [
        { id: 'f1', name: 'Market_Trends_2024.pdf', size: '2.4 MB', type: 'pdf' },
        { id: 'f2', name: 'Competitor_Analysis.docx', size: '45 KB', type: 'docx' },
    ],
    'p2': [
        { id: 'f3', name: 'Product_Demo_v2.mp4', size: '15.6 MB', type: 'mp4' },
        { id: 'f4', name: 'Design_Review.mp3', size: '4.2 MB', type: 'mp3' },
    ],
    'p3': [
        { id: 'f5', name: 'Dream_of_Red_Mansions_Complete.pdf', size: '12.1 MB', type: 'pdf' },
        { id: 'f6', name: 'Character_Summary.docx', size: '18 KB', type: 'docx' },
    ]
};

// Demo nodes showcasing the new card types
const DEMO_NODES: Node[] = [
    // Topic Cards
    { 
        id: 'demo-topic-1', 
        type: 'topic', 
        name: 'AI Trends', 
        subtitle: 'High growth sector',
        x: 200, 
        y: 150,
        accentColor: '#F97316',
        iconType: 'trending'
    },
    { 
        id: 'demo-topic-2', 
        type: 'topic', 
        name: 'Competitor Moves', 
        subtitle: 'Pricing strategy shift',
        x: 550, 
        y: 150,
        accentColor: '#EF4444',
        iconType: 'target'
    },
    // Mind Map Card
    {
        id: 'demo-mindmap-1',
        type: 'mindmap',
        name: 'Q1 Market Overview',
        x: 380,
        y: 320
    },
    // Podcast Card
    {
        id: 'demo-podcast-1',
        type: 'podcast',
        name: 'Key Insights Q1',
        duration: '14:20',
        x: 620,
        y: 350,
        accentColor: '#8B5CF6'
    },
    // Data Card
    {
        id: 'demo-data-1',
        type: 'data',
        name: 'Revenue Data',
        metric: '+15% YoY Growth',
        x: 450,
        y: 480,
        accentColor: '#10B981'
    },
    // Brief Card
    {
        id: 'demo-brief-1',
        type: 'brief',
        name: 'Executive Brief',
        x: 120,
        y: 380,
        accentColor: '#3B82F6'
    },
    // Flashcard
    {
        id: 'demo-flashcard-1',
        type: 'flashcard',
        name: 'Market Terms',
        term: 'Enterprise AI Adoption',
        definition: 'The implementation of artificial intelligence technologies within large organizations to improve operations and decision-making.',
        cardCount: 24,
        x: 380,
        y: 600,
        accentColor: '#F97316'
    }
];

// Demo edges connecting the nodes
const DEMO_EDGES: Edge[] = [
    { id: 'e1', source: 'demo-topic-1', target: 'demo-mindmap-1' },
    { id: 'e2', source: 'demo-topic-2', target: 'demo-mindmap-1' },
    { id: 'e3', source: 'demo-mindmap-1', target: 'demo-podcast-1' },
    { id: 'e4', source: 'demo-mindmap-1', target: 'demo-data-1' },
    { id: 'e5', source: 'demo-data-1', target: 'demo-flashcard-1' },
];

export default function FreeformPrototype() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [currentProject, setCurrentProject] = useState<Project>(MOCK_PROJECTS[0]);
    const [availableFiles, setAvailableFiles] = useState<any[]>(PROJECT_FILES[MOCK_PROJECTS[0].id] || []);
    const [nodes, setNodes] = useState<Node[]>(DEMO_NODES);
    const [edges, setEdges] = useState<Edge[]>(DEMO_EDGES);
    const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([]);
    const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
    const [isConnectionMode, setIsConnectionMode] = useState(false);
    const [isPreviewMode, setIsPreviewMode] = useState(false);
    const [reviewingFile, setReviewingFile] = useState<{ id: string; name: string; type: string } | null>(null);
    const [mappingPromptNodeId, setMappingPromptNodeId] = useState<string | null>(null);
    const [canvasView, setCanvasView] = useState({ x: 0, y: 0, k: 1 });
    const [isChatMode, setIsChatMode] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    const [interactionMode, setInteractionMode] = useState<'select' | 'hand'>('select');

    useEffect(() => {
        setFocusedNodeId(null);
    }, [interactionMode]);

    const screenToCanvas = (clientX: number, clientY: number) => {
        const rect = { left: GLOBAL_SIDEBAR_WIDTH, top: 56 };
        return {
            x: (clientX - rect.left - canvasView.x) / canvasView.k,
            y: (clientY - rect.top - canvasView.y) / canvasView.k
        };
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const coords = screenToCanvas(e.clientX, e.clientY);
        try {
            const dataString = e.dataTransfer.getData('application/json');
            if (!dataString) return;
            const fileData = JSON.parse(dataString);
            handleAddNode(fileData, coords.x, coords.y);
        } catch (err) {
            console.error('Failed to parse dropped data', err);
        }
    };

    const handleProjectChange = (project: Project) => {
        setCurrentProject(project);
        setAvailableFiles(PROJECT_FILES[project.id] || []);
        // Reset canvas for now to simulate separate project spaces
        setNodes([]);
        setEdges([]);
        setSelectedNodeIds([]);
        setFocusedNodeId(null);
        setIsPreviewMode(false);
        setIsChatMode(false);
        setCanvasView({ x: 0, y: 0, k: 1 });
    };

    const handleAddNode = (file: { id?: string; name: string; type: string; content?: string }, x: number, y: number) => {
        const id = Math.random().toString(36).substr(2, 9);

        // Handle Note Node
        if (file.type === 'note') {
            const newNode: Node = {
                id,
                type: 'note',
                name: file.name || 'New Note',
                content: file.content || '',
                x,
                y,
            };
            setNodes(prev => [...prev, newNode]);
            return;
        }

        // Handle Insight Node from PDF Highlight
        if (file.type === 'insight') {
            const newNode: Node = {
                id,
                type: 'insight',
                name: 'Key Finding',
                content: file.content,
                x,
                y,
                parentId: file.id // Reference to original file if available
            };
            setNodes(prev => [...prev, newNode]);

            if (file.id) {
                const newEdge: Edge = {
                    id: `edge-${file.id}-${id}-${Date.now()}`,
                    source: file.id,
                    target: id
                };
                setEdges(prev => [...prev, newEdge]);
            }
            return;
        }

        const newNode: Node = {
            id,
            type: 'file',
            name: file.name,
            x,
            y,
            icon: file.type || (file.name.toLowerCase().includes('slack') ? 'slack' :
                file.name.toLowerCase().includes('spotify') ? 'spotify' : 'file')
        };
        setNodes(prev => [...prev, newNode]);
    };

    const handleConnectNodes = (sourceId: string, targetId: string) => {
        // Prevent duplicate edges
        if (edges.some(e => (e.source === sourceId && e.target === targetId) || (e.source === targetId && e.target === sourceId))) {
            return;
        }
        const newEdge: Edge = {
            id: `edge-${sourceId}-${targetId}-${Date.now()}`,
            source: sourceId,
            target: targetId
        };
        setEdges(prev => [...prev, newEdge]);
    };

    const handleChatSubmit = (value: string) => {
        const selectedChatNode = selectedNodeIds.length === 1
            ? nodes.find(n => n.id === selectedNodeIds[0] && n.type === 'chat')
            : null;

        if (selectedChatNode) {
            // Append to existing chat
            setNodes(prev => prev.map(n => n.id === selectedChatNode.id ? {
                ...n,
                messages: [...(n.messages || []), { role: 'user', content: value }],
                isThinking: true
            } : n));

            // Simulate follow-up response
            setTimeout(() => {
                setNodes(prev => prev.map(n => n.id === selectedChatNode.id ? {
                    ...n,
                    isThinking: false,
                    messages: [
                        ...(n.messages || []),
                        { role: 'assistant', content: "That's an interesting follow-up. Based on the documents, this relates to the 'multi-head' part of the mechanism which allows for localized focus across different projection subspaces." }
                    ]
                } : n));
            }, 2000);
            return;
        }

        const id = `chat-${Date.now()}`;

        // Calculate center position of selected nodes
        let x = 0;
        let y = 0;

        const selectedNodes = nodes.filter(n => selectedNodeIds.includes(n.id));
        if (selectedNodes.length > 0) {
            x = selectedNodes.reduce((acc, n) => acc + n.x, 0) / selectedNodes.length;
            y = selectedNodes.reduce((acc, n) => acc + n.y, 0) / selectedNodes.length + 400;
        } else {
            // Default center if nothing selected (using a large coordinate for the infinite canvas)
            x = 1000;
            y = 1000;
        }

        const newChatNode: Node = {
            id,
            type: 'chat',
            name: 'Research Analysis',
            x,
            y,
            messages: [{ role: 'user', content: value }],
            isThinking: true
        };

        const newEdges: Edge[] = selectedNodeIds.map(sourceId => ({
            id: `edge-${sourceId}-${id}-${Date.now()}`,
            source: sourceId,
            target: id,
            label: 'analyzing'
        }));

        setNodes(prev => [...prev, newChatNode]);
        setEdges(prev => [...prev, ...newEdges]);
        setSelectedNodeIds([id]);

        // Simulate AI Response and Insight Spawning
        setTimeout(() => {
            setNodes(prev => prev.map(n => n.id === id ? {
                ...n,
                isThinking: false,
                messages: [
                    ...(n.messages || []),
                    { role: 'assistant', content: "I've analyzed the connection between these documents. There are several key themes around the transformer's impact on parallel processing and its scalability." }
                ]
            } : n));

            // Spawn some insights in a radial layout
            const insights = [
                "Parallelization enables faster training on large datasets",
                "Self-attention solves vanishing gradient problems",
                "Transformer architecture scales better than RNNs",
                "Positional encoding preserves sequence order without recurrence"
            ];

            const radius = 350;
            const newInsights: Node[] = insights.map((text, i) => {
                const angle = (i / insights.length) * Math.PI + Math.PI / 4; // Semi-circle below
                return {
                    id: `insight-chat-${id}-${i}`,
                    type: 'insight',
                    name: 'Key Finding',
                    content: text,
                    x: x + Math.cos(angle) * radius,
                    y: y + Math.sin(angle) * radius,
                    parentId: id
                };
            });

            const insightEdges: Edge[] = newInsights.map(n => ({
                id: `edge-${id}-${n.id}`,
                source: id,
                target: n.id,
                label: 'found'
            }));

            setNodes(prev => [...prev, ...newInsights]);
            setEdges(prev => [...prev, ...insightEdges]);
        }, 2500);
    };

    const handleUpdateNodePosition = (nodeId: string, x: number, y: number) => {
        setNodes(prev => prev.map(n => n.id === nodeId ? { ...n, x, y } : n));
    };

    const handleCanvasDrop = (e: React.DragEvent) => {
        // This will be called by Canvas or ReviewModal
        // We need to calculate coordinates relative to the canvas
        // page.tsx doesn't have the canvasRef, so we'll pass a coordinate converter or handle it in Canvas.tsx
    };

    const handleClearCanvas = () => {
        if (confirm('Are you sure you want to clear the canvas?')) {
            setNodes([]);
            setEdges([]);
            setSelectedNodeIds([]);
        }
    };

    const handleAIMapping = (parentId: string, prompt: string) => {
        const parentNode = nodes.find(n => n.id === parentId);
        if (!parentNode) return;

        // Simulate AI logic based on prompt
        let newEntities: Partial<Node>[] = [];
        let newRelations: { targetIdx: number; label: string }[] = [];

        if (prompt.includes('红楼梦') || prompt.includes('人物')) {
            newEntities = [
                { name: '贾宝玉', category: 'Person', color: '#EF4444' },
                { name: '林黛玉', category: 'Person', color: '#10B981' },
                { name: '薛宝钗', category: 'Person', color: '#8B5CF6' },
                { name: '王熙凤', category: 'Person', color: '#F59E0B' }
            ];
            newRelations = [
                { targetIdx: 0, label: '主角' },
                { targetIdx: 1, label: '木石前盟' },
                { targetIdx: 2, label: '金玉良缘' }
            ];
        } else if (prompt.includes('技术') || prompt.includes('API') || prompt.includes('架构')) {
            newEntities = [
                { name: 'Auth Service', category: 'Service', color: '#3B82F6' },
                { name: 'Database', category: 'Data', color: '#6B7280' },
                { name: 'API Gateway', category: 'Infrastructure', color: '#EC4899' }
            ];
            newRelations = [
                { targetIdx: 0, label: 'Calls' },
                { targetIdx: 1, label: 'Persists' }
            ];
        } else {
            newEntities = [
                { name: 'Concept A', category: 'Idea', color: '#6366F1' },
                { name: 'Concept B', category: 'Idea', color: '#6366F1' }
            ];
            newRelations = [
                { targetIdx: 0, label: 'Relates' }
            ];
        }

        const spawnedNodes: Node[] = newEntities.map((ent, i) => ({
            id: `entity-${parentId}-${i}-${Date.now()}`,
            type: 'entity',
            name: ent.name!,
            category: ent.category,
            color: ent.color,
            x: parentNode.x + Math.cos(i * (2 * Math.PI / newEntities.length)) * 250,
            y: parentNode.y + Math.sin(i * (2 * Math.PI / newEntities.length)) * 250,
            parentId
        }));

        const spawnedEdges: Edge[] = newRelations.map((rel, i) => ({
            id: `edge-ai-${parentId}-${spawnedNodes[rel.targetIdx].id}`,
            source: parentId,
            target: spawnedNodes[rel.targetIdx].id,
            label: rel.label
        }));

        setNodes(prev => [...prev, ...spawnedNodes]);
        setEdges(prev => [...prev, ...spawnedEdges]);
        setMappingPromptNodeId(null);
    };

    const handleSynthesisAction = (type: string, nodeIds: string[]) => {
        const id = `synthesis-${Date.now()}`;
        const selectedNodes = nodes.filter(n => nodeIds.includes(n.id));

        if (selectedNodes.length === 0) return;

        // Centroid for new synthesis node
        const x = selectedNodes.reduce((acc, n) => acc + n.x, 0) / selectedNodes.length;
        const y = selectedNodes.reduce((acc, n) => acc + n.y, 0) / selectedNodes.length;

        if (type === 'mindmap') {
            // Simulate "Big Bang" - push sources to periphery and spawn central mindmap
            const radius = 600;
            const newNodes: Node[] = [];
            const newEdges: Edge[] = [];

            // Move existing selected nodes to periphery
            setNodes(prev => prev.map(n => {
                if (nodeIds.includes(n.id)) {
                    const idx = nodeIds.indexOf(n.id);
                    const angle = (idx / nodeIds.length) * 2 * Math.PI;
                    return {
                        ...n,
                        x: x + Math.cos(angle) * radius,
                        y: y + Math.sin(angle) * radius
                    };
                }
                return n;
            }));

            // Create central Nexus Node
            const nexusId = id;
            newNodes.push({
                id: nexusId,
                type: 'synthesis',
                name: 'Global Nexus Map',
                outputType: 'mindmap',
                status: 'ready',
                parentIds: nodeIds,
                x,
                y
            });

            // Create some thematic clusters
            const themes = [
                { name: 'Consensus', color: '#10B981' },
                { name: 'Friction Points', color: '#EF4444' },
                { name: 'Future Roadmap', color: '#F59E0B' },
                { name: 'Strategic Gaps', color: '#3B82F6' }
            ];

            themes.forEach((theme, i) => {
                const themeId = `nexus-theme-${i}-${Date.now()}`;
                const angle = (i / themes.length) * 2 * Math.PI;
                newNodes.push({
                    id: themeId,
                    type: 'insight',
                    name: theme.name,
                    content: `Synthesis of ${theme.name.toLowerCase()} found across ${nodeIds.length} sources.`,
                    x: x + Math.cos(angle) * 300,
                    y: y + Math.sin(angle) * 300,
                    parentId: nexusId,
                    color: theme.color
                });
                newEdges.push({
                    id: `edge-nexus-${nexusId}-${themeId}`,
                    source: nexusId,
                    target: themeId,
                    label: 'categorizes'
                });
            });

            // Connect sources to Nexus
            nodeIds.forEach(sourceId => {
                newEdges.push({
                    id: `edge-source-${sourceId}-nexus-${nexusId}`,
                    source: sourceId,
                    target: nexusId
                });
            });

            setNodes(prev => [...prev, ...newNodes]);
            setEdges(prev => [...prev, ...newEdges]);
            setSelectedNodeIds([nexusId]);
            return;
        }

        const newNode: Node = {
            id,
            type: 'synthesis',
            name: `Synthesized ${type === 'podcast' ? 'Podcast' : type === 'ppt' ? 'Presentation' : type === 'briefing' ? 'Briefing Doc' : type.charAt(0).toUpperCase() + type.slice(1)}`,
            outputType: type as any,
            status: 'analyzing',
            parentIds: nodeIds,
            x,
            y
        };

        const newEdges: Edge[] = nodeIds.map(sourceId => ({
            id: `edge-${sourceId}-${id}-${Date.now()}`,
            source: sourceId,
            target: id
        }));

        setNodes(prev => [...prev, newNode]);
        setEdges(prev => [...prev, ...newEdges]);
        setSelectedNodeIds([id]);

        // Simulate analysis completion
        setTimeout(() => {
            setNodes(prev => prev.map(n => n.id === id ? { ...n, status: 'ready' } : n));
        }, 3000);
    };

    const handleAddAction = (parentId: string, actionType: string, x: number, y: number) => {
        const parentNode = nodes.find(n => n.id === parentId);
        if (!parentNode) return;

        if (actionType === 'New Note') {
            const newNode: Node = {
                id: Math.random().toString(36).substr(2, 9),
                type: 'note',
                name: 'Untitled Note',
                content: '',
                x: parentNode.x + 300,
                y: parentNode.y,
                parentId
            };
            const newEdge: Edge = {
                id: `edge-${parentId}-${newNode.id}`,
                source: parentId,
                target: newNode.id,
                label: 'drafts'
            };
            setNodes(prev => [...prev, newNode]);
            setEdges(prev => [...prev, newEdge]);
            return;
        }

        if (actionType === 'Mindmap') {
            // Spawn a cluster of concepts
            const concepts = [
                { name: 'Core Architecture', color: '#3B82F6' },
                { name: 'Data Pipeline', color: '#10B981' },
                { name: 'Optimization', color: '#F59E0B' }
            ];

            const spawnedNodes: Node[] = concepts.map((c, i) => ({
                id: `mindmap-${parentId}-${i}-${Date.now()}`,
                type: 'entity',
                name: c.name,
                x: parentNode.x + (i - 1) * 200,
                y: parentNode.y + 180,
                parentId,
                color: c.color,
                category: 'Concept'
            }));

            const spawnedEdges: Edge[] = spawnedNodes.map(n => ({
                id: `edge-${parentId}-${n.id}`,
                source: parentId,
                target: n.id,
                label: 'relates'
            }));

            setNodes(prev => [...prev, ...spawnedNodes]);
            setEdges(prev => [...prev, ...spawnedEdges]);
            return;
        }

        const newNode: Node = {
            id: Math.random().toString(36).substr(2, 9),
            type: 'action',
            name: actionType,
            x,
            y,
            parentId
        };
        const newEdge: Edge = {
            id: `edge-${parentId}-${newNode.id}`,
            source: parentId,
            target: newNode.id
        };
        setNodes(prev => [...prev, newNode]);
        setEdges(prev => [...prev, newEdge]);
    };

    const handleSmartStart = (fileId: string, actionType: 'summarize' | 'map') => {
        const file = availableFiles.find(f => f.id === fileId);
        if (!file) return;

        // 1. Add File Node in Center
        const fileNodeId = fileId; // Reuse ID for simplicity in prototype, or generate new
        const centerX = 0;
        const centerY = 0;

        const fileNode: Node = {
            id: fileNodeId,
            type: 'file',
            name: file.name,
            x: centerX,
            y: centerY,
            icon: file.type
        };

        const newNodes: Node[] = [fileNode];
        const newEdges: Edge[] = [];

        if (actionType === 'summarize') {
            // 2. Add Summary Insight Node
            const summaryId = `smart-summary-${Date.now()}`;
            newNodes.push({
                id: summaryId,
                type: 'insight',
                name: 'Executive Summary',
                content: `Automated summary of ${file.name}: The document outlines key strategic shifts for Q1 2024, focusing on AI adoption and market consolidation.`,
                x: centerX + 300,
                y: centerY,
                parentId: fileNodeId
            });
            newEdges.push({
                id: `edge-${fileNodeId}-${summaryId}`,
                source: fileNodeId,
                target: summaryId,
                label: 'summarizes'
            });
        } else if (actionType === 'map') {
            // 2. Add Mindmap Structure
            const concepts = [
                { name: 'Key Drivers', color: '#EF4444' },
                { name: 'Opportunities', color: '#10B981' },
                { name: 'Risks', color: '#F59E0B' }
            ];

            concepts.forEach((c, i) => {
                const conceptId = `smart-concept-${i}-${Date.now()}`;
                const angle = (i / concepts.length) * 2 * Math.PI - Math.PI / 2;
                newNodes.push({
                    id: conceptId,
                    type: 'entity',
                    name: c.name,
                    category: 'Dimension',
                    color: c.color,
                    x: centerX + Math.cos(angle) * 250,
                    y: centerY + Math.sin(angle) * 250,
                    parentId: fileNodeId
                });
                newEdges.push({
                    id: `edge-${fileNodeId}-${conceptId}`,
                    source: fileNodeId,
                    target: conceptId,
                    label: 'extracts'
                });
            });
        }

        setNodes(prev => [...prev, ...newNodes]);
        setEdges(prev => [...prev, ...newEdges]);
        
        // Auto-select the main file
        setSelectedNodeIds([fileNodeId]);
        
        // Reset view to center
        setCanvasView({ x: window.innerWidth / 2 - GLOBAL_SIDEBAR_WIDTH, y: window.innerHeight / 2 - 56, k: 1 });
    };

    const focusedNode = nodes.find(n => n.id === focusedNodeId);

    return (
        <Box sx={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
            {/* Global Sidebar */}
            <GlobalSidebar />

            {/* Main Content Area */}
            <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, ml: `${GLOBAL_SIDEBAR_WIDTH}px`, bgcolor: 'background.default' }}>
                {/* Top Navigation Bar */}
                <ProjectHeader
                    projects={MOCK_PROJECTS}
                    currentProject={currentProject}
                    onProjectChange={handleProjectChange}
                />

                <Box sx={{ display: 'flex', flexGrow: 1, pt: '56px', position: 'relative' }}>
                    {/* Background Canvas */}
                    <Canvas
                        nodes={nodes}
                        edges={edges}
                        onAddNode={handleAddNode}
                        onAddAction={handleAddAction}
                        onConnectNodes={handleConnectNodes}
                        onUpdateNodePosition={handleUpdateNodePosition}
                        onAIMapping={handleAIMapping}
                        selectedNodeIds={selectedNodeIds}
                        onSelectNodes={setSelectedNodeIds}
                        focusedNodeId={focusedNodeId}
                        onFocusNode={setFocusedNodeId}
                        isConnectionMode={isConnectionMode}
                        onToggleConnectionMode={setIsConnectionMode}
                        onPreview={() => setIsPreviewMode(true)}
                        onSynthesisAction={handleSynthesisAction}
                        mappingPromptNodeId={mappingPromptNodeId}
                        onSetMappingPrompt={setMappingPromptNodeId}
                        view={canvasView}
                        onViewChange={setCanvasView}
                        projectColor={currentProject.color}
                        projectName={currentProject.name}
                        isExternalDragging={isDragging}
                        mode={interactionMode}
                        availableFiles={availableFiles}
                        onSmartStart={handleSmartStart}
                    />

                    {/* Left Collapsible Sidebar */}
                    <Sidebar
                        onToggle={setSidebarOpen}
                        onReview={(file) => setReviewingFile(file)}
                        projectColor={currentProject.color}
                        projectId={currentProject.id}
                        onDragStateChange={setIsDragging}
                        files={availableFiles}
                        onFilesChange={setAvailableFiles}
                    />

                    {/* Immersive Review Modal */}
                    <ReviewModal
                        file={reviewingFile}
                        onClose={() => setReviewingFile(null)}
                        isDragging={isDragging}
                        onDragStateChange={setIsDragging}
                        onDrop={handleDrop}
                    />

                    {/* Right Collapsible Detail Panel */}
                    <Box
                        sx={{
                            position: 'fixed',
                            right: 0,
                            top: 56,
                            height: 'calc(100vh - 56px)',
                            width: (focusedNodeId && interactionMode === 'select') ? (isPreviewMode ? 600 : 320) : 0,
                            transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            zIndex: 1100,
                            backgroundColor: 'background.paper',
                            borderLeft: (focusedNodeId && interactionMode === 'select') ? '1px solid' : 'none',
                            borderColor: 'divider',
                            display: 'flex',
                            flexDirection: 'column',
                            overflow: 'hidden',
                            boxShadow: '-4px 0 12px rgba(0,0,0,0.05)'
                        }}
                    >
                        {focusedNode && interactionMode === 'select' && (
                            <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', height: '100%' }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        {isChatMode && (
                                            <IconButton onClick={() => setIsChatMode(false)} size="small" sx={{ mr: 1 }}>
                                                <ChevronLeft size={20} />
                                            </IconButton>
                                        )}
                                        <Typography variant="h6" fontWeight={600}>
                                            {isChatMode ? 'Node Assistant' : 'Details'}
                                        </Typography>
                                    </Box>
                                    <IconButton onClick={() => {
                                        setFocusedNodeId(null);
                                        setIsPreviewMode(false);
                                        setIsChatMode(false);
                                    }} size="small">
                                        <X size={20} />
                                    </IconButton>
                                </Box>

                                {/* Detail content */}
                                {!isPreviewMode ? (
                                    <>
                                        {isChatMode ? (
                                            <NodeChat nodeName={focusedNode.name} />
                                        ) : focusedNode.type === 'synthesis' ? (
                                            focusedNode.outputType === 'podcast' ? (
                                                <PodcastView
                                                    fileName={focusedNode.name}
                                                    sourceNames={nodes.filter(n => focusedNode.parentIds?.includes(n.id)).map(n => n.name)}
                                                />
                                            ) : focusedNode.outputType === 'ppt' ? (
                                                <PPTSynthesisView
                                                    fileName={focusedNode.name}
                                                    sourceNames={nodes.filter(n => focusedNode.parentIds?.includes(n.id)).map(n => n.name)}
                                                />
                                            ) : focusedNode.outputType === 'flashcards' ? (
                                                <FlashCardView />
                                            ) : focusedNode.outputType === 'quiz' ? (
                                                <Box sx={{ p: 3 }}>
                                                    <Typography variant="h6" gutterBottom>Knowledge Quiz</Typography>
                                                    <Typography variant="body2" color="text.secondary">
                                                        Test your understanding of the selected materials.
                                                    </Typography>
                                                    <Box sx={{ mt: 2, p: 2, border: '1px dashed grey', borderRadius: 2 }}>
                                                        <Typography variant="body2">Quiz generation in progress...</Typography>
                                                    </Box>
                                                </Box>
                                            ) : focusedNode.outputType === 'briefing' ? (
                                                <Box sx={{ p: 3 }}>
                                                    <Typography variant="h6" gutterBottom>Executive Briefing</Typography>
                                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                                        # Executive Summary

                                                        Based on the analysis of {nodes.filter(n => focusedNode.parentIds?.includes(n.id)).length} documents, the key findings are:

                                                        1. Market trends indicate a shift towards AI-driven analysis.
                                                        2. Competitor landscape is consolidating.
                                                    </Typography>
                                                </Box>
                                            ) : (
                                                <Box sx={{ p: 2 }}>
                                                    <Typography variant="h6" gutterBottom>Global Nexus Map</Typography>
                                                    <Typography variant="body2" color="text.secondary">
                                                        The Global Nexus Map provides a structural view of consensus and friction across your selected sources.
                                                        Explore the nodes on the canvas to see the connections.
                                                    </Typography>
                                                </Box>
                                            )
                                        ) : focusedNode.name === 'Audio Summary' ? (
                                            <PodcastView fileName={nodes.find(n => n.id === focusedNode.parentId)?.name || 'Document'} />
                                        ) : focusedNode.name === 'Flash Cards' ? (
                                            <FlashCardView />
                                        ) : (
                                            <>
                                                <Box sx={{ mb: 4, textAlign: 'center' }}>
                                                    <Paper
                                                        variant="outlined"
                                                        sx={{
                                                            p: 3,
                                                            mb: 2,
                                                            bgcolor: focusedNode.type === 'insight' ? '#FEF9C3' : (focusedNode.type === 'chat' ? '#F8FAFC' : 'grey.50'),
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontSize: '32px',
                                                            borderColor: focusedNode.type === 'entity' ? focusedNode.color : 'divider'
                                                        }}
                                                    >
                                                        {focusedNode.type === 'insight' ? '💡' :
                                                            focusedNode.type === 'chat' ? '🧠' :
                                                                focusedNode.type === 'entity' ? '👤' :
                                                                    focusedNode.icon === 'slack' ? '💬' :
                                                                        focusedNode.icon === 'spotify' ? '🎵' :
                                                                            focusedNode.icon === 'pdf' ? '📄' :
                                                                                focusedNode.icon === 'mp4' ? '📺' :
                                                                                    focusedNode.icon === 'mp3' ? '📻' : '📄'}
                                                    </Paper>
                                                    <Typography variant="subtitle1" fontWeight={600}>
                                                        {focusedNode.type === 'insight' ? 'Knowledge Insight' : (focusedNode.type === 'chat' ? 'Analysis' : focusedNode.name)}
                                                    </Typography>
                                                    <Typography variant="body2" color="text.secondary">
                                                        {focusedNode.type === 'insight' ? 'Extracted from PDF' :
                                                            focusedNode.type === 'chat' ? 'Visual Thinking Thread' :
                                                                focusedNode.type === 'entity' ? focusedNode.category :
                                                                    `${focusedNode.icon?.toUpperCase()} Document · 2.4 MB`}
                                                    </Typography>
                                                </Box>

                                                <Divider sx={{ mb: 3 }} />

                                                {focusedNode.type === 'insight' && (
                                                    <Box sx={{ mb: 4 }}>
                                                        <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>Extracted Text</Typography>
                                                        <Typography variant="body2" sx={{ fontStyle: 'italic', bgcolor: '#FEF9C3', p: 2, borderRadius: 2, border: '1px solid rgba(0,0,0,0.05)' }}>
                                                            "{focusedNode.content}"
                                                        </Typography>
                                                    </Box>
                                                )}

                                                {focusedNode.type === 'chat' && (
                                                    <Box sx={{ mb: 4 }}>
                                                        <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>Conversation Summary</Typography>
                                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                                            {focusedNode.messages?.map((m, i) => (
                                                                <Box key={i} sx={{
                                                                    alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                                                                    bgcolor: m.role === 'user' ? 'primary.main' : 'grey.100',
                                                                    color: m.role === 'user' ? 'white' : 'text.primary',
                                                                    p: 1.5,
                                                                    borderRadius: 2,
                                                                    maxWidth: '90%',
                                                                    fontSize: '0.85rem'
                                                                }}>
                                                                    {m.content}
                                                                </Box>
                                                            ))}
                                                        </Box>
                                                    </Box>
                                                )}

                                                <Box sx={{ mb: 3 }}>
                                                    <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>Actions</Typography>
                                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                                        <IconButton title="Chat" onClick={() => setIsChatMode(true)} color={isChatMode ? "primary" : "default"}>
                                                            <MessageCircle size={20} />
                                                        </IconButton>
                                                        <IconButton title="Share"><Share2 size={20} /></IconButton>
                                                        <IconButton title="Info"><Info size={20} /></IconButton>
                                                        {focusedNode.icon === 'pdf' && (
                                                            <IconButton title="Open Review" onClick={() => setReviewingFile({ id: focusedNode.id, name: focusedNode.name, type: 'pdf' })}>
                                                                <Highlighter size={20} />
                                                            </IconButton>
                                                        )}
                                                    </Box>
                                                </Box>

                                                <Box sx={{ flexGrow: 1 }}>
                                                    <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>AI Context</Typography>
                                                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                                                        {focusedNode.type === 'insight'
                                                            ? "This insight was identified as a critical definition of the Transformer's attention mechanism. It bridges the gap between traditional RNN sequence modeling and parallelized self-attention."
                                                            : "This document contains key research findings for the Q1 project. It outlines the methodology and results of user interviews conducted in November."}
                                                    </Typography>
                                                </Box>
                                            </>
                                        )}
                                    </>
                                ) : (
                                    <MediaPreview file={{ name: focusedNode.name, type: focusedNode.icon || 'file' }} />
                                )}
                            </Box>
                        )}
                    </Box>

                    {/* Main Content Area (Overlaying Canvas) */}
                    <Box
                        sx={{
                            flexGrow: 1,
                            height: '100%',
                            ml: sidebarOpen ? '280px' : 0,
                            mr: (focusedNodeId && interactionMode === 'select') ? (isPreviewMode ? '600px' : '320px') : 0,
                            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            position: 'relative',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            pointerEvents: 'none',
                        }}
                    >
                        {/* Chat Input at Bottom Center */}
                        <Box sx={{ pointerEvents: 'auto', width: '100%', display: 'flex', justifyContent: 'center' }}>
                            <ChatInput
                                isConnectionMode={isConnectionMode}
                                onToggleConnectionMode={setIsConnectionMode}
                                onChatSubmit={handleChatSubmit}
                            />
                        </Box>
                    </Box>

                    {/* Canvas Toolbar */}
                    <CanvasToolbar
                        zoom={canvasView.k}
                        onZoomIn={() => setCanvasView(v => ({ ...v, k: Math.min(v.k + 0.1, 5) }))}
                        onZoomOut={() => setCanvasView(v => ({ ...v, k: Math.max(v.k - 0.1, 0.1) }))}
                        onReset={() => setCanvasView({ x: 0, y: 0, k: 1 })}
                        onClear={handleClearCanvas}
                        mode={interactionMode}
                        onModeChange={setInteractionMode}
                    />
                </Box>
            </Box>
        </Box>
    );
}
