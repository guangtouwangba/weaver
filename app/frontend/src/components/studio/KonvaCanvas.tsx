'use client';

/**
 * High-performance Konva.js-powered Canvas
 * Replaces DOM-based rendering with HTML5 Canvas for better performance
 */

import {
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
  useLayoutEffect,
} from 'react';
import {
  Stage,
  Layer,
  Group,
  Rect,
  Text,
  Line,
  Circle,
  Image,
  Path,
  RegularPolygon,
} from 'react-konva';

interface URLImageProps {
  src?: string;
  x: number;
  y: number;
  width: number;
  height: number;
  opacity?: number;
  cornerRadius?: number | number[];
}

const URLImage = ({
  src,
  x,
  y,
  width,
  height,
  opacity,
  cornerRadius,
}: URLImageProps) => {
  const [image, setImage] = useState<HTMLImageElement | undefined>(undefined);

  useEffect(() => {
    if (!src) {
      return;
    }

    // Resolve relative API paths to full URLs
    let fullSrc = src;
    if (src.startsWith('/api/')) {
      // Get base URL from environment or default to localhost
      const baseUrl =
        process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      fullSrc = `${baseUrl}${src}`;
    }

    const img = new window.Image();
    img.crossOrigin = 'anonymous';
    img.src = fullSrc;
    img.onload = () => {
      if (img.width > 0 && img.height > 0) {
        setImage(img);
      }
    };
    img.onerror = () => {
      // Silently fail - the component will simply not render an image
    };
  }, [src]);

  return image ? (
    <Image
      x={x}
      y={y}
      width={width}
      height={height}
      image={image}
      opacity={opacity}
      cornerRadius={cornerRadius}
    />
  ) : null;
};

import Konva from 'konva';
import { Menu, MenuItem, TextField } from '@/components/ui/composites';
import {
  Chip,
  IconButton,
  Button,
  Spinner,
  Stack,
  Surface,
  Text as UiText,
} from '@/components/ui/primitives';
import { colors } from '@/components/ui/tokens';
import {
  ArrowUpwardIcon,
  CloseIcon,
  CheckIcon,
  LayersIcon,
  AutoAwesomeIcon,
  SearchIcon,
  EditIcon,
  DeleteIcon,
} from '@/components/ui/icons';
import { useNotification } from '@/contexts/NotificationContext';
import { useStudio } from '@/contexts/StudioContext';
import { useCanvasActions } from '@/hooks/useCanvasActions';
import { ToolMode } from './CanvasToolbar';
import InspirationDock from './InspirationDock';
import IntentMenu, { IntentAction } from './IntentMenu';
import CanvasContextMenu from './CanvasContextMenu';
import LinkTypeDialog, { LinkTypeDialogProps } from './LinkTypeDialog';
import GenerationOutputsOverlay from './GenerationOutputsOverlay';
import {
  CanvasNode,
  CanvasEdge,
  canvasApi,
  outputsApi,
  OutputType,
} from '@/lib/api';
import {
  getAnchorPoint,
  resolveAnchor,
  getStraightPath,
  getBezierPath,
  getOrthogonalPath,
  getArrowPoints,
  getAllAnchorPoints,
  AnchorDirection,
} from '@/lib/connectionUtils';
import { useSpatialIndex, SpatialItem } from '@/hooks/useSpatialIndex';
import { useViewportCulling } from '@/hooks/useViewportCulling';
import GridBackground from './canvas/GridBackground';
import SynthesisModeMenu, { SynthesisMode } from './canvas/SynthesisModeMenu';
import NoteEditor, { NoteData } from './NoteEditor';
import ArticleEditor, { ArticleData } from './ArticleEditor';
import ActionListEditor, { ActionListData } from './ActionListEditor';
import { MindMapEditor } from './mindmap/MindMapEditor';
import { MindmapData, SummaryData } from '@/lib/api';
import useOutputWebSocket from '@/hooks/useOutputWebSocket';
import WebPageReaderModal from '@/components/studio/WebPageReaderModal';
import YouTubePlayerModal from '@/components/studio/YouTubePlayerModal';
import { useFpsMonitor } from '@/components/dev/DevFpsMonitor';

interface Viewport {
  x: number;
  y: number;
  scale: number;
}

interface KonvaCanvasProps {
  nodes?: CanvasNode[];
  edges?: CanvasEdge[];
  viewport?: Viewport;
  currentView?: 'free' | 'thinking';
  onNodesChange?: (nodes: CanvasNode[]) => void;
  onEdgesChange?: (edges: CanvasEdge[]) => void;
  onViewportChange?: (viewport: Viewport) => void;
  onNodeAdd?: (node: Partial<CanvasNode>) => void;
  highlightedNodeId?: string | null; // Node to highlight (for navigation from chat)
  onNodeClick?: (node: CanvasNode) => void; // Callback when node is clicked
  onNodeDoubleClick?: (node: CanvasNode) => void; // Phase 1: Callback for drill-down (opening source)
  onOpenSource?: (sourceId: string, pageNumber?: number) => void; // Phase 1: Navigate to source document
  toolMode?: ToolMode; // New prop
  onToolChange?: (tool: ToolMode) => void; // Callback to change tool mode
  onOpenImport?: () => void; // For Context Menu Import
  onSelectionChange?: (count: number) => void; // Callback when selection changes
}

// Node style configuration based on type
const getNodeStyle = (
  type: string,
  subType?: string,
  fileType?: string,
  isDraft?: boolean,
  branchType?: string
) => {
  const styles: Record<
    string,
    {
      borderColor: string;
      borderStyle: 'solid' | 'dashed';
      bgColor: string;
      icon: string;
      topBarColor: string;
    }
  > = {
    // === Source Node Types (The Portal) ===
    source_pdf: {
      borderColor: '#DC2626', // Red - PDF documents
      borderStyle: 'solid',
      bgColor: '#FEF2F2', // Light red
      icon: '📕', // Book/PDF icon
      topBarColor: '#DC2626',
    },
    source_markdown: {
      borderColor: '#3B82F6', // Blue - Markdown
      borderStyle: 'solid',
      bgColor: '#EFF6FF', // Light blue
      icon: '📝', // Markdown/Note icon
      topBarColor: '#3B82F6',
    },
    source_web: {
      borderColor: '#0D9488', // Teal - Web pages
      borderStyle: 'solid',
      bgColor: '#F0FDFA', // Light teal
      icon: '🌐', // Globe icon
      topBarColor: '#0D9488',
    },
    source_text: {
      borderColor: '#78716C', // Stone - Plain text
      borderStyle: 'solid',
      bgColor: '#FAFAF9', // Light stone
      icon: '📄', // Document icon
      topBarColor: '#78716C',
    },
    source_youtube: {
      borderColor: '#FF0000', // YouTube Red
      borderStyle: 'solid',
      bgColor: '#FEE2E2', // Light red
      icon: '▶️', // Play button
      topBarColor: '#FF0000',
    },
    source_video: {
      borderColor: '#8B5CF6', // Purple - Generic video
      borderStyle: 'solid',
      bgColor: '#F5F3FF', // Light purple
      icon: '🎬', // Video icon
      topBarColor: '#8B5CF6',
    },
    source_bilibili: {
      borderColor: '#00A1D6', // Bilibili Blue
      borderStyle: 'solid',
      bgColor: '#E0F7FA', // Light cyan
      icon: '📺', // TV icon
      topBarColor: '#00A1D6',
    },
    source_douyin: {
      borderColor: '#000000', // Douyin Black
      borderStyle: 'solid',
      bgColor: '#F5F5F5', // Light gray
      icon: '🎵', // Music note
      topBarColor: '#000000',
    },
    // === Thinking Path Node Types (User Conversation Visualization) ===
    question: {
      borderColor: '#3B82F6', // Blue
      borderStyle: 'dashed',
      bgColor: '#EFF6FF', // Light blue
      icon: '❓', // Question mark
      topBarColor: '#3B82F6',
    },
    answer: {
      borderColor: '#10B981', // Green
      borderStyle: 'solid',
      bgColor: '#F0FDF4', // Light green
      icon: '💬', // Chat bubble
      topBarColor: '#10B981',
    },
    insight: {
      borderColor: '#D97706', // Amber/Gold
      borderStyle: 'solid',
      bgColor: '#FFFBEB', // Light yellow
      icon: '💡', // Lightbulb
      topBarColor: '#D97706',
    },
    // === Thinking Graph Node Types (Dynamic Mind Map) ===
    thinking_step: {
      borderColor: '#3B82F6', // Blue for finalized
      borderStyle: 'solid',
      bgColor: '#EFF6FF', // Light blue
      icon: '🧠', // Brain icon
      topBarColor: '#3B82F6',
    },
    thinking_step_draft: {
      borderColor: '#8B5CF6', // Purple for draft
      borderStyle: 'dashed',
      bgColor: '#F5F3FF', // Light purple
      icon: '⏳', // Hourglass for pending
      topBarColor: '#8B5CF6',
    },
    thinking_branch: {
      borderColor: '#F59E0B', // Yellow/Gold for branches
      borderStyle: 'solid',
      bgColor: '#FFFBEB', // Light yellow
      icon: '🔀', // Branch icon
      topBarColor: '#F59E0B',
    },
    thinking_branch_question: {
      borderColor: '#3B82F6', // Blue for question branches
      borderStyle: 'dashed',
      bgColor: '#EFF6FF', // Light blue
      icon: '❓', // Question mark
      topBarColor: '#3B82F6',
    },
    thinking_branch_alternative: {
      borderColor: '#10B981', // Green for alternative branches
      borderStyle: 'solid',
      bgColor: '#F0FDF4', // Light green
      icon: '🔄', // Alternative icon
      topBarColor: '#10B981',
    },
    thinking_branch_counterargument: {
      borderColor: '#EF4444', // Red for counterargument branches
      borderStyle: 'solid',
      bgColor: '#FEF2F2', // Light red
      icon: '⚡', // Counterargument icon
      topBarColor: '#EF4444',
    },
    // === Generated Output Node Types ===
    summary_output: {
      borderColor: '#8B5CF6', // Purple for AI outputs
      borderStyle: 'solid',
      bgColor: '#FAF5FF', // Light purple
      icon: '⚡', // Zap icon for summary
      topBarColor: '#8B5CF6',
    },
    mindmap_output: {
      borderColor: '#0D9488', // Teal for mindmap
      borderStyle: 'solid',
      bgColor: '#F0FDFA', // Light teal
      icon: '🔀', // Network icon for mindmap
      topBarColor: '#0D9488',
    },
    // === Other Node Types ===
    knowledge: {
      borderColor: '#E7E5E4',
      borderStyle: 'solid',
      bgColor: '#FFFFFF',
      icon: '📄',
      topBarColor: '#E7E5E4',
    },
    manual: {
      borderColor: '#E7E5E4',
      borderStyle: 'solid',
      bgColor: '#FFFFFF',
      icon: '✏️',
      topBarColor: '#A8A29E',
    },
    conclusion: {
      borderColor: '#8B5CF6', // Purple
      borderStyle: 'solid',
      bgColor: '#F5F3FF', // Light purple
      icon: '✨',
      topBarColor: '#8B5CF6',
    },
    // === Inspiration Dock Generated Types ===
    podcast: {
      borderColor: '#8B5CF6', // Purple
      borderStyle: 'solid',
      bgColor: '#F5F3FF', // Light purple
      icon: '🎙️',
      topBarColor: '#8B5CF6',
    },
    quiz: {
      borderColor: '#F97316', // Orange
      borderStyle: 'solid',
      bgColor: '#FFF7ED', // Light orange
      icon: '❓',
      topBarColor: '#F97316',
    },
    timeline: {
      borderColor: '#EC4899', // Pink
      borderStyle: 'solid',
      bgColor: '#FDF2F8', // Light pink
      icon: '📅',
      topBarColor: '#EC4899',
    },
    compare: {
      borderColor: '#0D9488', // Teal
      borderStyle: 'solid',
      bgColor: '#F0FDFA', // Light teal
      icon: '⚖️',
      topBarColor: '#0D9488',
    },
    // === Sticky Note ===
    sticky: {
      borderColor: '#FCD34D', // Amber 300
      borderStyle: 'solid',
      bgColor: '#FEF3C7', // Amber 100
      icon: '📝',
      topBarColor: '#FCD34D',
    },
    // === Magic Cursor Super Cards ===
    super_article: {
      borderColor: '#667eea', // Purple/Indigo - Article
      borderStyle: 'solid',
      bgColor: '#FAFBFF', // Light purple-blue
      icon: '📄', // Document icon
      topBarColor: '#667eea',
    },
    super_action_list: {
      borderColor: '#f59e0b', // Amber - Action List
      borderStyle: 'solid',
      bgColor: '#FFFCF5', // Light amber
      icon: '✅', // Checklist icon
      topBarColor: '#f59e0b',
    },
  };

  // Handle source nodes with specific file types
  if (subType === 'source' && fileType) {
    const sourceKey = `source_${fileType}`;
    if (styles[sourceKey]) {
      return styles[sourceKey];
    }
    // Fallback for unknown source types
    return styles.source_text;
  }

  // Handle thinking_step nodes with draft status
  if (type === 'thinking_step') {
    if (isDraft) {
      return styles.thinking_step_draft;
    }
    return styles.thinking_step;
  }

  // Handle thinking_branch nodes with branch type
  if (type === 'thinking_branch') {
    if (branchType === 'question') {
      return styles.thinking_branch_question;
    }
    if (branchType === 'alternative') {
      return styles.thinking_branch_alternative;
    }
    if (branchType === 'counterargument') {
      return styles.thinking_branch_counterargument;
    }
    return styles.thinking_branch;
  }

  // Default to knowledge style for backward compatibility
  return styles[type] || styles.knowledge;
};

// --- Icon Paths ---
const PDF_ICON_BODY =
  'M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z';
const PDF_ICON_FOLD = 'M14 2V8H20';
const PLAY_ICON = 'M8 5v14l11-7z';
const YOUTUBE_ICON =
  'M21.582 7.186a2.506 2.506 0 0 0-1.768-1.768C18.254 5 12 5 12 5s-6.254 0-7.814.418c-.86.23-1.538.908-1.768 1.768C2 8.746 2 12 2 12s0 3.254.418 4.814c.23.86.908 1.538 1.768 1.768C5.746 19 12 19 12 19s6.254 0 7.814-.418a2.506 2.506 0 0 0 1.768-1.768C22 15.254 22 12 22 12s0-3.254-.418-4.814zM10 15V9l5.196 3L10 15z';
const EXTERNAL_LINK_ICON =
  'M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3';
const LINK_ICON =
  'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71';
const MORE_ICON =
  'M12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2zM19 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2zM5 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z';
const GLOBE_ICON =
  'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z';

// --- Helper: Format duration ---
const formatDuration = (seconds?: number): string => {
  if (!seconds) return '';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// --- Helper: Get channel initials ---
const getChannelInitials = (channelName?: string): string => {
  if (!channelName) return '?';
  const words = channelName.split(' ').filter((w) => w.length > 0);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return channelName.substring(0, 2).toUpperCase();
};

// --- Video Platform Configuration ---
const getVideoPlatformConfig = (fileType?: string) => {
  const configs: Record<
    string,
    {
      name: string;
      icon: string;
      primaryColor: string;
      avatarColor: string;
    }
  > = {
    youtube: {
      name: 'YouTube',
      icon: YOUTUBE_ICON,
      primaryColor: '#FF0000',
      avatarColor: '#8B5CF6',
    },
    bilibili: {
      name: 'Bilibili',
      icon: YOUTUBE_ICON, // Using same icon, could be replaced with Bilibili icon
      primaryColor: '#00A1D6',
      avatarColor: '#00A1D6',
    },
    douyin: {
      name: 'Douyin',
      icon: YOUTUBE_ICON,
      primaryColor: '#000000',
      avatarColor: '#FE2C55',
    },
    video: {
      name: 'Video',
      icon: YOUTUBE_ICON,
      primaryColor: '#8B5CF6',
      avatarColor: '#8B5CF6',
    },
  };
  return configs[fileType || 'youtube'] || configs.youtube;
};

// --- Video Card (YouTube/Bilibili/Douyin style) ---
const VideoCard = ({
  node,
  width,
  isSelected,
  isHighlighted,
}: {
  node: CanvasNode;
  width: number;
  isSelected: boolean;
  isHighlighted?: boolean;
}) => {
  const meta = node.fileMetadata;
  const fileType = meta?.fileType || 'youtube';
  const platformConfig = getVideoPlatformConfig(fileType);

  const thumbUrl = meta?.thumbnailUrl;
  const channelName = meta?.channelName || 'Unknown Channel';
  const viewCount = meta?.viewCount || '';
  const publishedAt = meta?.publishedAt || '';
  const duration = formatDuration(meta?.duration);
  const sourceUrl = meta?.sourceUrl || '';

  // Card dimensions - larger for better visibility
  const padding = 16;
  const headerHeight = 48;
  const thumbWidth = width - padding * 2;
  const thumbHeight = (thumbWidth * 9) / 16; // 16:9 aspect ratio
  const infoHeight = 90;
  const linkHeight = 44;
  const cardHeight = headerHeight + thumbHeight + infoHeight + linkHeight + 20;

  const strokeColor = isHighlighted
    ? '#3B82F6'
    : isSelected
      ? platformConfig.primaryColor
      : '#E5E7EB';
  const strokeWidth = isSelected || isHighlighted ? 2 : 1;

  // Build meta string: "ChannelName • 24K views • 2 days ago"
  const metaParts = [channelName];
  if (viewCount) metaParts.push(viewCount);
  if (publishedAt) metaParts.push(publishedAt);
  const metaString = metaParts.join(' • ');

  return (
    <Group>
      {/* Main Card */}
      <Rect
        width={width}
        height={cardHeight}
        fill="white"
        cornerRadius={16}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        shadowColor="rgba(0, 0, 0, 0.08)"
        shadowBlur={12}
        shadowOffsetY={4}
      />

      {/* === Header === */}
      <Group x={padding} y={14}>
        {/* Platform Logo */}
        <Group scaleX={1} scaleY={1}>
          <Path data={platformConfig.icon} fill={platformConfig.primaryColor} />
        </Group>
        <Text
          x={32}
          y={4}
          text={platformConfig.name}
          fontSize={15}
          fontStyle="600"
          fill="#1F2937"
          fontFamily="Inter, system-ui, sans-serif"
        />
      </Group>

      {/* Header Right Icons */}
      <Group x={width - 60} y={14}>
        {/* External Link Icon */}
        <Group scaleX={0.85} scaleY={0.85}>
          <Path
            data={EXTERNAL_LINK_ICON}
            stroke="#9CA3AF"
            strokeWidth={2}
            fill="transparent"
          />
        </Group>
        {/* More Icon */}
        <Group x={30} scaleX={0.85} scaleY={0.85}>
          <Path data={MORE_ICON} fill="#9CA3AF" />
        </Group>
      </Group>

      {/* === Thumbnail Area === */}
      <Group x={padding} y={headerHeight}>
        {/* Thumbnail Background */}
        <Rect
          width={thumbWidth}
          height={thumbHeight}
          fill="#1F2937"
          cornerRadius={12}
        />

        {/* Thumbnail Image */}
        {thumbUrl && (
          <URLImage
            src={thumbUrl}
            width={thumbWidth}
            height={thumbHeight}
            cornerRadius={12}
          />
        )}

        {/* Play Button Overlay (centered) - larger size */}
        <Group x={thumbWidth / 2 - 32} y={thumbHeight / 2 - 32}>
          {/* Outer circle with platform color */}
          <Circle
            x={32}
            y={32}
            radius={32}
            fill={platformConfig.primaryColor}
            opacity={0.9}
          />
          {/* Inner play triangle */}
          <RegularPolygon
            x={36}
            y={32}
            sides={3}
            radius={16}
            rotation={90}
            fill="white"
          />
        </Group>

        {/* Duration Badge (bottom-right) - larger */}
        {duration && (
          <Group x={thumbWidth - 56} y={thumbHeight - 32}>
            <Rect
              width={48}
              height={24}
              fill="rgba(0, 0, 0, 0.8)"
              cornerRadius={4}
            />
            <Text
              x={8}
              y={5}
              text={duration}
              fontSize={13}
              fontStyle="600"
              fill="white"
              fontFamily="Inter, system-ui, sans-serif"
            />
          </Group>
        )}
      </Group>

      {/* === Video Info Section === */}
      <Group x={padding} y={headerHeight + thumbHeight + 16}>
        {/* Channel Avatar - larger */}
        <Circle x={22} y={22} radius={22} fill={platformConfig.avatarColor} />
        <Text
          x={9}
          y={13}
          width={26}
          text={getChannelInitials(channelName)}
          fontSize={13}
          fontStyle="bold"
          fill="white"
          align="center"
          fontFamily="Inter, system-ui, sans-serif"
        />

        {/* Title & Meta */}
        <Group x={54}>
          <Text
            text={node.title}
            width={thumbWidth - 64}
            height={40}
            fontSize={15}
            fontStyle="600"
            fill="#1F2937"
            wrap="word"
            ellipsis={true}
            fontFamily="Inter, system-ui, sans-serif"
          />
          <Text
            y={44}
            text={metaString}
            width={thumbWidth - 64}
            fontSize={13}
            fill="#6B7280"
            ellipsis={true}
            fontFamily="Inter, system-ui, sans-serif"
          />
        </Group>
      </Group>

      {/* === URL Link Section === */}
      <Group x={padding} y={headerHeight + thumbHeight + infoHeight + 8}>
        {/* Separator Line */}
        <Line
          points={[-padding + 1, -8, width - padding - 1, -8]}
          stroke="#F3F4F6"
          strokeWidth={1}
        />

        {/* Link Icon */}
        <Group y={6} scaleX={0.7} scaleY={0.7}>
          <Path
            data={LINK_ICON}
            stroke="#3B82F6"
            strokeWidth={2}
            fill="transparent"
          />
        </Group>

        {/* URL Text */}
        <Text
          x={22}
          y={8}
          text={
            sourceUrl.length > 45
              ? sourceUrl.substring(0, 45) + '...'
              : sourceUrl
          }
          fontSize={12}
          fill="#3B82F6"
          fontFamily="Inter, system-ui, sans-serif"
        />
      </Group>
    </Group>
  );
};

// --- Web Page Card (for web/URL types) ---
const WebPageCard = ({
  node,
  width,
  isSelected,
  isHighlighted,
}: {
  node: CanvasNode;
  width: number;
  isSelected: boolean;
  isHighlighted?: boolean;
}) => {
  const meta = node.fileMetadata;
  const sourceUrl = meta?.sourceUrl || '';
  const title = node.title || 'Web Page';
  const description = node.content || '';
  const thumbnailUrl = meta?.thumbnailUrl;

  // Extract domain from URL for display
  const getDomain = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname.replace('www.', '');
    } catch {
      return url;
    }
  };

  // Get favicon URL (using Google's favicon service as it's CORS-friendly)
  const getFaviconUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return `https://www.google.com/s2/favicons?domain=${urlObj.hostname}&sz=64`;
    } catch {
      return '';
    }
  };

  const domain = getDomain(sourceUrl);
  const faviconUrl = getFaviconUrl(sourceUrl);

  // Card dimensions
  const padding = 16;
  const headerHeight = 48;

  // Calculate heights
  const thumbWidth = width - padding * 2;
  // Use 16:9 for thumbnail if available
  const thumbHeight = thumbnailUrl ? (thumbWidth * 9) / 16 : 0;

  // Content area height adjustments
  // If thumbnail exists, reduce text area slightly
  const textContentHeight = thumbnailUrl ? 130 : 160;
  const footerHeight = 50;

  const cardHeight =
    headerHeight +
    (thumbnailUrl ? thumbHeight + 16 : 0) +
    textContentHeight +
    footerHeight;

  const primaryColor = '#0D9488'; // Teal for web
  const strokeColor = isHighlighted
    ? '#3B82F6'
    : isSelected
      ? primaryColor
      : '#E5E7EB';
  const strokeWidth = isSelected || isHighlighted ? 2 : 1;

  return (
    <Group>
      {/* Main Card */}
      <Rect
        width={width}
        height={cardHeight}
        fill="white"
        cornerRadius={16}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        shadowColor="rgba(0, 0, 0, 0.08)"
        shadowBlur={12}
        shadowOffsetY={4}
      />

      {/* === Header === */}
      <Group x={padding} y={14}>
        {/* Globe Icon */}
        <Group scaleX={0.9} scaleY={0.9}>
          <Path data={GLOBE_ICON} fill={primaryColor} />
        </Group>
        <Text
          x={28}
          y={4}
          text="Web Page"
          fontSize={14}
          fontStyle="600"
          fill="#1F2937"
          fontFamily="Inter, system-ui, sans-serif"
        />
      </Group>

      {/* Header Right Icons */}
      <Group x={width - 60} y={14}>
        <Group scaleX={0.85} scaleY={0.85}>
          <Path
            data={EXTERNAL_LINK_ICON}
            stroke="#9CA3AF"
            strokeWidth={2}
            fill="transparent"
          />
        </Group>
        <Group x={30} scaleX={0.85} scaleY={0.85}>
          <Path data={MORE_ICON} fill="#9CA3AF" />
        </Group>
      </Group>

      {/* === Thumbnail Area (Optional) === */}
      {thumbnailUrl && (
        <Group x={padding} y={headerHeight}>
          {/* Placeholder Background (Globe) - Shows while loading or if error */}
          <Group>
            <Rect
              width={thumbWidth}
              height={thumbHeight}
              fill="#F0FDFA"
              cornerRadius={8}
            />
            <Group
              x={thumbWidth / 2 - 20}
              y={thumbHeight / 2 - 20}
              opacity={0.3}
            >
              <Path
                data={GLOBE_ICON}
                fill={primaryColor}
                scaleX={2}
                scaleY={2}
              />
            </Group>
          </Group>

          {/* Actual Thumbnail */}
          <URLImage
            src={thumbnailUrl}
            width={thumbWidth}
            height={thumbHeight}
            cornerRadius={8}
          />
        </Group>
      )}

      {/* === Content Area === */}
      <Group
        x={padding}
        y={headerHeight + (thumbnailUrl ? thumbHeight + 16 : 0)}
      >
        {/* Content Background (Only if no thumbnail, to keep it clean) */}
        {!thumbnailUrl && (
          <Rect
            x={-padding + 1}
            y={0}
            width={width - 2}
            height={textContentHeight}
            fill="#F0FDFA"
          />
        )}

        {/* Favicon and Domain */}
        <Group y={16}>
          {/* Favicon background circle */}
          <Rect
            width={32}
            height={32}
            fill="white"
            cornerRadius={8}
            stroke="#E5E7EB"
            strokeWidth={1}
          />
          {/* Favicon image */}
          {faviconUrl && (
            <URLImage src={faviconUrl} x={4} y={4} width={24} height={24} />
          )}

          {/* Domain name */}
          <Text
            x={40}
            y={8}
            text={domain}
            fontSize={12}
            fontStyle="500"
            fill={primaryColor}
            fontFamily="Inter, system-ui, sans-serif"
          />
        </Group>

        {/* Title */}
        <Text
          y={56}
          width={width - padding * 2}
          text={title.length > 60 ? title.substring(0, 60) + '...' : title}
          fontSize={15}
          fontStyle="600"
          fill="#1F2937"
          fontFamily="Inter, system-ui, sans-serif"
          lineHeight={1.3}
          wrap="word"
          ellipsis={true}
          height={42}
        />

        {/* Description snippet */}
        {description && (
          <Text
            y={102}
            width={width - padding * 2}
            height={textContentHeight - 102}
            text={
              description.length > 120
                ? description.substring(0, 120) + '...'
                : description
            }
            fontSize={12}
            fill="#6B7280"
            fontFamily="Inter, system-ui, sans-serif"
            lineHeight={1.4}
            wrap="word"
            ellipsis={true}
          />
        )}
      </Group>

      {/* === Footer === */}
      <Group
        x={padding}
        y={
          headerHeight +
          (thumbnailUrl ? thumbHeight + 16 : 0) +
          textContentHeight
        }
      >
        {/* Separator Line */}
        <Line
          points={[-padding + 1, 0, width - padding - 1, 0]}
          stroke="#E5E7EB"
          strokeWidth={1}
        />

        {/* Link Icon */}
        <Group y={16} scaleX={0.65} scaleY={0.65}>
          <Path
            data={LINK_ICON}
            stroke="#0D9488"
            strokeWidth={2}
            fill="transparent"
          />
        </Group>

        {/* URL Text */}
        <Text
          x={20}
          y={18}
          width={width - padding * 2 - 24}
          text={
            sourceUrl.length > 50
              ? sourceUrl.substring(0, 50) + '...'
              : sourceUrl
          }
          fontSize={11}
          fill="#0D9488"
          fontFamily="Inter, system-ui, sans-serif"
          ellipsis={true}
        />
      </Group>
    </Group>
  );
};

