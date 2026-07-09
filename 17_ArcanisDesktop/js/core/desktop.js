class Desktop {
  constructor() {
    this.iconsContainer = document.getElementById('desktop-icons');
    this.wallpaper = document.getElementById('wallpaper');
    this.contextMenu = document.getElementById('context-menu');
    this.init();
  }

  init() {
    this.setupContextMenu();
    this.setupWallpaper();
    this.renderDesktopIcons();
  }

  renderDesktopIcons() {
    const icons = [
      { name: 'Terminal', icon: '>', appId: 'terminal', color: 'linear-gradient(135deg, #2d2d2d, #1a1a1a)' },
      { name: 'Files', icon: '📁', appId: 'file-manager', color: 'linear-gradient(135deg, #4a90d9, #357abd)' },
      { name: 'Browser', icon: '🌐', appId: 'browser', color: 'linear-gradient(135deg, #e74c3c, #c0392b)' },
      { name: 'Editor', icon: '📝', appId: 'text-editor', color: 'linear-gradient(135deg, #27ae60, #229954)' },
      { name: 'Settings', icon: '⚙', appId: 'settings', color: 'linear-gradient(135deg, #7c5cff, #5c8cff)' },
    ];

    this.iconsContainer.innerHTML = icons.map((item) => `
      <div class="desktop-icon" data-app="${item.appId}" ondblclick="window.arcanisDesktop.launchApp('${item.appId}')">
        <div class="icon" style="background:${item.color}; color: white; font-weight: bold; font-size: 20px;">${item.icon}</div>
        <div class="label">${item.name}</div>
      </div>
    `).join('');
  }

  setupContextMenu() {
    document.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      this.showContextMenu(e.clientX, e.clientY);
    });

    document.addEventListener('click', () => this.hideContextMenu());
  }

  showContextMenu(x, y) {
    const items = [
      { label: 'New Terminal', action: () => window.arcanisDesktop.launchApp('terminal') },
      { label: 'New File', action: () => window.arcanisDesktop.launchApp('text-editor') },
      { separator: true },
      { label: 'AI Command Center', action: () => window.arcanisDesktop.toggleAICenter() },
      { label: 'Refresh Desktop', action: () => this.refresh() },
      { separator: true },
      { label: 'Settings', action: () => window.arcanisDesktop.launchApp('settings') },
    ];

    this.contextMenu.innerHTML = items.map((item) => {
      if (item.separator) return '<div class="ctx-separator"></div>';
      return `<div class="ctx-item">${item.label}</div>`;
    }).join('');

    this.contextMenu.style.left = x + 'px';
    this.contextMenu.style.top = y + 'px';
    this.contextMenu.classList.remove('hidden');

    const rect = this.contextMenu.getBoundingClientRect();
    if (rect.right > window.innerWidth) this.contextMenu.style.left = (x - rect.width) + 'px';
    if (rect.bottom > window.innerHeight - 48) this.contextMenu.style.top = (y - rect.height) + 'px';

    this.contextMenu.querySelectorAll('.ctx-item').forEach((el, i) => {
      const realItems = items.filter((it) => !it.separator);
      el.addEventListener('click', () => realItems[i].action());
    });
  }

  hideContextMenu() {
    this.contextMenu.classList.add('hidden');
  }

  setupWallpaper() {
    const saved = localStorage.getItem('arcanis-wallpaper');
    if (saved) this.setWallpaper(saved);
  }

  setWallpaper(url) {
    if (url) {
      this.wallpaper.style.background = `url(${url}) center/cover no-repeat`;
    } else {
      this.wallpaper.style.background = '';
    }
    localStorage.setItem('arcanis-wallpaper', url || '');
  }

  refresh() {
    this.renderDesktopIcons();
  }
}
