import * as https from 'https';
import * as http from 'http';
import { IDisposable } from '../api/types';
import { EventBus } from '../core/EventBus';

export interface PackageOptions {
  isDev?: boolean;
  force?: boolean;
  registry?: string;
  global?: boolean;
}

export interface PackageResult {
  success: boolean;
  packageName: string;
  version: string;
  output: string;
  duration: number;
}

export interface PackageSearchResult {
  name: string;
  version: string;
  description: string;
  author: string;
  downloads: number;
  tags: string[];
}

export interface InstalledPackage {
  name: string;
  version: string;
  description: string;
  dependencies: string[];
  isDev: boolean;
}

export interface PackageInfo {
  name: string;
  version: string;
  description: string;
  author: string;
  license: string;
  homepage?: string;
  repository?: string;
  dependencies: Record<string, string>;
  readme?: string;
}

export class PackageManager {
  private packages = new Map<string, InstalledPackage>();
  private registryUrl: string;

  constructor(private eventBus: EventBus, registryUrl?: string) {
    this.registryUrl = registryUrl || 'https://registry.arcanis.dev';
  }

  private async httpGet(url: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const client = url.startsWith('https') ? https : http;
      const req = client.get(url, { timeout: 15000 }, (res) => {
        if (res.statusCode === 301 || res.statusCode === 302) {
          const location = res.headers.location;
          if (location) {
            this.httpGet(location).then(resolve).catch(reject);
            return;
          }
        }

        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch {
            resolve(data);
          }
        });
      });
      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timed out'));
      });
    });
  }

  private async httpPut(url: string, body: any, token?: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const parsedUrl = new URL(url);
      const options: https.RequestOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname,
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        timeout: 15000,
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode, body: JSON.parse(data) });
          } catch {
            resolve({ status: res.statusCode, body: data });
          }
        });
      });
      req.on('error', reject);
      req.write(JSON.stringify(body));
      req.end();
    });
  }

  private async httpPost(url: string, body: any, token?: string): Promise<any> {
    return new Promise((resolve, reject) => {
      const parsedUrl = new URL(url);
      const options: https.RequestOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        timeout: 15000,
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode, body: JSON.parse(data) });
          } catch {
            resolve({ status: res.statusCode, body: data });
          }
        });
      });
      req.on('error', reject);
      req.write(JSON.stringify(body));
      req.end();
    });
  }

  async install(packageName: string, version?: string, options?: PackageOptions): Promise<PackageResult> {
    const startTime = Date.now();
    const versionSpec = version || 'latest';

    try {
      const info = await this.info(packageName);
      if (!info) {
        return {
          success: false,
          packageName,
          version: versionSpec,
          output: `Package not found: ${packageName}`,
          duration: Date.now() - startTime,
        };
      }

      const pkg: InstalledPackage = {
        name: packageName,
        version: info.version,
        description: info.description,
        dependencies: Object.keys(info.dependencies || {}),
        isDev: options?.isDev || false,
      };

      this.packages.set(packageName, pkg);
      this.eventBus.emit('package:installed', pkg);

      return {
        success: true,
        packageName,
        version: pkg.version,
        output: `Installed ${packageName}@${pkg.version}`,
        duration: Date.now() - startTime,
      };
    } catch (err: any) {
      return {
        success: false,
        packageName,
        version: versionSpec,
        output: `Failed to install ${packageName}: ${err.message}`,
        duration: Date.now() - startTime,
      };
    }
  }

  async uninstall(packageName: string): Promise<PackageResult> {
    const pkg = this.packages.get(packageName);
    if (!pkg) {
      return {
        success: false,
        packageName,
        version: '',
        output: `Package ${packageName} not found`,
        duration: 0,
      };
    }

    this.packages.delete(packageName);
    this.eventBus.emit('package:uninstalled', pkg);

    return {
      success: true,
      packageName,
      version: pkg.version,
      output: `Uninstalled ${packageName}@${pkg.version}`,
      duration: 0,
    };
  }

  async update(packageName?: string): Promise<PackageResult> {
    const startTime = Date.now();
    const name = packageName || 'all';

    try {
      if (packageName) {
        const pkg = this.packages.get(packageName);
        if (!pkg) {
          return {
            success: false,
            packageName,
            version: '',
            output: `Package ${packageName} not found`,
            duration: Date.now() - startTime,
          };
        }

        const info = await this.info(packageName);
        if (info && info.version !== pkg.version) {
          pkg.version = info.version;
          this.eventBus.emit('package:updated', pkg);
        }
      } else {
        for (const pkg of this.packages.values()) {
          const info = await this.info(pkg.name);
          if (info) {
            pkg.version = info.version;
          }
          this.eventBus.emit('package:updated', pkg);
        }
      }

      return {
        success: true,
        packageName: name,
        version: 'latest',
        output: `Updated ${name}`,
        duration: Date.now() - startTime,
      };
    } catch (err: any) {
      return {
        success: false,
        packageName: name,
        version: '',
        output: `Failed to update ${name}: ${err.message}`,
        duration: Date.now() - startTime,
      };
    }
  }

  async search(query: string): Promise<PackageSearchResult[]> {
    try {
      const url = `${this.registryUrl}/-/v1/search?text=${encodeURIComponent(query)}&size=20`;
      const result = await this.httpGet(url);

      if (result && result.objects) {
        return result.objects.map((obj: any) => ({
          name: obj.package?.name || '',
          version: obj.package?.version || '',
          description: obj.package?.description || '',
          author: obj.package?.author?.name || obj.package?.publisher?.username || '',
          downloads: obj.downloads?.monthly || 0,
          tags: obj.package?.keywords || [],
        }));
      }

      return [];
    } catch {
      return [];
    }
  }

  async list(): Promise<InstalledPackage[]> {
    return Array.from(this.packages.values());
  }

  async publish(packagePath: string, token?: string): Promise<PackageResult> {
    const startTime = Date.now();

    try {
      const url = `${this.registryUrl}/${encodeURIComponent(packagePath)}`;
      const result = await this.httpPut(url, { name: packagePath }, token);

      return {
        success: result.status === 201 || result.status === 200,
        packageName: packagePath,
        version: result.body?.version || '1.0.0',
        output: `Published ${packagePath}`,
        duration: Date.now() - startTime,
      };
    } catch (err: any) {
      return {
        success: false,
        packageName: packagePath,
        version: '',
        output: `Failed to publish ${packagePath}: ${err.message}`,
        duration: Date.now() - startTime,
      };
    }
  }

  async info(packageName: string): Promise<PackageInfo | undefined> {
    try {
      const url = `${this.registryUrl}/${encodeURIComponent(packageName).replace('%40', '@')}`;
      const data = await this.httpGet(url);

      if (!data || !data.name) return undefined;

      const latestVersion = data['dist-tags']?.latest || Object.keys(data.versions || {})[0];
      const versionData = data.versions?.[latestVersion] || {};

      return {
        name: data.name,
        version: latestVersion,
        description: data.description || '',
        author: data.author?.name || data.maintainers?.[0]?.name || '',
        license: data.license || 'MIT',
        homepage: data.homepage,
        repository: typeof data.repository === 'string' ? data.repository : data.repository?.url,
        dependencies: versionData.dependencies || {},
        readme: data.readme,
      };
    } catch {
      return undefined;
    }
  }
}
