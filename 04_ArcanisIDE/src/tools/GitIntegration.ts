import { exec, spawn } from 'child_process';
import { promisify } from 'util';
import { GitStatus, GitChange } from '../api/types';
import { EventBus } from '../core/EventBus';
import { Configuration } from '../core/Configuration';

const execAsync = promisify(exec);

export interface GitResult {
  success: boolean;
  output: string;
  error?: string;
}

export interface GitBranch {
  name: string;
  current: boolean;
  remote?: string;
  behind: number;
  ahead: number;
}

export interface GitCommit {
  hash: string;
  author: string;
  email: string;
  date: Date;
  message: string;
  refs?: string[];
}

export interface GitRemote {
  name: string;
  url: string;
  fetchUrl: string;
  pushUrl: string;
}

export class GitIntegration {
  private cwd: string;

  constructor(
    private eventBus: EventBus,
    private configuration: Configuration
  ) {
    this.cwd = configuration.get<string>('workspace.root', process.cwd());
  }

  private async runGit(args: string[]): Promise<{ stdout: string; stderr: string }> {
    try {
      const result = await execAsync(`git ${args.join(' ')}`, {
        cwd: this.cwd,
        timeout: 30000,
        maxBuffer: 1024 * 1024,
      });
      return { stdout: result.stdout.trim(), stderr: result.stderr.trim() };
    } catch (err: any) {
      return { stdout: err.stdout?.trim() || '', stderr: err.stderr?.trim() || err.message };
    }
  }

  async init(path?: string): Promise<GitResult> {
    this.eventBus.emit('git:operationStart', { operation: 'init', path });

    const args = ['init'];
    if (path) args.push(path);

    const { stdout, stderr } = await this.runGit(args);
    const success = !stderr || stderr.includes('Initialized');

    const result: GitResult = {
      success,
      output: stdout || stderr,
      error: success ? undefined : stderr,
    };

    this.eventBus.emit('git:operationEnd', { operation: 'init', result });
    return result;
  }

  async clone(url: string, targetPath: string): Promise<GitResult> {
    this.eventBus.emit('git:operationStart', { operation: 'clone', url, targetPath });

    const { stdout, stderr } = await this.runGit(['clone', url, targetPath]);
    const success = !stderr || !stderr.includes('fatal');

    const result: GitResult = {
      success,
      output: stdout || `Cloned ${url}`,
      error: success ? undefined : stderr,
    };

    this.eventBus.emit('git:operationEnd', { operation: 'clone', result });
    return result;
  }

  async status(): Promise<GitStatus> {
    const { stdout } = await this.runGit(['status', '--porcelain=v1']);
    const { stdout: branchOut } = await this.runGit(['branch', '--show-current']);

    const changes: GitChange[] = [];
    let staged = 0;
    let modified = 0;
    let untracked = 0;
    let conflicts = 0;

    for (const line of stdout.split('\n').filter(Boolean)) {
      const indexStatus = line[0];
      const workStatus = line[1];
      const filePath = line.slice(3);

      const change: GitChange = {
        path: filePath,
        type: this.getChangeType(indexStatus, workStatus),
        staged: indexStatus !== ' ' && indexStatus !== '?',
      };

      changes.push(change);

      if (change.staged) staged++;
      if (workStatus === 'M' || indexStatus === 'M') modified++;
      if (indexStatus === '?') untracked++;
      if (indexStatus === 'U' || workStatus === 'U') conflicts++;
    }

    const { stdout: aheadBehind } = await this.runGit([
      'rev-list', '--left-right', '--count', `HEAD...@{upstream}`
    ]);
    const [ahead = '0', behind = '0'] = aheadBehind.split('\t');

    return {
      branch: branchOut || 'main',
      changes,
      ahead: parseInt(ahead) || 0,
      behind: parseInt(behind) || 0,
      staged,
      modified,
      untracked,
      conflicts,
    };
  }

  private getChangeType(index: string, work: string): GitChange['type'] {
    if (index === '?' || work === '?') return 'added';
    if (index === 'A' || work === 'A') return 'added';
    if (index === 'D' || work === 'D') return 'deleted';
    if (index === 'R' || work === 'R') return 'renamed';
    return 'modified';
  }

  async add(files?: string[]): Promise<GitResult> {
    const args = files ? ['add', ...files] : ['add', '.'];
    const { stdout, stderr } = await this.runGit(args);

    return {
      success: !stderr.includes('fatal'),
      output: files ? `Staged ${files.length} file(s)` : 'Staged all files',
      error: stderr.includes('fatal') ? stderr : undefined,
    };
  }

