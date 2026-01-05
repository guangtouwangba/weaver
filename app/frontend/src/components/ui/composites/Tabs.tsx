'use client';

import React, { createContext, useContext } from 'react';
import { colors, radii, fontSize, fontWeight } from '../tokens';

/**
 * Tabs Component
 *
 * A tabbed interface for switching between views.
 * Pure CSS implementation without MUI dependency.
 */

// Context for sharing state
interface TabsContextValue {
    value: string;
    onChange: (value: string) => void;
    variant: 'default' | 'pills' | 'underlined';
}

const TabsContext = createContext<TabsContextValue | null>(null);

export interface TabsProps {
    /** Currently selected tab value */
    value: string;
    /** Callback when tab changes */
    onChange: (value: string) => void;
    /** Tab items */
    children: React.ReactNode;
    /** Visual variant */
    variant?: 'default' | 'pills' | 'underlined';
    /** Full width tabs */
    fullWidth?: boolean;
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

export function Tabs({
    value,
    onChange,
    children,
    variant = 'default',
    fullWidth = false,
    className,
    style,
}: TabsProps) {
    return (
        <TabsContext.Provider value={{ value, onChange, variant }}>
            <div
                role="tablist"
                className={className}
                style={{
                    display: 'flex',
                    gap: variant === 'pills' ? 8 : 0,
                    borderBottom: variant === 'underlined' ? `1px solid ${colors.border.default}` : undefined,
                    backgroundColor: variant === 'default' ? colors.neutral[100] : undefined,
                    borderRadius: variant === 'default' ? radii.md : undefined,
                    padding: variant === 'default' ? 4 : undefined,
                    width: fullWidth ? '100%' : 'fit-content',
                    ...style,
                }}
            >
                {children}
            </div>
        </TabsContext.Provider>
    );
}

export interface TabProps {
    /** Unique value for this tab */
    value: string;
    /** Tab label */
    label: string;
    /** Optional icon */
    icon?: React.ReactNode;
    /** Whether the tab is disabled */
    disabled?: boolean;
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

export function Tab({
    value,
    label,
    icon,
    disabled = false,
    className,
    style,
}: TabProps) {
    const context = useContext(TabsContext);
    if (!context) {
        throw new Error('Tab must be used within Tabs');
    }

    const { value: selectedValue, onChange, variant } = context;
    const isSelected = selectedValue === value;

    const handleClick = () => {
        if (!disabled) {
            onChange(value);
        }
    };

    // Variant-specific styles
    const getVariantStyles = (): React.CSSProperties => {
        const base: React.CSSProperties = {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            padding: '8px 16px',
            fontSize: fontSize.sm,
            fontWeight: isSelected ? fontWeight.medium : fontWeight.normal,
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.5 : 1,
            transition: 'all 0.15s ease',
            border: 'none',
            outline: 'none',
            fontFamily: 'inherit',
        };

        switch (variant) {
            case 'pills':
                return {
                    ...base,
                    borderRadius: radii.md,
                    backgroundColor: isSelected ? colors.primary[500] : 'transparent',
                    color: isSelected ? '#fff' : colors.text.secondary,
                };
            case 'underlined':
                return {
                    ...base,
                    backgroundColor: 'transparent',
                    color: isSelected ? colors.primary[600] : colors.text.secondary,
                    borderBottom: `2px solid ${isSelected ? colors.primary[500] : 'transparent'}`,
                    marginBottom: -1,
                    borderRadius: 0,
                };
            default:
                return {
                    ...base,
                    borderRadius: radii.sm,
                    backgroundColor: isSelected ? colors.background.paper : 'transparent',
                    color: isSelected ? colors.text.primary : colors.text.secondary,
                    boxShadow: isSelected ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                };
        }
    };

    return (
        <button
            role="tab"
            aria-selected={isSelected}
            tabIndex={isSelected ? 0 : -1}
            disabled={disabled}
            onClick={handleClick}
            className={className}
            style={{
                ...getVariantStyles(),
                ...style,
            }}
        >
            {icon && <span style={{ display: 'flex' }}>{icon}</span>}
            <span>{label}</span>
        </button>
    );
}

// TabPanel for content
export interface TabPanelProps {
    /** Value that corresponds to the tab */
    value: string;
    /** Currently selected value (from Tabs) */
    selectedValue: string;
    /** Panel content */
    children: React.ReactNode;
    /** Keep content mounted when hidden */
    keepMounted?: boolean;
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

export function TabPanel({
    value,
    selectedValue,
    children,
    keepMounted = false,
    className,
    style,
}: TabPanelProps) {
    const isSelected = value === selectedValue;

    if (!isSelected && !keepMounted) {
        return null;
    }

    return (
        <div
            role="tabpanel"
            hidden={!isSelected}
            className={className}
            style={{
                display: isSelected ? 'block' : 'none',
                ...style,
            }}
        >
            {children}
        </div>
    );
}

Tabs.displayName = 'Tabs';
Tab.displayName = 'Tab';
TabPanel.displayName = 'TabPanel';

export default Tabs;
