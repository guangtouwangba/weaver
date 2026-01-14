/**
 * Server-side logging with Winston and Loki integration
 * This logger only works on the server side (API routes, Server Components)
 * For client-side logging, use console.log or send to an API endpoint
 */

import winston from 'winston';
import LokiTransport from 'winston-loki';

const isServer = typeof window === 'undefined';
const lokiUrl = process.env.LOKI_URL || '';
const lokiEnabled = process.env.LOKI_ENABLED === 'true';
const environment = process.env.NODE_ENV || 'development';

// Create Winston logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'frontend', environment },
  transports: [
    // Console transport (always enabled for development)
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      ),
    }),
  ],
});

// Add Loki transport if enabled and running on server
if (isServer && lokiEnabled && lokiUrl) {
  try {
    logger.add(
      new LokiTransport({
        host: lokiUrl,
        labels: { service: 'frontend', environment },
        json: true,
        format: winston.format.json(),
        replaceTimestamp: true,
        onConnectionError: (err) => {
          console.error('Loki connection error:', err);
        },
      })
    );
    logger.info('Loki transport initialized', { lokiUrl });
  } catch (error) {
    console.error('Failed to initialize Loki transport:', error);
  }
}

// Client-side stub (prevents errors when imported in browser)
if (!isServer) {
  const noopLogger = {
    info: (...args: unknown[]) => console.log(...args),
    warn: (...args: unknown[]) => console.warn(...args),
    error: (...args: unknown[]) => console.error(...args),
    debug: (...args: unknown[]) => console.debug(...args),
  };
  
  // Export noop logger for client-side
  module.exports = noopLogger;
} else {
  module.exports = logger;
}

export default logger;
