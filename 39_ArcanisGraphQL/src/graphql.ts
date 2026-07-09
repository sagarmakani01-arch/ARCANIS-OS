import { EventEmitter } from 'events';
import { randomBytes } from 'crypto';

function generateId(len = 12): string { return randomBytes(len / 2).toString('hex'); }

export type GqlType = 'String' | 'Int' | 'Float' | 'Boolean' | 'ID' | string;
export interface GqlField { name: string; type: GqlType; nullable?: boolean; isArray?: boolean; args?: GqlArg[]; description?: string; }
export interface GqlArg { name: string; type: GqlType; required?: boolean; defaultValue?: unknown; }
export interface GqlObjectType { name: string; fields: GqlField[]; description?: string; interfaces?: string[]; }
export interface GqlInputType { name: string; fields: GqlField[]; description?: string; }
export interface GqlEnumType { name: string; values: string[]; description?: string; }
export interface GqlQuery { name: string; returnType: GqlType; args?: GqlArg[]; resolver: string; description?: string; }
export interface GqlMutation { name: string; returnType: GqlType; args?: GqlArg[]; resolver: string; description?: string; }
export interface GqlSubscription { name: string; returnType: GqlType; args?: GqlArg[]; resolver: string; description?: string; }
export interface GqlDirective { name: string; locations: string[]; args?: GqlArg[]; }
export interface GqlSchema { types: GqlObjectType[]; inputTypes: GqlInputType[]; enums: GqlEnumType[]; queries: GqlQuery[]; mutations: GqlMutation[]; subscriptions: GqlSubscription[]; directives: GqlDirective[]; }
export interface GqlRequest { query: string; variables?: Record<string, unknown>; operationName?: string; }
export interface GqlResponse { data?: unknown; errors?: { message: string; path?: string[]; extensions?: Record<string, unknown> }[]; extensions?: Record<string, unknown>; }
export interface GqlQueryLog { id: string; query: string; variables?: Record<string, unknown>; duration: number; timestamp: Date; success: boolean; }
export interface GqlRateLimitRule { maxQueries: number; windowMs: number; }

export class GraphQLGateway extends EventEmitter {
  private schema: GqlSchema = { types: [], inputTypes: [], enums: [], queries: [], mutations: [], subscriptions: [], directives: [] };
  private resolvers: Map<string, Function> = new Map();
  private queryLogs: GqlQueryLog[] = [];
  private rateLimits: GqlRateLimitRule = { maxQueries: 100, windowMs: 60000 };
  private queryCounts: Map<string, number> = new Map();
  private persistedQueries: Map<string, string> = new Map();
  private depthLimit: number;

  constructor(options: { depthLimit?: number; rateLimit?: GqlRateLimitRule } = {}) {
    super();
    this.depthLimit = options.depthLimit || 10;
    if (options.rateLimit) this.rateLimits = options.rateLimit;
  }

  addType(type: GqlObjectType): void { this.schema.types.push(type); this.emit('type:add', type); }
  addInputType(type: GqlInputType): void { this.schema.inputTypes.push(type); }
  addEnum(type: GqlEnumType): void { this.schema.enums.push(type); }
  addQuery(query: GqlQuery): void { this.schema.queries.push(query); this.resolvers.set(`Query.${query.name}`, null); this.emit('query:add', query); }
  addMutation(mutation: GqlMutation): void { this.schema.mutations.push(mutation); this.resolvers.set(`Mutation.${mutation.name}`, null); }
  addSubscription(sub: GqlSubscription): void { this.schema.subscriptions.push(sub); }
  addDirective(directive: GqlDirective): void { this.schema.directives.push(directive); }

  registerResolver(typeName: string, fieldName: string, resolver: Function): void {
    this.resolvers.set(`${typeName}.${fieldName}`, resolver);
  }

  async execute(request: GqlRequest): Promise<GqlResponse> {
    const startTime = Date.now();
    const depth = this.measureDepth(request.query);
    if (depth > this.depthLimit) return { errors: [{ message: `Query depth ${depth} exceeds limit ${this.depthLimit}` }] };

    try {
      const operation = this.parseOperation(request.query);
      const resolverKey = `${operation.type}.${operation.name}`;
      const resolver = this.resolvers.get(resolverKey);
      if (!resolver) return { errors: [{ message: `No resolver for ${resolverKey}` }] };
      const result = await resolver(request.variables || {});
      const duration = Date.now() - startTime;
      this.queryLogs.push({ id: generateId(8), query: request.query, variables: request.variables, duration, timestamp: new Date(), success: true });
      this.emit('query:execute', { operation, duration });
      return { data: result };
    } catch (error: any) {
      const duration = Date.now() - startTime;
      this.queryLogs.push({ id: generateId(8), query: request.query, variables: request.variables, duration, timestamp: new Date(), success: false });
      return { errors: [{ message: error.message || 'Internal error' }] };
    }
  }

  private parseOperation(query: string): { type: string; name: string } {
    const trimmed = query.trim();
    if (trimmed.startsWith('mutation')) return { type: 'Mutation', name: trimmed.split(/\s+/)[1] || 'default' };
    if (trimmed.startsWith('subscription')) return { type: 'Subscription', name: trimmed.split(/\s+/)[1] || 'default' };
    return { type: 'Query', name: trimmed.split(/\s+/)[1] || 'default' };
  }

  measureDepth(query: string): number {
    let depth = 0; let maxDepth = 0;
    for (const ch of query) {
      if (ch === '{') { depth++; maxDepth = Math.max(maxDepth, depth); }
      if (ch === '}') depth--;
    }
    return maxDepth;
  }

  persistQuery(key: string, query: string): void { this.persistedQueries.set(key, query); }
  getPersistedQuery(key: string): string | undefined { return this.persistedQueries.get(key); }

  introspect(): GqlSchema { return this.schema; }
  getQueryLogs(limit?: number): GqlQueryLog[] { return limit ? this.queryLogs.slice(-limit) : [...this.queryLogs]; }
  generateSchemaString(): string { return `type Query { ${this.schema.queries.map(q => `${q.name}: ${q.returnType}`).join('\n  ')} }\ntype Mutation { ${this.schema.mutations.map(m => `${m.name}: ${m.returnType}`).join('\n  ')} }`; }
  getResolverCount(): number { return this.resolvers.size; }
}
