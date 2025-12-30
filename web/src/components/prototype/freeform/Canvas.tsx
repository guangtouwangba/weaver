'use client';

import React, { useRef, useState, useEffect, useCallback, useMemo } from 'react';
import { Box, Paper, Typography, List, ListItem, ListItemButton, ListItemIcon, ListItemText, IconButton, CircularProgress, Tooltip } from '@mui/material';
import { Plus, Music, Mic, CreditCard, Layout, Zap, PlayCircle, Sparkles, Send, Brain, MessageSquare, FileText, Network, HelpCircle, GripVertical } from 'lucide-react';
import { Node, Edge } from '@/app/prototype/freeform/page';
import SynthesisOrb, { SynthesisAction } from './SynthesisOrb';
import { TopicCard, MindMapCard, PodcastCard, DataCard, BriefCard, FlashcardNode } from './cards';

const GLOBAL_SIDEBAR_WIDTH = 72;
const HEADER_HEIGHT = 56;

interface CanvasProps {
    nodes: Node[];
    edges: Edge[];
    onAddNode: (file: { name: string; type: string }, x: number, y: number) => void;
    onAddAction: (parentId: string, actionType: string, x: number, y: number) => void;
    onConnectNodes: (sourceId: string, targetId: string) => void;
    onUpdateNodePosition: (nodeId: string, x: number, y: number) => void;
    onAIMapping: (parentId: string, prompt: string) => void;
    selectedNodeIds: string[];
    onSelectNodes: (ids: string[]) => void;
    focusedNodeId: string | null;
    onFocusNode: (id: string | null) => void;
    isConnectionMode: boolean;
    onToggleConnectionMode: (active: boolean) => void;
    onPreview: () => void;
    onSynthesisAction?: (type: string, nodeIds: string[]) => void;
    mappingPromptNodeId: string | null;
    onSetMappingPrompt: (id: string | null) => void;
    view: { x: number; y: number; k: number };
    onViewChange: (view: { x: number; y: number; k: number }) => void;
    projectColor?: string;
    projectName?: string;
    isExternalDragging?: boolean;
    mode: 'select' | 'hand';
    availableFiles?: any[];
    onSmartStart?: (fileId: string, actionType: 'summarize' | 'map') => void;
}

