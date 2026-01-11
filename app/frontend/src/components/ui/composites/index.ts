'use client';

/**
 * UI Composites - Barrel Export
 *
 * Higher-level components built from primitives.
 * Import from '@/components/ui/composites' for all composites.
 */

// Card
export { Card } from './Card';
export type { CardProps } from './Card';

// Dialog (legacy wrapper, use Modal from primitives for new code)
export { Dialog } from './Dialog';
export type { DialogProps } from './Dialog';

// Menu
export { Menu, MenuItem, MenuDivider } from './Menu';
export type { MenuProps, MenuItemProps } from './Menu';

// Input (legacy wrapper, use TextField for new code)
export { Input } from './Input';
export type { InputProps } from './Input';

// TextField
export { TextField } from './TextField';
export type { TextFieldProps } from './TextField';

// ConfirmDialog
export { ConfirmDialog } from './ConfirmDialog';
export type { ConfirmDialogProps } from './ConfirmDialog';

// Tabs
export { Tabs, Tab, TabPanel } from './Tabs';
export type { TabsProps, TabProps, TabPanelProps } from './Tabs';
