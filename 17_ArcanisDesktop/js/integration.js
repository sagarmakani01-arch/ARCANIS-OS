class ArcanisIntegration {
  constructor() {
    this.ArcanisUI = this.createUIBridge();
    this.ArcanisShell = this.createShellBridge();
    this.ArcanisBrain = this.createBrainBridge();
  }

  createUIBridge() {
    return {
      getTheme: () => document.documentElement.getAttribute('data-theme'),
      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('arcanis-theme', theme);
      },
      getAccentColor: () => getComputedStyle(document.documentElement).getPropertyValue('--accent-primary').trim(),
      setAccentColor: (color) => {
        document.documentElement.style.setProperty('--accent-primary', color);
      },
      getSetting: (key) => localStorage.getItem(`arcanis-${key}`),
      setSetting: (key, value) => localStorage.setItem(`arcanis-${key}`, value),
      showNotification: (title, body, type) => {
        window.arcanisDesktop?.notifications.notify(title, body, type);
      },
    };
  }

  createShellBridge() {
    return {
      openApp: (appId) => window.arcanisDesktop?.launchApp(appId),
      closeApp: (appId) => {
        const wm = window.arcanisDesktop?.windowManager;
        if (!wm) return;
        wm.windows.forEach((win, id) => {
          if (win.config.appId === appId) wm.closeWindow(id);
        });
      },
      getOpenApps: () => {
        const apps = [];
        window.arcanisDesktop?.windowManager.windows.forEach((win) => {
          apps.push({ id: win.config.appId, title: win.config.title, winId: win.id });
        });
        return apps;
      },
      minimizeAll: () => {
        window.arcanisDesktop?.windowManager.windows.forEach((_, id) => {
          window.arcanisDesktop.windowManager.minimizeWindow(id);
        });
      },
      closeAll: () => {
        const ids = [...window.arcanisDesktop?.windowManager.windows.keys() || []];
        ids.forEach((id) => window.arcanisDesktop.windowManager.closeWindow(id));
      },
      executeCommand: (cmd) => window.arcanisDesktop?.terminalApp?.execute(cmd),
      getWorkspaces: () => window.arcanisDesktop?.workspace?.getLayout(),
      switchWorkspace: (id) => window.arcanisDesktop?.workspace?.switchWorkspace(id),
    };
  }

  createBrainBridge() {
    return {
      processCommand: (input) => window.arcanisDesktop?.aiCenter?.processCommand(input),
      getConversationHistory: () => window.arcanisDesktop?.aiCenter?.conversationHistory || [],
      createWorkflow: (name, steps) => window.arcanisDesktop?.workflows?.createWorkflow(name, steps),
      runWorkflow: (id) => window.arcanisDesktop?.workflows?.runWorkflow(id),
      getWorkflows: () => window.arcanisDesktop?.workflows?.getWorkflows() || [],
    };
  }

  getCapabilities() {
    return {
      ui: Object.keys(this.ArcanisUI),
      shell: Object.keys(this.ArcanisShell),
      brain: Object.keys(this.ArcanisBrain),
    };
  }
}
