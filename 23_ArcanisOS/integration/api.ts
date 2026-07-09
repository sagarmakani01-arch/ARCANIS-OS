export interface ApiEndpoint {
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  path: string;
  handler: (params: Record<string, unknown>, body?: unknown) => Promise<ApiResponse>;
}

export interface ApiResponse {
  status: number;
  data: unknown;
  error?: string;
}

export class ApiGateway {
  private endpoints: Map<string, ApiEndpoint> = new Map();

  register(endpoint: ApiEndpoint): void {
    const key = `${endpoint.method}:${endpoint.path}`;
    this.endpoints.set(key, endpoint);
  }

  unregister(method: string, path: string): void {
    const key = `${method}:${path}`;
    this.endpoints.delete(key);
  }

  async call(method: string, path: string, params: Record<string, unknown> = {}, body?: unknown): Promise<ApiResponse> {
    const key = `${method}:${path}`;
    const endpoint = this.endpoints.get(key);
    if (!endpoint) {
      return { status: 404, data: null, error: `No endpoint found: ${method} ${path}` };
    }
    try {
      return await endpoint.handler(params, body);
    } catch (error) {
      return { status: 500, data: null, error: String(error) };
    }
  }

  list(): ApiEndpoint[] {
    return Array.from(this.endpoints.values());
  }
}
