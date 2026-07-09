export function generateId(len = 12): string { return require('crypto').randomBytes(len / 2).toString('hex'); }