// --- Source Type Configuration (for non-video types) ---
const getSourceTypeConfig = (fileType?: string) => {
  const configs: Record<
    string,
    {
      label: string;
      icon: string;
      primaryColor: string;
      bgColor: string;
      iconBgColor: string;
      bodyBgColor: string;
      metaLabel: (meta: CanvasNode['fileMetadata']) => string;
    }
  > = {
    pdf: {
      label: 'PDF Document',
      icon: '📕',
      primaryColor: '#DC2626',
      bgColor: '#FEF2F2',
      iconBgColor: '#FEF2F2',
      bodyBgColor: '#FFF7ED',
      metaLabel: (meta) =>
        meta?.pageCount ? `${meta.pageCount} pages` : 'Unknown size',
    },
    markdown: {
      label: 'Markdown',
      icon: '📝',
      primaryColor: '#3B82F6',
      bgColor: '#EFF6FF',
      iconBgColor: '#EFF6FF',
      bodyBgColor: '#F8FAFC',
      metaLabel: () => 'Markdown Document',
    },
    web: {
      label: 'Web Page',
      icon: '🌐',
      primaryColor: '#0D9488',
      bgColor: '#F0FDFA',
      iconBgColor: '#F0FDFA',
      bodyBgColor: '#F0FDFA',
      metaLabel: () => 'Web Page',
    },
    text: {
      label: 'Text File',
      icon: '📄',
      primaryColor: '#78716C',
      bgColor: '#FAFAF9',
      iconBgColor: '#FAFAF9',
      bodyBgColor: '#FAFAF9',
      metaLabel: () => 'Text File',
    },
  };
  return configs[fileType || 'pdf'] || configs.pdf;
};

// --- Source Preview Card (Routes to appropriate card type) ---
const SourcePreviewCard = ({
  node,
  width,
  height,
  isSelected,
  isHighlighted,
  isActiveThinking,
}: {
  node: CanvasNode;
  width: number;
  height: number;
  isSelected: boolean;
  isHighlighted?: boolean;
  isActiveThinking?: boolean;
}) => {
  const fileType = node.fileMetadata?.fileType || 'pdf';
  const isVideoType = ['youtube', 'video', 'bilibili', 'douyin'].includes(
    fileType
  );
  const isWebType = fileType === 'web';

  // Use new video card for video types (YouTube, Bilibili, Douyin, etc.)
  if (isVideoType) {
    return (
      <VideoCard
        node={node}
        width={width}
        isSelected={isSelected}
        isHighlighted={isHighlighted}
      />
    );
  }

  // Use web page card for web/URL types
  if (isWebType) {
    return (
      <WebPageCard
        node={node}
        width={width}
        isSelected={isSelected}
        isHighlighted={isHighlighted}
      />
    );
  }

  // Original PDF/Document card for non-video types
  const thumbUrl = node.fileMetadata?.thumbnailUrl;
  const config = getSourceTypeConfig(fileType);

  const strokeColor = isActiveThinking
    ? '#8B5CF6'
    : isHighlighted
      ? '#3B82F6'
      : isSelected
        ? config.primaryColor
        : '#E7E5E4';
  const strokeWidth = isSelected || isHighlighted ? 2 : 1;
  const shadowBlur = isSelected ? 12 : 4;
  const shadowOpacity = isSelected ? 0.15 : 0.05;

  const displayHeight = Math.max(height, 320);

  return (
    <Group>
      {/* Main Card Container */}
      <Rect
        width={width}
        height={displayHeight}
        fill="white"
        cornerRadius={12}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        shadowColor="black"
        shadowBlur={shadowBlur}
        shadowOpacity={shadowOpacity}
        shadowOffsetY={4}
      />

      {/* Header */}
      <Group x={12} y={12}>
        {fileType === 'pdf' ? (
          <Group scaleX={0.7} scaleY={0.7}>
            <Path data={PDF_ICON_BODY} fill={config.primaryColor} />
            <Path
              data={PDF_ICON_FOLD}
              fill={config.primaryColor}
              fillOpacity={0.5}
            />
          </Group>
        ) : (
          <Text text={config.icon} fontSize={16} />
        )}
        <Text
          x={24}
          y={2}
          text={config.label}
          fontSize={12}
          fontStyle="bold"
          fill="#78716C"
          fontFamily="Inter, sans-serif"
        />
      </Group>

      {/* Header Separator */}
      <Line points={[0, 40, width, 40]} stroke="#F5F5F4" strokeWidth={1} />

      {/* Body */}
      <Rect
        x={1}
        y={40}
        width={width - 2}
        height={displayHeight - 90}
        fill={config.bodyBgColor}
        opacity={0.5}
      />

      {/* Thumbnail */}
      {thumbUrl ? (
        <Group x={(width - 120) / 2} y={55}>
          <Rect
            x={4}
            y={4}
            width={120}
            height={150}
            fill="black"
            opacity={0.1}
            cornerRadius={2}
          />
          <Rect width={120} height={150} fill="white" cornerRadius={2} />
          <URLImage src={thumbUrl} width={120} height={150} cornerRadius={2} />
        </Group>
      ) : (
        <Group x={(width - 100) / 2} y={60}>
          <Rect
            width={100}
            height={130}
            fill="white"
            stroke="#E7E5E4"
            dash={[4, 4]}
            cornerRadius={4}
          />
          <Text x={10} y={60} text="No Preview" fontSize={12} fill="#A8A29E" />
        </Group>
      )}

      {/* Footer */}
      <Line
        points={[0, displayHeight - 50, width, displayHeight - 50]}
        stroke="#F5F5F4"
        strokeWidth={1}
      />

      <Group x={12} y={displayHeight - 38}>
        <Rect
          width={28}
          height={28}
          fill={config.iconBgColor}
          cornerRadius={6}
        />
        {fileType === 'pdf' ? (
          <Group x={6} y={6} scaleX={0.7} scaleY={0.7}>
            <Path data={PDF_ICON_BODY} fill={config.primaryColor} />
          </Group>
        ) : (
          <Text x={6} y={4} text={config.icon} fontSize={14} />
        )}

        <Group x={36} y={-2}>
          <Text
            text={node.title}
            width={width - 60}
            ellipsis={true}
            fontSize={13}
            fontStyle="bold"
            fill="#292524"
            height={20}
          />
          <Text
            y={18}
            text={config.metaLabel(node.fileMetadata)}
            fontSize={10}
            fill="#78716C"
          />
        </Group>
      </Group>
    </Group>
  );
};

// --- Super Article Card (Magic Cursor Generated) ---
const SuperArticleCard = ({
  node,
  width,
  height,
  isSelected,
  isHighlighted,
}: {
  node: CanvasNode;
  width: number;
  height: number;
  isSelected: boolean;
  isHighlighted?: boolean;
}) => {
  // Parse article data from content
  let articleData: {
    title: string;
    sections: Array<{ heading: string; content: string }>;
  } | null = null;
  try {
    articleData = JSON.parse(node.content || '{}');
  } catch {
    articleData = null;
  }

  const borderColor = '#667eea';
  const bgColor = '#FAFBFF';

  // Get first section preview
  const firstSection = articleData?.sections?.[0];
  const sectionCount = articleData?.sections?.length || 0;
  const previewText =
    firstSection?.content?.substring(0, 150) || 'Article content...';

  return (
    <Group>
      {/* Card Background */}
      <Rect
        width={width}
        height={height}
        fill={bgColor}
        cornerRadius={12}
        stroke={
          isHighlighted ? '#3B82F6' : isSelected ? borderColor : '#E5E7EB'
        }
        strokeWidth={isSelected ? 2 : 1}
        shadowColor="rgba(102, 126, 234, 0.15)"
        shadowBlur={isSelected ? 16 : 8}
        shadowOffsetY={4}
      />

      {/* Top Accent Bar - Gradient effect with two rects */}
      <Rect
        y={0}
        width={width}
        height={5}
        fill={borderColor}
        cornerRadius={[12, 12, 0, 0]}
      />

      {/* Document Icon */}
      <Text x={12} y={14} text="📄" fontSize={16} />

      {/* Type Badge */}
      <Rect
        x={width - 60}
        y={12}
        width={48}
        height={20}
        fill="#EEF2FF"
        cornerRadius={10}
      />
      <Text
        x={width - 55}
        y={16}
        text="Article"
        fontSize={10}
        fontStyle="bold"
        fill={borderColor}
      />

      {/* Title */}
      <Text
        x={36}
        y={14}
        width={width - 105}
        text={articleData?.title || node.title || 'Generated Article'}
        fontSize={14}
        fontStyle="bold"
        fill="#1F2937"
        wrap="word"
        ellipsis
      />

      {/* Divider */}
      <Rect x={12} y={42} width={width - 24} height={1} fill="#E5E7EB" />

      {/* Content Preview */}
      <Text
        x={12}
        y={52}
        width={width - 24}
        height={height - 90}
        text={previewText + (previewText.length >= 150 ? '...' : '')}
        fontSize={12}
        fill="#6B7280"
        wrap="word"
        ellipsis
        lineHeight={1.4}
      />

      {/* Footer - Section count */}
      <Rect
        x={12}
        y={height - 28}
        width={width - 24}
        height={20}
        fill="#F3F4F6"
        cornerRadius={4}
      />
      <Text
        x={20}
        y={height - 24}
        text={`📑 ${sectionCount} section${sectionCount !== 1 ? 's' : ''} • Double-click to view`}
        fontSize={10}
        fill="#6B7280"
      />
    </Group>
  );
};

// --- Super Action List Card (Magic Cursor Generated) ---
const SuperActionListCard = ({
  node,
  width,
  height,
  isSelected,
  isHighlighted,
}: {
  node: CanvasNode;
  width: number;
  height: number;
  isSelected: boolean;
  isHighlighted?: boolean;
}) => {
  // Parse action list data from content
  let actionData: {
    title: string;
    items: Array<{
      id: string;
      text: string;
      done: boolean;
      priority?: string;
    }>;
  } | null = null;
  try {
    actionData = JSON.parse(node.content || '{}');
  } catch {
    actionData = null;
  }

  const borderColor = '#f59e0b';
  const bgColor = '#FFFCF5';

  const items = actionData?.items || [];
  const completedCount = items.filter((item) => item.done).length;
  const totalCount = items.length;

  // Show first 4 items max
  const visibleItems = items.slice(0, 4);

  return (
    <Group>
      {/* Card Background */}
      <Rect
        width={width}
        height={height}
        fill={bgColor}
        cornerRadius={12}
        stroke={
          isHighlighted ? '#3B82F6' : isSelected ? borderColor : '#E5E7EB'
        }
        strokeWidth={isSelected ? 2 : 1}
        shadowColor="rgba(245, 158, 11, 0.15)"
        shadowBlur={isSelected ? 16 : 8}
        shadowOffsetY={4}
      />

      {/* Top Accent Bar */}
      <Rect
        y={0}
        width={width}
        height={5}
        fill={borderColor}
        cornerRadius={[12, 12, 0, 0]}
      />

      {/* Checklist Icon */}
      <Text x={12} y={14} text="✅" fontSize={16} />

      {/* Type Badge */}
      <Rect
        x={width - 52}
        y={12}
        width={40}
        height={20}
        fill="#FEF3C7"
        cornerRadius={10}
      />
      <Text
        x={width - 46}
        y={16}
        text="Tasks"
        fontSize={10}
        fontStyle="bold"
        fill="#D97706"
      />

      {/* Title */}
      <Text
        x={36}
        y={14}
        width={width - 100}
        text={actionData?.title || node.title || 'Action Items'}
        fontSize={14}
        fontStyle="bold"
        fill="#1F2937"
        wrap="word"
        ellipsis
      />

      {/* Divider */}
      <Rect x={12} y={42} width={width - 24} height={1} fill="#E5E7EB" />

      {/* Action Items List */}
      {visibleItems.map((item, index) => (
        <Group key={item.id} y={52 + index * 26}>
          {/* Checkbox */}
          <Rect
            x={12}
            width={16}
            height={16}
            fill={item.done ? '#10B981' : '#FFFFFF'}
            stroke={item.done ? '#10B981' : '#D1D5DB'}
            strokeWidth={1.5}
            cornerRadius={4}
          />
          {item.done && (
            <Text
              x={14}
              y={1}
              text="✓"
              fontSize={12}
              fontStyle="bold"
              fill="#FFFFFF"
            />
          )}
          {/* Item Text */}
          <Text
            x={34}
            y={2}
            width={width - 50}
            text={item.text}
            fontSize={12}
            fill={item.done ? '#9CA3AF' : '#374151'}
            textDecoration={item.done ? 'line-through' : undefined}
            ellipsis
          />
        </Group>
      ))}

      {/* More items indicator */}
      {items.length > 4 && (
        <Text
          x={12}
          y={52 + 4 * 26}
          text={`+ ${items.length - 4} more items...`}
          fontSize={11}
          fill="#9CA3AF"
          fontStyle="italic"
        />
      )}

      {/* Footer - Progress */}
      <Rect
        x={12}
        y={height - 28}
        width={width - 24}
        height={20}
        fill="#F3F4F6"
        cornerRadius={4}
      />
      <Text
        x={20}
        y={height - 24}
        text={`${completedCount}/${totalCount} completed • Double-click to edit`}
        fontSize={10}
        fill="#6B7280"
      />
    </Group>
  );
};

// --- Mindmap Konva Card (Unified Node Model) ---
const MindmapKonvaCard = ({
  node,
  width,
  height,
  isSelected,
  isHighlighted,
}: {
  node: CanvasNode;
  width: number;
  height: number;
  isSelected: boolean;
  isHighlighted?: boolean;
}) => {
  // Parse mindmap data from outputData or content
  let mindmapData: {
    nodes?: Array<{ id: string; label: string; depth?: number }>;
    edges?: Array<{ source: string; target: string }>;
  } | null = null;
  try {
    if (node.outputData && typeof node.outputData === 'object') {
      mindmapData = node.outputData as unknown as typeof mindmapData;
    } else {
      const rawContent =
        (node.outputData as unknown as string) || node.content || '{}';
      mindmapData =
        typeof rawContent === 'string'
          ? JSON.parse(rawContent)
          : (rawContent as unknown as typeof mindmapData);
    }
    console.log(
      `[MindmapCard:${node.id}] Parsed nodes:`,
      mindmapData?.nodes?.length || 0
    );
  } catch (e) {
    console.error(`[MindmapCard:${node.id}] Parse error:`, e);
    mindmapData = null;
  }

  const borderColor = '#10B981'; // Green for mindmap
  const bgColor = '#F0FDF4';

  const nodes = mindmapData?.nodes || [];
  const rootNode = nodes.find((n) => n.depth === 0) || nodes[0];
  const firstLevelNodes = nodes.filter((n) => n.depth === 1).slice(0, 4);
  const totalNodeCount = nodes.length;

  return (
    <Group>
      {/* Card Background */}
      <Rect
        width={width}
        height={height}
        fill={bgColor}
        cornerRadius={12}
        stroke={
          isHighlighted ? '#3B82F6' : isSelected ? borderColor : '#E5E7EB'
        }
        strokeWidth={isSelected ? 2 : 1}
        shadowColor="rgba(16, 185, 129, 0.15)"
        shadowBlur={isSelected ? 16 : 8}
        shadowOffsetY={4}
      />

      {/* Top Accent Bar */}
      <Rect
        y={0}
        width={width}
        height={5}
        fill={borderColor}
        cornerRadius={[12, 12, 0, 0]}
      />

      {/* Mindmap Icon */}
      <Text x={12} y={14} text="🗺️" fontSize={16} />

      {/* Type Badge */}
      <Rect
        x={width - 68}
        y={12}
        width={56}
        height={20}
        fill="#DCFCE7"
        cornerRadius={10}
      />
      <Text
        x={width - 62}
        y={16}
        text="Mindmap"
        fontSize={10}
        fontStyle="bold"
        fill={borderColor}
      />

      {/* Title */}
      <Text
        x={36}
        y={14}
        width={width - 115}
        text={node.title || 'Generated Mindmap'}
        fontSize={14}
        fontStyle="bold"
        fill="#1F2937"
        wrap="word"
        ellipsis
      />

      {/* Divider */}
      <Rect x={12} y={42} width={width - 24} height={1} fill="#E5E7EB" />

      {/* Root Node Preview */}
      {rootNode && (
        <Group y={52}>
          <Rect
            x={12}
            width={width - 24}
            height={24}
            fill="#DCFCE7"
            cornerRadius={6}
          />
          <Text
            x={20}
            y={6}
            width={width - 40}
            text={`🌳 ${rootNode.label}`}
            fontSize={12}
            fontStyle="bold"
            fill="#166534"
            ellipsis
          />
        </Group>
      )}

      {/* First Level Nodes Preview */}
      {firstLevelNodes.map((n, index) => (
        <Group key={n.id} y={84 + index * 22}>
          <Text
            x={24}
            text="├─"
            fontSize={11}
            fill="#9CA3AF"
            fontFamily="monospace"
          />
          <Text
            x={48}
            width={width - 60}
            text={n.label}
            fontSize={11}
            fill="#374151"
            ellipsis
          />
        </Group>
      ))}

      {/* More nodes indicator */}
      {nodes.length > 5 && (
        <Text
          x={48}
          y={84 + firstLevelNodes.length * 22}
          text={`... ${nodes.length - 5} more nodes`}
          fontSize={10}
          fill="#9CA3AF"
          fontStyle="italic"
        />
      )}

      {/* Footer */}
      <Rect
        x={12}
        y={height - 28}
        width={width - 24}
        height={20}
        fill="#F3F4F6"
        cornerRadius={4}
      />
      <Text
        x={20}
        y={height - 24}
        text={`🔗 ${totalNodeCount} nodes • Double-click to expand`}
        fontSize={10}
        fill="#6B7280"
      />
    </Group>
  );
};

