class FileManagerApp {
  constructor() {
    this.currentPath = '~';
    this.history = ['~'];
    this.historyIndex = 0;
    this.filesystem = {
      '~': {
        type: 'dir',
        children: {
          'Documents': { type: 'dir', icon: '📁', children: {
            'report.txt': { type: 'file', icon: '📄', size: '2.4 KB' },
            'presentation.pdf': { type: 'file', icon: '📕', size: '1.2 MB' },
          }},
          'Downloads': { type: 'dir', icon: '📁', children: {
            'installer.exe': { type: 'file', icon: '⚙️', size: '45 MB' },
            'image.png': { type: 'file', icon: '🖼️', size: '3.1 MB' },
          }},
          'Music': { type: 'dir', icon: '🎵', children: {} },
          'Pictures': { type: 'dir', icon: '🖼️', children: {
            'photo1.jpg': { type: 'file', icon: '📷', size: '4.2 MB' },
            'screenshot.png': { type: 'file', icon: '🖼️', size: '890 KB' },
          }},
          'Videos': { type: 'dir', icon: '🎬', children: {} },
          'Projects': { type: 'dir', icon: '📁', children: {
            'arcanis-ui': { type: 'dir', icon: '📁', children: {} },
            'arcanis-brain': { type: 'dir', icon: '📁', children: {} },
          }},
          '.config': { type: 'dir', icon: '⚙️', children: {
            'settings.json': { type: 'file', icon: '📄', size: '128 B' },
          }},
          'readme.md': { type: 'file', icon: '📄', size: '512 B' },
        },
      },
    };
    this.selected = null;
  }

  getContent() {
    return `
      <div class="file-manager">
        <div class="fm-sidebar">
          <div class="fm-sidebar-section">Quick Access</div>
          <div class="fm-sidebar-item active" data-path="~">
            <span>🏠</span> Home
          </div>
          <div class="fm-sidebar-item" data-path="~/Desktop">
            <span>🖥️</span> Desktop
          </div>
          <div class="fm-sidebar-item" data-path="~/Documents">
            <span>📄</span> Documents
          </div>
          <div class="fm-sidebar-item" data-path="~/Downloads">
            <span>⬇️</span> Downloads
          </div>
          <div class="fm-sidebar-item" data-path="~/Pictures">
            <span>🖼️</span> Pictures
          </div>
          <div class="fm-sidebar-section">Devices</div>
          <div class="fm-sidebar-item" data-path="/">
            <span>💾</span> System
          </div>
        </div>
        <div class="fm-content">
          <div class="fm-toolbar">
            <button class="fm-toolbar-btn" id="fm-back" title="Back">◀</button>
            <button class="fm-toolbar-btn" id="fm-forward" title="Forward">▶</button>
            <button class="fm-toolbar-btn" id="fm-up" title="Up">▲</button>
            <button class="fm-toolbar-btn" id="fm-refresh" title="Refresh">⟳</button>
            <div class="fm-path" id="fm-path"></div>
          </div>
          <div class="fm-grid" id="fm-grid"></div>
        </div>
      </div>
    `;
  }

  onReady(winElement) {
    this.winElement = winElement;
    this.grid = winElement.querySelector('#fm-grid');
    this.pathBar = winElement.querySelector('#fm-path');

    winElement.querySelector('#fm-back').addEventListener('click', () => this.goBack());
    winElement.querySelector('#fm-forward').addEventListener('click', () => this.goForward());
    winElement.querySelector('#fm-up').addEventListener('click', () => this.goUp());
    winElement.querySelector('#fm-refresh').addEventListener('click', () => this.navigate(this.currentPath));

    winElement.querySelectorAll('.fm-sidebar-item').forEach((item) => {
      item.addEventListener('click', () => {
        const path = item.dataset.path;
        winElement.querySelectorAll('.fm-sidebar-item').forEach((i) => i.classList.remove('active'));
        item.classList.add('active');
        this.navigate(path);
      });
    });

    this.navigate('~');
  }

  navigate(path) {
    const dir = this.resolveDir(path);
    if (!dir || dir.type !== 'dir') return;

    this.currentPath = path;
    if (this.historyIndex < this.history.length - 1) {
      this.history = this.history.slice(0, this.historyIndex + 1);
    }
    this.history.push(path);
    this.historyIndex = this.history.length - 1;

    this.renderPath();
    this.renderGrid(dir);
  }

  renderPath() {
    const segments = this.currentPath.split('/');
    this.pathBar.innerHTML = segments.map((seg, i) => {
      const path = segments.slice(0, i + 1).join('/') || '~';
      return `<span class="fm-path-segment" data-path="${path}">${seg}</span>`;
    }).join(' <span style="color:var(--text-muted)">›</span> ');

    this.pathBar.querySelectorAll('.fm-path-segment').forEach((el) => {
      el.addEventListener('click', () => this.navigate(el.dataset.path));
    });
  }

  renderGrid(dir) {
    const items = Object.entries(dir.children || {});
    this.grid.innerHTML = items.map(([name, item]) => `
      <div class="fm-item" data-name="${name}" data-type="${item.type}">
        <div class="fm-item-icon">${item.icon || (item.type === 'dir' ? '📁' : '📄')}</div>
        <div class="fm-item-name">${name}</div>
      </div>
    `).join('');

    if (items.length === 0) {
      this.grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-muted)">This folder is empty</div>';
    }

    this.grid.querySelectorAll('.fm-item').forEach((el) => {
      el.addEventListener('click', (e) => {
        this.grid.querySelectorAll('.fm-item').forEach((i) => i.classList.remove('selected'));
        el.classList.add('selected');
        this.selected = el.dataset.name;
      });
      el.addEventListener('dblclick', () => {
        const name = el.dataset.name;
        const item = dir.children[name];
        if (item.type === 'dir') {
          const newPath = this.currentPath === '~' ? `~/${name}` : `${this.currentPath}/${name}`;
          this.navigate(newPath);
        }
      });
    });
  }

  goBack() {
    if (this.historyIndex > 0) {
      this.historyIndex--;
      this.currentPath = this.history[this.historyIndex];
      const dir = this.resolveDir(this.currentPath);
      if (dir) {
        this.renderPath();
        this.renderGrid(dir);
      }
    }
  }

  goForward() {
    if (this.historyIndex < this.history.length - 1) {
      this.historyIndex++;
      this.currentPath = this.history[this.historyIndex];
      const dir = this.resolveDir(this.currentPath);
      if (dir) {
        this.renderPath();
        this.renderGrid(dir);
      }
    }
  }

  goUp() {
    if (this.currentPath === '~') return;
    const parts = this.currentPath.split('/');
    parts.pop();
    this.navigate(parts.join('/') || '~');
  }

  resolveDir(path) {
    if (path === '~') return this.filesystem['~'];
    const parts = path.replace('~/', '').split('/');
    let current = this.filesystem['~'];
    for (const part of parts) {
      if (current.children && current.children[part]) {
        current = current.children[part];
      } else {
        return null;
      }
    }
    return current;
  }
}
