export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';
export type RouteMatch = { route: Route; params: Record<string, string> };
export interface Route { id: string; method: HttpMethod; path: string; handler: string; middleware: string[]; rateLimit?: number; auth?: boolean; version?: string; }
export interface ApiRequest { id: string; method: HttpMethod; path: string; headers: Record<string, string>; query: Record<string, string>; body?: unknown; userId?: string; timestamp: Date; }
export interface ApiResponse { status: number; headers: Record<string, string>; body: unknown; duration: number; }
export interface Middleware { id: string; name: string; order: number; handler: string; }
export interface RateLimitRule { id: string; path: string; maxRequests: number; windowMs: number; }
export interface ApiKey { id: string; key: string; name: string; scopes: string[]; rateLimit: number; createdAt: Date; expiresAt?: Date; }
export interface CircuitBreaker { id: string; serviceId: string; state: 'closed' | 'open' | 'half-open'; failureCount: number; threshold: number; timeout: number; lastFailure?: Date; }
export interface Transformer { id: string; name: string; type: 'request' | 'response'; rules: TransformRule[]; }
export interface TransformRule { path: string; action: 'add' | 'remove' | 'rename' | 'transform'; value?: string; }
