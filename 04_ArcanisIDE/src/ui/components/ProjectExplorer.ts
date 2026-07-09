import * as fs from 'fs';
import * as path from 'path';
import { FileItem, WorkspaceFolder, IDisposable } from '../../api/types';
import { EventBus } from '../../core/EventBus';
import { UIComponent } from '../UIEngine';

export class ProjectExplorer implements UIComponent {
  id = 'project-explorer';
  private workspaceFolders: WorkspaceFolder[] = [];
  private fileTree: FileItem[] = [];
  private disposables: IDisposable[] = [];
  private watcher: fs.FSWatcher | null = null;

  constructor(private eventBus: EventBus) {}

  render(): string {
    if (this.workspaceFolders.length === 0) {
      return `<div class="explorer-empty">
        <div class="explorer-message">No folders open</div>
        <button class="explorer-open-folder" data-action="openFolder">Open Folder</button>
      </div>`;
    }

    const treeHtml = this.renderTree(this.fileTree, 0);
    return `<div class="explorer-container">
      <div class="explorer-header">
        <span class="explorer-title">EXPLORER</span>
        <div class="explorer-actions">
          <button data-action="newFile" title="New File">+</button>
          <button data-action="collapseAll" title="Collapse All">--</button>
        </div>
      </div>
      <div class="explorer-tree">${treeHtml}</div>
    </div>`;
  }

  private renderTree(items: FileItem[], depth: number): string {
    let html = '<ul class="explorer-tree-list">';
    for (const item of items) {
      const icon = item.isDirectory ? (this.hasChildren(item) ? '▾' : '▸') : '📄';
      html += `<li class="explorer-tree-item" data-path="${item.path}" data-isdirectory="${item.isDirectory}" style="padding-left:${depth * 16}px">
        <span class="explorer-item-icon">${icon}</span>
        <span class="explorer-item-name">${this.escapeHtml(item.name)}</span>
      </li>`;
      if (item.children && item.children.length > 0) {
        html += `<li class="explorer-tree-children">${this.renderTree(item.children, depth + 1)}</li>`;
      }
    }
    html += '</ul>';
    return html;
  }

  private hasChildren(item: FileItem): boolean {
    return !!(item.children && item.children.length > 0);
  }

  private escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  onMount(): void {
    this.startWatching();
  }

  onUnmount(): void {
    this.stopWatching();
    for (const d of this.disposables) {
      d.dispose();
    }
    this.disposables = [];
  }

  update(props: Record<string, unknown>): void {
    if (props.workspaceFolders) {
      this.workspaceFolders = props.workspaceFolders as WorkspaceFolder[];
    }
    if (props.fileTree) {
      this.fileTree = props.fileTree as FileItem[];
    }
  }

  async openFolder(folderPath: string): Promise<void> {
    const resolvedPath = path.resolve(folderPath);
    if (!fs.existsSync(resolvedPath)) {
      throw new Error(`Folder does not exist: ${resolvedPath}`);
    }

    const stat = fs.statSync(resolvedPath);
    if (!stat.isDirectory()) {
      throw new Error(`Path is not a directory: ${resolvedPath}`);
    }

    const folder: WorkspaceFolder = {
      uri: `file:///${resolvedPath.replace(/\\/g, '/')}`,
      name: path.basename(resolvedPath),
      path: resolvedPath,
    };

    const existingIndex = this.workspaceFolders.findIndex((wf) => wf.path === resolvedPath);
    if (existingIndex >= 0) {
      this.workspaceFolders[existingIndex] = folder;
    } else {
      this.workspaceFolders.push(folder);
    }

    await this.refresh();
    this.eventBus.emit('explorer:folderOpened', { folder });
  }

  getWorkspaceFolders(): WorkspaceFolder[] {
    return [...this.workspaceFolders];
  }

  getFileTree(): FileItem[] {
    return this.fileTree;
  }

