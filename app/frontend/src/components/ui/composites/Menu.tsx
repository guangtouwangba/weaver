'use client';

import React from 'react';
import {
    Menu as MuiMenu,
    MenuProps as MuiMenuProps,
    MenuItem as MuiMenuItem,
    MenuItemProps as MuiMenuItemProps,
    ListItemIcon,
    ListItemText,
    Divider,
} from '@mui/material';
import { colors, radii, shadows, fontSize, fontWeight } from '../tokens';

/**
 * Menu Component
 *
 * Dropdown menu with consistent styling.
 * Wraps MUI Menu with design system tokens.
 */

export interface MenuProps extends MuiMenuProps {
    /** Menu items */
    children?: React.ReactNode;
}

export const Menu = React.forwardRef<HTMLDivElement, MenuProps>(
    function Menu({ children, ...props }, ref) {
        return (
            <MuiMenu
                ref={ref}
                PaperProps={{
                    sx: {
                        borderRadius: `${radii.lg}px`,
                        boxShadow: shadows.lg,
                        border: `1px solid ${colors.border.default}`,
                        minWidth: 180,
                        py: 0.5,
                    },
                }}
                {...props}
            >
                {children}
            </MuiMenu>
        );
    }
);

Menu.displayName = 'Menu';

/**
 * MenuItem Component
 */

export interface MenuItemProps extends MuiMenuItemProps {
    /** Icon to display */
    icon?: React.ReactNode;
    /** Whether this is a destructive action */
    danger?: boolean;
}

export const MenuItem = React.forwardRef<HTMLLIElement, MenuItemProps>(
    function MenuItem({ icon, danger = false, children, ...props }, ref) {
        return (
            <MuiMenuItem
                ref={ref}
                sx={{
                    py: 1,
                    px: 2,
                    fontSize: fontSize.sm,
                    fontWeight: fontWeight.medium,
                    color: danger ? colors.error[600] : colors.text.primary,
                    '&:hover': {
                        bgcolor: danger ? colors.error[50] : colors.neutral[100],
                    },
                }}
                {...props}
            >
                {icon && (
                    <ListItemIcon sx={{ color: danger ? colors.error[500] : colors.text.secondary, minWidth: 32 }}>
                        {icon}
                    </ListItemIcon>
                )}
                <ListItemText primary={children} />
            </MuiMenuItem>
        );
    }
);

MenuItem.displayName = 'MenuItem';

/**
 * MenuDivider Component
 */
export const MenuDivider = () => (
    <Divider sx={{ my: 0.5, borderColor: colors.border.default }} />
);

MenuDivider.displayName = 'MenuDivider';

export default Menu;