// --- Summary Konva Card (Unified Node Model) ---
const SummaryKonvaCard = ({
  node,
  width,
  height,
  isSelected,
  isHighlighted,
}: {
  node: CanvasNode;
  width: number;
  height: number;
  isSelected: boolean;
  isHighlighted?: boolean;
}) => {
  // Parse summary data from outputData or content
  let summaryData: {
    summary?: string;
    keyFindings?: Array<{ label: string; content: string }>;
    documentTitle?: string;
  } | null = null;
  try {
    if (node.outputData && typeof node.outputData === 'object') {
      summaryData = node.outputData as unknown as typeof summaryData;
    } else {
      const rawContent =
        (node.outputData as unknown as string) || node.content || '{}';
      summaryData =
        typeof rawContent === 'string'
          ? JSON.parse(rawContent)
          : (rawContent as unknown as typeof summaryData);
    }
    console.log(
      `[SummaryCard:${node.id}] Parsed summary length:`,
      summaryData?.summary?.length || 0
    );
  } catch (e) {
    console.error(`[SummaryCard:${node.id}] Parse error:`, e);
    summaryData = null;
  }

  const borderColor = '#8B5CF6'; // Purple for summary
  const bgColor = '#FAF5FF';

  const summary = summaryData?.summary || '';
  const keyFindings = summaryData?.keyFindings || [];
  const previewText = summary.substring(0, 180);

  return (
    <Group>
      {/* Card Background */}
      <Rect
        width={width}
        height={height}
        fill={bgColor}
        cornerRadius={12}
        stroke={
          isHighlighted ? '#3B82F6' : isSelected ? borderColor : '#E5E7EB'
        }
        strokeWidth={isSelected ? 2 : 1}
        shadowColor="rgba(139, 92, 246, 0.15)"
        shadowBlur={isSelected ? 16 : 8}
        shadowOffsetY={4}
      />

      {/* Top Accent Bar */}
      <Rect
        y={0}
        width={width}
        height={5}
        fill={borderColor}
        cornerRadius={[12, 12, 0, 0]}
      />

      {/* Summary Icon */}
      <Text x={12} y={14} text="📋" fontSize={16} />

      {/* Type Badge */}
      <Rect
        x={width - 68}
        y={12}
        width={56}
        height={20}
        fill="#EDE9FE"
        cornerRadius={10}
      />
      <Text
        x={width - 60}
        y={16}
        text="Summary"
        fontSize={10}
        fontStyle="bold"
        fill={borderColor}
      />

      {/* Title */}
      <Text
        x={36}
        y={14}
        width={width - 115}
        text={node.title || summaryData?.documentTitle || 'Document Summary'}
        fontSize={14}
        fontStyle="bold"
        fill="#1F2937"
        wrap="word"
        ellipsis
      />

      {/* Divider */}
      <Rect x={12} y={42} width={width - 24} height={1} fill="#E5E7EB" />

      {/* Summary Preview */}
      <Text
        x={12}
        y={52}
        width={width - 24}
        height={height - 100}
        text={previewText + (previewText.length >= 180 ? '...' : '')}
        fontSize={12}
        fill="#6B7280"
        wrap="word"
        ellipsis
        lineHeight={1.4}
      />

      {/* Footer */}
      <Rect
        x={12}
        y={height - 28}
        width={width - 24}
        height={20}
        fill="#F3F4F6"
        cornerRadius={4}
      />
      <Text
        x={20}
        y={height - 24}
        text={`💡 ${keyFindings.length} key finding${keyFindings.length !== 1 ? 's' : ''} • Double-click to view`}
        fontSize={10}
        fill="#6B7280"
      />
    </Group>
  );
};

