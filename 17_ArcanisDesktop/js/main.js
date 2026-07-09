class ArcanisDesktop {
  constructor() {
    this.windowManager = new WindowManager();
    this.taskbar = new Taskbar();
    this.notifications = new NotificationSystem();
    this.desktop = new Desktop();
    this.workspace = new WorkspaceManager();
    this.aiCenter = new AICenter();
    this.workflows = new WorkflowEngine();
    this.integration = new ArcanisIntegration();

    this.appRegistry = {};
    this.apps = {};

    this.registerApps();
    this.initApps();
    this.loadTheme();
    this.showWelcome();
  }

  registerApps() {
    const appDefs = [
      { id: 'terminal', name: 'Terminal', icon: '>', description: 'Command line interface', pinned: true, color: 'linear-gradient(135deg, #2d2d2d, #1a1a1a)', instance: new TerminalApp() },
      { id: 'file-manager', name: 'Files', icon: '📁', description: 'File manager', pinned: true, color: 'linear-gradient(135deg, #4a90d9, #357abd)', instance: new FileManagerApp() },
      { id: 'browser', name: 'Browser', icon: '🌐', description: 'Web browser', pinned: true, color: 'linear-gradient(135deg, #e74c3c, #c0392b)', instance: new BrowserApp() },
      { id: 'text-editor', name: 'Text Editor', icon: '📝', description: 'Code and text editor', pinned: true, color: 'linear-gradient(135deg, #27ae60, #229954)', instance: new TextEditorApp() },
      { id: 'settings', name: 'Settings', icon: '⚙', description: 'System settings', pinned: true, color: 'linear-gradient(135deg, #7c5cff, #5c8cff)', instance: new SettingsApp() },
    ];

    appDefs.forEach((def) => {
      this.appRegistry[def.id] = def;
      this.taskbar.registerApp(def);
    });
  }

  initApps() {
    Object.values(this.appRegistry).forEach((def) => {
      this.apps[def.id] = def.instance;
    });
  }

  launchApp(appId) {
    const def = this.appRegistry[appId];
    if (!def) return;

    const existing = this.windowManager.getWindowByAppId(appId);
    if (existing) {
      if (existing.minimized) {
        this.windowManager.restoreWindow(existing.id);
      } else {
        this.windowManager.focusWindow(existing.id);
      }
      return;
    }

    const instance = def.instance;
    const content = instance.getContent ? instance.getContent() : '';

    const win = this.windowManager.createWindow({
      title: def.name,
      icon: `<span style="font-size:13px">${def.icon}</span>`,
      appId: def.id,
      content,
      onClose: () => {
        if (instance.onClose) instance.onClose();
      },
      onReady: (winEl, winId) => {
        if (instance.onReady) instance.onReady(winEl, winId);
        this.taskbar.addRunningApp(winId, def.id, def.name, def.icon);
      },
    });
  }

  toggleAICenter() {
    this.aiCenter.toggle();
  }

  loadTheme() {
    const saved = localStorage.getItem('arcanis-theme');
    if (saved) {
      document.documentElement.setAttribute('data-theme', saved);
    }
  }

  showWelcome() {
    setTimeout(() => {
      this.notifications.notify(
        'Welcome to ArcanisDesktop',
        'Your AI-native desktop is ready. Press Ctrl+Space or click the AI icon to open ArcanisBrain.',
        'info'
      );
    }, 800);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.arcanisDesktop = new ArcanisDesktop();
});
