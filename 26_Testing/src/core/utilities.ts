// Utilities for ArcanisTesting Framework

import { v4 as uuidv4 } from 'uuid';

export const generateId = (): string => uuidv4();

export const delay = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

export const formatDuration = (ms: number): string => {
  if (ms < 1) return '< 1ms';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
};

export const formatPercentage = (value: number): string => `${value.toFixed(1)}%`;

export const sleep = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

export const retry = async <T>(
  fn: () => Promise<T>,
  maxRetries: number,
  delayMs: number = 100
): Promise<T> => {
  let lastError: Error | undefined;
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (i < maxRetries) {
        await sleep(delayMs * Math.pow(2, i)); // Exponential backoff
      }
    }
  }
  throw lastError;
};

export const chunk = <T>(array: T[], size: number): T[][] => {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
};

export const flatten = <T>(arrays: T[][]): T[] => arrays.reduce((a, b) => a.concat(b), []);

export const unique = <T>(array: T[]): T[] => [...new Set(array)];

export const groupBy = <T>(array: T[], key: (item: T) => string): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const group = key(item);
    groups[group] = groups[group] || [];
    groups[group].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

export const pick = <T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  for (const key of keys) {
    if (key in obj) {
      result[key] = obj[key];
    }
  }
  return result;
};

export const omit = <T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> => {
  const result = { ...obj };
  for (const key of keys) {
    delete result[key];
  }
  return result as Omit<T, K>;
};

export const isObject = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
};

export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as T;
  if (obj instanceof Object) {
    const clonedObj = {} as T;
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        clonedObj[key] = deepClone(obj[key as keyof T]);
      }
    }
    return clonedObj;
  }
  return obj;
};

export const measurePerformance = async <T>(
  fn: () => Promise<T>,
  iterations: number = 100
): Promise<{
  result: T;
  avg: number;
  min: number;
  max: number;
  p50: number;
  p90: number;
  p95: number;
  p99: number;
}> => {
  const durations: number[] = [];
  let result: T;

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    result = await fn();
    durations.push(performance.now() - start);
  }

  durations.sort((a, b) => a - b);

  return {
    result: result!,
    avg: durations.reduce((a, b) => a + b, 0) / durations.length,
    min: durations[0],
    max: durations[durations.length - 1],
    p50: durations[Math.floor(durations.length * 0.5)],
    p90: durations[Math.floor(durations.length * 0.9)],
    p95: durations[Math.floor(durations.length * 0.95)],
    p99: durations[Math.floor(durations.length * 0.99)],
  };
};

export const calculatePercentile = (sorted: number[], percentile: number): number => {
  const index = Math.ceil(sorted.length * percentile) - 1;
  return sorted[Math.max(0, index)];
};

export const calculateMean = (numbers: number[]): number => {
  if (numbers.length === 0) return 0;
  return numbers.reduce((a, b) => a + b, 0) / numbers.length;
};

export const calculateStandardDeviation = (numbers: number[]): number => {
  const mean = calculateMean(numbers);
  const squareDiffs = numbers.map(n => Math.pow(n - mean, 2));
  const variance = calculateMean(squareDiffs);
  return Math.sqrt(variance);
};