// Knowledge Node Component
const KnowledgeNode = ({
  node,
  isSelected,
  isHighlighted,
  isMergeTarget,
  isHovered,
  isConnecting,
  isConnectTarget,
  isActiveThinking,
  onSelect,
  onClick,
  onDoubleClick,
  onLinkBack,
  onDragStart,
  onDragMove,
  onDragEnd,
  onContextMenu,
  onConnectionStart,
  onMouseEnter,
  onMouseLeave,
  isDraggable = true,
  isSynthesisSource = false,
}: {
  node: CanvasNode;
  isSelected: boolean;
  isHighlighted?: boolean;
  isMergeTarget?: boolean; // Synthesis: Show merge target highlight
  isHovered?: boolean; // Phase 2: Show connection handles
  isConnecting?: boolean; // Phase 2: Currently dragging a connection from this node
  isConnectTarget?: boolean; // Phase 2: Currently a potential connection target
  isActiveThinking?: boolean; // Thinking Graph: Is this the active thinking node (fork point)
  isSynthesisSource?: boolean; // Synthesis: This node is being used as input for synthesis
  isDraggable?: boolean; // Controls whether the node can be dragged
  onSelect: (e: Konva.KonvaEventObject<MouseEvent | TouchEvent>) => void;
  onClick?: () => void;
  onDoubleClick?: () => void; // Phase 1: Drill-down
  onLinkBack?: () => void; // Phase 1: Navigate to source
  onDragStart: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onDragMove?: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onDragEnd: (e: Konva.KonvaEventObject<DragEvent>) => void;
  onContextMenu?: (e: Konva.KonvaEventObject<PointerEvent>) => void;
  onConnectionStart?: () => void; // Phase 2: Start dragging connection
  onMouseEnter?: () => void; // Phase 2: For hover state
  onMouseLeave?: () => void; // Phase 2: For hover state
}) => {
  const width = node.width || 280;
  const height = node.height || 200;
  const style = getNodeStyle(
    node.type,
    node.subType,
    node.fileMetadata?.fileType,
    node.isDraft,
    node.branchType
  );

  // Thinking Graph: Check if this is a thinking step or branch node
  const isThinkingStep = node.type === 'thinking_step';
  const isThinkingBranch = node.type === 'thinking_branch';

  // Highlight animation effect
  const highlightStrokeWidth = isActiveThinking
    ? 4
    : isMergeTarget
      ? 3
      : isHighlighted
        ? 3
        : isSelected
          ? 2
          : 1;
  const highlightStrokeColor = isActiveThinking
    ? '#8B5CF6'
    : isMergeTarget
      ? '#8B5CF6'
      : isHighlighted
        ? '#3B82F6'
        : isSelected
          ? style.borderColor
          : style.borderColor;
  const highlightShadowColor = isMergeTarget
    ? '#8B5CF6'
    : isActiveThinking
      ? '#8B5CF6'
      : isHighlighted
        ? '#3B82F6'
        : 'black';
  const highlightShadowBlur = isMergeTarget
    ? 24
    : isActiveThinking
      ? 20
      : isHighlighted
        ? 16
        : isSelected
          ? 12
          : 8;

  // Check if this is a source node (for visual distinction)
  const isSourceNode = node.subType === 'source';
  // Check if this node has a source reference (for link-back feature)
  const hasSourceRef = !isSourceNode && node.sourceId;

  // Check for Magic Cursor generated super cards
  const isSuperArticle = node.type === 'super_article';
  const isSuperActionList = node.type === 'super_action_list';
  const isSuperCard = isSuperArticle || isSuperActionList;

  // Check for unified node model types (generation outputs as CanvasNodes)
  const isMindmap = node.type === 'mindmap';
  const isSummary = node.type === 'summary';
  const isGenerationOutput = isSuperCard || isMindmap || isSummary;

  // Calculate opacity: reduce if this node is being used as synthesis input
  const nodeOpacity = isSynthesisSource ? 0.4 : 1;

  return (
    <Group
      id={`node-${node.id}`} // Assign ID for finding during bulk drag
      x={node.x}
      y={node.y}
      opacity={nodeOpacity}
      draggable={isDraggable}
      onClick={(e) => {
        onSelect(e);
        onClick?.();
      }}
      onTap={(e) => {
        onSelect(e);
        onClick?.();
      }}
      onDblClick={() => onDoubleClick?.()}
      onDblTap={() => onDoubleClick?.()}
      onDragStart={onDragStart}
      onDragMove={onDragMove}
      onDragEnd={onDragEnd}
      onContextMenu={onContextMenu}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* Use specialized cards for different node types */}
      {isSuperArticle ? (
        <SuperArticleCard
          node={node}
          width={width}
          height={height}
          isSelected={isSelected}
          isHighlighted={isHighlighted}
        />
      ) : isSuperActionList ? (
        <SuperActionListCard
          node={node}
          width={width}
          height={height}
          isSelected={isSelected}
          isHighlighted={isHighlighted}
        />
      ) : isMindmap ? (
        <MindmapKonvaCard
          node={node}
          width={width}
          height={height}
          isSelected={isSelected}
          isHighlighted={isHighlighted}
        />
      ) : isSummary ? (
        <SummaryKonvaCard
          node={node}
          width={width}
          height={height}
          isSelected={isSelected}
          isHighlighted={isHighlighted}
        />
      ) : isSourceNode ? (
        /* Use SourcePreviewCard for PDF Source Nodes */
        <SourcePreviewCard
          node={node}
          width={width}
          height={height}
          isSelected={isSelected}
          isHighlighted={isHighlighted}
          isActiveThinking={isActiveThinking}
        />
      ) : (
        <>
          {/* Standard Node Rendering */}

          {/* Border/Background */}
          <Rect
            width={width}
            height={height}
            fill={style.bgColor}
            cornerRadius={12}
            stroke={highlightStrokeColor}
            strokeWidth={highlightStrokeWidth}
            dash={style.borderStyle === 'dashed' ? [8, 4] : undefined}
            shadowColor={
              isActiveThinking ? '#8B5CF6' : isHighlighted ? '#3B82F6' : 'black'
            }
            shadowBlur={
              isActiveThinking ? 20 : isHighlighted ? 16 : isSelected ? 12 : 8
            }
            shadowOpacity={
              isActiveThinking
                ? 0.4
                : isHighlighted
                  ? 0.3
                  : isSelected
                    ? 0.15
                    : 0.08
            }
            shadowOffsetY={4}
          />

          {/* Top Color Bar - thicker for source nodes */}
          <Rect
            y={0}
            width={width}
            height={isSourceNode ? 6 : 4}
            fill={style.topBarColor}
            cornerRadius={[12, 12, 0, 0]}
          />

          {/* Type Icon (top-left) */}
          <Text
            x={12}
            y={isSourceNode ? 14 : 12}
            text={style.icon}
            fontSize={isSourceNode ? 18 : 16}
          />

          {/* Title (adjust for icon) */}
          <Text
            x={40}
            y={isSourceNode ? 16 : 14}
            width={width - (hasSourceRef ? 80 : 56) - (isThinkingStep ? 60 : 0)}
            text={node.title}
            fontSize={isSourceNode ? 15 : 16}
            fontStyle="bold"
            fill="#292524"
            wrap="word"
            ellipsis={true}
          />

          {/* Thinking Graph: Step Index Badge */}
          {isThinkingStep && node.thinkingStepIndex && (
            <>
              <Rect
                x={width - 45}
                y={12}
                width={36}
                height={20}
                fill={node.isDraft ? '#8B5CF6' : '#3B82F6'}
                cornerRadius={10}
              />
              <Text
                x={width - 42}
                y={15}
                text={`#${node.thinkingStepIndex}`}
                fontSize={11}
                fontStyle="bold"
                fill="#FFFFFF"
              />
            </>
          )}

          {/* Thinking Graph: Active Context Badge */}
          {isActiveThinking && (
            <>
              <Rect
                x={width - 52}
                y={35}
                width={44}
                height={16}
                fill="#F3E8FF"
                cornerRadius={8}
              />
              <Text
                x={width - 48}
                y={37}
                text="Active"
                fontSize={9}
                fontStyle="bold"
                fill="#7C3AED"
              />
            </>
          )}

          {/* Thinking Graph: Draft Badge */}
          {node.isDraft && (
            <>
              <Rect
                x={width - (isActiveThinking ? 100 : 52)}
                y={35}
                width={40}
                height={16}
                fill="#FEF3C7"
                cornerRadius={8}
              />
              <Text
                x={width - (isActiveThinking ? 96 : 48)}
                y={37}
                text="Draft"
                fontSize={9}
                fontStyle="bold"
                fill="#D97706"
              />
            </>
          )}

          {/* Source Node: File metadata badge */}
          {isSourceNode && node.fileMetadata && (
            <>
              <Rect
                x={width - 60}
                y={14}
                width={48}
                height={18}
                fill={style.topBarColor}
                cornerRadius={4}
                opacity={0.2}
              />
              <Text
                x={width - 56}
                y={17}
                text={node.fileMetadata.fileType?.toUpperCase() || 'FILE'}
                fontSize={10}
                fontStyle="bold"
                fill={style.topBarColor}
              />
            </>
          )}

          {/* Link-Back Icon (top-right) for nodes with source reference */}
          {hasSourceRef && (
            <Group
              x={width - 32}
              y={12}
              onClick={(e) => {
                e.cancelBubble = true;
                onLinkBack?.();
              }}
              onTap={(e) => {
                e.cancelBubble = true;
                onLinkBack?.();
              }}
            >
              <Rect width={24} height={24} fill="#E0E7FF" cornerRadius={6} />
              <Text x={4} y={4} text="🔗" fontSize={14} />
            </Group>
          )}

          {/* Content */}
          <Text
            x={16}
            y={isSourceNode ? 50 : 48}
            width={width - 32}
            height={isSourceNode ? 85 : 95}
            text={node.content}
            fontSize={14}
            fill="#6B7280"
            wrap="word"
            ellipsis={true}
            visible={!(isSourceNode && node.fileMetadata?.thumbnailUrl)}
          />
          {isSourceNode && node.fileMetadata?.thumbnailUrl && (
            <URLImage
              src={node.fileMetadata.thumbnailUrl}
              x={16}
              y={50}
              width={width - 32}
              height={isSourceNode ? 85 : 95}
              cornerRadius={8}
            />
          )}

          {/* Source Node: Page count info */}
          {isSourceNode && node.fileMetadata?.pageCount && (
            <Text
              x={16}
              y={height - 50}
              text={`${node.fileMetadata.pageCount} pages`}
              fontSize={11}
              fill="#A8A29E"
            />
          )}

          {/* Tags (simplified - show first tag only) */}
          {node.tags && node.tags.length > 0 && (
            <>
              <Rect
                x={16}
                y={height - 35}
                width={Math.min(node.tags[0].length * 7 + 16, width - 32)}
                height={20}
                fill="#F5F5F4"
                cornerRadius={4}
              />
              <Text
                x={24}
                y={height - 32}
                text={node.tags[0]}
                fontSize={10}
                fill="#6B7280"
              />
            </>
          )}

          {/* Source info (for non-source nodes that reference a source) */}
          {hasSourceRef && (
            <Text
              x={16}
              y={height - 25}
              width={width - 32}
              text={`📄 ${node.sourceId!.substring(0, 8)}${node.sourcePage ? ` • p.${node.sourcePage}` : ''}`}
              fontSize={11}
              fill="#9CA3AF"
            />
          )}

          {/* Double-click hint for source nodes */}
          {isSourceNode && isSelected && (
            <Text
              x={16}
              y={height - 18}
              text="Double-click to open"
              fontSize={10}
              fill="#78716C"
              fontStyle="italic"
            />
          )}
        </>
      )}

      {/* Connection Handles - rendered for ALL node types (draw.io style: 4 directions) */}
      {(isHovered || isSelected || isConnecting) && (
        <>
          {/* Top Handle (N) */}
          <Group
            x={width / 2}
            y={0}
            onMouseDown={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
            onTouchStart={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
          >
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill={isConnecting ? '#3B82F6' : '#FFFFFF'}
              stroke="#3B82F6"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>

          {/* Bottom Handle (S) */}
          <Group
            x={width / 2}
            y={height}
            onMouseDown={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
            onTouchStart={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
          >
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill={isConnecting ? '#3B82F6' : '#FFFFFF'}
              stroke="#3B82F6"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>

          {/* Left Handle (W) */}
          <Group
            x={0}
            y={height / 2}
            onMouseDown={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
            onTouchStart={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
          >
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill={isConnecting ? '#3B82F6' : '#FFFFFF'}
              stroke="#3B82F6"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>

          {/* Right Handle (E) */}
          <Group
            x={width}
            y={height / 2}
            onMouseDown={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
            onTouchStart={(e) => {
              e.cancelBubble = true;
              onConnectionStart?.();
            }}
          >
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill={isConnecting ? '#3B82F6' : '#FFFFFF'}
              stroke="#3B82F6"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>
        </>
      )}

      {/* Connection Target Handles - show on all 4 sides when this node is a potential target */}
      {isConnectTarget && (
        <>
          {/* Top Target */}
          <Group x={width / 2} y={0}>
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill="#10B981"
              stroke="#059669"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>
          {/* Bottom Target */}
          <Group x={width / 2} y={height}>
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill="#10B981"
              stroke="#059669"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>
          {/* Left Target */}
          <Group x={0} y={height / 2}>
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill="#10B981"
              stroke="#059669"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>
          {/* Right Target */}
          <Group x={width} y={height / 2}>
            <Rect
              x={-6}
              y={-6}
              width={12}
              height={12}
              fill="#10B981"
              stroke="#059669"
              strokeWidth={2}
              cornerRadius={6}
            />
          </Group>
        </>
      )}
    </Group>
  );
};

export default function KonvaCanvas({
  nodes: propNodes,
  edges: propEdges,
  viewport: propViewport,
  currentView: propCurrentView,
  onNodesChange: propOnNodesChange,
  onEdgesChange: propOnEdgesChange,
  onViewportChange: propOnViewportChange,
  onNodeAdd,
  highlightedNodeId,
  onNodeClick,
  onNodeDoubleClick,
  onOpenSource,
  toolMode = 'select', // Default to select
  onToolChange,
  onOpenImport,
  onSelectionChange,
}: KonvaCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const lastWheelTimeRef = useRef(0); // For wheel event throttling
  const WHEEL_THROTTLE_MS = 8; // ~120fps throttle for high-refresh-rate displays
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // FPS Monitor - measures canvas render performance
  const {
    begin: fpsBegin,
    end: fpsEnd,
    isVisible: fpsVisible,
  } = useFpsMonitor();

  // Call begin at start of render, end after layout effects complete
  if (fpsVisible) fpsBegin();
  useLayoutEffect(() => {
    if (fpsVisible) fpsEnd();
  });

  // Selection State
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(
    new Set()
  );

  // Notify parent when selection changes
  useEffect(() => {
    onSelectionChange?.(selectedNodeIds.size);
  }, [selectedNodeIds, onSelectionChange]);

  const [selectionRect, setSelectionRect] = useState<{
    startX: number;
    startY: number;
    x: number;
    y: number;
    width: number;
    height: number;
  } | null>(null);

  // Magic Cursor state
  const [magicSelection, setMagicSelection] = useState<{
    rect: { x: number; y: number; width: number; height: number };
    nodeIds: string[];
    screenPosition: { x: number; y: number };
  } | null>(null);

  // Magic Cursor generation state
  const [magicGenerationTask, setMagicGenerationTask] = useState<{
    taskId: string;
    outputType: 'article' | 'action_list';
    snapshotContext: { x: number; y: number; width: number; height: number };
    sourceNodeIds: string[]; // IDs of nodes used as generation input
  } | null>(null);
  const [isGeneratingMagic, setIsGeneratingMagic] = useState(false);

  const [isPanning, setIsPanning] = useState(false);
  const [isSpacePressed, setIsSpacePressed] = useState(false);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    nodeId?: string;
    sectionId?: string;
  } | null>(null);

  // Phase 2: Manual Connection State
  const [connectingFromNodeId, setConnectingFromNodeId] = useState<
    string | null
  >(null);
  const [connectingLineEnd, setConnectingLineEnd] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [edgeLabelDialog, setEdgeLabelDialog] = useState<{
    edge: CanvasEdge;
    position: { x: number; y: number };
  } | null>(null);
  const [linkTypeDialog, setLinkTypeDialog] = useState<{
    edge: CanvasEdge;
    position: { x: number; y: number };
  } | null>(null);

  // P1: Edge Selection & Reconnection
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [reconnectingEdge, setReconnectingEdge] = useState<{
    edgeId: string;
    type: 'source' | 'target';
    x?: number;
    y?: number;
  } | null>(null);

  // Merge/Synthesis State
  const [mergeTargetNodeId, setMergeTargetNodeId] = useState<string | null>(
    null
  );
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);
  const [pendingSynthesisResult, setPendingSynthesisResult] = useState<{
    id: string;
    title: string;
    content: string;
    recommendation?: string;
    keyRisk?: string;
    confidence?: 'high' | 'medium' | 'low';
    themes?: string[];
    sourceNodeIds?: string[];
    mode: 'connect' | 'inspire' | 'debate';
    position: { x: number; y: number };
  } | null>(null);

  // Node Editing State
  const [editingNodeId, setEditingNodeId] = useState<string | null>(null);
  const [isCreatingNote, setIsCreatingNote] = useState(false);

  // Web Page Reader State
  const [webPageReader, setWebPageReader] = useState<{
    open: boolean;
    node: CanvasNode | null;
  }>({ open: false, node: null });

  // YouTube Player State
  const [youtubePlayer, setYoutubePlayer] = useState<{
    open: boolean;
    node: CanvasNode | null;
  }>({ open: false, node: null });

  // Super Card Editing State (unified: includes mindmap, summary, article, action_list)
  const [editingSuperCardId, setEditingSuperCardId] = useState<string | null>(
    null
  );
  const [editingSuperCardType, setEditingSuperCardType] = useState<
    'article' | 'action_list' | 'mindmap' | 'summary' | null
  >(null);
  const onCreateNotePosition = useRef<{ x: number; y: number } | null>(null);

  // Handle opening editor for new note from Context Menu
  const handleCreateNote = useCallback((position: { x: number; y: number }) => {
    onCreateNotePosition.current = position;
    setIsCreatingNote(true);
    setEditingNodeId(null);
  }, []);

  // Refs for Drag/Pan
  const lastPosRef = useRef({ x: 0, y: 0 });
  const draggedNodeRef = useRef<string | null>(null);
  const lastDragPosRef = useRef<{ x: number; y: number } | null>(null);
  // Ref for RAF-based wheel handling (auto-adapts to display refresh rate)
  const wheelRafIdRef = useRef<number | null>(null);
  const pendingWheelDeltaRef = useRef({ deltaX: 0, deltaY: 0, ctrlKey: false });

  const {
    dragPreview,
    setDragPreview,
    projectId, // Get projectId for WebSocket connection
    dragContentRef,
    promoteNode,
    deleteSection,
    addSection,
    canvasSections,
    setCanvasSections,
    // Alias currentView to avoid conflict if used locally, or just use it directly
    currentView: studioCurrentView,
    activeThinkingId,
    setActiveThinkingId,
    setCrossBoundaryDragNode,
    documents, // Get documents for Inspiration Dock
    urlContents, // Get URL contents (videos)
    generationTasks, // Get generation tasks to check for completed outputs
    // Get canvas state from context as fallback
    canvasNodes: contextNodes,
    canvasEdges: contextEdges,
    canvasViewport: contextViewport,
    setCanvasNodes: contextSetNodes,
    setCanvasEdges: contextSetEdges,
    setCanvasViewport: contextSetViewport,
    addNodeToCanvas,
    saveCanvas,
    clearCanvas,
    // currentView, // We aliased it to studioCurrentView above
    viewStates,
    setViewStates,
    setCurrentView,
    switchView,
    navigateToMessage,
    setHighlightedNodeId,
    crossBoundaryDragNode,
    startNewTopic,
    autoThinkingPathEnabled,
  } = useStudio();

  const {
    handleDeleteNode,
    handleSynthesizeNodes: synthesizeNodes,
    handleGenerateContent,
    handleGenerateContentConcurrent,
    getViewportCenterPosition,
    handleImportSource,
  } = useCanvasActions({ onOpenImport });

  const toast = useNotification();

  // Use props if provided, otherwise fall back to context values
  const nodes = propNodes ?? contextNodes ?? [];
  const edges = propEdges ?? contextEdges ?? [];
  const viewport = propViewport ?? contextViewport ?? { x: 0, y: 0, scale: 1 };
  const currentView = propCurrentView ?? studioCurrentView ?? 'free';
  const onNodesChange = propOnNodesChange ?? contextSetNodes ?? (() => {});
  const onEdgesChange = propOnEdgesChange ?? contextSetEdges ?? (() => {});
  const onViewportChange =
    propOnViewportChange ?? contextSetViewport ?? (() => {});

  // Filter nodes and sections by current view
  const visibleNodes = (nodes || []).filter(
    (node) => node.viewType === currentView
  );
  const visibleSections = (canvasSections || []).filter(
    (section) => section.viewType === currentView
  );

  // Spatial index for O(log N) box selection queries
  const spatialIndex = useSpatialIndex(visibleNodes);

  // Viewport culling - only render nodes within visible viewport (+ padding)
  const culledNodes = useViewportCulling(
    viewport,
    dimensions,
    spatialIndex,
    visibleNodes,
    300 // Extra padding to prevent pop-in during fast panning
  );

  // Check if there are any completed generation outputs on the canvas
  const hasCompletedOutputs = useMemo(() => {
    return Array.from(generationTasks.values()).some(
      (task) => task.status === 'complete'
    );
  }, [generationTasks]);

  // Update dimensions on resize
  useEffect(() => {
    if (!containerRef.current) return;

    // Set initial dimensions (ensure minimum 1x1 to avoid canvas errors)
    const initialWidth = containerRef.current.offsetWidth || 800;
    const initialHeight = containerRef.current.offsetHeight || 600;
    setDimensions({
      width: Math.max(1, initialWidth),
      height: Math.max(1, initialHeight),
    });

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          // Ensure minimum 1x1 dimensions to prevent drawImage errors
          const width = Math.max(1, entry.contentRect.width);
          const height = Math.max(1, entry.contentRect.height);
          setDimensions({ width, height });
        }
      }
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  // Pan to highlighted node when navigating from chat
  useEffect(() => {
    if (!highlightedNodeId) return;

    const node = nodes.find((n) => n.id === highlightedNodeId);
    if (!node) return;

    // Calculate center of the node
    const nodeWidth = node.width || 280;
    const nodeHeight = node.height || 200;
    const nodeCenterX = node.x + nodeWidth / 2;
    const nodeCenterY = node.y + nodeHeight / 2;

    // Calculate new viewport position to center the node on screen
    const scale = viewport.scale;
    const newX = dimensions.width / 2 - nodeCenterX * scale;
    const newY = dimensions.height / 2 - nodeCenterY * scale;

    // Update viewport to center on the node
    onViewportChange({
      scale,
      x: newX,
      y: newY,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightedNodeId]); // Only trigger when highlightedNodeId changes

  // Handle keyboard shortcuts (Space for panning, Delete for deletion, Cmd+A for Select All)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const isInput =
        target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';

      if (isInput) return;

      // Space for Pan
      if (e.code === 'Space' && !e.repeat) {
        e.preventDefault();
        setIsSpacePressed(true);
      }

      // Delete / Backspace - Delete selected nodes or edges
      if (e.key === 'Delete' || e.key === 'Backspace') {
        let deleted = false;

        if (selectedNodeIds.size > 0) {
          e.preventDefault();
          // Delete each selected node via API (handles optimistic updates and rollback)
          selectedNodeIds.forEach((nodeId) => {
            handleDeleteNode(nodeId).catch((err) => {
              console.error('Failed to delete node:', err);
            });
          });
          setSelectedNodeIds(new Set());
          deleted = true;
        }

        if (selectedEdgeId) {
          e.preventDefault();
          if (onEdgesChange) {
            onEdgesChange(edges.filter((edge) => edge.id !== selectedEdgeId));
          }
          setSelectedEdgeId(null);
          setEdgeLabelDialog(null);
          deleted = true;
        }
      }

      // Cmd+A / Ctrl+A for Select All
      if ((e.metaKey || e.ctrlKey) && e.key === 'a') {
        e.preventDefault();
        // Select all VISIBLE nodes
        const allVisibleIds = visibleNodes.map((n) => n.id);
        setSelectedNodeIds(new Set(allVisibleIds));
      }

      // Tool Shortcuts (V for Select, H for Hand, M for Magic, L for Connect, K for Logic Connect)
      if (e.key.toLowerCase() === 'v') {
        onToolChange?.('select');
      }
      if (e.key.toLowerCase() === 'h') {
        onToolChange?.('hand');
      }
      if (e.key.toLowerCase() === 'm') {
        onToolChange?.('magic');
      }
      if (e.key.toLowerCase() === 'l') {
        onToolChange?.('connect');
      }
      if (e.key.toLowerCase() === 'k') {
        onToolChange?.('logic_connect');
      }

      // Cmd+D / Ctrl+D for Duplicate
      if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
        e.preventDefault();
        if (selectedNodeIds.size > 0) {
          const nodesToDuplicate = nodes.filter((n) =>
            selectedNodeIds.has(n.id)
          );
          const newNodes = nodesToDuplicate.map((node) => ({
            ...node,
            id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            x: node.x + 20,
            y: node.y + 20,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }));

          onNodesChange([...nodes, ...newNodes]);
          // Select the new nodes
          setSelectedNodeIds(new Set(newNodes.map((n) => n.id)));
        }
      }

      // Nudge (Arrow Keys)
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
        if (selectedNodeIds.size > 0) {
          e.preventDefault();
          const step = e.shiftKey ? 10 : 1;
          const dx =
            e.key === 'ArrowLeft' ? -step : e.key === 'ArrowRight' ? step : 0;
          const dy =
            e.key === 'ArrowUp' ? -step : e.key === 'ArrowDown' ? step : 0;

          const updatedNodes = nodes.map((n) => {
            if (selectedNodeIds.has(n.id)) {
              return { ...n, x: n.x + dx, y: n.y + dy };
            }
            return n;
          });
          onNodesChange(updatedNodes);
        }
      }

      // Group (Cmd+G / Ctrl+G)
      if ((e.metaKey || e.ctrlKey) && e.key === 'g') {
        e.preventDefault();
        const selectedNodes = visibleNodes.filter((n) =>
          selectedNodeIds.has(n.id)
        );

        if (selectedNodes.length >= 2) {
          let minX = Infinity,
            minY = Infinity,
            maxX = -Infinity,
            maxY = -Infinity;
          selectedNodes.forEach((node) => {
            minX = Math.min(minX, node.x);
            minY = Math.min(minY, node.y);
            maxX = Math.max(maxX, node.x + (node.width || 280));
            maxY = Math.max(maxY, node.y + (node.height || 200));
          });

          const padding = 24;
          const headerHeight = 48;
          const sectionId = `section-${crypto.randomUUID()}`;

          const newSection = {
            id: sectionId,
            title: `Group (${selectedNodes.length})`,
            viewType: currentView as 'free' | 'thinking',
            isCollapsed: false,
            nodeIds: Array.from(selectedNodeIds),
            x: minX - padding,
            y: minY - padding - headerHeight,
            width: maxX - minX + padding * 2,
            height: maxY - minY + padding * 2 + headerHeight,
          };

          addSection(newSection);

          const updatedNodes = nodes.map((node) =>
            selectedNodeIds.has(node.id) ? { ...node, sectionId } : node
          );
          onNodesChange(updatedNodes);
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
        setIsPanning(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [
    selectedNodeIds,
    nodes,
    visibleNodes,
    onNodesChange,
    addSection,
    currentView,
    onToolChange,
  ]);

  // Handle Node Selection Logic
  const handleNodeSelect = useCallback(
    (nodeId: string, e: Konva.KonvaEventObject<MouseEvent | TouchEvent>) => {
      // In Hand mode or holding space, let event bubble to Stage for panning
      if (toolMode === 'hand' || isSpacePressed) return;

      // Connect Mode Logic
      if (toolMode === 'connect' || toolMode === 'logic_connect') {
        e.cancelBubble = true;
        setConnectingFromNodeId(nodeId);
        const stage = e.target.getStage();
        const pointer = stage?.getPointerPosition();
        if (pointer) {
          const canvasX = (pointer.x - viewport.x) / viewport.scale;
          const canvasY = (pointer.y - viewport.y) / viewport.scale;
          setConnectingLineEnd({ x: canvasX, y: canvasY });
        }
        return;
      }

      e.cancelBubble = true; // Prevent stage click (only in select mode)

      const isShift = e.evt.shiftKey || e.evt.ctrlKey || e.evt.metaKey;
      const isSelected = selectedNodeIds.has(nodeId);

      if (isShift) {
        // Toggle selection
        const newSet = new Set(selectedNodeIds);
        if (isSelected) {
          newSet.delete(nodeId);
        } else {
          newSet.add(nodeId);
        }
        setSelectedNodeIds(newSet);
      } else {
        if (!isSelected) {
          setSelectedNodeIds(new Set([nodeId]));
        }
      }
    },
    [selectedNodeIds, toolMode, isSpacePressed]
  );

  // Handle Bulk Drag
  const handleNodeDragStart = useCallback(
    (nodeId: string) => (e: Konva.KonvaEventObject<DragEvent>) => {
      // Prevent drag if in hand mode (though draggable prop should control this)
      if (toolMode === 'hand') {
        e.target.stopDrag();
        return;
      }

      e.cancelBubble = true;
      draggedNodeRef.current = nodeId;
      lastDragPosRef.current = e.target.position();

      // Enable cross-boundary drag (to Chat)
      const node = nodes.find((n) => n.id === nodeId);
      if (node) {
        setCrossBoundaryDragNode({
          id: node.id,
          title: node.title,
          content: node.content,
          sourceMessageId: node.sourceMessageId,
        });
      }

      // Ensure dragging node is selected and determine effective selection
      let effectiveSelectionIds = new Set(selectedNodeIds);
      if (!selectedNodeIds.has(nodeId)) {
        if (!e.evt.shiftKey) {
          effectiveSelectionIds = new Set([nodeId]);
          setSelectedNodeIds(effectiveSelectionIds);
        } else {
          effectiveSelectionIds.add(nodeId);
          setSelectedNodeIds(new Set(effectiveSelectionIds));
        }
      }

      // Alt + Drag: Leave a copy behind (Duplicate)
      if (e.evt.altKey) {
        const nodesToClone = nodes.filter((n) =>
          effectiveSelectionIds.has(n.id)
        );

        const newStaticNodes = nodesToClone.map((node) => ({
          ...node,
          id: `node-${crypto.randomUUID()}-copy`,
          // Keep original position (this will be the "left behind" copy)
          x: node.x,
          y: node.y,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          // Clear selection for the copy, as we are dragging the original
        }));

        // Add static copies to canvas
        onNodesChange([...nodes, ...newStaticNodes]);
        // Selection stays on the moving nodes (original IDs), which is what we want.
      }
    },
    [selectedNodeIds, toolMode, nodes, setCrossBoundaryDragNode]
  );

  const handleNodeDragMove = useCallback(
    (nodeId: string) => (e: Konva.KonvaEventObject<DragEvent>) => {
      e.cancelBubble = true;
      if (!lastDragPosRef.current) return;

      const newPos = e.target.position();
      const dx = newPos.x - lastDragPosRef.current.x;
      const dy = newPos.y - lastDragPosRef.current.y;

      lastDragPosRef.current = newPos;

      // Move other selected nodes
      const stage = stageRef.current;
      if (!stage) return;

      selectedNodeIds.forEach((id) => {
        if (id === nodeId) return; // Skip self
        const node = stage.findOne(`#node-${id}`);
        if (node) {
          node.x(node.x() + dx);
          node.y(node.y() + dy);
        }
      });
    },
    [selectedNodeIds]
  );

  const handleNodeDragEnd = useCallback(
    (nodeId: string) => (e: Konva.KonvaEventObject<DragEvent>) => {
      e.cancelBubble = true;
      draggedNodeRef.current = null;
      lastDragPosRef.current = null;

      // Check if mouse is outside the canvas container (cross-boundary drag)
      const container = containerRef.current;
      const mouseX = e.evt.clientX;
      const mouseY = e.evt.clientY;
      const stage = stageRef.current;

      if (container) {
        const rect = container.getBoundingClientRect();
        const isOutsideCanvas =
          mouseX < rect.left ||
          mouseX > rect.right ||
          mouseY < rect.top ||
          mouseY > rect.bottom;

        if (isOutsideCanvas) {
          // Cross-boundary drag: Reset node position back to original (from state)
          // This keeps the node visible in canvas while also adding it as context
          if (stage) {
            selectedNodeIds.forEach((id) => {
              const originalNode = nodes.find((n) => n.id === id);
              const konvaNode = stage.findOne(`#node-${id}`);
              if (originalNode && konvaNode) {
                konvaNode.x(originalNode.x);
                konvaNode.y(originalNode.y);
              }
            });
          }

          // Clear crossBoundaryDragNode after a short delay to allow AssistantPanel to detect it
          setTimeout(() => setCrossBoundaryDragNode(null), 100);
          return;
        }
      }

      // Clear cross-boundary drag state since we're dropping inside canvas
      setCrossBoundaryDragNode(null);

      // Sync all selected nodes positions to state
      if (!stage) return;

      const updatedNodes = nodes.map((n) => {
        if (selectedNodeIds.has(n.id)) {
          // If it's the dragged node, use event target
          if (n.id === nodeId) {
            return { ...n, x: e.target.x(), y: e.target.y() };
          }
          // For others, look up by ID
          const nodeNode = stage.findOne(`#node-${n.id}`);
          if (nodeNode) {
            return { ...n, x: nodeNode.x(), y: nodeNode.y() };
          }
        }
        return n;
      });

      onNodesChange(updatedNodes);
    },
    [nodes, selectedNodeIds, onNodesChange, setCrossBoundaryDragNode]
  );

  // Handle wheel zoom and pan (with throttling for smooth Mac trackpad scrolling)
  const handleWheel = (e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();

    const stage = stageRef.current;
    if (!stage) return;

    // Zoom Logic (Ctrl + Wheel / Pinch) - needs React state for scale
    if (e.evt.ctrlKey) {
      // Throttle zoom events (less frequent than pan)
      const now = Date.now();
      if (now - lastWheelTimeRef.current < WHEEL_THROTTLE_MS) {
        return;
      }
      lastWheelTimeRef.current = now;

      const scaleBy = 1.05;
      const oldScale = viewport.scale;
      const pointer = stage.getPointerPosition();

      if (!pointer) return;

      const mousePointTo = {
        x: (pointer.x - viewport.x) / oldScale,
        y: (pointer.y - viewport.y) / oldScale,
      };

      const newScale =
        e.evt.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;
      const clampedScale = Math.max(0.1, Math.min(5, newScale));

      onViewportChange({
        scale: clampedScale,
        x: pointer.x - mousePointTo.x * clampedScale,
        y: pointer.y - mousePointTo.y * clampedScale,
      });
    } else {
      // Pan Logic - Use RAF for 120fps capable updates
      // Accumulate deltas and process in next animation frame
      pendingWheelDeltaRef.current.deltaX += -e.evt.deltaX;
      pendingWheelDeltaRef.current.deltaY += -e.evt.deltaY;

      if (wheelRafIdRef.current === null) {
        wheelRafIdRef.current = requestAnimationFrame(() => {
          const { deltaX, deltaY } = pendingWheelDeltaRef.current;

          // Use Konva native transform for smooth panning
          stage.position({
            x: stage.x() + deltaX,
            y: stage.y() + deltaY,
          });
          stage.batchDraw();

          // Sync React state after animation frame
          onViewportChange({
            ...viewport,
            x: stage.x(),
            y: stage.y(),
          });

          // Reset accumulated deltas
          pendingWheelDeltaRef.current = {
            deltaX: 0,
            deltaY: 0,
            ctrlKey: false,
          };
          wheelRafIdRef.current = null;
        });
      }
    }
  };

  // Handle Stage Interaction (Pan vs Box Select)
  const handleStageMouseDown = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Check if we are in Pan mode (Hand tool or Spacebar)
    // In Hand mode/Spacebar, we ALWAYS pan, regardless of what was clicked (node or stage)
    const isHandMode = toolMode === 'hand' || isSpacePressed;

    if (isHandMode) {
      if (e.evt.button === 0) {
        // Left click only for primary pan
        setIsPanning(true);
        lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
        return; // Stop here, do not process selection
      }
    }

    // Existing "Clicked on Empty" check for Select Mode behaviors
    const clickedOnEmpty =
      e.target === e.target.getStage() || e.target.getClassName() === 'Rect';

    if (clickedOnEmpty) {
      // Left click
      if (e.evt.button === 0) {
        // If NOT Hand/Space (already handled above), then it's Box Selection
        if (!isHandMode) {
          // Box Selection mode
          const stage = e.target.getStage();
          const pointer = stage?.getPointerPosition();
          if (pointer) {
            const x = (pointer.x - viewport.x) / viewport.scale;
            const y = (pointer.y - viewport.y) / viewport.scale;
            setSelectionRect({
              startX: x,
              startY: y,
              x,
              y,
              width: 0,
              height: 0,
            });
          }
          // Clear selection if not Shift
          if (!e.evt.shiftKey) {
            setSelectedNodeIds(new Set());
            setSelectedEdgeId(null);
          }
        }
      } else if (e.evt.button === 1) {
        // Middle click pan (always works)
        setIsPanning(true);
        lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
      }
    }
  };

  const handleStageMouseMove = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Phase 2: Handle Connection Line dragging
    if (connectingFromNodeId) {
      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (pointer) {
        const canvasX = (pointer.x - viewport.x) / viewport.scale;
        const canvasY = (pointer.y - viewport.y) / viewport.scale;
        setConnectingLineEnd({ x: canvasX, y: canvasY });
      }
      return;
    }

    // Handle Pan - Use Konva native transform for 120fps performance
    // Skip React state updates during panning, sync only on mouseUp
    if (isPanning) {
      const stage = stageRef.current;
      if (!stage) return;

      const dx = e.evt.clientX - lastPosRef.current.x;
      const dy = e.evt.clientY - lastPosRef.current.y;

      // Use Konva native position update (bypasses React reconciliation)
      stage.position({
        x: stage.x() + dx,
        y: stage.y() + dy,
      });
      stage.batchDraw();

      lastPosRef.current = { x: e.evt.clientX, y: e.evt.clientY };
      return;
    }

    // Handle Box Selection
    if (selectionRect) {
      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (pointer) {
        const currentX = (pointer.x - viewport.x) / viewport.scale;
        const currentY = (pointer.y - viewport.y) / viewport.scale;

        const startX = selectionRect.startX;
        const startY = selectionRect.startY;

        setSelectionRect({
          ...selectionRect,
          x: Math.min(startX, currentX),
          y: Math.min(startY, currentY),
          width: Math.abs(currentX - startX),
          height: Math.abs(currentY - startY),
        });
      }
    }
  };

  // --- Merge Handlers (Synthesis) ---
  const MERGE_PROXIMITY_THRESHOLD = 150; // pixels

  // Helper to get raw node ID from event target (traversing up to parent Group if needed)
  // WebSocket for Synthesis
  const [synthesisTaskId, setSynthesisTaskId] = useState<string | null>(null);

  useOutputWebSocket({
    projectId: projectId || '',
    taskId: synthesisTaskId,
    enabled: !!projectId && !!synthesisTaskId,
    onNodeAdded: (nodeId, nodeData) => {
      console.log('[KonvaCanvas] onNodeAdded:', nodeId, nodeData);

      // Since we are scoped to the task_id, any node added is likely our result.
      // But we still check if we have a pending result to update.
      if (pendingSynthesisResult) {
        // Extract synthesis specific fields from metadata if available
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const metadata = (nodeData as any).metadata || {};

        // Parse content field which contains Markdown formatted insight
        // We might want to keep the raw parts if available, but for now we have the full content string
        // The synthesis agent returns a formatted markdown string in nodeData.content

        setPendingSynthesisResult((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            // Update with real data
            id: nodeId, // Use server-generated ID
            title: nodeData.label || prev.title,
            content: nodeData.content || prev.content,
            // Try to extract structured data if we can, otherwise these might stay as defaults
            // The Agent puts them in metadata themes/confidence
            confidence: metadata.confidence || 'medium',
            themes: (metadata.themes as string[]) || [],
            // Clear the "Processing..." state
            recommendation: metadata.themes ? undefined : prev.recommendation, // If we have themes, assume real data
            keyRisk: undefined,
          };
        });

        // Clear task ID to satisfy "one-off" synthesis
        setSynthesisTaskId(null);
        setIsSynthesizing(false);
      }
    },
    onGenerationError: (error) => {
      console.error('Synthesis error:', error);
      setPendingSynthesisResult((prev) =>
        prev ? { ...prev, content: `Error: ${error}` } : null
      );
      setSynthesisTaskId(null);
      setIsSynthesizing(false);
    },
  });

  // WebSocket for Magic Cursor generation (article/action_list)
  const magicWsEnabled = !!projectId && !!magicGenerationTask?.taskId;

  useOutputWebSocket({
    projectId: projectId || '',
    taskId: magicGenerationTask?.taskId || null,
    enabled: magicWsEnabled,
    onGenerationComplete: async (outputId, message) => {
      console.log(
        '[KonvaCanvas] Magic generation complete:',
        outputId,
        message
      );

      // IMPORTANT: Only process events with a valid outputId
      // Multiple events may be received; ignore ones without outputId
      if (!outputId) {
        console.log(
          '[KonvaCanvas] Ignoring generation_complete without outputId'
        );
        return; // Early return - don't clear state for invalid events
      }

      if (magicGenerationTask && projectId) {
        try {
          // Fetch the full output data
          const output = await outputsApi.get(projectId, outputId);
          console.log('[KonvaCanvas] Fetched output:', output);

          if (output && output.data) {
            const { snapshotContext, outputType } = magicGenerationTask;

            // Position at bottom-right of selection + 20px offset
            const newNodeX = snapshotContext.x + snapshotContext.width + 20;
            const newNodeY = snapshotContext.y;

            // Get title from output data
            const outputData = output.data as Record<string, unknown>;
            const title =
              (outputData.title as string) ||
              (outputType === 'article' ? 'Generated Article' : 'Action Items');

            // Create the new canvas node (unified node model)
            const newNode: Partial<CanvasNode> = {
              id: `supercard-${outputId}`,
              type:
                outputType === 'article'
                  ? 'super_article'
                  : 'super_action_list',
              title,
              content: JSON.stringify(output.data), // Store full data as JSON
              x: newNodeX,
              y: newNodeY,
              width: outputType === 'article' ? 320 : 280,
              height: outputType === 'article' ? 200 : 180,
              color: outputType === 'article' ? '#667eea' : '#f59e0b',
              viewType: 'free',
              tags: ['magic-cursor', outputType],
              // Unified node model fields
              outputId: outputId,
              outputData: output.data as Record<string, unknown>,
              generatedFrom: {
                nodeIds: magicGenerationTask.sourceNodeIds,
                snapshotContext,
              },
            };

            // Add the node via callback
            onNodeAdd?.(newNode);

            console.log('[KonvaCanvas] Created Super Card node:', newNode);
          }
        } catch (fetchError) {
          console.error('[KonvaCanvas] Failed to fetch output:', fetchError);
        }
      }

      // Clear generation state - only after processing valid event
      setMagicGenerationTask(null);
      setIsGeneratingMagic(false);
    },
    onGenerationError: (error) => {
      console.error('[KonvaCanvas] Magic generation error:', error);
      toast.error(
        'Generation failed',
        'Could not generate content. Please try again.'
      );
      setMagicGenerationTask(null);
      setIsGeneratingMagic(false);
    },
  });

  const getNodeIdFromEvent = (e: Konva.KonvaEventObject<DragEvent>) => {
    // The drag event target might be a child element (e.g., Rect inside Group)
    // We need to traverse up to find the Group with the node-{uuid} ID
    let target = e.target;
    while (target) {
      const id = target.id();
      if (id && id.startsWith('node-')) {
        return id.replace('node-', '');
      }
      target = target.getParent() as Konva.Node | null;
    }
    // Fallback: use target directly (shouldn't reach here normally)
    const id = e.target.id();
    return id.startsWith('node-') ? id.replace('node-', '') : id;
  };

  const handleNodeDragMoveWithMerge = useCallback(
    (e: Konva.KonvaEventObject<DragEvent>) => {
      const nodeId = getNodeIdFromEvent(e);
      console.log(
        '[Synthesis Debug] handleNodeDragMoveWithMerge called, nodeId:',
        nodeId
      );

      if (!nodeId) {
        console.warn('[Synthesis Debug] Could not get nodeId from event');
        return;
      }

      const draggedNode = nodes.find((n) => n.id === nodeId);
      if (!draggedNode) {
        console.warn('[Synthesis Debug] Could not find node:', nodeId);
        return;
      }

      const draggedWidth = draggedNode.width || 280;
      const draggedHeight = draggedNode.height || 200;

      // Find the draggable Group element to get its actual position
      // The event target might be this Group or we need to find the parent Group
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let groupNode: any = e.target;
      while (groupNode && !groupNode.id()?.startsWith('node-')) {
        groupNode = groupNode.getParent() as Konva.Node | null;
      }

      const x = groupNode ? groupNode.x() : e.target.x();
      const y = groupNode ? groupNode.y() : e.target.y();

      const draggedCenterX = x + draggedWidth / 2;
      const draggedCenterY = y + draggedHeight / 2;

      let closestNodeId: string | null = null;
      let closestDistance = Infinity;

      console.log(
        '[Synthesis Debug] Checking proximity against',
        nodes.length - 1,
        'other nodes, threshold:',
        MERGE_PROXIMITY_THRESHOLD
      );

      for (const node of nodes) {
        if (node.id === nodeId) continue;

        const nodeWidth = node.width || 280;
        const nodeHeight = node.height || 200;
        const nodeCenterX = node.x + nodeWidth / 2;
        const nodeCenterY = node.y + nodeHeight / 2;

        const distance = Math.sqrt(
          Math.pow(draggedCenterX - nodeCenterX, 2) +
            Math.pow(draggedCenterY - nodeCenterY, 2)
        );

        if (
          distance < closestDistance &&
          distance < MERGE_PROXIMITY_THRESHOLD
        ) {
          closestDistance = distance;
          closestNodeId = node.id;
          console.log(
            '[Synthesis Debug] Found close node:',
            node.id,
            'distance:',
            Math.round(distance)
          );
        }
      }

      if (closestNodeId && closestNodeId !== mergeTargetNodeId) {
        console.log(
          '[Synthesis Debug] ✅ Merge detected:',
          nodeId,
          '->',
          closestNodeId,
          'dist:',
          Math.round(closestDistance)
        );
      }

      console.log(
        '[Synthesis Debug] Setting mergeTargetNodeId:',
        closestNodeId,
        'draggedNodeId:',
        closestNodeId ? nodeId : null
      );
      setMergeTargetNodeId(closestNodeId);
      if (closestNodeId) setDraggedNodeId(nodeId);
    },
    [nodes, mergeTargetNodeId]
  );

  const handleNodeDragEndWithMerge = useCallback(
    (e: Konva.KonvaEventObject<DragEvent>) => {
      const nodeId = getNodeIdFromEvent(e);
      const x = e.target.x();
      const y = e.target.y();

      // Check for merge
      if (mergeTargetNodeId && draggedNodeId === nodeId) {
        // Merge detected - keep state for prompt
      } else {
        setDraggedNodeId(null);
        setMergeTargetNodeId(null);
      }

      // Always update position
      const targetNode = nodes.find((n) => n.id === nodeId);
      if (targetNode && onNodesChange) {
        const updatedNodes = nodes.map((n) =>
          n.id === nodeId ? { ...n, x, y } : n
        );
        onNodesChange(updatedNodes);
      }
    },
    [nodes, onNodesChange, mergeTargetNodeId, draggedNodeId]
  );

  // P1: Edge Reconnection Handlers
  const handleEdgeHandleDragMove = useCallback(
    (
      e: Konva.KonvaEventObject<DragEvent>,
      edgeId: string,
      type: 'source' | 'target'
    ) => {
      // Current pointer position relative to canvas
      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (!pointer) return;

      const canvasX = (pointer.x - viewport.x) / viewport.scale;
      const canvasY = (pointer.y - viewport.y) / viewport.scale;

      setReconnectingEdge({ edgeId, type, x: canvasX, y: canvasY });

      // Check for drop target (node) under cursor
      const targetNode = visibleNodes.find((node) => {
        const nodeWidth = node.width || 280;
        const nodeHeight = node.height || 200;
        return (
          canvasX >= node.x &&
          canvasX <= node.x + nodeWidth &&
          canvasY >= node.y &&
          canvasY <= node.y + nodeHeight
        );
      });

      setHoveredNodeId(targetNode ? targetNode.id : null);
    },
    [viewport, visibleNodes]
  );

  const handleEdgeHandleDragEnd = useCallback(
    (
      e: Konva.KonvaEventObject<DragEvent>,
      edge: CanvasEdge,
      type: 'source' | 'target'
    ) => {
      setReconnectingEdge(null);
      setHoveredNodeId(null);

      // Reset handle position visually (Konva keeps it at drop location otherwise)
      e.target.position({ x: 0, y: 0 });

      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (!pointer) return;

      const canvasX = (pointer.x - viewport.x) / viewport.scale;
      const canvasY = (pointer.y - viewport.y) / viewport.scale;

      // Find target node
      const targetNode = visibleNodes.find((node) => {
        const nodeWidth = node.width || 280;
        const nodeHeight = node.height || 200;
        return (
          canvasX >= node.x &&
          canvasX <= node.x + nodeWidth &&
          canvasY >= node.y &&
          canvasY <= node.y + nodeHeight
        );
      });

      if (targetNode) {
        // Don't allow self-loops if source===target (unless we want to support self-loops, but P2 says 'Prevent self-loops')
        // Actually P2.3 says 'Validation: Prevent self-loops (if desired)'
        // For now let's allow basic reconnect.

        const newEdge = { ...edge };

        if (type === 'source') {
          if (targetNode.id === edge.target) return; // No change
          newEdge.source = targetNode.id;
          newEdge.sourceAnchor = 'auto'; // Reset anchor to auto
        } else {
          if (targetNode.id === edge.source) return; // No change
          newEdge.target = targetNode.id;
          newEdge.targetAnchor = 'auto'; // Reset anchor to auto
        }

        // Check for duplicates
        const exists = edges.some(
          (e) =>
            e.id !== edge.id &&
            ((e.source === newEdge.source && e.target === newEdge.target) ||
              (e.source === newEdge.target && e.target === newEdge.source))
        );

        if (!exists && onEdgesChange) {
          onEdgesChange(edges.map((e) => (e.id === edge.id ? newEdge : e)));
        }
      }
    },
    [viewport, visibleNodes, edges, onEdgesChange]
  );

  const handleCancelMerge = () => {
    setMergeTargetNodeId(null);
    setDraggedNodeId(null);
  };

  const handleSynthesize = async (mode: SynthesisMode) => {
    if (!draggedNodeId || !mergeTargetNodeId) return;

    const sourceNodeIds = [draggedNodeId, mergeTargetNodeId];
    setIsSynthesizing(true);

    try {
      const targetNode = nodes.find((n) => n.id === mergeTargetNodeId);
      const draggedNode = nodes.find((n) => n.id === draggedNodeId);

      // Calculate position for result card (between the two nodes) - CANVAS coordinates
      const midX =
        targetNode && draggedNode
          ? (targetNode.x + draggedNode.x + (draggedNode.width || 280)) / 2
          : 400;
      const maxY =
        targetNode && draggedNode
          ? Math.max(
              targetNode.y + (targetNode.height || 200),
              draggedNode.y + (draggedNode.height || 200)
            ) + 50
          : 300;

      // Use canvas coordinates directly (not screen coords) for Konva rendering
      const resultPosition = { x: midX, y: maxY };

      // Call the synthesis API and get task_id (returned by synthesizeNodes)
      // The backend will generate the result and we poll/wait for it
      // For now, we'll extract content from the source nodes and create a mock pending result
      // This will be replaced with proper WebSocket handling

      const sourceContents = sourceNodeIds.map((id) => {
        const node = nodes.find((n) => n.id === id);
        return { title: node?.title || '', content: node?.content || '' };
      });

      // Start synthesis via API
      const response = await synthesizeNodes(
        sourceNodeIds,
        resultPosition,
        mode
      );

      // Set task ID to enable WebSocket listening
      if (response && response.task_id) {
        console.log('[Canvas] Synthesis task started:', response.task_id);
        setSynthesisTaskId(response.task_id);
      }

      // Create a pending result to show immediately
      // In production, this would come from WebSocket NODE_ADDED event
      const modeLabels = {
        connect: 'Connection Found',
        inspire: 'New Perspective',
        debate: 'Key Tension Identified',
      };

      setPendingSynthesisResult({
        id: `synthesis-${crypto.randomUUID()}`,
        title: modeLabels[mode],
        content: `Analyzing "${sourceContents[0].title}" and "${sourceContents[1].title}" to find ${mode === 'connect' ? 'connections' : mode === 'inspire' ? 'new perspectives' : 'tensions'}...`,
        recommendation: 'Processing...',
        keyRisk: 'Processing...',
        confidence: 'medium',
        themes: [],
        sourceNodeIds,
        mode,
        position: resultPosition,
      });

      // Note: In full implementation, WebSocket would update this with actual LLM result
      // For demo, we'll keep the loading state until user discards or adds
    } catch (e) {
      console.error(e);
      setPendingSynthesisResult(null);
    } finally {
      setIsSynthesizing(false);
      setMergeTargetNodeId(null);
      setDraggedNodeId(null);
    }
  };

  const handleNodeSave = (data: NoteData) => {
    if (editingNodeId) {
      if (onNodesChange) {
        const updatedNodes = nodes.map((n) =>
          n.id === editingNodeId
            ? { ...n, title: data.title, content: data.content }
            : n
        );
        onNodesChange(updatedNodes);
      }
    } else if (onNodeAdd) {
      // Use saved click position if available, otherwise use fallback
      const noteWidth = 220;
      const noteHeight = 160;

      let newX: number;
      let newY: number;

      if (onCreateNotePosition.current) {
        // Use the position where user clicked
        newX = onCreateNotePosition.current.x - noteWidth / 2; // Center the note on click
        newY = onCreateNotePosition.current.y - noteHeight / 2;
        onCreateNotePosition.current = null; // Clear after use
      } else {
        // Fallback: place at viewport position with offset
        const baseX = (viewport.x * -1 + 100) / viewport.scale;
        const baseY = (viewport.y * -1 + 100) / viewport.scale;
        const offset = 30;
        const existingNotesCount = nodes.filter(
          (n) => n.type === 'sticky'
        ).length;
        const offsetMultiplier = existingNotesCount % 5;
        newX = baseX + offsetMultiplier * offset;
        newY = baseY + offsetMultiplier * offset;
      }

      onNodeAdd({
        type: 'sticky',
        title: data.title,
        content: data.content,
        x: newX,
        y: newY,
        width: noteWidth,
        height: noteHeight,
        color: '#fef3c7',
        tags: [],
        viewType: 'free',
      });
    }
    setEditingNodeId(null);
    setIsCreatingNote(false);
  };

  const handleNodeEditCancel = () => {
    setEditingNodeId(null);
  };

  const handleStageMouseUp = (e: Konva.KonvaEventObject<MouseEvent>) => {
    // Phase 2: Handle Connection creation
    if (connectingFromNodeId && connectingLineEnd) {
      const stage = e.target.getStage();
      const pointer = stage?.getPointerPosition();
      if (pointer) {
        const canvasX = (pointer.x - viewport.x) / viewport.scale;
        const canvasY = (pointer.y - viewport.y) / viewport.scale;

        // Find target node under the mouse
        const targetNode = visibleNodes.find((node) => {
          const nodeWidth = node.width || 280;
          const nodeHeight = node.height || 200;
          return (
            canvasX >= node.x &&
            canvasX <= node.x + nodeWidth &&
            canvasY >= node.y &&
            canvasY <= node.y + nodeHeight &&
            node.id !== connectingFromNodeId
          );
        });

        if (targetNode) {
          // Check if edge already exists
          const edgeExists = edges.some(
            (e) =>
              (e.source === connectingFromNodeId &&
                e.target === targetNode.id) ||
              (e.source === targetNode.id && e.target === connectingFromNodeId)
          );

          if (!edgeExists) {
            // Create new edge with default label
            const newEdge: CanvasEdge = {
              id: `edge-${crypto.randomUUID()}`,
              source: connectingFromNodeId,
              target: targetNode.id,
              label: '',
              relationType:
                toolMode === 'logic_connect' ? 'related' : 'related', // 'structural' not in type
            };
            onEdgesChange([...edges, newEdge]);

            // Show label dialog
            const sourceNode = visibleNodes.find(
              (n) => n.id === connectingFromNodeId
            );
            if (sourceNode) {
              const midX =
                (sourceNode.x + (sourceNode.width || 280) + targetNode.x) / 2;
              const midY =
                (sourceNode.y +
                  (sourceNode.height || 200) / 2 +
                  (targetNode.y + (targetNode.height || 200) / 2)) /
                2;
              // Convert to screen coordinates
              const screenX = midX * viewport.scale + viewport.x;
              const screenY = midY * viewport.scale + viewport.y;

              if (toolMode === 'logic_connect') {
                setLinkTypeDialog({
                  edge: newEdge,
                  position: { x: screenX, y: screenY },
                });
                // Auto-switch back to select mode after creating a logic link
                onToolChange?.('select');
              }
              // Regular connect doesn't auto-open dialog
            }
          }
        }
      }
      setConnectingFromNodeId(null);
      setConnectingLineEnd(null);
      return;
    }

    if (isPanning) {
      // Sync React state from Konva stage position after panning ends
      const stage = stageRef.current;
      if (stage) {
        onViewportChange({
          ...viewport,
          x: stage.x(),
          y: stage.y(),
        });
      }
      setIsPanning(false);
    }

    if (selectionRect) {
      // Calculate Intersection using spatial index O(log N) query
      const box = selectionRect;
      // Optimization: only check intersection if box has size
      if (box.width > 0 || box.height > 0) {
        // Use spatial index for efficient box selection
        const intersectingItems = spatialIndex.search({
          minX: box.x,
          minY: box.y,
          maxX: box.x + box.width,
          maxY: box.y + box.height,
        });

        const selectedIds = intersectingItems.map(
          (item: SpatialItem) => item.nodeId
        );

        // Magic Mode: Show Intent Menu instead of just selecting
        if (toolMode === 'magic' && selectedIds.length > 0) {
          // Calculate screen position for Intent Menu (bottom-right of selection)
          const screenX = (box.x + box.width) * viewport.scale + viewport.x;
          const screenY = (box.y + box.height) * viewport.scale + viewport.y;

          setMagicSelection({
            rect: { x: box.x, y: box.y, width: box.width, height: box.height },
            nodeIds: selectedIds,
            screenPosition: { x: screenX + 8, y: screenY + 8 },
          });

          // Also update selection for visual feedback
          setSelectedNodeIds(new Set(selectedIds));
        } else {
          // Normal selection mode
          const newSelection = new Set(selectedNodeIds);
          intersectingItems.forEach((item: SpatialItem) => {
            newSelection.add(item.nodeId);
          });
          setSelectedNodeIds(newSelection);
        }
      }
      setSelectionRect(null);
    }
  };

  // Determine Cursor Style
  const getCursorStyle = () => {
    if (isPanning) return 'grabbing';
    if (toolMode === 'hand' || isSpacePressed) return 'grab';
    if (toolMode === 'magic') return 'crosshair'; // Magic mode always shows crosshair
    if (selectionRect) return 'crosshair';
    if (hoveredNodeId && toolMode === 'select') return 'move';
    return 'default';
  };

  // Handle Intent Menu action
  const handleIntentAction = useCallback(
    async (action: IntentAction) => {
      if (!magicSelection || !projectId) return;

      // Validate max nodes (50 limit per design)
      const MAX_NODES = 50;
      if (magicSelection.nodeIds.length > MAX_NODES) {
        console.warn(
          `[KonvaCanvas] Too many nodes selected (${magicSelection.nodeIds.length}). Max is ${MAX_NODES}.`
        );
        // TODO: Show toast notification
        return;
      }

      console.log(
        '[KonvaCanvas] Intent action:',
        action,
        'for nodes:',
        magicSelection.nodeIds
      );

      // Helper to extract content from different node types
      const extractNodeContent = (node: CanvasNode | undefined): string => {
        if (!node) return '';

        // Handle mindmap nodes - extract node labels
        if (node.type === 'mindmap') {
          try {
            const mindmapData =
              (node.outputData as {
                nodes?: Array<{ label: string; content?: string }>;
              }) || JSON.parse(node.content || '{}');
            if (mindmapData.nodes) {
              return mindmapData.nodes
                .map((n) => `${n.label}${n.content ? `: ${n.content}` : ''}`)
                .join('\n');
            }
          } catch {
            /* ignore parse errors */
          }
        }

        // Handle summary nodes - extract summary and key findings
        if (node.type === 'summary') {
          try {
            const summaryData =
              (node.outputData as {
                summary?: string;
                keyFindings?: Array<{ label: string; content: string }>;
              }) || JSON.parse(node.content || '{}');
            let content = summaryData.summary || '';
            if (summaryData.keyFindings) {
              content +=
                '\n\nKey Findings:\n' +
                summaryData.keyFindings
                  .map((f) => `- ${f.label}: ${f.content}`)
                  .join('\n');
            }
            return content;
          } catch {
            /* ignore parse errors */
          }
        }

        // Default: return regular content
        return node.content || '';
      };

      // Gather node data for generation (with type-specific content extraction)
      const nodeData = magicSelection.nodeIds
        .map((nodeId) => {
          const node = nodes.find((n) => n.id === nodeId);
          return {
            id: nodeId,
            title: node?.title || 'Untitled',
            content: extractNodeContent(node),
            type: node?.type || 'note', // Include type for backend context
          };
        })
        .filter((nd) => nd.content || nd.title);

      // Map intent action to output type
      const outputTypeMap: Record<IntentAction, OutputType> = {
        draft_article: 'article',
        action_list: 'action_list',
      };
      const outputType = outputTypeMap[action];

      // Store snapshot context for future refresh
      const snapshotContext = {
        x: magicSelection.rect.x,
        y: magicSelection.rect.y,
        width: magicSelection.rect.width,
        height: magicSelection.rect.height,
      };

      try {
        // Set loading state
        setIsGeneratingMagic(true);

        // Call the API to start generation
        const response = await outputsApi.generate(
          projectId,
          outputType,
          [], // No source IDs - using canvas node data
          action === 'draft_article' ? 'Generated Article' : 'Action Items',
          {
            node_data: nodeData,
            snapshot_context: snapshotContext,
          }
        );

        console.log('[KonvaCanvas] Generation started:', response);

        // Set the task ID to enable WebSocket listening
        setMagicGenerationTask({
          taskId: response.task_id,
          outputType: outputType as 'article' | 'action_list',
          snapshotContext,
          sourceNodeIds: magicSelection.nodeIds,
        });
      } catch (error) {
        console.error('[KonvaCanvas] Generation failed:', error);
        setIsGeneratingMagic(false);
        toast.error(
          'Generation failed',
          'Could not generate content. Please try again.'
        );
      }

      // Clear magic selection
      setMagicSelection(null);

      // Switch back to select mode
      onToolChange?.('select');
    },
    [magicSelection, projectId, nodes, onToolChange]
  );

  const handleIntentMenuClose = useCallback(() => {
    setMagicSelection(null);
  }, []);

  // Edge style configuration for different relation types
  interface EdgeStyleConfig {
    color: string;
    bgColor: string;
    strokeWidth: number;
    dash?: number[];
    icon?: string; // Icon name for edge midpoint
  }

  const EDGE_STYLES: Record<string, EdgeStyleConfig> = {
    // Core Q&A relationships
    answers: {
      color: '#10B981',
      bgColor: '#ECFDF5',
      strokeWidth: 2,
      icon: '✓',
    }, // Green - check
    prompts_question: {
      color: '#8B5CF6',
      bgColor: '#F5F3FF',
      strokeWidth: 2,
      dash: [8, 4],
      icon: '?',
    }, // Violet - question
    derives: {
      color: '#F59E0B',
      bgColor: '#FFFBEB',
      strokeWidth: 2,
      icon: '💡',
    }, // Amber - lightbulb

    // Logical relationships
    causes: { color: '#EF4444', bgColor: '#FEF2F2', strokeWidth: 3, icon: '→' }, // Red - arrow
    compares: {
      color: '#3B82F6',
      bgColor: '#EFF6FF',
      strokeWidth: 2,
      dash: [4, 4],
      icon: '⇆',
    }, // Blue - bidirectional
    supports: {
      color: '#059669',
      bgColor: '#ECFDF5',
      strokeWidth: 2,
      icon: '+',
    }, // Green - plus
    contradicts: {
      color: '#DC2626',
      bgColor: '#FEF2F2',
      strokeWidth: 2,
      icon: '×',
    }, // Red - cross

    // Evolution relationships
    revises: {
      color: '#EC4899',
      bgColor: '#FCE7F3',
      strokeWidth: 2,
      dash: [12, 6],
      icon: '✎',
    }, // Pink - edit
    extends: {
      color: '#06B6D4',
      bgColor: '#ECFEFF',
      strokeWidth: 2,
      icon: '↗',
    }, // Cyan - extend

    // Organization
    parks: {
      color: '#9CA3AF',
      bgColor: '#F3F4F6',
      strokeWidth: 1.5,
      dash: [4, 8],
      icon: '⏸',
    }, // Gray - pause
    groups: {
      color: '#7C3AED',
      bgColor: '#F5F3FF',
      strokeWidth: 1.5,
      dash: [2, 2],
      icon: '▢',
    }, // Purple - group
    belongs_to: { color: '#7C3AED', bgColor: '#F5F3FF', strokeWidth: 2 }, // Purple (legacy)
    related: { color: '#6B7280', bgColor: '#F3F4F6', strokeWidth: 2 }, // Gray (legacy)

    // User-defined
    custom: { color: '#6B7280', bgColor: '#F3F4F6', strokeWidth: 2 }, // Gray

    // Thinking Path edge types (for styling compatibility)
    branch: {
      color: '#F59E0B',
      bgColor: '#FFFBEB',
      strokeWidth: 2.5,
      icon: '↳',
    }, // Amber - branch from insight
    progression: {
      color: '#8B5CF6',
      bgColor: '#F5F3FF',
      strokeWidth: 2.5,
      dash: [8, 4],
      icon: '→',
    }, // Violet - topic follow-up
  };

  // Get edge style with fallback
  const getEdgeStyle = (
    relationType?: string,
    edgeType?: string
  ): EdgeStyleConfig => {
    // Check edge type first (for thinking path edges), then relation type
    if (edgeType && EDGE_STYLES[edgeType]) {
      return EDGE_STYLES[edgeType];
    }
    return EDGE_STYLES[relationType || 'related'] || EDGE_STYLES.related;
  };

  // Legacy function for backwards compatibility
  const getEdgeLabelStyle = (relationType?: string, edgeType?: string) => {
    const style = getEdgeStyle(relationType, edgeType);
    return { color: style.color, bgColor: style.bgColor };
  };

  // Draw connections with labels and relation-specific styling
  const renderEdges = () => {
    return edges.map((edge, index) => {
      const source = visibleNodes.find((n) => n.id === edge.source);
      const target = visibleNodes.find((n) => n.id === edge.target);

      if (!source || !target) return null;

      const isSelected = selectedEdgeId === edge.id;
      const isReconnecting = reconnectingEdge?.edgeId === edge.id;

      // === P0: Dynamic anchor selection ===
      const sourceAnchorDir = resolveAnchor(edge, source, target, 'source');
      const targetAnchorDir = resolveAnchor(edge, source, target, 'target');

      let sourceAnchor = getAnchorPoint(source, sourceAnchorDir);
      let targetAnchor = getAnchorPoint(target, targetAnchorDir);

      // === P1: Reconnection Live Preview ===
      // If we are dragging an endpoint, use the cursor position instead of the anchor
      if (
        isReconnecting &&
        reconnectingEdge &&
        reconnectingEdge.x !== undefined &&
        reconnectingEdge.y !== undefined
      ) {
        if (reconnectingEdge.type === 'source') {
          // Keep direction for now, or calculate based on relative pos
          sourceAnchor = {
            x: reconnectingEdge.x,
            y: reconnectingEdge.y,
            direction: sourceAnchorDir,
          };
        } else {
          targetAnchor = {
            x: reconnectingEdge.x,
            y: reconnectingEdge.y,
            direction: targetAnchorDir,
          };
        }
      }

      // === P0: Routing type selection ===
      const routingType = edge.routingType || 'bezier'; // Default to bezier for backwards compatibility

      let pathPoints: number[] = [];
      if (routingType === 'straight') {
        pathPoints = getStraightPath(sourceAnchor, targetAnchor);
      } else if (routingType === 'orthogonal') {
        // P1: Orthogonal routing
        // For now pass empty obstacles, will add collision detection later
        pathPoints = getOrthogonalPath(sourceAnchor, targetAnchor, []);
      } else {
        pathPoints = getBezierPath(sourceAnchor, targetAnchor);
      }

      // Calculate midpoint for label/icon placement
      const midX = (sourceAnchor.x + targetAnchor.x) / 2;
      const midY = (sourceAnchor.y + targetAnchor.y) / 2;

      // Get edge style configuration
      const baseEdgeStyle = getEdgeStyle(edge.relationType, edge.type);

      // Apply overrides from edge data
      const edgeStyle = {
        color: edge.color || baseEdgeStyle.color,
        bgColor: baseEdgeStyle.bgColor, // Background usually doesn't need override, but could add if needed
        strokeWidth: edge.strokeWidth || baseEdgeStyle.strokeWidth,
        dash: edge.strokeDash || baseEdgeStyle.dash,
        icon: baseEdgeStyle.icon,
      };

      const hasLabel = edge.label && edge.label.trim().length > 0;

      // Determine if this edge should have special styling
      const hasRelationType =
        !!edge.relationType &&
        edge.relationType !== 'related' &&
        edge.relationType !== 'custom';
      const isThinkingPathEdge =
        edge.type === 'branch' || edge.type === 'progression';
      const hasCustomStyle =
        !!edge.color || !!edge.strokeWidth || !!edge.strokeDash;

      const shouldHighlight =
        hasLabel ||
        hasRelationType ||
        isThinkingPathEdge ||
        hasCustomStyle ||
        isSelected;

      // Check for bidirectional edge (compares)
      const isBidirectional =
        edge.direction === 'bidirectional' || edge.relationType === 'compares';

      // === P0: Dynamic arrow points ===
      // If reconnecting target, arrow should follow cursor
      const targetArrowPoints = getArrowPoints(targetAnchor);
      const sourceArrowPoints = isBidirectional
        ? getArrowPoints(sourceAnchor)
        : null;

      return (
        <Group
          key={edge.id || `${edge.source}-${edge.target}-${index}`}
          onClick={(e) => {
            e.cancelBubble = true;
            setSelectedEdgeId(edge.id || null);
          }}
          onTap={(e) => {
            e.cancelBubble = true;
            setSelectedEdgeId(edge.id || null);
          }}
        >
          {/* Hit area for easier selection - invisible wide stroke */}
          <Line
            points={pathPoints}
            stroke="transparent"
            strokeWidth={20}
            tension={routingType === 'bezier' ? 0.5 : 0}
            bezier={routingType === 'bezier'}
          />

          {/* Selection Halo */}
          {isSelected && (
            <Line
              points={pathPoints}
              stroke="#3B82F6"
              strokeWidth={(edgeStyle.strokeWidth || 2) + 4}
              opacity={0.3}
              tension={routingType === 'bezier' ? 0.5 : 0}
              bezier={routingType === 'bezier'}
            />
          )}

          {/* Main edge line */}
          <Line
            points={pathPoints}
            stroke={shouldHighlight ? edgeStyle.color : '#94A3B8'}
            strokeWidth={edgeStyle.strokeWidth}
            dash={edgeStyle.dash}
            tension={routingType === 'bezier' ? 0.5 : 0}
            bezier={routingType === 'bezier'}
          />

          {/* Arrow at target end */}
          <Line
            points={targetArrowPoints}
            stroke={shouldHighlight ? edgeStyle.color : '#94A3B8'}
            strokeWidth={edgeStyle.strokeWidth}
            lineCap="round"
            lineJoin="round"
          />

          {/* Arrow at source end for bidirectional edges */}
          {isBidirectional && sourceArrowPoints && (
            <Line
              points={sourceArrowPoints}
              stroke={edgeStyle.color}
              strokeWidth={edgeStyle.strokeWidth}
              lineCap="round"
              lineJoin="round"
            />
          )}

          {/* Edge Label (AI-generated or user-defined) */}
          {(hasLabel || edgeStyle.icon) && (
            <Group
              x={midX}
              y={midY}
              onClick={(e) => {
                e.cancelBubble = true;
                const stage = e.target.getStage();
                const pointer = stage?.getPointerPosition();

                // If the edge selection bubble didn't happen first, we ensure it's selected
                setSelectedEdgeId(edge.id || null);

                if (pointer) {
                  setEdgeLabelDialog({
                    edge,
                    position: pointer, // Use screen coords or stage coords? Dialog uses fixed div position, likely needs client position.
                    // IMPORTANT: The existing code for setEdgeLabelDialog expects screen coordinates because the dialog is an HTML overlay.
                    // pointer is {x, y} relative to stage container? No, getPointerPosition is relative to stage container.
                    // The dialog is positioned with position: absolute LEFT/TOP.
                    // If the dialog is inside a container, we need coords relative to that container.
                    // Looking at existing usage (line 1785), it receives event properties.
                    // Let's use `e.evt.clientX` / `e.evt.clientY` which are screen coords if possible.
                    // Konva event `e.evt` is the native MouseEvent.
                  });
                }
              }}
            >
              {hasLabel ? (
                <>
                  <Rect
                    x={-edge.label!.length * 4 - 10}
                    y={-12}
                    width={edge.label!.length * 8 + 20}
                    height={24}
                    fill={edgeStyle.bgColor}
                    stroke={edgeStyle.color}
                    strokeWidth={1}
                    cornerRadius={12}
                    shadowColor="rgba(0,0,0,0.1)"
                    shadowBlur={4}
                    shadowOffsetY={2}
                  />
                  {edgeStyle.icon && (
                    <Text
                      x={-edge.label!.length * 4 - 6}
                      y={-8}
                      text={edgeStyle.icon}
                      fontSize={12}
                      fill={edgeStyle.color}
                    />
                  )}
                  <Text
                    x={
                      edgeStyle.icon
                        ? -edge.label!.length * 4 + 8
                        : -edge.label!.length * 4
                    }
                    y={-7}
                    text={edge.label}
                    fontSize={11}
                    fill={edgeStyle.color}
                    fontStyle="600"
                  />
                </>
              ) : (
                <>
                  <Circle
                    radius={12}
                    fill={edgeStyle.bgColor}
                    stroke={edgeStyle.color}
                    strokeWidth={1}
                  />
                  <Text
                    x={-6}
                    y={-7}
                    text={edgeStyle.icon}
                    fontSize={12}
                    fill={edgeStyle.color}
                    align="center"
                  />
                </>
              )}
            </Group>
          )}

          {/* P1: Reconnection Handles (only if selected) */}
          {isSelected && (
            <>
              {/* Source Handle */}
              <Circle
                x={sourceAnchor.x}
                y={sourceAnchor.y}
                radius={6}
                fill="#3B82F6"
                stroke="white"
                strokeWidth={2}
                draggable
                onDragMove={(e) =>
                  handleEdgeHandleDragMove(e, edge.id || '', 'source')
                }
                onDragEnd={(e) => handleEdgeHandleDragEnd(e, edge, 'source')}
                onMouseEnter={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'crosshair';
                }}
                onMouseLeave={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'default';
                }}
              />
              {/* Target Handle */}
              <Circle
                x={targetAnchor.x}
                y={targetAnchor.y}
                radius={6}
                fill="#3B82F6"
                stroke="white"
                strokeWidth={2}
                draggable
                onDragMove={(e) =>
                  handleEdgeHandleDragMove(e, edge.id || '', 'target')
                }
                onDragEnd={(e) => handleEdgeHandleDragEnd(e, edge, 'target')}
                onMouseEnter={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'crosshair';
                }}
                onMouseLeave={() => {
                  const container = stageRef.current?.container();
                  if (container) container.style.cursor = 'default';
                }}
              />
            </>
          )}
        </Group>
      );
    });
  };

  return (
    <div
      style={{
        flexGrow: 1,
        minWidth: 0,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Canvas Container */}
      <div
        ref={containerRef}
        style={{
          flexGrow: 1,
          backgroundColor: '#FAFAFA',
          position: 'relative',
          overflow: 'hidden',
        }}
        onContextMenu={(e) => {
          // Prevent browser default context menu at container level
          // The Konva Stage's onContextMenu will handle showing our custom menu
          e.preventDefault();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = 'copy';
          if (dragContentRef.current && containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            const screenX = e.clientX - rect.left;
            const screenY = e.clientY - rect.top;
            const canvasX = (screenX - viewport.x) / viewport.scale;
            const canvasY = (screenY - viewport.y) / viewport.scale;
            setDragPreview({
              x: canvasX,
              y: canvasY,
              content: dragContentRef.current,
            });
          }
        }}
        onDragLeave={() => setDragPreview(null)}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (!containerRef.current) return;
          const rect = containerRef.current.getBoundingClientRect();
          const screenX = e.clientX - rect.left;
          const screenY = e.clientY - rect.top;
          const canvasX = (screenX - viewport.x) / viewport.scale;
          const canvasY = (screenY - viewport.y) / viewport.scale;

          const cardWidth = 280;
          const cardHeight = 200;
          const centeredX = canvasX - cardWidth / 2;
          const centeredY = canvasY - cardHeight / 2;

          let handled = false;
          const jsonData = e.dataTransfer.getData('application/json');

          if (jsonData && onNodeAdd) {
            try {
              const data = JSON.parse(jsonData);

              if (data.type === 'ai_response') {
                onNodeAdd({
                  type: 'ai_insight',
                  title: data.source?.query || 'AI Insight',
                  content: data.content,
                  x: centeredX,
                  y: centeredY,
                  width: cardWidth,
                  height: cardHeight,
                  color: 'blue',
                  tags: ['#ai'],
                });
                handled = true;
              }
              // Handle document drops from sidebar
              if (data.type === 'document') {
                const nodeData = {
                  type: 'knowledge',

                  title: data.title,
                  content: '', // Will be populated with summary if available
                  x: centeredX,
                  y: centeredY,
                  width: cardWidth,
                  height: cardHeight,
                  color: 'red',
                  tags: ['#source'],
                  sourceId: data.documentId,
                  fileMetadata: {
                    fileType: data.fileType || 'pdf',
                    pageCount: data.pageCount,
                    thumbnailUrl: data.thumbnailUrl,
                  },
                  viewType: 'free' as const,
                  subType: 'source' as const,
                };
                onNodeAdd(nodeData);
                handled = true;
              }

              // Handle URL drops from sidebar (YouTube, Bilibili, Douyin, Web)
              if (data.type === 'url') {
                // Map platform to fileType
                const platformToFileType: Record<
                  string,
                  'youtube' | 'video' | 'bilibili' | 'douyin' | 'web'
                > = {
                  youtube: 'youtube',
                  bilibili: 'bilibili',
                  douyin: 'douyin',
                  web: 'web',
                };
                const fileType = platformToFileType[data.platform] || 'web';

                // Video cards are wider than regular cards for better thumbnail display
                const videoCardWidth = 320;
                // Calculate proper height for video cards based on 16:9 thumbnail
                const videoCardHeight =
                  48 + ((videoCardWidth - 32) * 9) / 16 + 90 + 44 + 20; // header + thumb + info + link + padding

                const nodeData = {
                  type: 'knowledge',
                  title: data.title || data.url,
                  content: data.content || '',
                  x: centeredX - (videoCardWidth - cardWidth) / 2, // Center the wider card
                  y: centeredY,
                  width: videoCardWidth,
                  height: Math.ceil(videoCardHeight), // Dynamic height for video cards
                  color: fileType === 'youtube' ? 'red' : 'blue',
                  tags: [`#${data.platform || 'url'}`],
                  sourceId: data.id,
                  fileMetadata: {
                    fileType: fileType,
                    thumbnailUrl: data.thumbnailUrl,
                    videoId: data.videoId || data.metadata?.videoId,
                    duration: data.duration || data.metadata?.duration,
                    channelName: data.channelName || data.metadata?.channelName,
                    viewCount: data.viewCount || data.metadata?.viewCount,
                    publishedAt: data.publishedAt || data.metadata?.publishedAt,
                    sourceUrl: data.url,
                  },
                  viewType: 'free' as const,
                  subType: 'source' as const,
                };
                onNodeAdd(nodeData);
                handled = true;
              }
            } catch (err) {
              console.error('[KonvaCanvas] onDrop - Error parsing JSON:', err);
            }
          }

          if (!handled && onNodeAdd) {
            const text = e.dataTransfer.getData('text/plain');
            if (text) {
              onNodeAdd({
                type: 'card',
                title: 'New Insight',
                content: text,
                x: centeredX,
                y: centeredY,
                width: cardWidth,
                height: cardHeight,
                color: 'blue',
                tags: ['#from-drag'],
              });
            }
          }
          setDragPreview(null);
        }}
      >
        {/* Context Menu for Canvas Background */}
        {contextMenu && !contextMenu.nodeId && !contextMenu.sectionId && (
          <CanvasContextMenu
            open={true}
            x={contextMenu.x}
            y={contextMenu.y}
            onClose={() => setContextMenu(null)}
            onOpenImport={onOpenImport || (() => {})}
            onAddStickyNote={handleCreateNote}
            viewport={viewport}
            canvasContainerRef={containerRef}
          />
        )}

        {/* Existing Menu for Nodes/Sections */}
        {contextMenu && (contextMenu.nodeId || contextMenu.sectionId) && (
          <Menu
            open={Boolean(contextMenu)}
            onClose={() => setContextMenu(null)}
            anchorReference="anchorPosition"
            anchorPosition={
              contextMenu
                ? { top: contextMenu.y, left: contextMenu.x }
                : undefined
            }
          >
            {contextMenu.nodeId && (
              <MenuItem
                onClick={() => {
                  setEditingNodeId(contextMenu.nodeId!);
                  setContextMenu(null);
                }}
                style={{ fontSize: 14 }}
              >
                <EditIcon size={16} style={{ marginRight: 8 }} />
                Edit
              </MenuItem>
            )}

            {contextMenu.nodeId && studioCurrentView === 'thinking' && (
              <MenuItem
                onClick={() => {
                  if (contextMenu.nodeId) promoteNode(contextMenu.nodeId);
                  setContextMenu(null);
                }}
                style={{ fontSize: 14 }}
              >
                <ArrowUpwardIcon size={14} style={{ marginRight: 8 }} />
                提升到自由画布
              </MenuItem>
            )}
            {/* Phase 4: Extract Insights for Source Nodes */}
            {contextMenu.nodeId &&
              (() => {
                const node = visibleNodes.find(
                  (n) => n.id === contextMenu.nodeId
                );
                return node?.subType === 'source';
              })() && (
                <MenuItem
                  onClick={() => {
                    const sourceNode = visibleNodes.find(
                      (n) => n.id === contextMenu.nodeId
                    );
                    if (!sourceNode) return;

                    // Generate mock insights with radial layout
                    const insights = [
                      {
                        title: '核心概念 1',
                        content: `从 "${sourceNode.title}" 中提取的核心概念。这是一个自动生成的洞察点。`,
                      },
                      {
                        title: '核心概念 2',
                        content:
                          '另一个重要的知识点。代表文档中的关键论述或结论。',
                      },
                      {
                        title: '关联主题',
                        content: '与主题相关的延伸内容。可用于进一步探索。',
                      },
                      {
                        title: '待验证观点',
                        content: '需要进一步确认的内容。建议查阅更多资料。',
                      },
                      {
                        title: '总结',
                        content: `"${sourceNode.title}" 的主要贡献和价值总结。`,
                      },
                    ];

                    // Radial layout calculation
                    const centerX =
                      sourceNode.x + (sourceNode.width || 280) / 2;
                    const centerY =
                      sourceNode.y + (sourceNode.height || 200) / 2;
                    const radius = 350; // Distance from center
                    const angleStep = (2 * Math.PI) / insights.length;
                    const startAngle = -Math.PI / 2; // Start from top

                    const newNodes: typeof nodes = [];
                    const newEdges: CanvasEdge[] = [];

                    insights.forEach((insight, index) => {
                      const angle = startAngle + angleStep * index;
                      const nodeWidth = 240;
                      const nodeHeight = 160;

                      const nodeId = `insight-${crypto.randomUUID()}-${index}`;
                      const x =
                        centerX + radius * Math.cos(angle) - nodeWidth / 2;
                      const y =
                        centerY + radius * Math.sin(angle) - nodeHeight / 2;

                      newNodes.push({
                        id: nodeId,
                        type: 'insight',
                        title: insight.title,
                        content: insight.content,
                        x,
                        y,
                        width: nodeWidth,
                        height: nodeHeight,
                        color: 'yellow',
                        tags: ['#extracted'],
                        sourceId: sourceNode.sourceId || sourceNode.id,
                        viewType: currentView as 'free' | 'thinking',
                      });

                      // Create edge from source to this insight
                      newEdges.push({
                        id: `edge-${crypto.randomUUID()}-${index}`,
                        source: sourceNode.id,
                        target: nodeId,
                        label: index === insights.length - 1 ? '总结' : '',
                        relationType:
                          index === insights.length - 1
                            ? 'belongs_to'
                            : 'related',
                      });
                    });

                    // Add all new nodes and edges
                    onNodesChange([...nodes, ...newNodes]);
                    onEdgesChange([...edges, ...newEdges]);

                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14 }}
                >
                  <AutoAwesomeIcon size={14} style={{ marginRight: 8 }} />
                  提取洞察 (Extract Insights)
                </MenuItem>
              )}
            {/* Verify Relation (2 nodes) */}
            {selectedNodeIds.size === 2 &&
              contextMenu.nodeId &&
              selectedNodeIds.has(contextMenu.nodeId) && (
                <MenuItem
                  onClick={async () => {
                    const selected = visibleNodes.filter((n) =>
                      selectedNodeIds.has(n.id)
                    );
                    if (selected.length === 2) {
                      const [source, target] = selected;
                      const edge = edges.find(
                        (e) =>
                          (e.source === source.id && e.target === target.id) ||
                          (e.source === target.id && e.target === source.id)
                      );
                      const relationType = edge?.relationType || 'related';

                      try {
                        // Using alert for MVP feedback
                        const result = await canvasApi.verifyRelation(
                          source.content || '',
                          target.content || '',
                          relationType
                        );
                        alert(
                          `Verification Result:\n\nValid: ${result.valid}\nConfidence: ${result.confidence}\nReasoning: ${result.reasoning}`
                        );
                      } catch (err) {
                        console.error('Verification failed:', err);
                        const message =
                          err instanceof Error ? err.message : String(err);
                        alert(`Verification failed: ${message}`);
                      }
                    }
                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14 }}
                >
                  <CheckIcon size={14} style={{ marginRight: 8 }} />
                  验证关系 (Verify)
                </MenuItem>
              )}

            {/* Phase 3: Create Group from Selection */}
            {selectedNodeIds.size >= 2 &&
              contextMenu.nodeId &&
              selectedNodeIds.has(contextMenu.nodeId) && (
                <MenuItem
                  onClick={() => {
                    // Get all selected nodes
                    const selectedNodes = visibleNodes.filter((n) =>
                      selectedNodeIds.has(n.id)
                    );
                    if (selectedNodes.length < 2) return;

                    // Calculate bounding box
                    let minX = Infinity,
                      minY = Infinity,
                      maxX = -Infinity,
                      maxY = -Infinity;
                    selectedNodes.forEach((node) => {
                      minX = Math.min(minX, node.x);
                      minY = Math.min(minY, node.y);
                      maxX = Math.max(maxX, node.x + (node.width || 280));
                      maxY = Math.max(maxY, node.y + (node.height || 200));
                    });

                    const padding = 24;
                    const headerHeight = 48;

                    // Create new section
                    const sectionId = `section-${crypto.randomUUID()}`;
                    const newSection = {
                      id: sectionId,
                      title: `组 (${selectedNodes.length} 个节点)`,
                      viewType: currentView as 'free' | 'thinking',
                      isCollapsed: false,
                      nodeIds: Array.from(selectedNodeIds),
                      x: minX - padding,
                      y: minY - padding - headerHeight,
                      width: maxX - minX + padding * 2,
                      height: maxY - minY + padding * 2 + headerHeight,
                    };

                    addSection(newSection);

                    // Update nodes with sectionId
                    const updatedNodes = nodes.map((node) =>
                      selectedNodeIds.has(node.id)
                        ? { ...node, sectionId }
                        : node
                    );
                    onNodesChange(updatedNodes);

                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14 }}
                >
                  <LayersIcon size={14} style={{ marginRight: 8 }} />
                  创建分组 ({selectedNodeIds.size})
                </MenuItem>
              )}
            {contextMenu.nodeId && (
              <MenuItem
                onClick={() => {
                  if (contextMenu.nodeId) {
                    // If the right-clicked node is in selection, delete all selected via API
                    // If not, delete only this one
                    if (selectedNodeIds.has(contextMenu.nodeId)) {
                      // Delete all selected nodes via API
                      selectedNodeIds.forEach((nodeId) => {
                        handleDeleteNode(nodeId).catch((err) => {
                          console.error('Failed to delete node:', err);
                          alert(
                            `Failed to delete node: ${err instanceof Error ? err.message : 'Unknown error'}`
                          );
                        });
                      });
                      setSelectedNodeIds(new Set());
                    } else {
                      // Delete single node via API
                      handleDeleteNode(contextMenu.nodeId).catch((err) => {
                        console.error('Failed to delete node:', err);
                        alert(
                          `Failed to delete node: ${err instanceof Error ? err.message : 'Unknown error'}`
                        );
                      });
                    }
                  }
                  setContextMenu(null);
                }}
                style={{ fontSize: 14, color: '#DC2626' }}
              >
                <DeleteIcon size={14} style={{ marginRight: 8 }} />
                Delete Node{' '}
                {selectedNodeIds.size > 1 &&
                selectedNodeIds.has(contextMenu.nodeId!)
                  ? `(${selectedNodeIds.size})`
                  : ''}
              </MenuItem>
            )}
            {contextMenu.sectionId && (
              <>
                <MenuItem
                  onClick={() => {
                    if (contextMenu.sectionId) {
                      setCanvasSections((prev) =>
                        prev.map((s) =>
                          s.id === contextMenu.sectionId
                            ? { ...s, isCollapsed: !s.isCollapsed }
                            : s
                        )
                      );
                    }
                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14 }}
                >
                  折叠/展开Section
                </MenuItem>
                <MenuItem
                  onClick={() => {
                    if (contextMenu.sectionId)
                      deleteSection(contextMenu.sectionId);
                    setContextMenu(null);
                  }}
                  style={{ fontSize: 14, color: '#DC2626' }}
                >
                  删除Section
                </MenuItem>
              </>
            )}
          </Menu>
        )}

        {/* Phase 2: Edge Label Dialog */}
        {edgeLabelDialog && (
          <Surface
            elevation={4}
            radius="md"
            style={{
              position: 'absolute',
              left: edgeLabelDialog.position.x,
              top: edgeLabelDialog.position.y,
              transform: 'translate(-50%, -50%)',
              padding: 16,
              minWidth: 240,
              zIndex: 1100,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 12,
              }}
            >
              <UiText variant="h6" style={{ fontWeight: 600 }}>
                连接关系
              </UiText>
              <div style={{ display: 'flex', gap: 4 }}>
                <IconButton
                  size="sm"
                  color="danger"
                  variant="ghost"
                  onClick={() => {
                    if (onEdgesChange) {
                      onEdgesChange(
                        edges.filter((e) => e.id !== edgeLabelDialog.edge.id)
                      );
                    }
                    setEdgeLabelDialog(null);
                    setSelectedEdgeId(null);
                  }}
                  title="删除连接 (Delete Connection)"
                >
                  <DeleteIcon size={16} />
                </IconButton>
                <IconButton
                  size="sm"
                  variant="ghost"
                  onClick={() => setEdgeLabelDialog(null)}
                >
                  <CloseIcon size={16} />
                </IconButton>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'row',
                gap: 4,
                flexWrap: 'wrap',
                marginBottom: 12,
              }}
            >
              {[
                { type: 'supports', label: '支持', color: '#059669' },
                { type: 'contradicts', label: '反对', color: '#DC2626' },
                { type: 'causes', label: '导致', color: '#D97706' },
                { type: 'belongs_to', label: '属于', color: '#7C3AED' },
                { type: 'related', label: '相关', color: '#6B7280' },
              ].map(({ type, label, color }) => (
                <Chip
                  key={type}
                  label={label}
                  size="sm"
                  onClick={() => {
                    const updatedEdges = edges.map((e) =>
                      e.id === edgeLabelDialog.edge.id
                        ? {
                            ...e,
                            label,
                            relationType: type as CanvasEdge['relationType'],
                          }
                        : e
                    );
                    onEdgesChange(updatedEdges);
                    setEdgeLabelDialog(null);
                  }}
                  style={{
                    borderColor: color,
                    color: color,
                    cursor: 'pointer',
                  }}
                  variant="outlined"
                />
              ))}
            </div>

            <TextField
              value=""
              placeholder="自定义标签..."
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const value = e.currentTarget.value.trim();
                  if (value) {
                    const updatedEdges = edges.map((edge) =>
                      edge.id === edgeLabelDialog.edge.id
                        ? {
                            ...edge,
                            label: value,
                            relationType: 'custom' as const,
                          }
                        : edge
                    );
                    onEdgesChange(updatedEdges);
                  }
                  setEdgeLabelDialog(null);
                }
              }}
              style={{ fontSize: 13 }}
            />
          </Surface>
        )}

        {/* Logic Link Dialog */}
        {linkTypeDialog && (
          <LinkTypeDialog
            position={linkTypeDialog.position}
            onSelect={(type, label) => {
              const updatedEdges = edges.map((e) =>
                e.id === linkTypeDialog.edge.id
                  ? {
                      ...e,
                      relationType: type as CanvasEdge['relationType'],
                      label: label || e.label,
                    }
                  : e
              );
              onEdgesChange(updatedEdges);
              setLinkTypeDialog(null);
            }}
            onCancel={() => {
              // Delete the temporary edge if cancelled
              onEdgesChange(
                edges.filter((e) => e.id !== linkTypeDialog.edge.id)
              );
              setLinkTypeDialog(null);
            }}
          />
        )}

        <Stage
          ref={stageRef}
          width={dimensions.width}
          height={dimensions.height}
          x={viewport.x}
          y={viewport.y}
          scaleX={viewport.scale}
          scaleY={viewport.scale}
          onWheel={handleWheel}
          onMouseDown={handleStageMouseDown}
          onMouseMove={handleStageMouseMove}
          onMouseUp={handleStageMouseUp}
          onDblClick={(e) => {
            // Check if clicked on empty stage
            const clickedOnEmpty = e.target === e.target.getStage();
            if (clickedOnEmpty && onNodeAdd) {
              const stage = e.target.getStage();
              const pointer = stage?.getPointerPosition();
              if (pointer) {
                const x = (pointer.x - viewport.x) / viewport.scale;
                const y = (pointer.y - viewport.y) / viewport.scale;

                onNodeAdd({
                  type: 'sticky', // Default to sticky note
                  title: '',
                  content: 'New Note',
                  x: x - 100, // Center approx (width/2)
                  y: y - 75, // Center approx (height/2)
                  width: 200,
                  height: 150,
                  color: 'yellow',
                  tags: [],
                });
              }
            }
          }}
          onMouseLeave={() => {
            handleStageMouseUp({} as Konva.KonvaEventObject<MouseEvent>);
            // Clear connection state on mouse leave
            setConnectingFromNodeId(null);
            setConnectingLineEnd(null);
          }}
          onContextMenu={(e) => {
            // Handle context menu for Stage (empty space)
            // Prevent default context menu
            e.evt.preventDefault();

            // If we are over a node or section, that handler will have fired first and called stopPropagation?
            // Actually, Konva event bubbling: Node -> Group -> Layer -> Stage.
            // If Node/Group handler calls cancelBubble, Stage handler won't see it?
            // Correct.

            // So this handler is for when we clicked on Stage background.
            setContextMenu({ x: e.evt.clientX, y: e.evt.clientY });
          }}
          style={{ cursor: getCursorStyle() }}
        >
          {/* Background Layer */}
          <Layer>
            <Rect
              x={-viewport.x / viewport.scale - 5000}
              y={-viewport.y / viewport.scale - 5000}
              width={10000}
              height={10000}
              fill="#FAFAFA"
            />
            {/* Infinite Dot Grid - Optimized with single Shape */}
            <GridBackground viewport={viewport} dimensions={dimensions} />
          </Layer>

          {/* Content Layer */}
          <Layer>
            {/* Sections */}
            {visibleSections.map((section) => {
              const sectionNodes = visibleNodes.filter(
                (n) => n.sectionId === section.id
              );
              if (sectionNodes.length === 0) return null;

              let minX = Infinity,
                minY = Infinity,
                maxX = -Infinity,
                maxY = -Infinity;
              sectionNodes.forEach((node) => {
                minX = Math.min(minX, node.x);
                minY = Math.min(minY, node.y);
                maxX = Math.max(maxX, node.x + (node.width || 280));
                maxY = Math.max(maxY, node.y + (node.height || 200));
              });

              const headerHeight = 48;
              const padding = 16;
              const contentWidth = maxX - minX + padding * 2;
              const contentHeight = maxY - minY + padding * 2;
              const totalHeight =
                headerHeight + (section.isCollapsed ? 0 : contentHeight);

              return (
                <Group
                  key={section.id}
                  x={section.x || minX - padding}
                  y={section.y || minY - padding - headerHeight}
                  onContextMenu={(e) => {
                    e.evt.preventDefault();
                    e.cancelBubble = true; // Stop propagation to stage
                    setContextMenu({
                      x: e.evt.clientX,
                      y: e.evt.clientY,
                      sectionId: section.id,
                    });
                  }}
                >
                  <Rect
                    width={contentWidth}
                    height={totalHeight}
                    fill="#F3F4F6"
                    cornerRadius={12}
                    stroke="#E5E7EB"
                    strokeWidth={1}
                    shadowColor="black"
                    shadowBlur={8}
                    shadowOpacity={0.08}
                    shadowOffsetY={2}
                  />
                  <Rect
                    width={contentWidth}
                    height={headerHeight}
                    fill="#FFFFFF"
                    cornerRadius={[12, 12, 0, 0]}
                    onClick={() => {
                      setCanvasSections((prev) =>
                        prev.map((s) =>
                          s.id === section.id
                            ? { ...s, isCollapsed: !s.isCollapsed }
                            : s
                        )
                      );
                    }}
                  />
                  <Text x={16} y={16} text="🌱" fontSize={18} />
                  <Text
                    x={48}
                    y={18}
                    width={contentWidth - 100}
                    text={section.title}
                    fontSize={14}
                    fontStyle="bold"
                    fill="#1F2937"
                    ellipsis
                  />
                  <Text
                    x={contentWidth - 40}
                    y={18}
                    text={section.isCollapsed ? '▶' : '▼'}
                    fontSize={12}
                    fill="#6B7280"
                  />
                </Group>
              );
            })}

            {/* Edges */}
            {renderEdges()}

            {/* Phase 2: Temporary Connection Line */}
            {connectingFromNodeId &&
              connectingLineEnd &&
              (() => {
                const sourceNode = visibleNodes.find(
                  (n) => n.id === connectingFromNodeId
                );
                if (!sourceNode) return null;

                const x1 = sourceNode.x + (sourceNode.width || 280);
                const y1 = sourceNode.y + (sourceNode.height || 200) / 2;
                const x2 = connectingLineEnd.x;
                const y2 = connectingLineEnd.y;
                const controlOffset = Math.max(Math.abs(x2 - x1) * 0.4, 50);

                return (
                  <Line
                    points={[
                      x1,
                      y1,
                      x1 + controlOffset,
                      y1,
                      x2 - controlOffset,
                      y2,
                      x2,
                      y2,
                    ]}
                    stroke="#3B82F6"
                    strokeWidth={2}
                    tension={0.5}
                    bezier
                    dash={[8, 4]}
                    listening={false}
                  />
                );
              })()}

            {/* Nodes - Using culledNodes for viewport culling optimization */}
            {culledNodes.map((node) => {
              if (node.sectionId) {
                const section = visibleSections.find(
                  (s) => s.id === node.sectionId
                );
                if (section?.isCollapsed) return null;
              }

              return (
                <KnowledgeNode
                  key={node.id}
                  node={node}
                  isSelected={selectedNodeIds.has(node.id)}
                  isHighlighted={highlightedNodeId === node.id}
                  isMergeTarget={mergeTargetNodeId === node.id}
                  isHovered={hoveredNodeId === node.id}
                  isConnecting={connectingFromNodeId === node.id}
                  isConnectTarget={
                    connectingFromNodeId !== null &&
                    connectingFromNodeId !== node.id
                  }
                  isActiveThinking={activeThinkingId === node.id}
                  isSynthesisSource={
                    pendingSynthesisResult?.sourceNodeIds?.includes(node.id) ??
                    false
                  }
                  isDraggable={toolMode === 'select' && !isSpacePressed}
                  onSelect={(e) => handleNodeSelect(node.id, e)}
                  onClick={() => {
                    // Thinking Graph: Set as active thinking node when clicked
                    if (
                      node.type === 'thinking_step' ||
                      node.type === 'thinking_branch'
                    ) {
                      setActiveThinkingId(node.id);
                    }
                    onNodeClick?.(node);
                  }}
                  onDoubleClick={() => {
                    const fileType = node.fileMetadata?.fileType;
                    const isVideoType = [
                      'youtube',
                      'video',
                      'bilibili',
                      'douyin',
                    ].includes(fileType || '');

                    // Handle video types first (YouTube, Bilibili, etc.) - open player modal
                    if (isVideoType) {
                      setYoutubePlayer({ open: true, node });
                    } else if (node.subType === 'source' && node.sourceId) {
                      // Handle other source nodes (web, pdf, etc.)
                      if (fileType === 'web') {
                        // Open web page reader
                        setWebPageReader({ open: true, node });
                      } else {
                        // PDF or other doc
                        onOpenSource?.(node.sourceId, node.sourcePage);
                      }
                    } else if (node.type === 'super_article') {
                      // Open Article Editor for super_article nodes
                      setEditingSuperCardId(node.id);
                      setEditingSuperCardType('article');
                    } else if (node.type === 'super_action_list') {
                      // Open Action List Editor for super_action_list nodes
                      setEditingSuperCardId(node.id);
                      setEditingSuperCardType('action_list');
                    } else if (node.type === 'mindmap') {
                      // Open Mindmap Editor for mindmap nodes
                      setEditingSuperCardId(node.id);
                      setEditingSuperCardType('mindmap');
                    } else if (node.type === 'summary') {
                      // Open Summary Viewer for summary nodes
                      setEditingSuperCardId(node.id);
                      setEditingSuperCardType('summary');
                    } else {
                      setEditingNodeId(node.id);
                    }
                    onNodeDoubleClick?.(node);
                  }}
                  onLinkBack={() => {
                    // Phase 1: Navigate to source document
                    if (node.sourceId) {
                      onOpenSource?.(node.sourceId, node.sourcePage);
                    }
                  }}
                  onDragStart={handleNodeDragStart(node.id)}
                  onDragMove={(e) => {
                    handleNodeDragMove(node.id)(e);
                    handleNodeDragMoveWithMerge(e);
                  }}
                  onDragEnd={(e) => {
                    handleNodeDragEnd(node.id)(e);
                    handleNodeDragEndWithMerge(e);
                  }}
                  onContextMenu={(e) => {
                    e.evt.preventDefault();
                    e.cancelBubble = true; // Stop propagation to stage
                    setContextMenu({
                      x: e.evt.clientX,
                      y: e.evt.clientY,
                      nodeId: node.id,
                    });
                  }}
                  onConnectionStart={() => {
                    // Phase 2: Start connection drag
                    setConnectingFromNodeId(node.id);
                  }}
                  onMouseEnter={() => setHoveredNodeId(node.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                />
              );
            })}

            {/* Selection Box */}
            {selectionRect && (
              <Rect
                x={selectionRect.x}
                y={selectionRect.y}
                width={selectionRect.width}
                height={selectionRect.height}
                fill={
                  toolMode === 'magic'
                    ? 'rgba(102, 126, 234, 0.15)'
                    : 'rgba(59, 130, 246, 0.1)'
                }
                stroke={toolMode === 'magic' ? '#764ba2' : '#3B82F6'}
                strokeWidth={toolMode === 'magic' ? 2 : 1}
                dash={toolMode === 'magic' ? [8, 4] : undefined}
                listening={false}
                cornerRadius={toolMode === 'magic' ? 4 : 0}
              />
            )}

            {/* Magic Selection Persistent Box (for Intent Menu) */}
            {magicSelection && !isGeneratingMagic && (
              <Rect
                x={magicSelection.rect.x}
                y={magicSelection.rect.y}
                width={magicSelection.rect.width}
                height={magicSelection.rect.height}
                fill="rgba(102, 126, 234, 0.1)"
                stroke="#667eea"
                strokeWidth={2}
                dash={[8, 4]}
                listening={false}
                cornerRadius={4}
              />
            )}

            {/* Magic Cursor Loading Animation */}
            {isGeneratingMagic && magicGenerationTask && (
              <Group
                x={
                  magicGenerationTask.snapshotContext.x +
                  magicGenerationTask.snapshotContext.width +
                  20
                }
                y={magicGenerationTask.snapshotContext.y}
              >
                {/* Loading Card Background */}
                <Rect
                  width={
                    magicGenerationTask.outputType === 'article' ? 320 : 280
                  }
                  height={
                    magicGenerationTask.outputType === 'article' ? 200 : 180
                  }
                  fill="#FFFFFF"
                  cornerRadius={12}
                  stroke={
                    magicGenerationTask.outputType === 'article'
                      ? '#667eea'
                      : '#f59e0b'
                  }
                  strokeWidth={2}
                  dash={[8, 4]}
                  shadowColor="rgba(0, 0, 0, 0.1)"
                  shadowBlur={12}
                  shadowOffsetY={4}
                />

                {/* Top Accent Bar */}
                <Rect
                  y={0}
                  width={
                    magicGenerationTask.outputType === 'article' ? 320 : 280
                  }
                  height={5}
                  fill={
                    magicGenerationTask.outputType === 'article'
                      ? '#667eea'
                      : '#f59e0b'
                  }
                  cornerRadius={[12, 12, 0, 0]}
                />

                {/* Loading Icon */}
                <Text
                  x={
                    (magicGenerationTask.outputType === 'article' ? 320 : 280) /
                      2 -
                    12
                  }
                  y={60}
                  text="✨"
                  fontSize={24}
                />

                {/* Loading Text */}
                <Text
                  x={0}
                  y={95}
                  width={
                    magicGenerationTask.outputType === 'article' ? 320 : 280
                  }
                  text={
                    magicGenerationTask.outputType === 'article'
                      ? 'Generating Article...'
                      : 'Extracting Actions...'
                  }
                  fontSize={14}
                  fontStyle="bold"
                  fill="#6B7280"
                  align="center"
                />

                {/* Subtitle */}
                <Text
                  x={0}
                  y={118}
                  width={
                    magicGenerationTask.outputType === 'article' ? 320 : 280
                  }
                  text="AI is analyzing your content"
                  fontSize={12}
                  fill="#9CA3AF"
                  align="center"
                />

                {/* Animated dots indicator (static representation) */}
                <Group y={145}>
                  <Rect
                    x={
                      (magicGenerationTask.outputType === 'article'
                        ? 320
                        : 280) /
                        2 -
                      25
                    }
                    width={8}
                    height={8}
                    fill={
                      magicGenerationTask.outputType === 'article'
                        ? '#667eea'
                        : '#f59e0b'
                    }
                    cornerRadius={4}
                    opacity={0.3}
                  />
                  <Rect
                    x={
                      (magicGenerationTask.outputType === 'article'
                        ? 320
                        : 280) /
                        2 -
                      5
                    }
                    width={8}
                    height={8}
                    fill={
                      magicGenerationTask.outputType === 'article'
                        ? '#667eea'
                        : '#f59e0b'
                    }
                    cornerRadius={4}
                    opacity={0.6}
                  />
                  <Rect
                    x={
                      (magicGenerationTask.outputType === 'article'
                        ? 320
                        : 280) /
                        2 +
                      15
                    }
                    width={8}
                    height={8}
                    fill={
                      magicGenerationTask.outputType === 'article'
                        ? '#667eea'
                        : '#f59e0b'
                    }
                    cornerRadius={4}
                    opacity={1}
                  />
                </Group>
              </Group>
            )}

            {/* Drag Preview */}
            {dragPreview && (
              <Group
                x={dragPreview.x - 140}
                y={dragPreview.y - 100}
                opacity={0.7}
                listening={false}
              >
                <Rect
                  width={280}
                  height={200}
                  fill="white"
                  cornerRadius={12}
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dash={[6, 4]}
                  shadowColor="black"
                  shadowBlur={8}
                  shadowOpacity={0.15}
                  shadowOffsetY={4}
                />
                <Rect
                  y={0}
                  width={280}
                  height={4}
                  fill="#3B82F6"
                  cornerRadius={[12, 12, 0, 0]}
                />
                <Text
                  x={16}
                  y={16}
                  width={280 - 32}
                  text="AI Insight"
                  fontSize={12}
                  fontStyle="bold"
                  fill="#1F2937"
                />
                <Text
                  x={16}
                  y={40}
                  width={280 - 32}
                  height={130}
                  text={dragPreview.content}
                  fontSize={12}
                  fill="#6B7280"
                  wrap="word"
                  ellipsis
                />
              </Group>
            )}
          </Layer>

          {/* Synthesis Connection Lines */}
          {pendingSynthesisResult && pendingSynthesisResult.sourceNodeIds && (
            <Layer>
              {pendingSynthesisResult.sourceNodeIds.map((sourceId) => {
                const sourceNode = nodes.find((n) => n.id === sourceId);
                if (!sourceNode) return null;

                // Position is now in canvas coordinates directly
                const targetX = pendingSynthesisResult.position.x;
                const targetY = pendingSynthesisResult.position.y;

                // Source center
                const sourceX = sourceNode.x + (sourceNode.width || 280) / 2;
                const sourceY = sourceNode.y + (sourceNode.height || 200) / 2;

                return (
                  <Line
                    key={`synthesis-line-${sourceId}`}
                    points={[sourceX, sourceY, targetX + 160, targetY]}
                    stroke="#6366F1"
                    strokeWidth={2}
                    dash={[10, 10]}
                    opacity={0.6}
                    listening={false}
                  />
                );
              })}

              {/* Konva Synthesis Node */}
              <Group
                x={pendingSynthesisResult.position.x}
                y={pendingSynthesisResult.position.y}
                draggable
                onDragEnd={(e) => {
                  setPendingSynthesisResult((prev) =>
                    prev
                      ? {
                          ...prev,
                          position: { x: e.target.x(), y: e.target.y() },
                        }
                      : null
                  );
                }}
              >
                {/* Card Background */}
                <Rect
                  width={320}
                  height={220}
                  fill="white"
                  cornerRadius={16}
                  stroke="#6366F1"
                  strokeWidth={2}
                  shadowColor="rgba(99, 102, 241, 0.3)"
                  shadowBlur={20}
                  shadowOffsetY={8}
                />

                {/* Top Accent Bar */}
                <Rect
                  y={0}
                  width={320}
                  height={6}
                  fill="#6366F1"
                  cornerRadius={[16, 16, 0, 0]}
                />

                {/* AI Icon Background */}
                <Rect
                  x={16}
                  y={16}
                  width={36}
                  height={36}
                  fill="#EEF2FF"
                  cornerRadius={8}
                />
                <Text x={22} y={22} text="✨" fontSize={18} />

                {/* Header Text */}
                <Text
                  x={60}
                  y={18}
                  text="Consolidated Insight"
                  fontSize={14}
                  fontStyle="bold"
                  fill="#1F2937"
                />
                <Text
                  x={60}
                  y={35}
                  text="AI GENERATED"
                  fontSize={10}
                  fill="#6366F1"
                  fontStyle="600"
                />

                {/* Confidence Badge */}
                <Rect
                  x={220}
                  y={20}
                  width={90}
                  height={24}
                  fill="transparent"
                  stroke={
                    pendingSynthesisResult.confidence === 'high'
                      ? '#059669'
                      : '#D97706'
                  }
                  strokeWidth={1}
                  cornerRadius={12}
                />
                <Text
                  x={230}
                  y={26}
                  text={`${(pendingSynthesisResult.confidence || 'medium').charAt(0).toUpperCase()}${(pendingSynthesisResult.confidence || 'medium').slice(1)} Conf.`}
                  fontSize={10}
                  fill={
                    pendingSynthesisResult.confidence === 'high'
                      ? '#059669'
                      : '#D97706'
                  }
                />

                {/* Title */}
                <Text
                  x={16}
                  y={65}
                  width={288}
                  text={pendingSynthesisResult.title}
                  fontSize={15}
                  fontStyle="bold"
                  fill="#1F2937"
                  wrap="word"
                />

                {/* Content */}
                <Text
                  x={16}
                  y={90}
                  width={288}
                  height={80}
                  text={pendingSynthesisResult.content}
                  fontSize={12}
                  fill="#4B5563"
                  wrap="word"
                  ellipsis
                />

                {/* Footer */}
                <Rect
                  y={180}
                  width={320}
                  height={40}
                  fill="#F9FAFB"
                  cornerRadius={[0, 0, 16, 16]}
                />
                <Text
                  x={16}
                  y={193}
                  text={`📄 Synthesized from ${pendingSynthesisResult.sourceNodeIds?.length || 2} sources`}
                  fontSize={11}
                  fill="#6B7280"
                />
              </Group>
            </Layer>
          )}
        </Stage>

        {/* Merge Prompt Overlay */}
        {/* Merge Prompt Overlay - Replaced with SynthesisModeMenu */}
        {/* Merge Prompt Overlay */}
        {(() => {
          console.log(
            '[Synthesis Debug] Render check - mergeTargetNodeId:',
            mergeTargetNodeId,
            'draggedNodeId:',
            draggedNodeId
          );
          return null;
        })()}
        {mergeTargetNodeId &&
          draggedNodeId &&
          (() => {
            console.log(
              '[Synthesis Debug] Both IDs present, looking for nodes...'
            );
            const targetNode = nodes.find((n) => n.id === mergeTargetNodeId);
            const draggedNode = nodes.find((n) => n.id === draggedNodeId);
            console.log(
              '[Synthesis Debug] targetNode found:',
              !!targetNode,
              'draggedNode found:',
              !!draggedNode
            );
            console.log(
              '[Synthesis Debug] Available node IDs:',
              nodes.map((n) => n.id)
            );

            let menuPosition;
            if (targetNode && draggedNode) {
              // Calculate midpoint top
              const targetCenterX =
                targetNode.x + (targetNode.width || 280) / 2;
              const draggedCenterX =
                draggedNode.x + (draggedNode.width || 280) / 2;
              const midX = (targetCenterX + draggedCenterX) / 2;

              // Use the higher (smaller Y) of the two nodes as the anchor for top
              const minY = Math.min(targetNode.y, draggedNode.y);

              // Convert to screen coordinates
              const screenX = midX * viewport.scale + viewport.x;
              const screenY = minY * viewport.scale + viewport.y - 20; // 20px padding above

              menuPosition = { x: screenX, y: screenY };
              console.log(
                '[Synthesis Debug] Menu position calculated:',
                menuPosition
              );
            } else {
              console.log(
                '[Synthesis Debug] ❌ Cannot render menu - nodes not found'
              );
              return null;
            }

            console.log('[Synthesis Debug] ✅ Rendering SynthesisModeMenu');
            return (
              <SynthesisModeMenu
                isSynthesizing={isSynthesizing}
                onSelect={handleSynthesize}
                onCancel={handleCancelMerge}
                position={menuPosition}
              />
            );
          })()}

        {/* Magic Cursor Intent Menu */}
        {magicSelection && (
          <IntentMenu
            position={magicSelection.screenPosition}
            onSelect={handleIntentAction}
            onClose={handleIntentMenuClose}
          />
        )}

        {/* Node Editor Overlay */}
        {(editingNodeId || isCreatingNote) &&
          (() => {
            let initialData;
            if (editingNodeId) {
              const node = nodes.find((n) => n.id === editingNodeId);
              if (!node) return null;
              initialData = {
                id: node.id,
                title: node.title || '',
                content: node.content || '',
              };
            } else {
              // New note defaults
              initialData = {
                title: '',
                content: '',
              };
            }

            return (
              <NoteEditor
                initialData={initialData}
                onSave={handleNodeSave}
                onCancel={() => {
                  setEditingNodeId(null);
                  setIsCreatingNote(false);
                }}
              />
            );
          })()}

        {/* Super Card Article Editor */}
        {editingSuperCardId &&
          editingSuperCardType === 'article' &&
          (() => {
            const node = nodes.find((n) => n.id === editingSuperCardId);
            if (!node) return null;

            let articleData: ArticleData;
            try {
              articleData = JSON.parse(node.content || '{}');
            } catch {
              articleData = {
                title: node.title || 'Untitled Article',
                sections: [],
              };
            }

            return (
              <ArticleEditor
                nodeId={node.id}
                initialData={articleData}
                onSave={(nodeId, data) => {
                  // Update the node with new data
                  if (onNodesChange) {
                    const updatedNodes = nodes.map((n) =>
                      n.id === nodeId
                        ? {
                            ...n,
                            title: data.title,
                            content: JSON.stringify(data),
                          }
                        : n
                    );
                    onNodesChange(updatedNodes);
                  }
                  setEditingSuperCardId(null);
                  setEditingSuperCardType(null);
                }}
                onCancel={() => {
                  setEditingSuperCardId(null);
                  setEditingSuperCardType(null);
                }}
              />
            );
          })()}

        {/* Super Card Action List Editor */}
        {editingSuperCardId &&
          editingSuperCardType === 'action_list' &&
          (() => {
            const node = nodes.find((n) => n.id === editingSuperCardId);
            if (!node) return null;

            let actionData: ActionListData;
            try {
              actionData = JSON.parse(node.content || '{}');
            } catch {
              actionData = { title: node.title || 'Action Items', items: [] };
            }

            return (
              <ActionListEditor
                nodeId={node.id}
                initialData={actionData}
                onSave={(nodeId, data) => {
                  // Update the node with new data
                  if (onNodesChange) {
                    const updatedNodes = nodes.map((n) =>
                      n.id === nodeId
                        ? {
                            ...n,
                            title: data.title,
                            content: JSON.stringify(data),
                          }
                        : n
                    );
                    onNodesChange(updatedNodes);
                  }
                  setEditingSuperCardId(null);
                  setEditingSuperCardType(null);
                }}
                onCancel={() => {
                  setEditingSuperCardId(null);
                  setEditingSuperCardType(null);
                }}
              />
            );
          })()}

        {/* Mindmap Editor Modal */}
        {editingSuperCardId &&
          editingSuperCardType === 'mindmap' &&
          (() => {
            const node = nodes.find((n) => n.id === editingSuperCardId);
            if (!node) return null;

            let mindmapData: MindmapData;
            try {
              mindmapData =
                (node.outputData as unknown as MindmapData) ||
                JSON.parse(node.content || '{}');
            } catch {
              mindmapData = { nodes: [], edges: [] };
            }

            return (
              <MindMapEditor
                initialData={mindmapData}
                title={node.title || 'Mindmap'}
                onClose={() => {
                  setEditingSuperCardId(null);
                  setEditingSuperCardType(null);
                }}
                onSave={(data) => {
                  // Update the node with new data
                  if (onNodesChange) {
                    const updatedNodes = nodes.map((n) =>
                      n.id === editingSuperCardId
                        ? {
                            ...n,
                            outputData: data as unknown as Record<
                              string,
                              unknown
                            >,
                            content: JSON.stringify(data),
                          }
                        : n
                    );
                    onNodesChange(updatedNodes);
                  }
                  setEditingSuperCardId(null);
                  setEditingSuperCardType(null);
                }}
                onOpenSourceRef={(sourceId, sourceType, location, quote) => {
                  console.log('[KonvaCanvas] onOpenSourceRef called:', {
                    sourceId,
                    sourceType,
                    location,
                  });

                  // Handle source reference navigation from mindmap
                  if (sourceType === 'video') {
                    // Strategy 1: Find the source node on the canvas
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    let videoMetadata: Record<string, any> | null = null;
                    let videoTitle = 'Video';

                    console.log(
                      '[KonvaCanvas] Looking for video source, sourceId:',
                      sourceId
                    );
                    console.log(
                      '[KonvaCanvas] Available urlContents:',
                      urlContents.map((u) => ({ id: u.id, title: u.title }))
                    );

                    // Try to find as a canvas node first
                    const sourceNode = nodes.find(
                      (n) => n.sourceId === sourceId || n.id === sourceId
                    );

                    if (sourceNode) {
                      videoMetadata = sourceNode.fileMetadata;
                      videoTitle = sourceNode.title || 'Video';
                    } else {
                      // Strategy 2: Fallback to project documents (PDF/Video uploads)
                      // Note: ProjectDocument interface currently doesn't expose metadata in frontend type
                      // but we cast to any to access potential backend fields or simply look in urlContents primarily.

                      // Strategy 3: Fallback to URL contents (Direct links) - MOST LIKELY for YouTube
                      const urlContent = urlContents.find(
                        (u) => u.id === sourceId
                      );
                      if (urlContent) {
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        const metaData = urlContent.meta_data as
                          | Record<string, any>
                          | undefined;
                        videoMetadata = {
                          videoId: metaData?.video_id,
                          channelName: metaData?.channel_name,
                          sourceUrl: urlContent.url,
                        };
                        videoTitle = urlContent.title || 'Video';
                      } else {
                        // Try documents as last resort (e.g. uploaded mp4)
                        const doc = documents.find((d) => d.id === sourceId);
                        if (doc) {
                          // Fallback structure if metadata missing
                          videoTitle = doc.filename || 'Video';
                        }
                      }
                    }

                    if (
                      videoMetadata &&
                      (videoMetadata.videoId || videoMetadata.sourceUrl)
                    ) {
                      // Parse timestamp from location (e.g., "12:30" or "1:23:45")
                      // Backend sends [TIME:MM:SS] but regex likely strips [TIME:] before we see it here
                      // If it still has [TIME:], strip it
                      let cleanLocation = location || '';
                      if (cleanLocation.includes('[TIME:')) {
                        cleanLocation = cleanLocation
                          .replace('[TIME:', '')
                          .replace(']', '');
                      }

                      let startTime = 0;
                      if (cleanLocation) {
                        const parts = cleanLocation
                          .split(':')
                          .map((p) => parseInt(p, 10));
                        // Handle MM:SS
                        if (
                          parts.length === 2 &&
                          !isNaN(parts[0]) &&
                          !isNaN(parts[1])
                        ) {
                          startTime = parts[0] * 60 + parts[1];
                        }
                        // Handle HH:MM:SS
                        else if (
                          parts.length === 3 &&
                          !isNaN(parts[0]) &&
                          !isNaN(parts[1]) &&
                          !isNaN(parts[2])
                        ) {
                          startTime =
                            parts[0] * 3600 + parts[1] * 60 + parts[2];
                        }
                        // Handle raw seconds string
                        else if (parts.length === 1 && !isNaN(parts[0])) {
                          startTime = parts[0];
                        }
                      }

                      console.log(
                        `[KonvaCanvas] Opening video player: ${videoTitle} at ${startTime}s (${location})`
                      );

                      // Open video player with the source node (will navigate to timestamp)
                      setYoutubePlayer({
                        open: true,
                        node: {
                          id: sourceId,
                          type: 'file', // Dummy type
                          title: videoTitle,
                          content: '',
                          x: 0,
                          y: 0,
                          width: 0,
                          height: 0,
                          color: 'red',
                          tags: [],
                          viewType: 'free',
                          fileMetadata: {
                            ...videoMetadata,
                            fileType: 'video',
                            startTime,
                          },
                        },
                      });
                    } else {
                      console.warn(
                        `[KonvaCanvas] Could not find video source for ID: ${sourceId}`
                      );
                    }
                  } else if (sourceType === 'web') {
                    // Find web source node and open reader
                    const sourceNode = nodes.find(
                      (n) => n.sourceId === sourceId || n.id === sourceId
                    );

                    if (sourceNode) {
                      setWebPageReader({ open: true, node: sourceNode });
                    } else {
                      // Fallback to URL contents
                      const urlContent = urlContents.find(
                        (u) => u.id === sourceId
                      );
                      if (urlContent) {
                        setWebPageReader({
                          open: true,
                          node: {
                            id: urlContent.id,
                            type: 'file',
                            title: urlContent.title || 'Web Page',
                            content: urlContent.content || '',
                            x: 0,
                            y: 0,
                            width: 0,
                            height: 0,
                            color: 'blue',
                            tags: [],
                            viewType: 'free',
                            fileMetadata: {
                              sourceUrl: urlContent.url,
                              fileType: 'web',
                            },
                          },
                        });
                      }
                    }
                  } else {
                    // PDF or document - use onOpenSource callback
                    // Extract page number from location (e.g., "Page 15" or "Page 15-17")
                    let pageNumber: number | undefined;
                    if (location) {
                      const pageMatch = location.match(/Page\s*(\d+)/i);
                      if (pageMatch) {
                        pageNumber = parseInt(pageMatch[1], 10);
                      }
                    }
                    onOpenSource?.(sourceId, pageNumber);
                  }
                }}
              />
            );
          })()}

        {/* Summary Viewer Modal */}
        {editingSuperCardId &&
          editingSuperCardType === 'summary' &&
          (() => {
            const node = nodes.find((n) => n.id === editingSuperCardId);
            if (!node) return null;

            let summaryData: SummaryData;
            try {
              summaryData =
                (node.outputData as unknown as SummaryData) ||
                JSON.parse(node.content || '{}');
            } catch {
              summaryData = { summary: '', keyFindings: [], documentTitle: '' };
            }

            return (
              <div
                style={{
                  position: 'fixed',
                  inset: 0,
                  backgroundColor: 'rgba(0,0,0,0.5)',
                  zIndex: 2500,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
                onClick={() => {
                  setEditingSuperCardId(null);
                  setEditingSuperCardType(null);
                }}
              >
                <div
                  style={{
                    backgroundColor: 'white',
                    borderRadius: 16,
                    padding: 24,
                    maxWidth: 600,
                    maxHeight: '80vh',
                    overflow: 'auto',
                    boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: 16,
                    }}
                  >
                    <h2
                      style={{
                        fontSize: 20,
                        fontWeight: 600,
                        color: '#1F2937',
                      }}
                    >
                      📋 {summaryData.documentTitle || node.title || 'Summary'}
                    </h2>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setEditingSuperCardId(null);
                        setEditingSuperCardType(null);
                      }}
                    >
                      <CloseIcon size={20} />
                    </Button>
                  </div>

                  <div style={{ marginBottom: 20 }}>
                    <h3
                      style={{
                        fontSize: 14,
                        fontWeight: 600,
                        color: '#6B7280',
                        marginBottom: 8,
                      }}
                    >
                      Summary
                    </h3>
                    <p
                      style={{
                        fontSize: 14,
                        color: '#374151',
                        lineHeight: 1.6,
                      }}
                    >
                      {summaryData.summary}
                    </p>
                  </div>

                  {summaryData.keyFindings &&
                    summaryData.keyFindings.length > 0 && (
                      <div>
                        <h3
                          style={{
                            fontSize: 14,
                            fontWeight: 600,
                            color: '#6B7280',
                            marginBottom: 12,
                          }}
                        >
                          💡 Key Findings ({summaryData.keyFindings.length})
                        </h3>
                        <div
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 12,
                          }}
                        >
                          {summaryData.keyFindings.map((finding, index) => (
                            <div
                              key={index}
                              style={{
                                backgroundColor: '#FAF5FF',
                                border: '1px solid #E9D5FF',
                                borderRadius: 8,
                                padding: 12,
                              }}
                            >
                              <div
                                style={{
                                  fontSize: 13,
                                  fontWeight: 600,
                                  color: '#7C3AED',
                                  marginBottom: 4,
                                }}
                              >
                                {finding.label}
                              </div>
                              <div style={{ fontSize: 13, color: '#374151' }}>
                                {finding.content}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              </div>
            );
          })()}

        {/* Web Page Reader Modal */}
        {webPageReader.open && webPageReader.node && (
          <WebPageReaderModal
            open={webPageReader.open}
            onClose={() => setWebPageReader({ open: false, node: null })}
            title={webPageReader.node.title || 'Web Page'}
            content={webPageReader.node.content || ''}
            sourceUrl={webPageReader.node.fileMetadata?.sourceUrl}
            domain={
              webPageReader.node.fileMetadata?.sourceUrl
                ? new URL(webPageReader.node.fileMetadata.sourceUrl).hostname
                : undefined
            }
          />
        )}

        {/* YouTube Player Modal */}
        {youtubePlayer.open && youtubePlayer.node && (
          <YouTubePlayerModal
            open={youtubePlayer.open}
            onClose={() => setYoutubePlayer({ open: false, node: null })}
            videoId={youtubePlayer.node.fileMetadata?.videoId || ''}
            title={youtubePlayer.node.title || 'Video'}
            channelName={youtubePlayer.node.fileMetadata?.channelName}
            viewCount={youtubePlayer.node.fileMetadata?.viewCount}
            publishedAt={youtubePlayer.node.fileMetadata?.publishedAt}
            sourceUrl={youtubePlayer.node.fileMetadata?.sourceUrl}
            startTime={youtubePlayer.node.fileMetadata?.startTime}
          />
        )}

        {/* Loading Overlay for Synthesis */}
        {isSynthesizing && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundColor: 'rgba(255,255,255,0.6)',
              backdropFilter: 'blur(2px)',
              zIndex: 1900,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Spinner size="lg" style={{ color: '#8B5CF6' }} />
          </div>
        )}

        {/* Generation Outputs Overlay - Renders completed generation tasks at their positions */}
        <GenerationOutputsOverlay viewport={viewport} />

        {/* Inspiration Dock - Shown when canvas is empty, no outputs exist, but sources are uploaded */}
        {visibleNodes.length === 0 &&
          (documents.length > 0 || urlContents.length > 0) &&
          !hasCompletedOutputs && <InspirationDock />}

        {/* Synthesis Connection Lines - Moved inside Stage */}

        {/* Synthesis Action Buttons - Floating overlay anchored to Konva node */}
        {pendingSynthesisResult &&
          (() => {
            // Convert canvas position to screen position
            const screenX =
              pendingSynthesisResult.position.x * viewport.scale + viewport.x;
            const screenY =
              (pendingSynthesisResult.position.y + 220) * viewport.scale +
              viewport.y; // Below the 220px tall card

            return (
              <div
                style={{
                  position: 'absolute',
                  left: screenX,
                  top: screenY + 8,
                  transform: 'translateX(-50%)',
                  display: 'flex',
                  gap: 8,
                  zIndex: 2100,
                  backgroundColor: 'white',
                  padding: 8,
                  borderRadius: 8,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                }}
              >
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setPendingSynthesisResult(null)}
                  style={{ color: colors.text.secondary }}
                >
                  Discard
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => {
                    // Create a new canvas node from the synthesis result
                    const newNode: CanvasNode = {
                      id: pendingSynthesisResult.id,
                      type: 'synthesis',
                      title: pendingSynthesisResult.title,
                      content:
                        pendingSynthesisResult.content +
                        (pendingSynthesisResult.recommendation
                          ? `\n\n**Recommendation:** ${pendingSynthesisResult.recommendation}`
                          : '') +
                        (pendingSynthesisResult.keyRisk
                          ? `\n\n**Key Risk:** ${pendingSynthesisResult.keyRisk}`
                          : ''),
                      x: pendingSynthesisResult.position.x,
                      y: pendingSynthesisResult.position.y,
                      width: 320,
                      height: 220,
                      color: '#EEF2FF',
                      tags: pendingSynthesisResult.themes || [],
                      viewType: 'free',
                      subType: 'insight',
                    };

                    if (onNodesChange) {
                      onNodesChange([...nodes, newNode]);
                    }
                    setPendingSynthesisResult(null);
                  }}
                  style={{
                    textTransform: 'none',
                    backgroundColor: '#6366F1',
                    borderRadius: 8,
                  }}
                >
                  Add to Board
                </Button>
              </div>
            );
          })()}
      </div>
    </div>
  );
}
