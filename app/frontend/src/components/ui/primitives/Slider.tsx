'use client';

import React from 'react';
import { colors, radii } from '../tokens';

/**
 * Slider Component
 *
 * A slider for selecting a value from a range.
 * Pure CSS implementation using input[type="range"].
 */

export interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange' | 'value' | 'min' | 'max' | 'step'> {
    value?: number;
    min?: number;
    max?: number;
    step?: number;
    onChange?: (value: number) => void;
    onCommit?: (value: number) => void;
    color?: 'primary' | 'secondary';
}

export const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
    function Slider(
        {
            value = 0,
            min = 0,
            max = 100,
            step = 1,
            onChange,
            onCommit,
            color = 'primary',
            disabled,
            style,
            className,
            ...props
        },
        ref
    ) {
        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
            onChange?.(Number(e.target.value));
        };

        const handleCommit = (e: React.MouseEvent<HTMLInputElement> | React.TouchEvent<HTMLInputElement>) => {
            onCommit?.(Number(e.currentTarget.value));
        };

        // Calculate percentage for background gradient
        const percentage = ((value - min) / (max - min)) * 100;
        const activeColor = color === 'secondary' ? colors.neutral[500] : colors.primary[500];

        // Unique class for this slider instance color to support dynamic colors if needed,
        // but for now we rely on inline styles for track and standard class for thumb.
        
        return (
            <div style={{ position: 'relative', width: '100%', height: 24, display: 'flex', alignItems: 'center' }}>
                <style dangerouslySetInnerHTML={{__html: `
                    .custom-slider-thumb::-webkit-slider-thumb {
                        -webkit-appearance: none;
                        appearance: none;
                        width: 16px;
                        height: 16px;
                        border-radius: 50%;
                        background: #ffffff;
                        cursor: pointer;
                        border: 2px solid currentColor;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        margin-top: -6px; /* align with track */
                        transition: transform 0.1s;
                    }
                    .custom-slider-thumb::-webkit-slider-thumb:hover {
                        transform: scale(1.1);
                        box-shadow: 0 0 0 4px rgba(0,0,0,0.05);
                    }
                    .custom-slider-thumb::-moz-range-thumb {
                        width: 16px;
                        height: 16px;
                        border-radius: 50%;
                        background: #ffffff;
                        cursor: pointer;
                        border: 2px solid currentColor;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                        transition: transform 0.1s;
                    }
                    .custom-slider-thumb::-moz-range-thumb:hover {
                        transform: scale(1.1);
                        box-shadow: 0 0 0 4px rgba(0,0,0,0.05);
                    }
                `}} />
                <input
                    ref={ref}
                    type="range"
                    value={value}
                    min={min}
                    max={max}
                    step={step}
                    onChange={handleChange}
                    onMouseUp={handleCommit}
                    onTouchEnd={handleCommit}
                    disabled={disabled}
                    className={`custom-slider-thumb ${className || ''}`}
                    style={{
                        width: '100%',
                        height: 4,
                        borderRadius: radii.full,
                        appearance: 'none',
                        backgroundColor: colors.neutral[200],
                        outline: 'none',
                        cursor: disabled ? 'not-allowed' : 'pointer',
                        backgroundImage: `linear-gradient(${activeColor}, ${activeColor})`,
                        backgroundSize: `${percentage}% 100%`,
                        backgroundRepeat: 'no-repeat',
                        color: activeColor, // Used by thumb border via currentColor
                        ...style,
                    }}
                    {...props}
                />
            </div>
        );
    }
);

Slider.displayName = 'Slider';
