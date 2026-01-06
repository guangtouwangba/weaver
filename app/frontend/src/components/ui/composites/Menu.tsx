'use client';

import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Surface, Text } from '../primitives';
import { colors, radii, shadows, fontSize, fontWeight } from '../tokens';

/**
 * Menu Component
 *
 * Dropdown menu with consistent styling.
 * Pure CSS implementation replacing MUI.
 */

export interface MenuProps {
    open: boolean;
    onClose: () => void;
    anchorReference?: 'anchorPosition' | 'anchorEl';
    anchorPosition?: { top: number; left: number };
    children?: React.ReactNode;
    className?: string;
    style?: React.CSSProperties;
}

export const Menu = ({
    open,
    onClose,
    anchorReference = 'anchorPosition',
    anchorPosition,
    children,
    className,
    style,
}: MenuProps) => {
    const menuRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        if (!open) return;

        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                onClose();
            }
        };

        // Use mousedown to capture the start of the click, which feels snappier
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [open, onClose]);

    // Close on Escape key
    useEffect(() => {
        if (!open) return;
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [open, onClose]);

    if (!open) return null;

    const content = (
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 1300, // MUI default modal z-index
                pointerEvents: 'none', // Allow clicks pass through the overlay to underlying elements if not hitting the menu? 
                // Actually MUI Menu usually has a backdrop (invisible or transparent). 
                // But here we implement "click outside" manually. 
                // So let's just render the menu at the position.
            }}
        >
            <Surface
                ref={menuRef}
                elevation={3}
                className={className}
                style={{
                    position: 'absolute',
                    top: anchorPosition?.top || 0,
                    left: anchorPosition?.left || 0,
                    borderRadius: radii.md,
                    padding: '4px 0',
                    border: `1px solid ${colors.border.default}`,
                    backgroundColor: colors.background.paper,
                    minWidth: 160,
                    pointerEvents: 'auto',
                    outline: 'none',
                    ...style,
                }}
            >
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                    {children}
                </ul>
            </Surface>
        </div>
    );

    // Portal to body to ensure it's on top
    if (typeof document !== 'undefined') {
        return createPortal(content, document.body);
    }
    return null;
};

Menu.displayName = 'Menu';

/**
 * MenuItem Component
 */

export interface MenuItemProps extends React.LiHTMLAttributes<HTMLLIElement> {
    icon?: React.ReactNode;
    danger?: boolean;
    disabled?: boolean;
}

export const MenuItem = React.forwardRef<HTMLLIElement, MenuItemProps>(
    function MenuItem({ icon, danger = false, disabled = false, children, style, className, onClick, ...props }, ref) {
        const [isHovered, setIsHovered] = React.useState(false);

        return (
            <li
                ref={ref}
                onMouseEnter={() => !disabled && setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                onClick={(e) => !disabled && onClick?.(e)}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '8px 16px',
                    fontSize: fontSize.sm,
                    fontWeight: fontWeight.medium,
                    cursor: disabled ? 'default' : 'pointer',
                    color: disabled
                        ? colors.text.disabled
                        : danger
                            ? colors.error[600]
                            : colors.text.primary,
                    backgroundColor: isHovered && !disabled
                        ? (danger ? colors.error[50] : colors.neutral[100])
                        : 'transparent',
                    opacity: disabled ? 0.5 : 1,
                    transition: 'background-color 0.1s ease',
                    ...style,
                }}
                className={className}
                {...props}
            >
                {icon && (
                    <span
                        style={{
                            marginRight: 12,
                            display: 'flex',
                            alignItems: 'center',
                            color: disabled
                                ? colors.text.disabled
                                : danger
                                    ? colors.error[500]
                                    : colors.text.secondary,
                        }}
                    >
                        {icon}
                    </span>
                )}
                <span style={{ flex: 1 }}>{children}</span>
            </li>
        );
    }
);

MenuItem.displayName = 'MenuItem';

/**
 * MenuDivider Component
 */
export const MenuDivider = () => (
    <li
        role="separator"
        style={{
            height: 1,
            margin: '4px 0',
            backgroundColor: colors.border.default,
        }}
    />
);

MenuDivider.displayName = 'MenuDivider';

export default Menu;

