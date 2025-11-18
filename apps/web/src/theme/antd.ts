/**
 * Ant Design Theme Configuration
 * Maps design system tokens to Ant Design theme configuration
 */

import type { ThemeConfig } from 'antd';
import { colors, radius, typography, shadows } from './tokens';

export const antdTheme: ThemeConfig = {
  token: {
    // Color tokens
    colorPrimary: colors.primary.strong,
    colorInfo: colors.status.info,
    colorSuccess: colors.status.success,
    colorWarning: colors.status.warning,
    colorError: colors.status.error,
    
    // Background colors
    colorBgContainer: colors.surface.card,
    colorBgLayout: colors.surface.page,
    colorBgElevated: colors.surface.card,
    
    // Border colors
    colorBorder: colors.border.subtle,
    colorBorderSecondary: colors.border.subtle,
    
    // Text colors
    colorText: colors.text.primary,
    colorTextSecondary: colors.text.secondary,
    colorTextTertiary: colors.text.muted,
    colorTextBase: colors.text.primary,
    
    // Typography
    fontFamily: typography.fontFamily,
    fontSize: typography.body.size,
    fontSizeHeading1: typography.displayLg.size,
    fontSizeHeading2: typography.displayMd.size,
    fontSizeHeading3: typography.title.size,
    fontSizeHeading4: typography.subtitle.size,
    fontSizeHeading5: typography.body.size,
    
    // Border radius
    borderRadius: radius.sm,
    borderRadiusLG: radius.lg,
    borderRadiusSM: radius.xs,
    
    // Spacing
    marginXS: 8,
    marginSM: 12,
    margin: 16,
    marginMD: 16,
    marginLG: 24,
    marginXL: 32,
    
    paddingXS: 8,
    paddingSM: 12,
    padding: 16,
    paddingMD: 16,
    paddingLG: 24,
    paddingXL: 32,
    
    // Shadows
    boxShadow: shadows.soft,
    boxShadowSecondary: shadows.medium,
    
    // Line height
    lineHeight: typography.body.lineHeight,
    lineHeightHeading1: typography.displayLg.lineHeight,
    lineHeightHeading2: typography.displayMd.lineHeight,
    lineHeightHeading3: typography.title.lineHeight,
    lineHeightHeading4: typography.subtitle.lineHeight,
    lineHeightHeading5: typography.body.lineHeight,
    
    // Motion
    motionDurationFast: '0.12s',
    motionDurationMid: '0.18s',
    motionDurationSlow: '0.24s',
    motionEaseInOut: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
    motionEaseOut: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
  },
  components: {
    Button: {
      // Primary button
      primaryColor: colors.text.onAccent,
      colorPrimaryHover: colors.primary.hover,
      colorPrimaryActive: colors.primary.pressed,
      borderRadius: radius.pill,
      controlHeight: 40,
      paddingContentHorizontal: 20,
      fontWeight: typography.bodyBold.weight,
      
      // Default button
      defaultBorderColor: colors.border.strong,
      defaultColor: colors.text.primary,
      defaultBg: colors.surface.card,
      
      // Ghost button
      ghostBg: 'transparent',
      textHoverBg: colors.surface.subtle,
    },
    Card: {
      borderRadiusLG: radius.lg,
      paddingLG: 20,
      boxShadow: shadows.soft,
    },
    Input: {
      borderRadius: radius.md,
      controlHeight: 40,
      paddingBlock: 8,
      paddingInline: 12,
      activeBorderColor: colors.border.focus,
      hoverBorderColor: colors.border.strong,
    },
    Select: {
      borderRadius: radius.md,
      controlHeight: 40,
    },
    Tabs: {
      itemActiveColor: colors.primary.strong,
      itemSelectedColor: colors.primary.strong,
      inkBarColor: colors.primary.strong,
      itemHoverColor: colors.primary.hover,
      titleFontSize: typography.body.size,
    },
    Tag: {
      borderRadiusSM: radius.pill,
      defaultBg: colors.surface.subtle,
      defaultColor: colors.text.secondary,
    },
    Modal: {
      borderRadiusLG: radius.lg,
      paddingLG: 20,
      boxShadow: shadows.medium,
    },
    Drawer: {
      paddingLG: 20,
      boxShadow: shadows.medium,
    },
    Message: {
      contentBg: colors.surface.card,
      boxShadow: shadows.medium,
    },
    Progress: {
      defaultColor: colors.primary.strong,
      remainingColor: colors.surface.subtle,
      circleTextColor: colors.text.primary,
    },
    Statistic: {
      contentFontSize: typography.displayMd.size,
      titleFontSize: typography.body.size,
    },
    Layout: {
      headerBg: colors.surface.card,
      bodyBg: colors.surface.page,
      footerBg: colors.surface.card,
      headerPadding: `0 ${24}px`,
      footerPadding: `${24}px ${24}px`,
    },
    List: {
      itemPadding: '12px 16px',
    },
  },
};