export default function Canvas({
    nodes,
    edges,
    onAddNode,
    onAddAction,
    onConnectNodes,
    onUpdateNodePosition,
    onAIMapping,
    selectedNodeIds,
    onSelectNodes,
    isConnectionMode,
    onToggleConnectionMode,
    onPreview,
    onSynthesisAction,
    mappingPromptNodeId,
    onSetMappingPrompt,
    view,
    onViewChange,
    projectColor = '#0096FF',
    projectName = 'Project',
    isExternalDragging = false,
    mode,
    focusedNodeId,
    onFocusNode,
    availableFiles = [],
    onSmartStart
}: CanvasProps) {
    const canvasRef = useRef<HTMLDivElement>(null);
    const [promptValue, setPromptValue] = useState('');
    const [showMoreActions, setShowMoreActions] = useState(false);

    // Dragging State
    const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
    const [hasMoved, setHasMoved] = useState(false);
    const [draggingCanvas, setDraggingCanvas] = useState(false);
    const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });

    // Connection State
    const [linkingSourceId, setLinkingSourceId] = useState<string | null>(null);
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
    const [hoveredSynthesisNodeId, setHoveredSynthesisNodeId] = useState<string | null>(null);

    // Lasso Selection State
    const [lassoStart, setLassoStart] = useState<{ x: number; y: number } | null>(null);
    const [lassoEnd, setLassoEnd] = useState<{ x: number; y: number } | null>(null);
    const [previewSelectionIds, setPreviewSelectionIds] = useState<string[]>([]);

    // Calculate centroid and bounding box for selection
    const selectionCentroid = useMemo(() => {
        if (selectedNodeIds.length === 0) return null;

        const selectedNodes = nodes.filter(n => selectedNodeIds.includes(n.id));
        if (selectedNodes.length === 0) return null;

        // Single selection: Offset orb to Top-Left to avoid blocking content and Genius card (which is on Right)
        if (selectedNodes.length === 1) {
            const node = selectedNodes[0];
            return {
                x: node.x - 90,
                y: node.y - 70
            };
        }

        // Multi selection: Centroid
        const sumX = selectedNodes.reduce((acc, n) => acc + n.x, 0);
        const sumY = selectedNodes.reduce((acc, n) => acc + n.y, 0);

        return {
            x: sumX / selectedNodes.length,
            y: sumY / selectedNodes.length
        };
    }, [selectedNodeIds, nodes]);

    const selectionBounds = useMemo(() => {
        if (selectedNodeIds.length <= 1) return null;
        const selectedNodes = nodes.filter(n => selectedNodeIds.includes(n.id));
        if (selectedNodes.length === 0) return null;

        const minX = Math.min(...selectedNodes.map(n => n.x)) - 80;
        const maxX = Math.max(...selectedNodes.map(n => n.x)) + 80;
        const minY = Math.min(...selectedNodes.map(n => n.y)) - 80;
        const maxY = Math.max(...selectedNodes.map(n => n.y)) + 80;

        return {
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY
        };
    }, [selectedNodeIds, nodes]);

    const handleNodeClick = (e: React.MouseEvent, nodeId: string) => {
        e.stopPropagation();
        if (isConnectionMode) return;

        if (e.metaKey || e.ctrlKey) {
            // Toggle selection
            if (selectedNodeIds.includes(nodeId)) {
                onSelectNodes(selectedNodeIds.filter(id => id !== nodeId));
            } else {
                onSelectNodes([...selectedNodeIds, nodeId]);
            }
        } else {
            // Single selection
            onSelectNodes([nodeId]);
        }
    };

    useEffect(() => {
        if (!isConnectionMode) {
            setLinkingSourceId(null);
        }
    }, [isConnectionMode]);

    const toCanvasCoords = useCallback((clientX: number, clientY: number) => {
        if (!canvasRef.current) return { x: 0, y: 0 };
        const rect = canvasRef.current.getBoundingClientRect();
        return {
            x: (clientX - rect.left - view.x) / view.k,
            y: (clientY - rect.top - view.y) / view.k
        };
    }, [view]);

    const handleMouseDown = (e: React.MouseEvent) => {
        const isShift = e.shiftKey;

        // PANNING: Middle Click OR (Left Click AND (Hand Mode AND !Shift))
        const isPanning = e.button === 1 || (e.button === 0 && (mode === 'hand' && !isShift));

        // LASSO: Left Click AND (Select Mode OR (Hand Mode AND ShiftKey)) AND target is Canvas
        const isLasso = e.button === 0 && !isConnectionMode && !isPanning && e.target === e.currentTarget;

        if (isPanning) {
            setDraggingCanvas(true);
            setLastMousePos({ x: e.clientX, y: e.clientY });
        } else if (isLasso) {
            const coords = toCanvasCoords(e.clientX, e.clientY);
            setLassoStart(coords);
            setLassoEnd(coords);

            // Additive selection logic: clear previous if not holding shift/meta/ctrl
            if (!e.metaKey && !e.ctrlKey && !e.shiftKey) {
                onSelectNodes([]);
            }
        }
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        const coords = toCanvasCoords(e.clientX, e.clientY);
        setMousePos(coords);

        if (draggingCanvas) {
            const dx = e.clientX - lastMousePos.x;
            const dy = e.clientY - lastMousePos.y;
            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) setHasMoved(true);
            onViewChange({ ...view, x: view.x + dx, y: view.y + dy });
            setLastMousePos({ x: e.clientX, y: e.clientY });
        } else if (draggingNodeId) {
            const dx = e.clientX - lastMousePos.x;
            const dy = e.clientY - lastMousePos.y;
            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) setHasMoved(true);
            onUpdateNodePosition(draggingNodeId, coords.x, coords.y);
        } else if (lassoStart) {
            setLassoEnd(coords);

            // Real-time intersection check for visual feedback
            const minX = Math.min(lassoStart.x, coords.x);
            const maxX = Math.max(lassoStart.x, coords.x);
            const minY = Math.min(lassoStart.y, coords.y);
            const maxY = Math.max(lassoStart.y, coords.y);

            const nodesInLasso = nodes.filter(n => {
                const nodeW = 150;
                const nodeH = 100;
                const nLeft = n.x - nodeW / 2;
                const nRight = n.x + nodeW / 2;
                const nTop = n.y - nodeH / 2;
                const nBottom = n.y + nodeH / 2;
                return nLeft < maxX && nRight > minX && nTop < maxY && nBottom > minY;
            }).map(n => n.id);

            setPreviewSelectionIds(nodesInLasso);
        }
    };

    const handleMouseUp = (e: React.MouseEvent) => {
        if (lassoStart) {
            // Recalculate intersection synchronously to ensure reliability
            const coords = toCanvasCoords(e.clientX, e.clientY);
            const minX = Math.min(lassoStart.x, coords.x);
            const maxX = Math.max(lassoStart.x, coords.x);
            const minY = Math.min(lassoStart.y, coords.y);
            const maxY = Math.max(lassoStart.y, coords.y);

            const nodesInLasso = nodes.filter(n => {
                const nodeW = 150;
                const nodeH = 100;
                const nLeft = n.x - nodeW / 2;
                const nRight = n.x + nodeW / 2;
                const nTop = n.y - nodeH / 2;
                const nBottom = n.y + nodeH / 2;
                return nLeft < maxX && nRight > minX && nTop < maxY && nBottom > minY;
            }).map(n => n.id);

            if (nodesInLasso.length > 0) {
                ignoreClickRef.current = true;
                if (e.shiftKey || e.metaKey || e.ctrlKey) {
                    const newSelection = Array.from(new Set([...selectedNodeIds, ...nodesInLasso]));
                    onSelectNodes(newSelection);
                } else {
                    onSelectNodes(nodesInLasso);
                }
            } else if (!hasMoved && !e.shiftKey && !e.metaKey && !e.ctrlKey) {
                onSelectNodes([]);
            } else if (hasMoved && !e.shiftKey && !e.metaKey && !e.ctrlKey) {
                onSelectNodes([]);
            }
        }

        setDraggingCanvas(false);
        setLassoStart(null);
        setLassoEnd(null);
        setPreviewSelectionIds([]);

        setTimeout(() => {
            setDraggingNodeId(null);
            setHasMoved(false);
        }, 50);
    };

    const handleWheel = (e: React.WheelEvent) => {
        if (!canvasRef.current) return;
        const rect = canvasRef.current.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const zoomSpeed = 0.001;
        const delta = -e.deltaY;
        const factor = Math.pow(1.1, delta / 100);
        const newK = Math.min(Math.max(view.k * factor, 0.1), 5);

        // Zoom relative to mouse position
        const newX = mouseX - (mouseX - view.x) * (newK / view.k);
        const newY = mouseY - (mouseY - view.y) * (newK / view.k);

        onViewChange({ x: newX, y: newY, k: newK });
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const coords = toCanvasCoords(e.clientX, e.clientY);
        try {
            const fileData = JSON.parse(e.dataTransfer.getData('application/json'));
            onAddNode(fileData, coords.x, coords.y);
        } catch (err) {
            console.error('Failed to parse dropped data', err);
        }
    };

    const ignoreClickRef = useRef(false);

    const handleCanvasClick = (e: React.MouseEvent) => {
        if (ignoreClickRef.current) {
            ignoreClickRef.current = false;
            return;
        }
        if (e.target === e.currentTarget) {
            onSelectNodes([]);
            onFocusNode(null);
        }
    };

    // Handle dragging nodes OUT of the canvas (e.g. to chat)
    const handleExternalDragStart = (e: React.DragEvent, node: Node) => {
        e.stopPropagation();
        const payload = {
            id: node.id,
            type: 'node',
            title: node.name || node.title || 'Untitled Node',
            content: node.content || node.description || '',
            nodeType: node.type
        };
        e.dataTransfer.effectAllowed = 'copy';
        e.dataTransfer.setData('application/json', JSON.stringify(payload));
        e.dataTransfer.setData('text/plain', node.name || node.title || 'Untitled Node');

        // Create a nice drag ghost
        const ghost = document.createElement('div');
        ghost.textContent = node.name || 'Node';
        ghost.style.background = 'white';
        ghost.style.padding = '8px 12px';
        ghost.style.border = `1px solid ${projectColor}`;
        ghost.style.borderRadius = '4px';
        ghost.style.position = 'absolute';
        ghost.style.top = '-1000px';
        document.body.appendChild(ghost);
        e.dataTransfer.setDragImage(ghost, 0, 0);
        setTimeout(() => document.body.removeChild(ghost), 0);
    };

    // Calculate connection path (curvy line)
    const renderEdge = (edge: Edge) => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);
        if (!source || !target) return null;

        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const cp1x = source.x + dx * 0.5;
        const cp1y = source.y;
        const cp2x = source.x + dx * 0.5;
        const cp2y = target.y;

        const path = `M ${source.x} ${source.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${target.x} ${target.y}`;

        // Determine edge style based on target type
        const isKnowledgeFlow = target.type === 'insight';
        const isAIGenerated = !!edge.label;
        const isAnalyzing = edge.label === 'analyzing';
        const isSynthesisThread = target.type === 'synthesis' || source.type === 'synthesis';
        const isHoveredTrace = hoveredSynthesisNodeId && (target.id === hoveredSynthesisNodeId || source.id === hoveredSynthesisNodeId);

        return (
            <g key={edge.id}>
                <path
                    id={`path-${edge.id}`}
                    d={path}
                    fill="none"
                    stroke={isSynthesisThread ? (isHoveredTrace ? projectColor : `${projectColor}22`) : (isAIGenerated ? (target.color || (isAnalyzing ? '#0096FF' : '#6366F1')) : (isKnowledgeFlow ? 'rgba(250, 204, 21, 0.2)' : 'rgba(0, 150, 255, 0.1)'))}
                    strokeWidth={isSynthesisThread ? (isHoveredTrace ? 3 : 1.5) : (isAIGenerated ? '2' : (isKnowledgeFlow ? '12' : '8'))}
                    style={{
                        filter: (isAIGenerated || isHoveredTrace) ? 'none' : 'blur(4px)',
                        opacity: isAIGenerated ? 0.6 : 1,
                        animation: (isAnalyzing || (isSynthesisThread && !isHoveredTrace)) ? 'dash 2s linear infinite' : 'none'
                    }}
                />
                <path
                    d={path}
                    fill="none"
                    stroke={isSynthesisThread ? projectColor : (isAIGenerated ? (target.color || (isAnalyzing ? '#0096FF' : '#6366F1')) : (isKnowledgeFlow ? '#FACC15' : '#E5E7EB'))}
                    strokeWidth={isSynthesisThread ? (isHoveredTrace ? 2 : 1) : (isAIGenerated ? '2' : (isKnowledgeFlow ? '3' : '2'))}
                    strokeDasharray={isSynthesisThread ? '4 4' : ((isKnowledgeFlow || isAIGenerated) && !isAnalyzing ? '' : '4 4')}
                    style={{
                        animation: (isAnalyzing || isSynthesisThread) ? 'dash 1s linear infinite' : 'none',
                        opacity: isSynthesisThread && !isHoveredTrace ? 0.3 : 1
                    }}
                />
                {(edge.label || (isSynthesisThread && isHoveredTrace)) && (
                    <text
                        dy="-6"
                        style={{
                            fontSize: '10px',
                            fill: isSynthesisThread ? projectColor : (target.color || '#6366F1'),
                            fontWeight: 700,
                            pointerEvents: 'none',
                            opacity: isSynthesisThread && !isHoveredTrace ? 0.5 : 1
                        }}
                    >
                        <textPath href={`#path-${edge.id}`} startOffset="50%" textAnchor="middle">
                            {isSynthesisThread && isHoveredTrace ? 'Neural Thread' : edge.label}
                        </textPath>
                    </text>
                )}
            </g>
        );
    };

    const ANCHOR_POSITIONS = [
        { top: -4, left: '50%', transform: 'translateX(-50%)' }, // N
        { top: -4, right: -4 }, // NE
        { top: '50%', right: -4, transform: 'translateY(-50%)' }, // E
        { bottom: -4, right: -4 }, // SE
        { bottom: -4, left: '50%', transform: 'translateX(-50%)' }, // S
        { bottom: -4, left: -4 }, // SW
        { top: '50%', left: -4, transform: 'translateY(-50%)' }, // W
        { top: -4, left: -4 }, // NW
    ];

    return (
        <Box
            ref={canvasRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onWheel={handleWheel}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={handleCanvasClick}
            sx={{
                position: 'fixed',
                top: HEADER_HEIGHT,
                left: GLOBAL_SIDEBAR_WIDTH,
                right: 0,
                bottom: 0,
                backgroundColor: 'background.default',
                backgroundImage: `radial-gradient(${projectColor}22 ${1.5 * view.k}px, transparent 0)`,
                backgroundSize: `${32 * view.k}px ${32 * view.k}px`,
                backgroundPosition: `${view.x}px ${view.y}px`,
                overflow: 'hidden',
                zIndex: 0,
                cursor: mode === 'hand'
                    ? (draggingCanvas ? 'grabbing' : 'grab')
                    : (isConnectionMode ? (linkingSourceId ? 'crosshair' : 'pointer') : 'default'),
                userSelect: 'none'
            }}
        >
            {/* Project Watermark */}
            <Typography
                variant="h1"
                sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    fontSize: '15vw',
                    fontWeight: 900,
                    color: projectColor,
                    opacity: 0.03,
                    pointerEvents: 'none',
                    userSelect: 'none',
                    whiteSpace: 'nowrap',
                    zIndex: 0
                }}
            >
                {projectName.toUpperCase()}
            </Typography>

            {/* Drag and Drop Guide Overlay */}
            {isExternalDragging && (
                <Box
                    sx={{
                        position: 'absolute',
                        inset: 20,
                        border: `2px dashed ${projectColor}`,
                        borderRadius: 4,
                        bgcolor: `${projectColor}08`,
                        zIndex: 50,
                        pointerEvents: 'none',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        animation: 'pulse 2s infinite ease-in-out',
                    }}
                >
                    <Box
                        sx={{
                            p: 3,
                            borderRadius: '50%',
                            bgcolor: 'white',
                            boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                            mb: 2,
                            display: 'flex',
                            color: projectColor
                        }}
                    >
                        <Plus size={48} strokeWidth={3} />
                    </Box>
                    <Typography variant="h5" fontWeight={700} sx={{ color: projectColor }}>
                        Drop to Add to Canvas
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Release to create a new node at this position
                    </Typography>
                </Box>
            )}

            <Box
                sx={{
                    transform: `translate(${view.x}px, ${view.y}px) scale(${view.k})`,
                    transformOrigin: '0 0',
                    width: '100%',
                    height: '100%',
                    position: 'relative',
                    zIndex: 1,
                    pointerEvents: 'none'
                }}
            >
                {/* Constellation Aura for Multi-selection */}
                {selectionBounds && (
                    <Box
                        sx={{
                            position: 'absolute',
                            left: selectionBounds.x,
                            top: selectionBounds.y,
                            width: selectionBounds.width,
                            height: selectionBounds.height,
                            borderRadius: '50%',
                            background: `radial-gradient(circle, ${projectColor}11 0%, transparent 70%)`,
                            border: `1px dashed ${projectColor}33`,
                            pointerEvents: 'none',
                            zIndex: 0,
                            animation: 'pulse 4s infinite ease-in-out',
                        }}
                    />
                )}

                {/* Box Selection (Lasso) UI */}
                {lassoStart && lassoEnd && (
                    <Box
                        sx={{
                            position: 'absolute',
                            left: Math.min(lassoStart.x, lassoEnd.x),
                            top: Math.min(lassoStart.y, lassoEnd.y),
                            width: Math.abs(lassoStart.x - lassoEnd.x),
                            height: Math.abs(lassoStart.y - lassoEnd.y),
                            bgcolor: `${projectColor}11`,
                            border: `1px solid ${projectColor}`,
                            borderRadius: '2px',
                            zIndex: 1000,
                            pointerEvents: 'none'
                        }}
                    />
                )}

                {/* SVG Layer for Edges */}
                <svg
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '10000px', // Large enough for panning
                        height: '10000px',
                        transform: 'translate(-5000px, -5000px)', // Center the large SVG
                        pointerEvents: 'none',
                    }}
                >
                    <g transform="translate(5000, 5000)">
                        {edges.map(renderEdge)}

                        {/* Rubber Band Preview Line */}
                        {isConnectionMode && linkingSourceId && (
                            <line
                                x1={nodes.find(n => n.id === linkingSourceId)?.x || 0}
                                y1={nodes.find(n => n.id === linkingSourceId)?.y || 0}
                                x2={mousePos.x}
                                y2={mousePos.y}
                                stroke="#0096FF"
                                strokeWidth="2"
                                strokeDasharray="4 4"
                            />
                        )}
                    </g>
                </svg>

                {/* Synthesis Orb */}
                {selectionCentroid && !isConnectionMode && (
                    <SynthesisOrb
                        x={selectionCentroid.x}
                        y={selectionCentroid.y}
                        actions={[
                            {
                                id: 'podcast',
                                label: 'Podcast',
                                icon: <Mic size={20} />,
                                handler: () => onSynthesisAction?.('podcast', selectedNodeIds),
                                category: 'audio'
                            },
                            {
                                id: 'ppt',
                                label: 'Presentation',
                                icon: <Layout size={20} />,
                                handler: () => onSynthesisAction?.('ppt', selectedNodeIds),
                                category: 'visual'
                            },
                            {
                                id: 'mindmap',
                                label: 'Mind Map',
                                icon: <Network size={20} />,
                                handler: () => onSynthesisAction?.('mindmap', selectedNodeIds),
                                category: 'visual'
                            },
                            {
                                id: 'flashcards',
                                label: 'Flash Cards',
                                icon: <CreditCard size={20} />,
                                handler: () => onSynthesisAction?.('flashcards', selectedNodeIds),
                                category: 'study'
                            },
                            {
                                id: 'quiz',
                                label: 'Quiz',
                                icon: <HelpCircle size={20} />,
                                handler: () => onSynthesisAction?.('quiz', selectedNodeIds),
                                category: 'study'
                            },
                            {
                                id: 'briefing',
                                label: 'Briefing Doc',
                                icon: <FileText size={20} />,
                                handler: () => onSynthesisAction?.('briefing', selectedNodeIds),
                                category: 'text'
                            }
                        ]}
                        projectColor={projectColor}
                    />
                )}

                {/* Nodes Layer */}
                {nodes.map((node) => {
                    const isSelected = selectedNodeIds.includes(node.id);
                    const isPreviewSelected = previewSelectionIds.includes(node.id);
                    const isPotentialTarget = isConnectionMode && linkingSourceId && linkingSourceId !== node.id;
                    const isParentOfHoveredSynth = hoveredSynthesisNodeId && nodes.find(n => n.id === hoveredSynthesisNodeId)?.parentIds?.includes(node.id);

                    if (node.type === 'synthesis') {
                        return (
                            <Box
                                key={node.id}
                                onMouseEnter={() => setHoveredSynthesisNodeId(node.id)}
                                onMouseLeave={() => setHoveredSynthesisNodeId(null)}
                                onMouseDown={(e) => {
                                    if (isConnectionMode) return;
                                    e.stopPropagation();
                                    setDraggingNodeId(node.id);
                                    setHasMoved(false);
                                    setLastMousePos({ x: e.clientX, y: e.clientY });
                                    handleNodeClick(e, node.id);
                                }}
                                onDoubleClick={(e) => {
                                    e.stopPropagation();
                                    if (mode === 'select') onFocusNode(node.id);
                                }}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: isParentOfHoveredSynth ? 'translate(-50%, -50%) scale(1.15)' : 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isParentOfHoveredSynth) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: 0,
                                        right: 0,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <Paper
                                    elevation={isSelected ? 12 : 6}
                                    sx={{
                                        p: 2,
                                        borderRadius: '50%',
                                        width: 100,
                                        height: 100,
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        bgcolor: 'white',
                                        border: `3px solid ${isSelected ? projectColor : (node.status === 'analyzing' ? '#FACC15' : projectColor + '88')}`,
                                        boxShadow: isSelected ? `0 0 20px ${projectColor}44` : 'none',
                                        cursor: mode === 'hand' ? 'grab' : (isConnectionMode ? 'crosshair' : 'pointer'),
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        animation: node.status === 'analyzing' ? 'spin 10s linear infinite' : 'none',
                                        position: 'relative',
                                        overflow: 'visible'
                                    }}
                                >
                                    <Box sx={{ color: projectColor, mb: 0.5 }}>
                                        {node.outputType === 'podcast' ? <Mic size={32} /> :
                                            node.outputType === 'ppt' ? <Layout size={32} /> :
                                                node.outputType === 'flashcards' ? <CreditCard size={32} /> :
                                                    node.outputType === 'quiz' ? <HelpCircle size={32} /> :
                                                        node.outputType === 'briefing' ? <FileText size={32} /> :
                                                            <Network size={32} />}
                                    </Box>
                                    <Typography variant="caption" sx={{ fontWeight: 800, color: projectColor, fontSize: '0.65rem' }}>
                                        {node.outputType?.toUpperCase()}
                                    </Typography>

                                    {node.status === 'analyzing' && (
                                        <Box sx={{ position: 'absolute', inset: -5, borderRadius: '50%', border: `2px dashed #FACC15`, animation: 'spin 3s linear infinite' }} />
                                    )}
                                </Paper>
                            </Box>
                        );
                    }

                    if (node.type === 'action') {
                        return (
                            <Box
                                key={node.id}
                                onMouseDown={(e) => {
                                    if (isConnectionMode) return;
                                    e.stopPropagation();
                                    setDraggingNodeId(node.id);
                                    setHasMoved(false);
                                    setLastMousePos({ x: e.clientX, y: e.clientY });
                                    handleNodeClick(e, node.id);
                                }}
                                onDoubleClick={(e) => {
                                    e.stopPropagation();
                                    if (mode === 'select') onFocusNode(node.id);
                                }}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: isParentOfHoveredSynth ? 'translate(-50%, -50%) scale(1.15)' : 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected || isParentOfHoveredSynth) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <Paper
                                    elevation={isSelected || isPreviewSelected ? 8 : 2}
                                    sx={{
                                        px: 2,
                                        py: 1.5,
                                        borderRadius: '12px',
                                        bgcolor: 'white',
                                        border: isSelected || isPreviewSelected ? `2px solid ${projectColor}` : '1px solid rgba(0,0,0,0.05)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 1.5,
                                        cursor: mode === 'hand' ? 'grab' : (isConnectionMode ? 'crosshair' : 'pointer'),
                                        transition: 'all 0.2s',
                                        whiteSpace: 'nowrap',
                                        minWidth: 140
                                    }}
                                >
                                    <Box sx={{ color: projectColor, display: 'flex' }}>
                                        {node.name === 'Mindmap' ? <Layout size={20} /> :
                                            node.name === 'Audio Summary' ? <Mic size={20} /> :
                                                node.name === 'Flash Cards' ? <CreditCard size={20} /> : <Zap size={20} />}
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" fontWeight={700}>{node.name}</Typography>
                                        <Typography variant="caption" color="text.secondary">AI Generated</Typography>
                                    </Box>
                                </Paper>
                            </Box>
                        );
                    }

                    // New Card Types
                    if (node.type === 'topic') {
                        return (
                            <Box
                                key={node.id}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <TopicCard
                                    id={node.id}
                                    name={node.name}
                                    subtitle={node.subtitle}
                                    accentColor={node.accentColor || node.color}
                                    iconType={node.iconType}
                                    isSelected={isSelected || isPreviewSelected}
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                />
                            </Box>
                        );
                    }

                    if (node.type === 'mindmap') {
                        return (
                            <Box
                                key={node.id}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <MindMapCard
                                    id={node.id}
                                    name={node.name}
                                    projectColor={projectColor}
                                    isSelected={isSelected || isPreviewSelected}
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                    onExpand={() => {
                                        // Could trigger an action to expand the mind map
                                    }}
                                />
                            </Box>
                        );
                    }

                    if (node.type === 'podcast') {
                        return (
                            <Box
                                key={node.id}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <PodcastCard
                                    id={node.id}
                                    name={node.name}
                                    duration={node.duration}
                                    accentColor={node.accentColor || '#8B5CF6'}
                                    isSelected={isSelected || isPreviewSelected}
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                />
                            </Box>
                        );
                    }

                    if (node.type === 'data') {
                        return (
                            <Box
                                key={node.id}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <DataCard
                                    id={node.id}
                                    name={node.name}
                                    metric={node.metric}
                                    accentColor={node.accentColor || '#10B981'}
                                    isSelected={isSelected || isPreviewSelected}
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                />
                            </Box>
                        );
                    }

                    if (node.type === 'brief') {
                        return (
                            <Box
                                key={node.id}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <BriefCard
                                    id={node.id}
                                    name={node.name}
                                    accentColor={node.accentColor || '#3B82F6'}
                                    isSelected={isSelected || isPreviewSelected}
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                    onOpen={() => {
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                />
                            </Box>
                        );
                    }

                    if (node.type === 'flashcard') {
                        return (
                            <Box
                                key={node.id}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <FlashcardNode
                                    id={node.id}
                                    term={node.term || node.name}
                                    definition={node.definition}
                                    cardCount={node.cardCount}
                                    totalCards={node.cardCount || 24}
                                    accentColor={node.accentColor || '#F97316'}
                                    isSelected={isSelected || isPreviewSelected}
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                />
                            </Box>
                        );
                    }

                    if (node.type === 'chat') {
                        return (
                            <Box
                                key={node.id}
                                onMouseDown={(e) => {
                                    if (isConnectionMode) return;
                                    e.stopPropagation();
                                    setDraggingNodeId(node.id);
                                    setHasMoved(false);
                                    setLastMousePos({ x: e.clientX, y: e.clientY });
                                    handleNodeClick(e, node.id);
                                }}
                                onDoubleClick={(e) => {
                                    e.stopPropagation();
                                    if (mode === 'select') onFocusNode(node.id);
                                }}
                                sx={{
                                    position: 'absolute',
                                    left: node.x,
                                    top: node.y,
                                    transform: 'translate(-50%, -50%)',
                                    zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                    pointerEvents: 'auto',
                                    '&:hover .drag-handle': { opacity: 1 }
                                }}
                            >
                                {/* External Drag Handle */}
                                <Box
                                    className="drag-handle"
                                    draggable
                                    onDragStart={(e) => handleExternalDragStart(e, node)}
                                    onMouseDown={(e) => e.stopPropagation()}
                                    sx={{
                                        position: 'absolute',
                                        top: -10,
                                        right: -10,
                                        zIndex: 20,
                                        bgcolor: 'white',
                                        borderRadius: '50%',
                                        p: 0.5,
                                        width: 24,
                                        height: 24,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        border: `1px solid ${projectColor}`,
                                        cursor: 'grab',
                                        opacity: 0,
                                        transition: 'all 0.2s',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                        '&:hover': { transform: 'scale(1.1)' }
                                    }}
                                >
                                    <GripVertical size={14} color={projectColor} />
                                </Box>
                                <Paper
                                    elevation={isSelected || isPreviewSelected ? 12 : 4}
                                    sx={{
                                        width: 320,
                                        borderRadius: '20px',
                                        bgcolor: 'white',
                                        border: isSelected || isPreviewSelected ? `2px solid ${projectColor}` : '1px solid rgba(0,0,0,0.08)',
                                        overflow: 'hidden',
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        cursor: mode === 'hand' ? 'grab' : (isConnectionMode ? 'crosshair' : 'pointer'),
                                    }}
                                >
                                    {/* Chat Header */}
                                    <Box sx={{
                                        p: 2,
                                        bgcolor: `${projectColor}11`,
                                        borderBottom: '1px solid rgba(0,0,0,0.05)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between'
                                    }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Brain size={18} color={projectColor} />
                                            <Typography variant="subtitle2" fontWeight={700} color={projectColor}>Analysis Thread</Typography>
                                        </Box>
                                        {node.isThinking && <CircularProgress size={14} thickness={6} sx={{ color: projectColor }} />}
                                    </Box>

                                    {/* Message Flow */}
                                    <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1.5, maxHeight: 400, overflowY: 'auto' }}>
                                        {node.messages?.map((msg, i) => (
                                            <Box key={i} sx={{
                                                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                                                bgcolor: msg.role === 'user' ? projectColor : 'grey.50',
                                                color: msg.role === 'user' ? 'white' : 'text.primary',
                                                p: 1.5,
                                                borderRadius: 3,
                                                maxWidth: '90%',
                                                boxShadow: msg.role === 'assistant' ? '0 2px 8px rgba(0,0,0,0.05)' : 'none'
                                            }}>
                                                <Typography variant="body2" sx={{ lineHeight: 1.5, fontSize: '0.85rem' }}>
                                                    {msg.content}
                                                </Typography>
                                            </Box>
                                        ))}
                                        {node.isThinking && (
                                            <Box sx={{ alignSelf: 'flex-start', display: 'flex', gap: 0.5, p: 1 }}>
                                                <Box sx={{ width: 6, height: 6, bgcolor: 'grey.300', borderRadius: '50%', animation: 'bounce 1s infinite' }} />
                                                <Box sx={{ width: 6, height: 6, bgcolor: 'grey.300', borderRadius: '50%', animation: 'bounce 1s infinite 0.2s' }} />
                                                <Box sx={{ width: 6, height: 6, bgcolor: 'grey.300', borderRadius: '50%', animation: 'bounce 1s infinite 0.4s' }} />
                                            </Box>
                                        )}
                                    </Box>

                                    {/* Action Footer */}
                                    <Box sx={{ p: 1.5, borderTop: '1px solid rgba(0,0,0,0.05)', display: 'flex', justifyContent: 'center' }}>
                                        <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                            <MessageSquare size={12} />
                                            Continue conversation below
                                        </Typography>
                                    </Box>
                                </Paper>
                            </Box>
                        );
                    }

                    return (
                        <Box
                            key={node.id}
                            sx={{
                                position: 'absolute',
                                left: node.x,
                                top: node.y,
                                transform: 'translate(-50%, -50%)',
                                zIndex: (isSelected || isPreviewSelected) ? 10 : 1,
                                pointerEvents: 'auto'
                            }}
                        >
                            {/* The Node Container */}
                            {node.type === 'insight' ? (
                                <Paper
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                    onClick={(e) => {
                                        if (isConnectionMode && linkingSourceId && linkingSourceId !== node.id) {
                                            e.stopPropagation();
                                            onConnectNodes(linkingSourceId, node.id);
                                            setLinkingSourceId(null);
                                            onToggleConnectionMode(false);
                                        }
                                    }}
                                    sx={{
                                        p: 2.5,
                                        width: 240,
                                        borderRadius: '2px', // Sharper corners for paper look
                                        bgcolor: '#FEF9C3', // Post-it yellow
                                        border: isSelected || isPreviewSelected ? '2px solid #FACC15' : (isPotentialTarget ? '2px solid #0096FF' : 'none'),
                                        boxShadow: isSelected || isPreviewSelected
                                            ? '0 12px 32px rgba(0,0,0,0.15)'
                                            : '0 4px 12px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.05)',
                                        cursor: mode === 'hand' ? 'grab' : (isConnectionMode ? 'crosshair' : 'pointer'),
                                        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                        '&:hover': {
                                            transform: draggingNodeId === node.id ? 'none' : 'rotate(1deg) scale(1.02)',
                                            boxShadow: '0 16px 40px rgba(0,0,0,0.12)',
                                        },
                                        position: 'relative',
                                        overflow: 'visible',
                                        animation: 'popIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
                                        // Corner fold effect
                                        '&::after': {
                                            content: '""',
                                            position: 'absolute',
                                            bottom: 0,
                                            right: 0,
                                            width: 0,
                                            height: 0,
                                            borderStyle: 'solid',
                                            borderWidth: '0 0 16px 16px',
                                            borderColor: `transparent transparent white #EAB308`,
                                            opacity: 0.3
                                        }
                                    }}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                                        <Zap size={14} fill="#854D0E" color="#854D0E" />
                                        <Typography variant="caption" sx={{ color: '#854D0E', fontWeight: 800, letterSpacing: '0.1em', fontSize: '0.65rem' }}>
                                            INSIGHT
                                        </Typography>
                                    </Box>
                                    <Typography variant="body2" sx={{
                                        lineHeight: 1.6,
                                        color: '#451A03',
                                        fontSize: '0.9rem',
                                        fontFamily: '"Georgia", serif',
                                        display: '-webkit-box',
                                        WebkitLineClamp: 6,
                                        WebkitBoxOrient: 'vertical',
                                        overflow: 'hidden'
                                    }}>
                                        {node.content}
                                    </Typography>

                                    {/* Connection Anchors for Insight Nodes */}
                                    {isConnectionMode && ANCHOR_POSITIONS.map((pos, idx) => (
                                        <Box
                                            key={idx}
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                setLinkingSourceId(node.id);
                                            }}
                                            sx={{
                                                position: 'absolute',
                                                width: 10,
                                                height: 10,
                                                borderRadius: '50%',
                                                backgroundColor: '#0096FF',
                                                border: '2px solid white',
                                                cursor: 'crosshair',
                                                zIndex: 20,
                                                ...pos,
                                                '&:hover': {
                                                    transform: `${pos.transform || ''} scale(1.3)`,
                                                    backgroundColor: '#007ACC'
                                                }
                                            }}
                                        />
                                    ))}
                                </Paper>
                            ) : node.type === 'note' ? (
                                <Paper
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                    sx={{
                                        p: 2,
                                        width: 200,
                                        minHeight: 120,
                                        borderRadius: '8px',
                                        bgcolor: 'white',
                                        border: isSelected || isPreviewSelected ? `2px solid ${projectColor}` : '1px solid rgba(0,0,0,0.05)',
                                        boxShadow: isSelected || isPreviewSelected
                                            ? '0 12px 32px rgba(0,0,0,0.12)'
                                            : '0 4px 12px rgba(0,0,0,0.06)',
                                        cursor: mode === 'hand' ? 'grab' : (isConnectionMode ? 'crosshair' : 'pointer'),
                                        position: 'relative',
                                        transition: 'all 0.2s',
                                        '&:hover': {
                                            transform: draggingNodeId === node.id ? 'none' : 'translateY(-2px)',
                                            boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
                                        }
                                    }}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, color: 'text.secondary' }}>
                                        <FileText size={16} />
                                        <Typography variant="caption" fontWeight={700} sx={{ letterSpacing: '0.05em' }}>NOTE</Typography>
                                    </Box>
                                    <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>{node.name}</Typography>
                                    <Typography variant="caption" color="text.secondary" sx={{
                                        display: '-webkit-box',
                                        WebkitLineClamp: 3,
                                        WebkitBoxOrient: 'vertical',
                                        overflow: 'hidden',
                                        lineHeight: 1.4
                                    }}>
                                        {node.content || 'Click to add content...'}
                                    </Typography>

                                    {/* Connection Anchors for Notes */}
                                    {isConnectionMode && ANCHOR_POSITIONS.map((pos, idx) => (
                                        <Box
                                            key={idx}
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                setLinkingSourceId(node.id);
                                            }}
                                            sx={{
                                                position: 'absolute',
                                                width: 10,
                                                height: 10,
                                                borderRadius: '50%',
                                                backgroundColor: projectColor,
                                                border: '2px solid white',
                                                cursor: 'crosshair',
                                                zIndex: 20,
                                                ...pos,
                                                '&:hover': {
                                                    transform: `${pos.transform || ''} scale(1.3)`,
                                                    backgroundColor: projectColor
                                                }
                                            }}
                                        />
                                    ))}
                                </Paper>
                            ) : node.type === 'entity' ? (
                                <Box
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                    sx={{
                                        width: 60,
                                        height: 60,
                                        borderRadius: '50%',
                                        backgroundColor: 'white',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: mode === 'hand' ? 'grab' : (isConnectionMode ? 'crosshair' : 'pointer'),
                                        border: `2px solid ${node.color || '#6366F1'}`,
                                        boxShadow: isSelected || isPreviewSelected ? `0 0 0 4px ${node.color}33, 0 8px 24px rgba(0,0,0,0.1)` : '0 4px 12px rgba(0,0,0,0.08)',
                                        transition: 'all 0.2s',
                                        '&:hover': { transform: draggingNodeId === node.id ? 'none' : 'scale(1.1)' },
                                        position: 'relative',
                                    }}
                                >
                                    <Typography variant="body2" fontWeight={700} sx={{ color: node.color || '#6366F1', fontSize: '0.75rem', textAlign: 'center', px: 1 }}>
                                        {node.name}
                                    </Typography>

                                    {isConnectionMode && ANCHOR_POSITIONS.map((pos, idx) => (
                                        <Box
                                            key={idx}
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                setLinkingSourceId(node.id);
                                            }}
                                            sx={{
                                                position: 'absolute',
                                                width: 8,
                                                height: 8,
                                                borderRadius: '50%',
                                                backgroundColor: node.color || '#6366F1',
                                                border: '2px solid white',
                                                cursor: 'crosshair',
                                                zIndex: 20,
                                                ...pos
                                            }}
                                        />
                                    ))}
                                </Box>
                            ) : (
                                <Box
                                    onMouseDown={(e) => {
                                        if (isConnectionMode) return;
                                        e.stopPropagation();
                                        setDraggingNodeId(node.id);
                                        setHasMoved(false);
                                        setLastMousePos({ x: e.clientX, y: e.clientY });
                                        handleNodeClick(e, node.id);
                                    }}
                                    onDoubleClick={(e) => {
                                        e.stopPropagation();
                                        if (mode === 'select') onFocusNode(node.id);
                                    }}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        if (isConnectionMode) {
                                            if (!linkingSourceId) {
                                                setLinkingSourceId(node.id);
                                            } else if (linkingSourceId !== node.id) {
                                                onConnectNodes(linkingSourceId, node.id);
                                                setLinkingSourceId(null);
                                                onToggleConnectionMode(false);
                                            }
                                        }
                                    }}
                                    sx={{
                                        width: 80,
                                        height: 80,
                                        borderRadius: '50%',
                                        backgroundColor: 'white',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        cursor: mode === 'hand' ? 'grab' : (isConnectionMode ? 'crosshair' : 'pointer'),
                                        border: isPotentialTarget ? '2px solid #0096FF' : 'none',
                                        boxShadow: isSelected || isPreviewSelected
                                            ? '0 0 0 4px rgba(0, 150, 255, 0.2), 0 8px 24px rgba(0,0,0,0.1)'
                                            : (linkingSourceId === node.id ? '0 0 0 4px #0096FF' : '0 4px 12px rgba(0,0,0,0.08)'),
                                        transition: 'box-shadow 0.2s',
                                        '&:hover': {
                                            transform: draggingNodeId === node.id ? 'none' : 'scale(1.05)',
                                            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                                        },
                                        '&:active': { cursor: mode === 'hand' ? 'grabbing' : 'default' },
                                        position: 'relative',
                                    }}
                                >
                                    {node.icon === 'slack' && <Box sx={{ fontSize: '32px' }}>💬</Box>}
                                    {node.icon === 'spotify' && <Box sx={{ fontSize: '32px' }}>🎵</Box>}
                                    {node.icon === 'pdf' && <Box sx={{ fontSize: '32px' }}>📄</Box>}
                                    {node.icon === 'mp4' && <Box sx={{ fontSize: '32px' }}>📺</Box>}
                                    {node.icon === 'mp3' && <Box sx={{ fontSize: '32px' }}>📻</Box>}
                                    {!['slack', 'spotify', 'pdf', 'mp4', 'mp3'].includes(node.icon || '') && <Box sx={{ fontSize: '32px' }}>📄</Box>}

                                    {isSelected && !isConnectionMode && (
                                        <Box
                                            sx={{
                                                position: 'absolute',
                                                inset: 0,
                                                border: '2px solid transparent',
                                                borderTopColor: '#0096FF',
                                                borderRadius: '50%',
                                                animation: 'spin 2s linear infinite',
                                            }}
                                        />
                                    )}

                                    {/* Connection Anchors */}
                                    {isConnectionMode && ANCHOR_POSITIONS.map((pos, idx) => (
                                        <Box
                                            key={idx}
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                setLinkingSourceId(node.id);
                                            }}
                                            sx={{
                                                position: 'absolute',
                                                width: 10,
                                                height: 10,
                                                borderRadius: '50%',
                                                backgroundColor: '#0096FF',
                                                border: '2px solid white',
                                                cursor: 'crosshair',
                                                zIndex: 20,
                                                ...pos,
                                                '&:hover': {
                                                    transform: `${pos.transform || ''} scale(1.3)`,
                                                    backgroundColor: '#007ACC'
                                                }
                                            }}
                                        />
                                    ))}
                                </Box>
                            )}

                            {/* Node Label */}
                            <Typography
                                variant="caption"
                                sx={{
                                    position: 'absolute',
                                    top: node.type === 'insight' ? 110 : 90,
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    whiteSpace: 'nowrap',
                                    backgroundColor: 'rgba(255,255,255,0.8)',
                                    px: 1,
                                    borderRadius: 1,
                                    fontWeight: 500,
                                    color: 'text.secondary'
                                }}
                            >
                                {node.type === 'insight' ? 'From PDF' : node.name}
                            </Typography>

                            {/* AI Mapping Prompt Overlay */}
                            {mappingPromptNodeId === node.id && (
                                <Paper
                                    elevation={12}
                                    sx={{
                                        position: 'absolute',
                                        left: 100,
                                        top: 0,
                                        width: 320,
                                        p: 2,
                                        borderRadius: 3,
                                        bgcolor: '#1E293B',
                                        color: 'white',
                                        zIndex: 100,
                                        animation: 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
                                    }}
                                >
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                                        <Sparkles size={18} color="#FACC15" />
                                        <Typography variant="subtitle2" fontWeight={700}>AI Intelligent Mapping</Typography>
                                    </Box>
                                    <Typography variant="caption" sx={{ display: 'block', mb: 1.5, opacity: 0.7 }}>
                                        What kind of relationship graph would you like to extract from this document?
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                        <input
                                            autoFocus
                                            value={promptValue}
                                            onChange={(e) => setPromptValue(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' && promptValue.trim()) {
                                                    onAIMapping(node.id, promptValue);
                                                    setPromptValue('');
                                                }
                                            }}
                                            placeholder="e.g. Character relationships, API logic..."
                                            style={{
                                                flex: 1,
                                                background: 'rgba(255,255,255,0.1)',
                                                border: '1px solid rgba(255,255,255,0.2)',
                                                borderRadius: '8px',
                                                padding: '8px 12px',
                                                color: 'white',
                                                fontSize: '0.85rem',
                                                outline: 'none'
                                            }}
                                        />
                                        <IconButton
                                            size="small"
                                            onClick={() => {
                                                if (promptValue.trim()) {
                                                    onAIMapping(node.id, promptValue);
                                                    setPromptValue('');
                                                }
                                            }}
                                            sx={{ color: '#FACC15' }}
                                        >
                                            <Send size={18} />
                                        </IconButton>
                                    </Box>
                                </Paper>
                            )}
                        </Box>
                    );
                })}
            </Box>

            {/* Empty State / Guided Start */}
            {nodes.length === 0 && (
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
                        pointerEvents: 'none' // Allow pass-through for background pan, but we'll enable pointer-events on children
                    }}
                >
                    {availableFiles && availableFiles.length > 0 ? (
                        <Box sx={{
                            pointerEvents: 'auto',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: 3,
                            animation: 'fadeIn 0.5s ease-out'
                        }}>
                            {/* Inspiration Dock - CENTERED */}
                            <Box sx={{ position: 'relative' }}>
                                {/* Mini App Launcher Popover (Shared Logic) */}
                                {showMoreActions && (
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
                                            zIndex: 10
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
                                                    // For prototype, just trigger a map action or similar
                                                    onSmartStart?.(availableFiles[0].id, 'map');
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
                                        gap: 2
                                    }}
                                >
                                    {/* Action 1: Summary */}
                                    <Tooltip title="Generate Executive Summary" placement="top" arrow>
                                        <IconButton
                                            onClick={() => onSmartStart?.(availableFiles[0].id, 'summarize')}
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
                                            onClick={() => onSmartStart?.(availableFiles[0].id, 'map')}
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
                                </Paper>
                            </Box>
                        </Box>
                    ) : (
                        <Box sx={{ textAlign: 'center', opacity: 0.4 }}>
                            <Box sx={{ fontSize: '64px', mb: 2 }}>📂</Box>
                            <Typography variant="h5" fontWeight={600}>Drag files here to start</Typography>
                            <Typography variant="body2">Scroll to zoom, drag background to pan</Typography>
                        </Box>
                    )}
                </Box>
            )}

            <style jsx global>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translate(-50%, -40%); }
                    to { opacity: 1; transform: translate(-50%, -50%); }
                }
                @keyframes floatUp {
                    from { opacity: 0; transform: translateX(-50%) translateY(10px) scale(0.95); }
                    to { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
                }
                @keyframes slideIn {
                    from { opacity: 0; transform: translateX(-10px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                @keyframes pulse {
                    0% { opacity: 0.8; transform: scale(0.98); }
                    50% { opacity: 1; transform: scale(1); }
                    100% { opacity: 0.8; transform: scale(0.98); }
                }
                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-4px); }
                }
                @keyframes dash {
                    to { stroke-dashoffset: -20; }
                }
            `}</style>
        </Box>
    );
}