  async commit(message: string): Promise<GitResult> {
    const { stdout, stderr } = await this.runGit(['commit', '-m', message]);
    const success = !stderr.includes('fatal');

    return {
      success,
      output: stdout || `Committed: ${message}`,
      error: success ? undefined : stderr,
    };
  }

  async push(remote?: string, branch?: string): Promise<GitResult> {
    const args = ['push'];
    if (remote) args.push(remote);
    if (branch) args.push(branch);

    const { stdout, stderr } = await this.runGit(args);
    const success = !stderr.includes('fatal') && !stderr.includes('error');

    return {
      success,
      output: stdout || `Pushed to ${remote || 'origin'}/${branch || 'current'}`,
      error: success ? undefined : stderr,
    };
  }

  async pull(remote?: string, branch?: string): Promise<GitResult> {
    const args = ['pull'];
    if (remote) args.push(remote);
    if (branch) args.push(branch);

    const { stdout, stderr } = await this.runGit(args);
    const success = !stderr.includes('fatal');

    return {
      success,
      output: stdout || `Pulled from ${remote || 'origin'}/${branch || 'current'}`,
      error: success ? undefined : stderr,
    };
  }

  async branch(name?: string): Promise<GitBranch[]> {
    if (name) {
      await this.runGit(['branch', name]);
      return [{ name, current: true, behind: 0, ahead: 0 }];
    }

    const { stdout } = await this.runGit(['branch', '-a']);
    const branches: GitBranch[] = [];

    for (const line of stdout.split('\n').filter(Boolean)) {
      const isCurrent = line.startsWith('* ');
      const branchName = line.replace(/^\*\s+/, '').trim();
      const isRemote = branchName.startsWith('remotes/');

      if (!isRemote) {
        branches.push({
          name: branchName,
          current: isCurrent,
          behind: 0,
          ahead: 0,
        });
      }
    }

    return branches;
  }

  async checkout(target: string): Promise<GitResult> {
    const { stdout, stderr } = await this.runGit(['checkout', target]);
    const success = !stderr.includes('fatal');

    return {
      success,
      output: stdout || `Switched to ${target}`,
      error: success ? undefined : stderr,
    };
  }

  async log(maxCount: number = 10): Promise<GitCommit[]> {
    const format = '%H|%an|%ae|%aI|%s';
    const { stdout } = await this.runGit([
      'log', `--max-count=${maxCount}`, `--format=${format}`
    ]);

    const commits: GitCommit[] = [];
    for (const line of stdout.split('\n').filter(Boolean)) {
      const [hash, author, email, dateStr, ...messageParts] = line.split('|');
      commits.push({
        hash,
        author,
        email,
        date: new Date(dateStr),
        message: messageParts.join('|'),
      });
    }

    return commits;
  }

  async diff(file?: string): Promise<string> {
    const args = ['diff'];
    if (file) args.push(file);

    const { stdout } = await this.runGit(args);
    return stdout;
  }

  async stash(message?: string): Promise<GitResult> {
    const args = ['stash'];
    if (message) {
      args.push('push', '-m', message);
    }

    const { stdout, stderr } = await this.runGit(args);

    return {
      success: !stderr.includes('fatal'),
      output: stdout || (message ? `Stashed: ${message}` : 'Stashed changes'),
      error: stderr.includes('fatal') ? stderr : undefined,
    };
  }

  async stashPop(): Promise<GitResult> {
    const { stdout, stderr } = await this.runGit(['stash', 'pop']);

    return {
      success: !stderr.includes('fatal'),
      output: stdout || 'Restored stashed changes',
      error: stderr.includes('fatal') ? stderr : undefined,
    };
  }

  async getRemotes(): Promise<GitRemote[]> {
    const { stdout: namesOut } = await this.runGit(['remote']);
    const remotes: GitRemote[] = [];

    for (const name of namesOut.split('\n').filter(Boolean)) {
      const { stdout: fetchUrl } = await this.runGit(['remote', 'get-url', name]);
      const { stdout: pushUrl } = await this.runGit(['remote', 'get-url', '--push', name]);

      remotes.push({
        name,
        url: fetchUrl,
        fetchUrl,
        pushUrl: pushUrl || fetchUrl,
      });
    }

    return remotes;
  }
}
