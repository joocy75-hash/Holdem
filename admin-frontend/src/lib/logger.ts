/**
 * Logger utility for conditional logging.
 * 
 * In production, only errors and warnings are logged.
 * In development, all logs are shown.
 */

const isDevelopment = process.env.NODE_ENV === 'development';

interface Logger {
  log: (...args: unknown[]) => void;
  info: (...args: unknown[]) => void;
  warn: (...args: unknown[]) => void;
  error: (...args: unknown[]) => void;
  debug: (...args: unknown[]) => void;
}

/**
 * Application logger that respects environment.
 * 
 * Usage:
 *   import { logger } from '@/lib/logger';
 *   logger.log('Debug info');  // Only in development
 *   logger.error('Error!');    // Always logged
 */
export const logger: Logger = {
  /**
   * Log general information (development only)
   */
  log: (...args: unknown[]) => {
    if (isDevelopment) {
      console.log(...args);
    }
  },

  /**
   * Log informational messages (development only)
   */
  info: (...args: unknown[]) => {
    if (isDevelopment) {
      console.info(...args);
    }
  },

  /**
   * Log warnings (always)
   */
  warn: (...args: unknown[]) => {
    console.warn(...args);
  },

  /**
   * Log errors (always)
   */
  error: (...args: unknown[]) => {
    console.error(...args);
  },

  /**
   * Log debug information (development only)
   */
  debug: (...args: unknown[]) => {
    if (isDevelopment) {
      console.debug(...args);
    }
  },
};

export default logger;
