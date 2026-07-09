class WindowManager {
  constructor() {
    this.windows = new Map();
    this.zIndexCounter = 100;
    this.activeWindow = null;
    this.container = document.getElementById('windows-container');
    this.dragState = null;
    this.resizeState = null;
    this.init();
  }

  init() {
    document.addEventListener('mousemove', (e) => this.onMouseMove(e));
    document.addEventListener('mouseup', (e) => this.onMouseUp(e));
    document.addEventListener('keydown', (e) => this.onKeyDown(e));
  }

  createWindow(options = {}) {
    const id = 'win-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
    const defaults = {
      title: 'Untitled',
      icon: '',
      appId: 'unknown',
      width: 800,
      height: 500,
      minWidth: 320,
      minHeight: 200,
      x: null,
      y: null,
      content: '',
      onClose: null,
      onFocus: null,
    };
    const config = { ...defaults, ...options };

    if (config.x === null) config.x = Math.max(40, (window.innerWidth - config.width) / 2 + (this.windows.size * 30));
    if (config.y === null) config.y = Math.max(40, (window.innerHeight - config.height) / 2 + (this.windows.size * 30) - 24);

    const win = document.createElement('div');
    win.className = 'window focused';
    win.id = id;
    win.style.cssText = `left:${config.x}px;top:${config.y}px;width:${config.width}px;height:${config.height}px;z-index:${++this.zIndexCounter}`;

    win.innerHTML = `
      <div class="window-titlebar" data-win="${id}">
        <div class="window-titlebar-icon">${config.icon}</div>
        <div class="window-title">${config.title}</div>
        <div class="window-controls">
          <button class="window-control-btn minimize" title="Minimize">&#8722;</button>
          <button class="window-control-btn maximize" title="Maximize">&#9633;</button>
          <button class="window-control-btn close" title="Close">&times;</button>
        </div>
      </div>
      <div class="window-body">${config.content}</div>
      <div class="resize-handle n"></div>
      <div class="resize-handle s"></div>
      <div class="resize-handle e"></div>
      <div class="resize-handle w"></div>
      <div class="resize-handle ne"></div>
      <div class="resize-handle nw"></div>
      <div class="resize-handle se"></div>
      <div class="resize-handle sw"></div>
    `;

    this.container.appendChild(win);

    const windowData = {
      id,
      element: win,
      config,
      minimized: false,
      maximized: false,
      prevBounds: null,
    };
    this.windows.set(id, windowData);

    this.setupWindowEvents(windowData);
    this.focusWindow(id);

    if (config.onReady) config.onReady(win, id);

    return windowData;
  }

  setupWindowEvents(winData) {
    const win = winData.element;
    const titlebar = win.querySelector('.window-titlebar');

    titlebar.addEventListener('mousedown', (e) => {
      if (e.target.closest('.window-controls')) return;
      this.focusWindow(winData.id);
      if (!winData.maximized) {
        this.dragState = {
          winId: winData.id,
          startX: e.clientX,
          startY: e.clientY,
          origLeft: win.offsetLeft,
          origTop: win.offsetTop,
        };
        e.preventDefault();
      }
    });

    titlebar.addEventListener('dblclick', (e) => {
      if (e.target.closest('.window-controls')) return;
      this.toggleMaximize(winData.id);
    });

    win.querySelectorAll('.resize-handle').forEach((handle) => {
      handle.addEventListener('mousedown', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.focusWindow(winData.id);
        const dir = Array.from(handle.classList).find((c) => c !== 'resize-handle');
        this.resizeState = {
          winId: winData.id,
          dir,
          startX: e.clientX,
          startY: e.clientY,
          origLeft: win.offsetLeft,
          origTop: win.offsetTop,
          origWidth: win.offsetWidth,
          origHeight: win.offsetHeight,
          minWidth: winData.config.minWidth,
          minHeight: winData.config.minHeight,
        };
      });
    });

    win.querySelector('.minimize').addEventListener('click', () => this.minimizeWindow(winData.id));
    win.querySelector('.maximize').addEventListener('click', () => this.toggleMaximize(winData.id));
    win.querySelector('.close').addEventListener('click', () => this.closeWindow(winData.id));

    win.addEventListener('mousedown', () => this.focusWindow(winData.id));
  }

  onMouseMove(e) {
    if (this.dragState) {
      const { winId, startX, startY, origLeft, origTop } = this.dragState;
      const win = this.windows.get(winId);
      if (!win) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      win.element.style.left = (origLeft + dx) + 'px';
      win.element.style.top = Math.max(0, origTop + dy) + 'px';
    }

    if (this.resizeState) {
      const s = this.resizeState;
      const win = this.windows.get(s.winId);
      if (!win) return;
      const dx = e.clientX - s.startX;
      const dy = e.clientY - s.startY;
      let newLeft = s.origLeft, newTop = s.origTop;
      let newWidth = s.origWidth, newHeight = s.origHeight;

      if (s.dir.includes('e')) newWidth = Math.max(s.minWidth, s.origWidth + dx);
      if (s.dir.includes('w')) {
        newWidth = Math.max(s.minWidth, s.origWidth - dx);
        newLeft = s.origLeft + (s.origWidth - newWidth);
      }
      if (s.dir.includes('s')) newHeight = Math.max(s.minHeight, s.origHeight + dy);
      if (s.dir.includes('n')) {
        newHeight = Math.max(s.minHeight, s.origHeight - dy);
        newTop = s.origTop + (s.origHeight - newHeight);
      }

      win.element.style.left = newLeft + 'px';
      win.element.style.top = newTop + 'px';
      win.element.style.width = newWidth + 'px';
      win.element.style.height = newHeight + 'px';
    }
  }

  onMouseUp() {
    this.dragState = null;
    this.resizeState = null;
  }

  onKeyDown(e) {
    if (e.key === 'Escape') {
      const aiCenter = document.getElementById('ai-center');
      const startMenu = document.getElementById('start-menu');
      if (!aiCenter.classList.contains('hidden')) aiCenter.classList.add('hidden');
      if (!startMenu.classList.contains('hidden')) startMenu.classList.add('hidden');
    }
  }

  focusWindow(id) {
    if (this.activeWindow === id) return;
    this.windows.forEach((w, wid) => {
      w.element.classList.toggle('focused', wid === id);
    });
    this.activeWindow = id;
    const win = this.windows.get(id);
    if (win) {
      win.element.style.zIndex = ++this.zIndexCounter;
      if (win.config.onFocus) win.config.onFocus();
    }
    if (window.arcanisDesktop) {
      window.arcanisDesktop.taskbar.setActiveApp(win?.config.appId || null);
    }
  }

  minimizeWindow(id) {
    const win = this.windows.get(id);
    if (!win) return;
    win.minimized = true;
    win.element.classList.add('minimized');
    if (this.activeWindow === id) this.activeWindow = null;
    if (window.arcanisDesktop) {
      window.arcanisDesktop.taskbar.setActiveApp(null);
    }
  }

  restoreWindow(id) {
    const win = this.windows.get(id);
    if (!win) return;
    win.minimized = false;
    win.element.classList.remove('minimized');
    this.focusWindow(id);
  }

  toggleMaximize(id) {
    const win = this.windows.get(id);
    if (!win) return;

    if (win.maximized) {
      win.element.classList.remove('maximized');
      if (win.prevBounds) {
        win.element.style.left = win.prevBounds.left;
        win.element.style.top = win.prevBounds.top;
        win.element.style.width = win.prevBounds.width;
        win.element.style.height = win.prevBounds.height;
      }
      win.maximized = false;
    } else {
      win.prevBounds = {
        left: win.element.style.left,
        top: win.element.style.top,
        width: win.element.style.width,
        height: win.element.style.height,
      };
      win.element.classList.add('maximized');
      win.element.style.left = '0';
      win.element.style.top = '0';
      win.element.style.width = '100%';
      win.element.style.height = `calc(100vh - var(--taskbar-height))`;
      win.maximized = true;
    }
  }

  closeWindow(id) {
    const win = this.windows.get(id);
    if (!win) return;
    if (win.config.onClose) win.config.onClose();
    win.element.remove();
    this.windows.delete(id);
    if (this.activeWindow === id) {
      this.activeWindow = null;
      if (window.arcanisDesktop) {
        window.arcanisDesktop.taskbar.setActiveApp(null);
      }
    }
    if (window.arcanisDesktop) {
      window.arcanisDesktop.taskbar.removeApp(id);
    }
  }

  getWindowByAppId(appId) {
    for (const [, win] of this.windows) {
      if (win.config.appId === appId) return win;
    }
    return null;
  }

  getWindowsByAppId(appId) {
    const results = [];
    for (const [, win] of this.windows) {
      if (win.config.appId === appId) results.push(win);
    }
    return results;
  }

  setTitle(id, title) {
    const win = this.windows.get(id);
    if (!win) return;
    win.config.title = title;
    win.element.querySelector('.window-title').textContent = title;
  }
}
