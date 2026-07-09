class Taskbar {
  constructor() {
    this.appsContainer = document.getElementById('taskbar-apps');
    this.clockEl = document.getElementById('clock');
    this.startBtn = document.getElementById('start-btn');
    this.startMenu = document.getElementById('start-menu');
    this.startSearch = document.getElementById('start-search');
    this.pinnedApps = document.getElementById('pinned-apps');
    this.allApps = document.getElementById('all-apps');
    this.settingsBtn = document.getElementById('settings-btn');
    this.activeAppId = null;
    this.runningApps = new Map();
    this.appDefinitions = [];
    this.init();
  }

  init() {
    this.updateClock();
    setInterval(() => this.updateClock(), 1000);

    this.startBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleStartMenu();
    });

    this.startSearch.addEventListener('input', (e) => this.filterApps(e.target.value));

    this.settingsBtn.addEventListener('click', () => {
      this.hideStartMenu();
      if (window.arcanisDesktop) {
        window.arcanisDesktop.launchApp('settings');
      }
    });

    document.addEventListener('click', (e) => {
      if (!this.startMenu.contains(e.target) && !this.startBtn.contains(e.target)) {
        this.hideStartMenu();
      }
    });
  }

  registerApp(def) {
    this.appDefinitions.push(def);
    this.renderPinnedApps();
    this.renderAllApps();
  }

  renderPinnedApps() {
    const pinned = this.appDefinitions.filter((a) => a.pinned);
    this.pinnedApps.innerHTML = pinned.map((app) => `
      <div class="app-grid-item" data-app="${app.id}" onclick="window.arcanisDesktop.launchApp('${app.id}')">
        <div class="app-icon" style="background:${app.color || 'var(--accent-gradient)'}">${app.icon}</div>
        <div class="app-name">${app.name}</div>
      </div>
    `).join('');
  }

  renderAllApps(filter = '') {
    const filtered = this.appDefinitions.filter((a) =>
      a.name.toLowerCase().includes(filter.toLowerCase())
    );
    this.allApps.innerHTML = filtered.map((app) => `
      <div class="app-list-item" data-app="${app.id}" onclick="window.arcanisDesktop.launchApp('${app.id}')">
        <div class="app-icon" style="background:${app.color || 'var(--accent-gradient)'}">${app.icon}</div>
        <div class="app-info">
          <div class="app-name">${app.name}</div>
          <div class="app-desc">${app.description || ''}</div>
        </div>
      </div>
    `).join('');
  }

  filterApps(query) {
    this.renderAllApps(query);
  }

  addRunningApp(winId, appId, title, icon) {
    const btn = document.createElement('button');
    btn.className = 'taskbar-app active';
    btn.dataset.winId = winId;
    btn.dataset.appId = appId;
    btn.innerHTML = `<span class="app-icon">${icon}</span><span class="app-title">${title}</span>`;
    btn.addEventListener('click', () => {
      const wm = window.arcanisDesktop.windowManager;
      const win = wm.windows.get(winId);
      if (win) {
        if (win.minimized) {
          wm.restoreWindow(winId);
        } else if (wm.activeWindow === winId) {
          wm.minimizeWindow(winId);
        } else {
          wm.focusWindow(winId);
        }
      }
    });
    this.appsContainer.appendChild(btn);
    this.runningApps.set(winId, btn);
  }

  removeApp(winId) {
    const btn = this.runningApps.get(winId);
    if (btn) {
      btn.remove();
      this.runningApps.delete(winId);
    }
  }

  setActiveApp(appId) {
    this.runningApps.forEach((btn, winId) => {
      const win = window.arcanisDesktop.windowManager.windows.get(winId);
      btn.classList.toggle('active', win && !win.minimized && win.config.appId === appId);
    });
  }

  updateTitle(winId, title) {
    const btn = this.runningApps.get(winId);
    if (btn) {
      btn.querySelector('.app-title').textContent = title;
    }
  }

  updateClock() {
    const now = new Date();
    const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const date = now.toLocaleDateString([], { month: 'short', day: 'numeric' });
    this.clockEl.innerHTML = `<div>${time}</div><div>${date}</div>`;
  }

  toggleStartMenu() {
    this.startMenu.classList.toggle('hidden');
    if (!this.startMenu.classList.contains('hidden')) {
      this.startSearch.value = '';
      this.renderAllApps();
      setTimeout(() => this.startSearch.focus(), 50);
    }
  }

  hideStartMenu() {
    this.startMenu.classList.add('hidden');
  }
}
