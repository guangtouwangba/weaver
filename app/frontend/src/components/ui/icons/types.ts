import { SxProps, Theme } from '@mui/material';

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export type IconColor = 
  | 'inherit' 
  | 'primary' 
  | 'secondary' 
  | 'error' 
  | 'warning' 
  | 'info' 
  | 'success' 
  | 'disabled'
  | 'action';

export interface IconProps {
  /**
   * Icon size - can be semantic ('xs', 'sm', 'md', 'lg', 'xl') or pixel number
   * @default 'md'
   */
  size?: IconSize | number;
  
  /**
   * Icon color - semantic color from theme
   * @default 'inherit'
   */
  color?: IconColor;
  
  /**
   * Additional CSS class name
   */
  className?: string;
  
  /**
   * Inline styles
   */
  style?: React.CSSProperties;
  
  /**
   * MUI sx prop for advanced styling
   */
  sx?: SxProps<Theme>;
  
  /**
   * Click handler
   */
  onClick?: (event: React.MouseEvent) => void;
  
  /**
   * Accessibility title
   */
  titleAccess?: string;
}

/**
 * Size mapping from semantic sizes to pixel values
 */
export const sizeMap: Record<IconSize, number> = {
  xs: 12,
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
};




