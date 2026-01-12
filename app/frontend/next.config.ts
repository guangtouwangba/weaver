import { config } from 'dotenv';
import { resolve } from 'path';

// Load root .env file for shared configuration (must be before NextConfig)
config({ path: resolve(__dirname, '../../.env') });

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    ignoreBuildErrors: true,
  },
  // Expose NEXT_PUBLIC_ env vars from root .env file
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    // Expose API_URL as NEXT_PUBLIC_API_URL for client-side WebSocket connections
    // This is needed because Next.js rewrites don't support WebSocket
    NEXT_PUBLIC_API_URL: process.env.API_URL || process.env.NEXT_PUBLIC_API_URL,
  },
  async rewrites() {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    // Remove trailing slash if present
    const baseUrl = apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl;
    console.log('[Next.js Rewrite] API_URL:', baseUrl);
    
    return [
      {
        source: '/api/:path*',
        destination: `${baseUrl}/api/:path*`,
      },
      // Also proxy health check
      {
        source: '/health',
        destination: `${baseUrl}/health`,
      },
    ];
  },
};

export default nextConfig;
