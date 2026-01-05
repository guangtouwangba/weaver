'use client';

import React from 'react';
import { colors } from '../tokens';

/**
 * Progress Component
 *
 * A progress indicator for loading states.
 * Pure CSS implementation without MUI dependency.
 */

export interface ProgressProps {
    /** Current progress value (0-100). Undefined = indeterminate */
    value?: number;
    /** Visual variant */
    variant?: 'linear' | 'circular';
    /** Color scheme */
    color?: 'primary' | 'success' | 'warning' | 'error';
    /** Size of the progress indicator */
    size?: 'sm' | 'md' | 'lg';
    /** Whether to show the percentage label */
    showLabel?: boolean;
    /** Additional CSS class */
    className?: string;
    /** Additional inline styles */
    style?: React.CSSProperties;
}

const sizeConfig = {
    linear: {
        sm: { height: 2 },
        md: { height: 4 },
        lg: { height: 8 },
    },
    circular: {
        sm: { size: 16, strokeWidth: 2 },
        md: { size: 24, strokeWidth: 3 },
        lg: { size: 40, strokeWidth: 4 },
    },
};

const colorMap = {
    primary: colors.primary[500],
    success: colors.success[500],
    warning: colors.warning[500],
    error: colors.error[500],
};

export const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
    function Progress(
        {
            value,
            variant = 'linear',
            color = 'primary',
            size = 'md',
            showLabel = false,
            className,
            style,
        },
        ref
    ) {
        const isIndeterminate = value === undefined;
        const progressColor = colorMap[color];

        if (variant === 'circular') {
            const config = sizeConfig.circular[size];
            const radius = (config.size - config.strokeWidth) / 2;
            const circumference = 2 * Math.PI * radius;
            const offset = isIndeterminate ? 0 : circumference - (circumference * (value ?? 0)) / 100;

            return (
                <div
                    ref={ref}
                    className={className}
                    style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        position: 'relative',
                        width: config.size,
                        height: config.size,
                        ...style,
                    }}
                >
                    <svg
                        width={config.size}
                        height={config.size}
                        style={{
                            transform: 'rotate(-90deg)',
                            animation: isIndeterminate ? 'spin 1.4s linear infinite' : undefined,
                        }}
                    >
                        {/* Background circle */}
                        <circle
                            cx={config.size / 2}
                            cy={config.size / 2}
                            r={radius}
                            fill="none"
                            stroke={colors.neutral[200]}
                            strokeWidth={config.strokeWidth}
                        />
                        {/* Progress circle */}
                        <circle
                            cx={config.size / 2}
                            cy={config.size / 2}
                            r={radius}
                            fill="none"
                            stroke={progressColor}
                            strokeWidth={config.strokeWidth}
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={isIndeterminate ? circumference * 0.75 : offset}
                            style={{
                                transition: isIndeterminate ? undefined : 'stroke-dashoffset 0.3s ease',
                            }}
                        />
                    </svg>
                    {showLabel && !isIndeterminate && (
                        <span
                            style={{
                                position: 'absolute',
                                fontSize: size === 'lg' ? 10 : 8,
                                fontWeight: 600,
                                color: colors.text.secondary,
                            }}
                        >
                            {Math.round(value ?? 0)}%
                        </span>
                    )}
                    <style>{`
            @keyframes spin {
              from { transform: rotate(-90deg); }
              to { transform: rotate(270deg); }
            }
          `}</style>
                </div>
            );
        }

        // Linear variant
        const config = sizeConfig.linear[size];

        return (
            <div
                ref={ref}
                className={className}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    width: '100%',
                    ...style,
                }}
            >
                <div
                    style={{
                        flex: 1,
                        height: config.height,
                        backgroundColor: colors.neutral[200],
                        borderRadius: config.height / 2,
                        overflow: 'hidden',
                        position: 'relative',
                    }}
                >
                    <div
                        style={{
                            height: '100%',
                            backgroundColor: progressColor,
                            borderRadius: config.height / 2,
                            width: isIndeterminate ? '30%' : `${value}%`,
                            transition: isIndeterminate ? undefined : 'width 0.3s ease',
                            animation: isIndeterminate ? 'indeterminate 1.5s ease-in-out infinite' : undefined,
                        }}
                    />
                </div>
                {showLabel && !isIndeterminate && (
                    <span
                        style={{
                            fontSize: 12,
                            fontWeight: 500,
                            color: colors.text.secondary,
                            minWidth: 32,
                            textAlign: 'right',
                        }}
                    >
                        {Math.round(value ?? 0)}%
                    </span>
                )}
                <style>{`
          @keyframes indeterminate {
            0% { 
              transform: translateX(-100%);
            }
            100% { 
              transform: translateX(400%);
            }
          }
        `}</style>
            </div>
        );
    }
);

Progress.displayName = 'Progress';

export default Progress;
