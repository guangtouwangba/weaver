'use client';

/**
 * Platform Icon Utility
 *
 * Maps platform identifiers to appropriate icons with platform-specific colors.
 */

import React from 'react';
import { GlobeIcon, YoutubeIcon, VideoIcon } from '@/components/ui/icons';
import type { IconSize } from '@/components/ui/icons';

export type Platform = 'youtube' | 'bilibili' | 'douyin' | 'web';

// Platform-specific brand colors
const platformColors: Record<Platform, string> = {
  youtube: '#FF0000',
  bilibili: '#00A1D6',
  douyin: '#000000',
  web: '#6B7280',
};

// Platform display names
const platformNames: Record<Platform, string> = {
  youtube: 'YouTube',
  bilibili: 'Bilibili',
  douyin: 'Douyin',
  web: 'Web Page',
};

interface PlatformIconProps {
  platform: Platform;
  size?: IconSize | number;
  showColor?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Get the appropriate icon component for a platform.
 */
export function PlatformIcon({
  platform,
  size = 'md',
  showColor = true,
  className,
  style,
}: PlatformIconProps) {
  const color = showColor ? platformColors[platform] : 'currentColor';

  const iconStyle = {
    ...style,
    color,
  };

  switch (platform) {
    case 'youtube':
      return <YoutubeIcon size={size} className={className} style={iconStyle} />;
    case 'bilibili':
      // Use video icon with Bilibili's brand color
      return <VideoIcon size={size} className={className} style={iconStyle} />;
    case 'douyin':
      // Use video icon with Douyin's brand color
      return <VideoIcon size={size} className={className} style={iconStyle} />;
    case 'web':
    default:
      return <GlobeIcon size={size} className={className} style={iconStyle} />;
  }
}

/**
 * Get platform color for styling purposes.
 */
export function getPlatformColor(platform: Platform): string {
  return platformColors[platform] || platformColors.web;
}

/**
 * Get platform display name.
 */
export function getPlatformName(platform: Platform): string {
  return platformNames[platform] || 'Unknown';
}

/**
 * Detect platform from URL (client-side utility).
 */
export function detectPlatform(url: string): Platform {
  const lowercaseUrl = url.toLowerCase();

  if (
    lowercaseUrl.includes('youtube.com') ||
    lowercaseUrl.includes('youtu.be')
  ) {
    return 'youtube';
  }

  if (
    lowercaseUrl.includes('bilibili.com') ||
    lowercaseUrl.includes('b23.tv')
  ) {
    return 'bilibili';
  }

  if (
    lowercaseUrl.includes('douyin.com') ||
    lowercaseUrl.includes('v.douyin.com')
  ) {
    return 'douyin';
  }

  return 'web';
}

