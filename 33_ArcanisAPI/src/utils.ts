import { randomBytes, createHash } from 'crypto';
export function generateId(len = 12): string { return randomBytes(len / 2).toString('hex'); }
export function sha256(d: string): string { return createHash('sha256').update(d).digest('hex'); }
export function sleep(ms: number): Promise<void> { return new Promise(r => setTimeout(r, ms)); }