  async refresh(): Promise<void> {
    this.fileTree = [];
    for (const folder of this.workspaceFolders) {
      const tree = await this.buildFileTree(folder.path);
      this.fileTree.push(tree);
    }
    this.stopWatching();
    this.startWatching();
  }

  private async buildFileTree(dirPath: string): Promise<FileItem> {
    const name = path.basename(dirPath);
    const item: FileItem = {
      name,
      path: dirPath,
      isDirectory: true,
      children: [],
    };

    try {
      const entries = fs.readdirSync(dirPath, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.name.startsWith('.')) continue;
        if (entry.name === 'node_modules') continue;

        const entryPath = path.join(dirPath, entry.name);
        if (entry.isDirectory()) {
          const child = await this.buildFileTree(entryPath);
          item.children!.push(child);
        } else {
          const stat = fs.statSync(entryPath);
          item.children!.push({
            name: entry.name,
            path: entryPath,
            isDirectory: false,
            size: stat.size,
            modifiedAt: stat.mtime,
          });
        }
      }

      item.children!.sort((a, b) => {
        if (a.isDirectory !== b.isDirectory) {
          return a.isDirectory ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
    } catch {
      // permission denied or other error
    }

    return item;
  }

  revealFile(filePath: string): void {
    this.eventBus.emit('explorer:revealFile', { filePath });
  }

  async createFile(parentPath: string, name: string): Promise<FileItem> {
    const fullPath = path.join(parentPath, name);
    fs.writeFileSync(fullPath, '', 'utf-8');
    const stat = fs.statSync(fullPath);
    const item: FileItem = {
      name,
      path: fullPath,
      isDirectory: false,
      size: stat.size,
      modifiedAt: stat.mtime,
    };
    await this.refresh();
    this.eventBus.emit('explorer:fileCreated', { item });
    return item;
  }

  async createFolder(parentPath: string, name: string): Promise<FileItem> {
    const fullPath = path.join(parentPath, name);
    fs.mkdirSync(fullPath, { recursive: true });
    const item: FileItem = {
      name,
      path: fullPath,
      isDirectory: true,
      children: [],
    };
    await this.refresh();
    this.eventBus.emit('explorer:fileCreated', { item });
    return item;
  }

  async deleteFile(item: FileItem): Promise<void> {
    if (item.isDirectory) {
      fs.rmdirSync(item.path, { recursive: true });
    } else {
      fs.unlinkSync(item.path);
    }
    await this.refresh();
    this.eventBus.emit('explorer:fileDeleted', { item });
  }

  async renameFile(item: FileItem, newName: string): Promise<FileItem> {
    const dir = path.dirname(item.path);
    const newPath = path.join(dir, newName);
    fs.renameSync(item.path, newPath);
    await this.refresh();
    const renamedItem: FileItem = { ...item, name: newName, path: newPath };
    this.eventBus.emit('explorer:fileRenamed', { oldItem: item, newItem: renamedItem });
    return renamedItem;
  }

  getContextMenuActions(): Array<{ id: string; label: string; action: (item?: FileItem) => void }> {
    return [
      { id: 'newFile', label: 'New File', action: () => {} },
      { id: 'newFolder', label: 'New Folder', action: () => {} },
      { id: 'rename', label: 'Rename', action: () => {} },
      { id: 'delete', label: 'Delete', action: () => {} },
      { id: 'copyPath', label: 'Copy Path', action: () => {} },
      { id: 'revealInExplorer', label: 'Reveal in File Explorer', action: () => {} },
    ];
  }

  private startWatching(): void {
    if (this.workspaceFolders.length === 0) return;
    this.stopWatching();

    try {
      const dirs = this.workspaceFolders.map((f) => f.path);
      this.watcher = fs.watch(dirs[0], { recursive: true }, (eventType, filename) => {
        if (filename) {
          this.refresh();
        }
      });
    } catch (err) {
      console.warn('[ProjectExplorer] File watching not available:', err);
    }
  }

  private stopWatching(): void {
    if (this.watcher) {
      this.watcher.close();
      this.watcher = null;
    }
  }
}
