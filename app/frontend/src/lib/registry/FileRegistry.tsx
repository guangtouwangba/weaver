import React from 'react';
import {
  FileTextIcon,
  VideoIcon,
  ImageIcon,
  CodeIcon,
  FileIcon,
} from '@/components/ui/icons';

// Define the shape of our file configuration
export interface FileTypeConfig {
  type: string;
  extensions: string[];
  color: string; // Tailwind color name or hex
  bgColor: string; // Tailwind bg color class
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  canPreview: boolean;
}

// PDF Icon Component (Local definition to keep registry self-contained or import from icons)
const PdfIcon = ({
  size = 24,
  className,
}: {
  size?: number;
  className?: string;
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"
      fill="currentColor"
    />
    <path d="M14 2V8H20" fill="currentColor" fillOpacity="0.5" />
    <text
      x="50%"
      y="15"
      fontFamily="sans-serif"
      fontSize="6"
      fill="white"
      fontWeight="bold"
      textAnchor="middle"
    >
      PDF
    </text>
  </svg>
);

class FileRegistry {
  private configs: FileTypeConfig[] = [];

  constructor() {
    this.registerDefaults();
  }

  private registerDefaults() {
    // PDF
    this.register({
      type: 'pdf',
      extensions: ['.pdf'],
      color: '#EF4444', // Red-500
      bgColor: '#FEF2F2', // Red-50
      icon: PdfIcon,
      label: 'PDF Document',
      canPreview: true,
    });

    // Text
    this.register({
      type: 'text',
      extensions: ['.txt', '.md', '.markdown', '.csv', '.json'],
      color: '#6B7280', // Gray-500
      bgColor: '#F9FAFB', // Gray-50
      icon: FileTextIcon,
      label: 'Text Document',
      canPreview: true,
    });

    // Video
    this.register({
      type: 'video',
      extensions: ['.mp4', '.mov', '.webm', '.avi'],
      color: '#8B5CF6', // Violet-500
      bgColor: '#F5F3FF', // Violet-50
      icon: VideoIcon,
      label: 'Video',
      canPreview: false, // For now
    });

    // Image
    this.register({
      type: 'image',
      extensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
      color: '#10B981', // Emerald-500
      bgColor: '#ECFDF5', // Emerald-50
      icon: ImageIcon,
      label: 'Image',
      canPreview: true,
    });

    // Code
    this.register({
      type: 'code',
      extensions: [
        '.py',
        '.js',
        '.ts',
        '.tsx',
        '.jsx',
        '.html',
        '.css',
        '.go',
        '.rs',
      ],
      color: '#3B82F6', // Blue-500
      bgColor: '#EFF6FF', // Blue-50
      icon: CodeIcon,
      label: 'Code',
      canPreview: true,
    });
  }

  register(config: FileTypeConfig) {
    this.configs.push(config);
  }

  getConfig(filename: string): FileTypeConfig {
    const ext = '.' + filename.split('.').pop()?.toLowerCase();
    const config = this.configs.find((c) => c.extensions.includes(ext));

    if (config) return config;

    // Default fallback
    return {
      type: 'unknown',
      extensions: [],
      color: '#9CA3AF', // Gray-400
      bgColor: '#F3F4F6', // Gray-100
      icon: FileIcon, // Generic icon
      label: 'File',
      canPreview: false,
    };
  }
}

export const fileRegistry = new FileRegistry();
