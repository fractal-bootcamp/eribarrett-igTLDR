/**
 * Shared utility functions for the ts-services module
 */
import fs from 'fs';
import path from 'path';

/**
 * File utility functions
 */
export const FileUtils = {
  /**
   * Get the latest file from a directory that matches a pattern
   * @param directory Directory to search in
   * @param pattern Pattern to match (regex or string)
   * @returns Full path to the latest file
   */
  getLatestFile(directory: string, pattern: string | RegExp): string | null {
    try {
      if (!fs.existsSync(directory)) {
        console.error(`Directory does not exist: ${directory}`);
        return null;
      }

      const files = fs.readdirSync(directory)
        .filter(file => {
          if (pattern instanceof RegExp) {
            return pattern.test(file);
          }
          return file.includes(pattern);
        })
        .map(file => path.join(directory, file))
        .filter(file => fs.statSync(file).isFile());

      if (files.length === 0) {
        return null;
      }

      // Sort by modification time, newest first
      files.sort((a, b) => {
        return fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime();
      });

      return files[0];
    } catch (error) {
      console.error('Error getting latest file:', error);
      return null;
    }
  },

  /**
   * Get the latest file from a directory using a latest.json reference
   * @param directory Directory to search in
   * @returns Full path to the latest file
   */
  getLatestFileFromReference(directory: string): string | null {
    try {
      const latestRefPath = path.join(directory, 'latest.json');

      if (!fs.existsSync(latestRefPath)) {
        console.log(`No latest.json reference found in ${directory}, falling back to timestamp sorting`);
        return this.getLatestFile(directory, '.json');
      }

      const latestRef = JSON.parse(fs.readFileSync(latestRefPath, 'utf-8'));
      const latestFile = path.join(directory, latestRef.latest_file);

      if (!fs.existsSync(latestFile)) {
        console.warn(`Latest file referenced in latest.json does not exist: ${latestFile}`);
        return this.getLatestFile(directory, '.json');
      }

      return latestFile;
    } catch (error) {
      console.error('Error getting latest file from reference:', error);
      return this.getLatestFile(directory, '.json');
    }
  },

  /**
   * Creates a timestamped filename
   * @param prefix Prefix for the filename
   * @param extension File extension (without dot)
   * @returns Formatted filename with date and time
   */
  getTimestampedFilename(prefix: string, extension: string): string {
    const now = new Date();
    const date = now.toISOString().split('T')[0]; // YYYY-MM-DD
    const timestamp = now.toISOString()
      .replace(/[:.]/g, '-')
      .replace('T', '_')
      .split('Z')[0];
    
    return `${prefix}_${date}_${timestamp}.${extension}`;
  },

  /**
   * Makes sure a directory exists, creating it if necessary
   * @param directory Path to ensure exists
   */
  ensureDirectoryExists(directory: string): void {
    if (!fs.existsSync(directory)) {
      fs.mkdirSync(directory, { recursive: true });
    }
  },
  
  /**
   * Update or create a latest.json reference file
   * @param directory Directory to create the reference in
   * @param filename Name of the latest file (not the full path)
   * @param metadata Any additional metadata to include
   */
  updateLatestReference(directory: string, filename: string, metadata: Record<string, any> = {}): void {
    try {
      this.ensureDirectoryExists(directory);
      
      const latestRefPath = path.join(directory, 'latest.json');
      const data = {
        latest_file: filename,
        timestamp: new Date().toISOString(),
        ...metadata
      };
      
      fs.writeFileSync(latestRefPath, JSON.stringify(data, null, 2));
    } catch (error) {
      console.error('Error updating latest reference:', error);
    }
  }
};

/**
 * Date utility functions
 */
export const DateUtils = {
  /**
   * Format date as YYYY-MM-DD
   */
  formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  },
  
  /**
   * Format date as YYYY-MM-DD_HH-MM-SS
   */
  formatDateTime(date: Date): string {
    return date.toISOString()
      .replace(/[:.]/g, '-')
      .replace('T', '_')
      .split('Z')[0];
  },
  
  /**
   * Get start of day
   */
  startOfDay(date: Date): Date {
    const result = new Date(date);
    result.setHours(0, 0, 0, 0);
    return result;
  },
  
  /**
   * Get end of day
   */
  endOfDay(date: Date): Date {
    const result = new Date(date);
    result.setHours(23, 59, 59, 999);
    return result;
  },
  
  /**
   * Check if a date is today
   */
  isToday(date: Date): boolean {
    const today = new Date();
    return this.formatDate(date) === this.formatDate(today);
  }
};

/**
 * Path constants for the application
 */
export const Paths = {
  DATA_DIR: path.join(process.cwd(), 'data'),
  POSTS_DIR: path.join(process.cwd(), 'data', 'posts'),
  DAILY_POSTS_DIR: path.join(process.cwd(), 'data', 'posts', 'daily'),
  SUMMARIES_DIR: path.join(process.cwd(), 'data', 'summaries'),
  PYTHON_DATA_DIR: path.resolve(process.cwd(), '../backend/data')
};

export default {
  FileUtils,
  DateUtils,
  Paths
};