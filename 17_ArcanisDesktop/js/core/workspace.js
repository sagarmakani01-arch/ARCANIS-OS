class WorkspaceManager {
  constructor() {
    this.workspaces = [];
    this.currentWorkspace = 0;
    this.init();
  }

  init() {
    this.createDefaultWorkspaces();
    this.setupKeyboardShortcuts();
  }

  createDefaultWorkspaces() {
    this.workspaces = [
      { id: 0, name: 'Desktop', windows: [] },
      { id: 1, name: 'Work', windows: [] },
      { id: 2, name: 'Personal', windows: [] },
    ];
  }

  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key >= '1' && e.key <= '3') {
        e.preventDefault();
        this.switchWorkspace(parseInt(e.key) - 1);
      }
      if (e.ctrlKey && e.key === 'Tab') {
        e.preventDefault();
        this.cycleWorkspaces(e.shiftKey ? -1 : 1);
      }
    });
  }

  switchWorkspace(id) {
    if (id < 0 || id >= this.workspaces.length) return;
    const wm = window.arcanisDesktop?.windowManager;
    if (!wm) return;

    this.workspaces[this.currentWorkspace].windows = [];
    wm.windows.forEach((win, winId) => {
      this.workspaces[this.currentWorkspace].windows.push(winId);
    });

    this.currentWorkspace = id;
    const targetWindows = new Set(this.workspaces[id].windows);

    wm.windows.forEach((win, winId) => {
      win.element.style.display = targetWindows.has(winId) ? '' : 'none';
    });

    this.updateIndicator();
    window.arcanisDesktop?.notifications.notify(
      'Workspace',
      `Switched to ${this.workspaces[id].name}`,
      'info',
      { toast: true }
    );
  }

  cycleWorkspaces(direction) {
    let next = this.currentWorkspace + direction;
    if (next < 0) next = this.workspaces.length - 1;
    if (next >= this.workspaces.length) next = 0;
    this.switchWorkspace(next);
  }

  addWorkspace(name) {
    const ws = {
      id: this.workspaces.length,
      name: name || `Workspace ${this.workspaces.length + 1}`,
      windows: [],
    };
    this.workspaces.push(ws);
    return ws;
  }

  removeWorkspace(id) {
    if (this.workspaces.length <= 1) return false;
    if (id === this.currentWorkspace) return false;
    this.workspaces = this.workspaces.filter((ws) => ws.id !== id);
    return true;
  }

  updateIndicator() {
    let indicator = document.getElementById('workspace-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'workspace-indicator';
      indicator.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 20px 32px;
        z-index: 9999;
        display: flex;
        gap: 12px;
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
      `;
      document.getElementById('desktop').appendChild(indicator);
    }

    indicator.innerHTML = this.workspaces.map((ws, i) => `
      <div style="
        padding: 12px 20px;
        border-radius: var(--radius-md);
        background: ${i === this.currentWorkspace ? 'var(--accent-primary)' : 'var(--bg-tertiary)'};
        color: ${i === this.currentWorkspace ? 'white' : 'var(--text-secondary)'};
        font-size: 13px;
        text-align: center;
        min-width: 80px;
        cursor: pointer;
        transition: all 0.2s ease;
      " onclick="window.arcanisDesktop.workspace.switchWorkspace(${i})">
        <div style="font-weight: 600;">${ws.name}</div>
        <div style="font-size: 11px; opacity: 0.7; margin-top: 2px;">Ctrl+${i + 1}</div>
      </div>
    `).join('');

    indicator.style.opacity = '1';
    clearTimeout(this._indicatorTimeout);
    this._indicatorTimeout = setTimeout(() => {
      indicator.style.opacity = '0';
    }, 1500);
  }

  getLayout() {
    return {
      currentWorkspace: this.currentWorkspace,
      workspaces: this.workspaces.map((ws) => ({
        ...ws,
        windowCount: ws.windows.length,
      })),
    };
  }
}
