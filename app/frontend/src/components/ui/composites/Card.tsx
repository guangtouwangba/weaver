'use client';

import React from 'react';
import { Surface, Stack, Text } from '../primitives';
import { SurfaceProps } from '../primitives/Surface';

/**
 * Card Component
 *
 * A structured container with optional header and footer.
 * Built from Surface + Stack primitives.
 */

export interface CardProps extends Omit<SurfaceProps, 'children'> {
    /** Card header title */
    title?: React.ReactNode;
    /** Card header subtitle */
    subtitle?: React.ReactNode;
    /** Right-side header action */
    headerAction?: React.ReactNode;
    /** Card body content */
    children?: React.ReactNode;
    /** Card footer content */
    footer?: React.ReactNode;
    /** Whether to show dividers between sections */
    divided?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
    function Card(
        {
            title,
            subtitle,
            headerAction,
            children,
            footer,
            divided = false,
            elevation = 1,
            radius = 'lg',
            bordered = true,
            ...props
        },
        ref
    ) {
        const hasHeader = title || subtitle || headerAction;

        return (
            <Surface
                ref={ref}
                elevation={elevation}
                radius={radius}
                bordered={bordered}
                {...props}
            >
                {hasHeader && (
                    <Stack
                        direction="row"
                        justify="between"
                        align="center"
                        sx={{
                            px: 3,
                            py: 2,
                            ...(divided && {
                                borderBottom: '1px solid',
                                borderColor: 'divider',
                            }),
                        }}
                    >
                        <Stack direction="column" gap={0}>
                            {title && (
                                <Text variant="h6" color="primary">
                                    {title}
                                </Text>
                            )}
                            {subtitle && (
                                <Text variant="caption" color="secondary">
                                    {subtitle}
                                </Text>
                            )}
                        </Stack>
                        {headerAction}
                    </Stack>
                )}

                {children && (
                    <div style={{ padding: hasHeader ? '16px 24px' : 24 }}>
                        {children}
                    </div>
                )}

                {footer && (
                    <Stack
                        direction="row"
                        justify="end"
                        gap={2}
                        sx={{
                            px: 3,
                            py: 2,
                            ...(divided && {
                                borderTop: '1px solid',
                                borderColor: 'divider',
                            }),
                        }}
                    >
                        {footer}
                    </Stack>
                )}
            </Surface>
        );
    }
);

Card.displayName = 'Card';

export default Card;
