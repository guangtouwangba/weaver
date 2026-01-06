'use client';

import React from 'react';
import { colors, radii, fontSize, fontWeight } from '../tokens';

/**
 * Avatar Component
 *
 * User profile image or initials.
 * Pure CSS implementation.
 */

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
    /** Size of the avatar */
    size?: number;
    /** Image source */
    src?: string;
    /** Image alt text */
    alt?: string;
}

export const Avatar = React.forwardRef<HTMLDivElement, AvatarProps>(
    function Avatar({ size, src, alt, style, children, className, ...props }, ref) {
        return (
            <div
                ref={ref}
                className={className}
                style={{
                    width: size || 40,
                    height: size || 40,
                    borderRadius: radii.full,
                    backgroundColor: colors.primary[500],
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: size ? size * 0.5 : fontSize.md,
                    fontWeight: fontWeight.bold,
                    overflow: 'hidden',
                    ...style,
                }}
                {...props}
            >
                {src ? (
                    <img 
                        src={src} 
                        alt={alt} 
                        style={{ 
                            width: '100%', 
                            height: '100%', 
                            objectFit: 'cover' 
                        }} 
                    />
                ) : (
                    children
                )}
            </div>
        );
    }
);

Avatar.displayName = 'Avatar';
