/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_BASE_URL || 'http://localhost:8000'}/:path*`,
      },
    ]
  },
  
  // Optimize for production
  experimental: {
    outputFileTracingRoot: undefined,
  },
  
  // Disable telemetry
  telemetry: false,
}

module.exports = nextConfig
