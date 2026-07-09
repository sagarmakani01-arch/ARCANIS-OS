const vm = require('vm');
const fs = require('fs');
const path = require('path');

let testsPassed = 0;
let testsFailed = 0;

function test(name, fn) {
  try {
    fn();
    testsPassed++;
    console.log(`  ✓ ${name}`);
  } catch (e) {
    testsFailed++;
    console.log(`  ✗ ${name}`);
    console.log(`    ${e.message}`);
  }
}

function expect(val) {
  return {
    toBe(expected) { if (val !== expected) throw new Error(`Expected ${JSON.stringify(expected)}, got ${JSON.stringify(val)}`); },
    toEqual(expected) { if (JSON.stringify(val) !== JSON.stringify(expected)) throw new Error(`Expected ${JSON.stringify(expected)}, got ${JSON.stringify(val)}`); },
    toBeTruthy() { if (!val) throw new Error(`Expected truthy, got ${JSON.stringify(val)}`); },
    toBeFalsy() { if (val) throw new Error(`Expected falsy, got ${JSON.stringify(val)}`); },
    toBeGreaterThan(n) { if (!(val > n)) throw new Error(`Expected ${val} > ${n}`); },
    toContain(item) {
      if (typeof val === 'string') { if (!val.includes(item)) throw new Error(`Expected string to contain "${item}"`); }
      else if (Array.isArray(val)) { if (!val.includes(item)) throw new Error(`Expected array to contain ${JSON.stringify(item)}`); }
      else if (val instanceof Map) { if (!val.has(item)) throw new Error(`Expected map to have key ${JSON.stringify(item)}`); }
      else throw new Error('toContain requires string, array, or Map');
    },
    toHaveLength(n) { if (val.length !== n) throw new Error(`Expected length ${n}, got ${val.length}`); },
    toBeNull() { if (val !== null) throw new Error(`Expected null, got ${JSON.stringify(val)}`); },
    toBeDefined() { if (val === undefined) throw new Error('Expected defined, got undefined'); },
    not: {
      toBeNull() { if (val === null) throw new Error('Expected not null'); },
      toBeUndefined() { if (val === undefined) throw new Error('Expected not undefined'); },
      toBe(expected) { if (val === expected) throw new Error(`Expected not ${JSON.stringify(expected)}`); },
      toContain(item) { if (typeof val === 'string' && val.includes(item)) throw new Error(`Expected string not to contain "${item}"`); },
    },
  };
}

function createMockDOM() {
  const elements = {};
  const listeners = {};

  function makeEl(id) {
    const el = {
      id, tagName: 'DIV', className: '', innerHTML: '', textContent: '',
      style: new Proxy({}, { get(t, p) { return t[p] || ''; }, set(t, p, v) { t[p] = v; return true; } }),
      dataset: {}, children: [], childNodes: [], parentNode: null, attributes: {},
      scrollTop: 0, scrollHeight: 1000, offsetWidth: 800, offsetHeight: 500, offsetLeft: 100, offsetTop: 100,
      classList: {
        _c: new Set(),
        add(c) { this._c.add(c); }, remove(c) { this._c.delete(c); },
        toggle(c, f) { f === undefined ? (this._c.has(c) ? this._c.delete(c) : this._c.add(c)) : (f ? this._c.add(c) : this._c.delete(c)); },
        contains(c) { return this._c.has(c); },
      },
      _listeners: {},
      addEventListener(t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); },
      removeEventListener(t, fn) { if (this._listeners[t]) this._listeners[t] = this._listeners[t].filter(f => f !== fn); },
      dispatchEvent(evt) { (this._listeners[evt.type] || []).forEach(fn => fn(evt)); },
      appendChild(child) { this.children.push(child); this.childNodes.push(child); child.parentNode = this; return child; },
      remove() { if (this.parentNode) { this.parentNode.children = this.parentNode.children.filter(c => c !== this); this.parentNode.childNodes = this.parentNode.childNodes.filter(c => c !== this); } },
      querySelector(sel) {
        if (sel.startsWith('#')) { const id = sel.slice(1); return this.children.find(c => c.id === id) || findTree(this, id); }
        if (sel.startsWith('.')) { const cls = sel.slice(1); return this.children.find(c => c.className && c.className.includes(cls)) || findTreeCls(this, cls); }
        return findTreeCls(this, sel);
      },
      querySelectorAll(sel) {
        if (sel.startsWith('.')) { const cls = sel.slice(1); return findAllCls(this, cls); }
        if (sel.startsWith('#')) { const el = this.querySelector(sel); return el ? [el] : []; }
        return findAllCls(this, sel);
      },
      getBoundingClientRect() { return { left: 0, top: 0, right: 800, bottom: 600, width: 800, height: 600 }; },
      setAttribute(k, v) { this.attributes[k] = v; },
      getAttribute(k) { return this.attributes[k] || null; },
    };
    return el;
  }

  function findTree(root, id) {
    for (const c of root.children) { if (c.id === id) return c; const f = findTree(c, id); if (f) return f; }
    return null;
  }
  function findTreeCls(root, cls) {
    for (const c of root.children) { if (c.className && c.className.includes(cls)) return c; const f = findTreeCls(c, cls); if (f) return f; }
    return null;
  }
  function findAllCls(root, cls) {
    const r = [];
    for (const c of root.children) { if (c.className && c.className.includes(cls)) r.push(c); r.push(...findAllCls(c, cls)); }
    return r;
  }

  const doc = makeEl('document');
  doc.documentElement = makeEl('html');
  doc.documentElement.setAttribute('data-theme', 'dark');
  doc.body = makeEl('body');

  doc.getElementById = (id) => {
    if (elements[id]) return elements[id];
    const el = makeEl(id); elements[id] = el; return el;
  };
  doc.createElement = (tag) => { const el = makeEl('c' + Math.random()); el.tagName = tag.toUpperCase(); return el; };
  doc.addEventListener = () => {};

  return { doc, elements, makeEl };
}

function loadClasses(ctx) {
  const base = path.resolve(__dirname, '..', 'js');
  const files = [
    'core/window-manager.js', 'core/taskbar.js', 'core/notifications.js',
    'core/desktop.js', 'core/workspace.js', 'apps/terminal.js',
    'apps/file-manager.js', 'apps/browser.js', 'apps/text-editor.js',
    'apps/settings.js', 'ai/ai-center.js', 'ai/workflows.js',
    'integration.js',
  ];
  let combined = '';
  for (const file of files) {
    combined += fs.readFileSync(path.join(base, file), 'utf-8') + '\n';
  }
  const classNames = [
    'WindowManager', 'Taskbar', 'NotificationSystem', 'Desktop', 'WorkspaceManager',
    'TerminalApp', 'FileManagerApp', 'BrowserApp', 'TextEditorApp', 'SettingsApp',
    'AICenter', 'WorkflowEngine', 'ArcanisIntegration',
  ];
  combined += '\n' + classNames.map(c => `this.${c} = ${c};`).join('\n');
  vm.runInContext(combined, ctx);
}

function createCtx() {
  const { doc, elements, makeEl } = createMockDOM();
  const timers = {};
  let tid = 0;

  const ctx = vm.createContext({
    console, require, __dirname, path, process, setTimeout: (fn, d) => { const id = ++tid; timers[id] = { fn, d }; return id; },
    clearTimeout: (id) => { delete timers[id]; }, setInterval: () => ++tid, clearTimeout,
    Date, Math, JSON, Object, Array, Map, Set, String, Number, RegExp, Error, TypeError,
    parseInt, parseFloat, isNaN, isFinite, undefined, NaN, Infinity,
    Proxy, Symbol, Promise, WeakMap, WeakSet, Map, Set,
    encodeURI, encodeURIComponent, decodeURI, decodeURIComponent, escape, unescape,
    eval: () => {}, Function: Function,
  });

  ctx.document = doc;
  ctx.window = { innerWidth: 1920, innerHeight: 1080, addEventListener: () => {}, arcanisDesktop: null };
  ctx.localStorage = { _s: {}, getItem(k) { return this._s[k] || null; }, setItem(k, v) { this._s[k] = v; }, removeItem(k) { delete this._s[k]; } };
  ctx.navigator = { platform: 'test', language: 'en-US', hardwareConcurrency: 8 };
  ctx.screen = { width: 1920, height: 1080 };
  ctx.getComputedStyle = () => ({ getPropertyValue: () => '' });
  ctx.globalThis = ctx;

  loadClasses(ctx);
  return { ctx, doc, elements, timers, makeEl };
}

function buildDesktop(ctx) {
  const { doc, elements } = (() => {
    const r = { doc: ctx.document, elements: {} };
    return r;
  })();

  const wm = new ctx.WindowManager();
  const taskbar = new ctx.Taskbar();
  const notifications = new ctx.NotificationSystem();
  const desktop = new ctx.Desktop();
  const workspace = new ctx.WorkspaceManager();
  const aiCenter = new ctx.AICenter();
  const workflows = new ctx.WorkflowEngine();
  const integration = new ctx.ArcanisIntegration();

  const arc = {
    windowManager: wm, taskbar, notifications, desktop, workspace, aiCenter, workflows, integration,
    appRegistry: {}, apps: {},
    registerApps() {}, initApps() {}, loadTheme() {}, showWelcome() {},
    launchApp(appId) {
      const def = this.appRegistry[appId];
      if (!def) return;
      const existing = this.windowManager.getWindowByAppId(appId);
      if (existing) {
        if (existing.minimized) this.windowManager.restoreWindow(existing.id);
        else this.windowManager.focusWindow(existing.id);
        return;
      }
      const inst = def.instance;
      const content = inst.getContent ? inst.getContent() : '';
      this.windowManager.createWindow({
        title: def.name, icon: def.icon, appId: def.id, content,
        onClose: () => { if (inst.onClose) inst.onClose(); },
        onReady: (winEl, winId) => { if (inst.onReady) inst.onReady(winEl, winId); this.taskbar.addRunningApp(winId, def.id, def.name, def.icon); },
      });
    },
    toggleAICenter() { this.aiCenter.toggle(); },
  };

  ctx.window.arcanisDesktop = arc;

  const defs = [
    { id: 'terminal', name: 'Terminal', icon: '>', description: 'CLI', pinned: true, color: 'g1', instance: new ctx.TerminalApp() },
    { id: 'file-manager', name: 'Files', icon: 'F', description: 'FM', pinned: true, color: 'g2', instance: new ctx.FileManagerApp() },
    { id: 'browser', name: 'Browser', icon: 'B', description: 'Web', pinned: true, color: 'g3', instance: new ctx.BrowserApp() },
    { id: 'text-editor', name: 'Text Editor', icon: 'E', description: 'Editor', pinned: true, color: 'g4', instance: new ctx.TextEditorApp() },
    { id: 'settings', name: 'Settings', icon: 'S', description: 'Settings', pinned: true, color: 'g5', instance: new ctx.SettingsApp() },
  ];
  defs.forEach(d => { arc.appRegistry[d.id] = d; arc.apps[d.id] = d.instance; });

  return arc;
}

console.log('\n=== ArcanisDesktop Tests ===\n');

console.log('ArcanisDesktop Initialization');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should initialize with all subsystems', () => {
    expect(arc.windowManager).toBeDefined();
    expect(arc.taskbar).toBeDefined();
    expect(arc.notifications).toBeDefined();
    expect(arc.desktop).toBeDefined();
    expect(arc.workspace).toBeDefined();
    expect(arc.aiCenter).toBeDefined();
    expect(arc.workflows).toBeDefined();
    expect(arc.integration).toBeDefined();
  });
  test('should have registered 5 apps', () => { expect(Object.keys(arc.appRegistry).length).toBe(5); });
  test('should have terminal in registry', () => { expect(arc.appRegistry['terminal']).toBeDefined(); expect(arc.appRegistry['terminal'].name).toBe('Terminal'); });
  test('should have file-manager in registry', () => { expect(arc.appRegistry['file-manager']).toBeDefined(); });
  test('should have browser in registry', () => { expect(arc.appRegistry['browser']).toBeDefined(); });
  test('should have text-editor in registry', () => { expect(arc.appRegistry['text-editor']).toBeDefined(); });
  test('should have settings in registry', () => { expect(arc.appRegistry['settings']).toBeDefined(); });
  test('should store app instances in apps map', () => {
    expect(arc.apps['terminal']).toBeDefined(); expect(arc.apps['file-manager']).toBeDefined();
    expect(arc.apps['browser']).toBeDefined(); expect(arc.apps['text-editor']).toBeDefined(); expect(arc.apps['settings']).toBeDefined();
  });
  test('should have integration bridges', () => { expect(arc.integration.ArcanisUI).toBeDefined(); expect(arc.integration.ArcanisShell).toBeDefined(); expect(arc.integration.ArcanisBrain).toBeDefined(); });
  test('should expose UI bridge methods', () => {
    const ui = arc.integration.ArcanisUI;
    expect(typeof ui.getTheme).toBe('function'); expect(typeof ui.setTheme).toBe('function');
    expect(typeof ui.setSetting).toBe('function'); expect(typeof ui.getSetting).toBe('function');
    expect(typeof ui.showNotification).toBe('function');
  });
  test('should expose Shell bridge methods', () => {
    const s = arc.integration.ArcanisShell;
    expect(typeof s.openApp).toBe('function'); expect(typeof s.closeApp).toBe('function');
    expect(typeof s.getOpenApps).toBe('function'); expect(typeof s.closeAll).toBe('function');
  });
  test('should expose Brain bridge methods', () => {
    const b = arc.integration.ArcanisBrain;
    expect(typeof b.processCommand).toBe('function'); expect(typeof b.getConversationHistory).toBe('function');
    expect(typeof b.createWorkflow).toBe('function'); expect(typeof b.getWorkflows).toBe('function');
  });
}

console.log('\nWindow Manager');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should start with no windows', () => { expect(arc.windowManager.windows.size).toBe(0); });
  test('should create a window and return windowData', () => {
    const win = arc.windowManager.createWindow({ title: 'Test Window', appId: 'test' });
    expect(win).toBeDefined(); expect(win.id).toBeDefined();
    expect(win.config.title).toBe('Test Window'); expect(win.config.appId).toBe('test');
    expect(win.minimized).toBe(false); expect(win.maximized).toBe(false);
  });
  test('should track windows in the map', () => {
    const win = arc.windowManager.createWindow({ title: 'W2', appId: 'test2' });
    expect(arc.windowManager.windows.size).toBeGreaterThan(0); expect(arc.windowManager.windows.has(win.id)).toBe(true);
  });
  test('should set the active window on create', () => {
    const win = arc.windowManager.createWindow({ title: 'Active', appId: 'test3' });
    expect(arc.windowManager.activeWindow).toBe(win.id);
  });
  test('should focus an existing window', () => {
    const w1 = arc.windowManager.createWindow({ title: 'W1', appId: 'a1' });
    const w2 = arc.windowManager.createWindow({ title: 'W2', appId: 'a2' });
    arc.windowManager.focusWindow(w1.id); expect(arc.windowManager.activeWindow).toBe(w1.id);
  });
  test('should minimize a window', () => {
    const win = arc.windowManager.createWindow({ title: 'Min', appId: 'min1' });
    arc.windowManager.minimizeWindow(win.id); expect(win.minimized).toBe(true);
  });
  test('should clear activeWindow when minimizing active window', () => {
    const win = arc.windowManager.createWindow({ title: 'Min2', appId: 'min2' });
    arc.windowManager.minimizeWindow(win.id); expect(arc.windowManager.activeWindow).toBeNull();
  });
  test('should restore a minimized window', () => {
    const win = arc.windowManager.createWindow({ title: 'Restore', appId: 'rest1' });
    arc.windowManager.minimizeWindow(win.id); expect(win.minimized).toBe(true);
    arc.windowManager.restoreWindow(win.id); expect(win.minimized).toBe(false); expect(arc.windowManager.activeWindow).toBe(win.id);
  });
  test('should toggle maximize on', () => {
    const win = arc.windowManager.createWindow({ title: 'Max', appId: 'max1' });
    arc.windowManager.toggleMaximize(win.id); expect(win.maximized).toBe(true); expect(win.prevBounds).toBeDefined();
  });
  test('should toggle maximize off', () => {
    const win = arc.windowManager.createWindow({ title: 'Max2', appId: 'max2' });
    const origLeft = win.element.style.left;
    arc.windowManager.toggleMaximize(win.id); expect(win.maximized).toBe(true);
    arc.windowManager.toggleMaximize(win.id); expect(win.maximized).toBe(false); expect(win.element.style.left).toBe(origLeft);
  });
  test('should close a window and remove from map', () => {
    let closed = false;
    const win = arc.windowManager.createWindow({ title: 'Close', appId: 'close1', onClose: () => { closed = true; } });
    const id = win.id; arc.windowManager.closeWindow(id);
    expect(arc.windowManager.windows.has(id)).toBe(false); expect(closed).toBe(true);
  });
  test('should clear activeWindow when closing active window', () => {
    const win = arc.windowManager.createWindow({ title: 'Close2', appId: 'close2' });
    arc.windowManager.closeWindow(win.id); expect(arc.windowManager.activeWindow).toBeNull();
  });
  test('should find window by appId', () => {
    arc.windowManager.createWindow({ title: 'FindMe', appId: 'findme' });
    const found = arc.windowManager.getWindowByAppId('findme');
    expect(found).toBeDefined(); expect(found.config.appId).toBe('findme');
  });
  test('should return null for unknown appId', () => { expect(arc.windowManager.getWindowByAppId('nonexistent')).toBeNull(); });
  test('should get multiple windows by appId', () => {
    arc.windowManager.createWindow({ title: 'M1', appId: 'multi' });
    arc.windowManager.createWindow({ title: 'M2', appId: 'multi' });
    expect(arc.windowManager.getWindowsByAppId('multi').length).toBe(2);
  });
  test('should set window title', () => {
    const win = arc.windowManager.createWindow({ title: 'Old', appId: 'title1' });
    arc.windowManager.setTitle(win.id, 'New');
    expect(win.config.title).toBe('New'); expect(win.element.querySelector('.window-title').textContent).toBe('New');
  });
  test('should generate unique window IDs', () => {
    const ids = new Set();
    for (let i = 0; i < 10; i++) ids.add(arc.windowManager.createWindow({ title: 'U' + i, appId: 'u' + i }).id);
    expect(ids.size).toBe(10);
  });
  test('should increment z-index counter', () => {
    const before = arc.windowManager.zIndexCounter;
    arc.windowManager.createWindow({ title: 'Z', appId: 'z1' });
    expect(arc.windowManager.zIndexCounter).toBeGreaterThan(before);
  });
  test('should not crash when minimizing unknown window', () => { arc.windowManager.minimizeWindow('nonexistent'); });
  test('should not crash when restoring unknown window', () => { arc.windowManager.restoreWindow('nonexistent'); });
  test('should not crash when toggling maximize on unknown window', () => { arc.windowManager.toggleMaximize('nonexistent'); });
  test('should not crash when closing unknown window', () => { arc.windowManager.closeWindow('nonexistent'); });
  test('should not crash when setting title on unknown window', () => { arc.windowManager.setTitle('nonexistent', 'X'); });
}

console.log('\nTaskbar');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should register apps', () => { expect(arc.taskbar.appDefinitions.length).toBe(5); });
  test('should track running apps', () => {
    arc.taskbar.addRunningApp('win-1', 'terminal', 'Terminal', '>');
    expect(arc.taskbar.runningApps.size).toBe(1); expect(arc.taskbar.runningApps.has('win-1')).toBe(true);
  });
  test('should remove running apps', () => {
    arc.taskbar.addRunningApp('win-r', 'terminal', 'Terminal', '>');
    expect(arc.taskbar.runningApps.size).toBeGreaterThan(0);
    arc.taskbar.removeApp('win-r'); expect(arc.taskbar.runningApps.has('win-r')).toBe(false);
  });
  test('should handle remove of unknown app gracefully', () => { arc.taskbar.removeApp('nonexistent'); });
  test('should set active app', () => {
    arc.taskbar.addRunningApp('win-a', 'terminal', 'Terminal', '>');
    arc.taskbar.setActiveApp('terminal');
    expect(arc.taskbar.runningApps.get('win-a')).toBeDefined();
  });
  test('should toggle start menu visibility', () => {
    const sm = ctx.document.getElementById('start-menu');
    expect(sm.classList.contains('hidden')).toBe(true);
    arc.taskbar.toggleStartMenu(); expect(sm.classList.contains('hidden')).toBe(false);
    arc.taskbar.toggleStartMenu(); expect(sm.classList.contains('hidden')).toBe(true);
  });
  test('should hide start menu', () => {
    const sm = ctx.document.getElementById('start-menu');
    sm.classList.remove('hidden'); arc.taskbar.hideStartMenu();
    expect(sm.classList.contains('hidden')).toBe(true);
  });
  test('should filter apps', () => {
    arc.taskbar.renderAllApps('Terminal');
    expect(ctx.document.getElementById('all-apps').innerHTML).toContain('Terminal');
  });
  test('should update clock element', () => {
    arc.taskbar.updateClock();
    expect(ctx.document.getElementById('clock').innerHTML.length).toBeGreaterThan(0);
  });
}

console.log('\nNotification System');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should start with no notifications', () => { expect(arc.notifications.notifications.length).toBe(0); });
  test('should create a notification', () => {
    const n = arc.notifications.notify('Test', 'Body', 'info');
    expect(n).toBeDefined(); expect(n.title).toBe('Test'); expect(n.body).toBe('Body');
    expect(n.type).toBe('info'); expect(n.read).toBe(false);
  });
  test('should add notification to list', () => {
    arc.notifications.notify('N1', 'B1', 'info'); arc.notifications.notify('N2', 'B2', 'success');
    expect(arc.notifications.notifications.length).toBeGreaterThan(1);
  });
  test('should update badge on notify', () => {
    arc.notifications.notifications = []; arc.notifications.updateBadge();
    expect(ctx.document.getElementById('notification-badge').classList.contains('hidden')).toBe(true);
    arc.notifications.notify('BadgeTest', 'Body', 'info');
    expect(ctx.document.getElementById('notification-badge').classList.contains('hidden')).toBe(false);
  });
  test('should clear all notifications', () => {
    arc.notifications.notify('C1', 'B', 'info'); arc.notifications.notify('C2', 'B', 'error');
    arc.notifications.clearAll(); expect(arc.notifications.notifications.length).toBe(0);
  });
  test('should show toast by default', () => { arc.notifications.notify('Toast', 'TB', 'success', {}); });
  test('should not show toast when disabled', () => { arc.notifications.notify('NT', 'B', 'info', { toast: false }); });
  test('should format time as Just now', () => { expect(arc.notifications.formatTime(new Date())).toBe('Just now'); });
  test('should toggle panel visibility', () => {
    const p = ctx.document.getElementById('notifications-panel');
    expect(p.classList.contains('hidden')).toBe(true);
    arc.notifications.togglePanel(); expect(p.classList.contains('hidden')).toBe(false);
  });
  test('should hide panel', () => {
    const p = ctx.document.getElementById('notifications-panel');
    p.classList.remove('hidden'); arc.notifications.hidePanel(); expect(p.classList.contains('hidden')).toBe(true);
  });
  test('should render list with no notifications', () => {
    arc.notifications.notifications = []; arc.notifications.renderList();
    expect(ctx.document.getElementById('notifications-list').innerHTML).toContain('No notifications');
  });
  test('should render list with notifications', () => {
    arc.notifications.notifications = [{ id: 1, title: 'T1', body: 'B1', type: 'info', time: new Date(), read: false }];
    arc.notifications.renderList(); expect(ctx.document.getElementById('notifications-list').innerHTML).toContain('T1');
  });
  test('should return correct type icon', () => {
    expect(arc.notifications.getTypeIcon('info')).toBe('\u2139');
    expect(arc.notifications.getTypeIcon('success')).toBe('\u2713');
    expect(arc.notifications.getTypeIcon('warning')).toBe('!');
    expect(arc.notifications.getTypeIcon('error')).toBe('\u2715');
    expect(arc.notifications.getTypeIcon('unknown')).toBe('\u2139');
  });
}

console.log('\nTerminal Commands');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);
  const terminal = arc.apps['terminal'];
  const mockOut = () => ({ innerHTML: '', scrollTop: 0, scrollHeight: 100, parentElement: { querySelector: () => ({ textContent: '' }) } });

  test('should have initial filesystem', () => {
    expect(terminal.filesystem).toBeDefined(); expect(terminal.filesystem['~']).toBeDefined();
    expect(terminal.filesystem['~'].type).toBe('dir');
  });
  test('should have initial env variables', () => {
    expect(terminal.env.USER).toBe('arcanis'); expect(terminal.env.HOME).toBe('/home/arcanis');
    expect(terminal.env.SHELL).toBe('arcanis-shell');
  });
  test('should start at home directory', () => { expect(terminal.cwd).toBe('~'); });
  test('should generate correct prompt', () => { expect(terminal.getPrompt()).toBe('arcanis@arcanis:~$ '); });
  test('getContent should return HTML string', () => {
    const c = terminal.getContent(); expect(typeof c).toBe('string'); expect(c).toContain('terminal-app');
  });
  test('should execute help command', () => {
    terminal.outputEl = mockOut(); terminal.execute('help');
    expect(terminal.outputEl.innerHTML).toContain('Available commands');
  });
  test('should execute ls command', () => {
    terminal.outputEl = mockOut(); terminal.cwd = '~'; terminal.execute('ls');
    expect(terminal.outputEl.innerHTML).toContain('Documents'); expect(terminal.outputEl.innerHTML).toContain('Downloads');
  });
  test('should execute pwd command', () => {
    terminal.outputEl = mockOut(); terminal.cwd = '~'; terminal.execute('pwd');
    expect(terminal.outputEl.innerHTML).toContain('/home/arcanis');
  });
  test('should execute cd command', () => {
    terminal.outputEl = mockOut(); terminal.cwd = '~'; terminal.execute('cd Documents');
    expect(terminal.cwd).toBe('~/Documents');
  });
  test('should execute cd .. command', () => {
    terminal.cwd = '~/Documents'; terminal.outputEl = mockOut(); terminal.execute('cd ..');
    expect(terminal.cwd).toBe('~');
  });
  test('should execute cd ~ command', () => {
    terminal.cwd = '~/Documents'; terminal.outputEl = mockOut(); terminal.execute('cd ~');
    expect(terminal.cwd).toBe('~');
  });
  test('should execute cd with invalid directory', () => {
    terminal.cwd = '~'; terminal.outputEl = mockOut(); terminal.execute('cd nonexistent');
    expect(terminal.outputEl.innerHTML).toContain('No such directory');
  });
  test('should execute cat command', () => {
    terminal.cwd = '~'; terminal.outputEl = mockOut(); terminal.execute('cat readme.md');
    expect(terminal.outputEl.innerHTML).toContain('ArcanisDesktop');
  });
  test('should execute cat on nested file', () => {
    terminal.cwd = '~/Documents'; terminal.outputEl = mockOut(); terminal.execute('cat notes.txt');
    expect(terminal.outputEl.innerHTML).toContain('Welcome to ArcanisDesktop!');
  });
  test('should execute cat with no args', () => {
    terminal.outputEl = mockOut(); terminal.execute('cat');
    expect(terminal.outputEl.innerHTML).toContain('missing file operand');
  });
  test('should execute cat with nonexistent file', () => {
    terminal.cwd = '~'; terminal.outputEl = mockOut(); terminal.execute('cat nofile.txt');
    expect(terminal.outputEl.innerHTML).toContain('No such file');
  });
  test('should execute echo command', () => {
    terminal.outputEl = mockOut(); terminal.execute('echo hello world');
    expect(terminal.outputEl.innerHTML).toContain('hello world');
  });
  test('should execute whoami command', () => {
    terminal.outputEl = mockOut(); terminal.execute('whoami');
    expect(terminal.outputEl.innerHTML).toContain('arcanis');
  });
  test('should execute uname command', () => {
    terminal.outputEl = mockOut(); terminal.execute('uname');
    expect(terminal.outputEl.innerHTML).toContain('ArcanisOS');
  });
  test('should execute mkdir command', () => {
    terminal.cwd = '~'; terminal.outputEl = mockOut(); terminal.execute('mkdir NewDir');
    const dir = terminal.resolveDir('~');
    expect(dir.children['NewDir']).toBeDefined(); expect(dir.children['NewDir'].type).toBe('dir');
  });
  test('should execute mkdir with no args', () => {
    terminal.outputEl = mockOut(); terminal.execute('mkdir');
    expect(terminal.outputEl.innerHTML).toContain('missing operand');
  });
  test('should execute touch command', () => {
    terminal.cwd = '~'; terminal.outputEl = mockOut(); terminal.execute('touch newfile.txt');
    const dir = terminal.resolveDir('~');
    expect(dir.children['newfile.txt']).toBeDefined(); expect(dir.children['newfile.txt'].type).toBe('file');
  });
  test('should execute touch with no args', () => {
    terminal.outputEl = mockOut(); terminal.execute('touch');
    expect(terminal.outputEl.innerHTML).toContain('missing operand');
  });
  test('should execute calc command', () => {
    terminal.outputEl = mockOut(); terminal.execute('calc 2+3');
    expect(terminal.outputEl.innerHTML).toContain('5');
  });
  test('should execute calc with multiplication', () => {
    terminal.outputEl = mockOut(); terminal.execute('calc 4*5');
    expect(terminal.outputEl.innerHTML).toContain('20');
  });
  test('should execute calc with no args', () => {
    terminal.outputEl = mockOut(); terminal.execute('calc');
    expect(terminal.outputEl.innerHTML).toContain('Usage');
  });
  test('should execute history command', () => {
    terminal.history = ['ls', 'cd Documents', 'pwd']; terminal.outputEl = mockOut(); terminal.execute('history');
    expect(terminal.outputEl.innerHTML).toContain('ls'); expect(terminal.outputEl.innerHTML).toContain('cd Documents');
  });
  test('should handle unknown command', () => {
    terminal.outputEl = mockOut(); terminal.execute('boguscmd');
    expect(terminal.outputEl.innerHTML).toContain('command not found');
  });
  test('should resolve directory', () => { const d = terminal.resolveDir('~'); expect(d).toBeDefined(); expect(d.type).toBe('dir'); });
  test('should resolve nested directory', () => {
    const d = terminal.resolveDir('~/Documents'); expect(d).toBeDefined();
    expect(d.type).toBe('dir'); expect(d.children['notes.txt']).toBeDefined();
  });
  test('should return null for nonexistent directory', () => { expect(terminal.resolveDir('~/Nonexistent')).toBeNull(); });
  test('should resolve file in current directory', () => {
    terminal.cwd = '~'; const f = terminal.resolveFile('readme.md');
    expect(f).toBeDefined(); expect(f.type).toBe('file');
  });
  test('should return null for nonexistent file', () => { terminal.cwd = '~'; expect(terminal.resolveFile('nofile.txt')).toBeNull(); });
}

console.log('\nAI Center Command Routing');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);
  const ai = arc.aiCenter;

  test('should have initial conversation history', () => { expect(Array.isArray(ai.conversationHistory)).toBe(true); });
  test('should toggle panel', () => {
    const p = ctx.document.getElementById('ai-center');
    expect(p.classList.contains('hidden')).toBe(true); ai.toggle(); expect(p.classList.contains('hidden')).toBe(false);
  });
  test('should show panel', () => {
    const p = ctx.document.getElementById('ai-center'); ai.hide(); ai.show();
    expect(p.classList.contains('hidden')).toBe(false);
  });
  test('should hide panel', () => {
    const p = ctx.document.getElementById('ai-center'); p.classList.remove('hidden'); ai.hide();
    expect(p.classList.contains('hidden')).toBe(true);
  });
  test('should escape HTML', () => {
    const r = ai.escapeHtml('<script>alert("xss")</script>');
    expect(r).not.toContain('<script>'); expect(r).toContain('&lt;');
  });
  test('should route open terminal command', () => {
    const r = ai.processCommand('open terminal'); expect(r).toContain('Terminal');
    expect(arc.windowManager.getWindowByAppId('terminal')).toBeDefined();
  });
  test('should route open files command', () => { expect(ai.processCommand('open files')).toContain('File Manager'); });
  test('should route open browser command', () => { expect(ai.processCommand('open browser')).toContain('Browser'); });
  test('should route open editor command', () => { expect(ai.processCommand('open editor')).toContain('Text Editor'); });
  test('should route open settings command', () => { expect(ai.processCommand('open settings')).toContain('Settings'); });
  test('should route launch terminal command', () => { expect(ai.processCommand('launch console')).toContain('Terminal'); });
  test('should route start shell command', () => { expect(ai.processCommand('start shell')).toContain('Terminal'); });
  test('should route run powershell command', () => { expect(ai.processCommand('run powershell')).toContain('Terminal'); });
  test('should route change theme to dark', () => {
    const r = ai.processCommand('change theme to dark'); expect(r).toContain('dark');
    expect(ctx.document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
  test('should route change theme to light', () => {
    const r = ai.processCommand('change theme to light'); expect(r).toContain('light');
    expect(ctx.document.documentElement.getAttribute('data-theme')).toBe('light');
  });
  test('should route change theme to midnight', () => { expect(ai.processCommand('switch theme to midnight')).toContain('midnight'); });
  test('should route set theme command', () => {
    ai.processCommand('set theme mode to dark');
    expect(ctx.document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
  test('should route minimize all command', () => {
    arc.windowManager.createWindow({ title: 'MinAll1', appId: 'm1' });
    arc.windowManager.createWindow({ title: 'MinAll2', appId: 'm2' });
    const r = ai.processCommand('minimize all'); expect(r).toContain('minimized');
    arc.windowManager.windows.forEach(w => { expect(w.minimized).toBe(true); });
  });
  test('should route maximize command with active window', () => {
    const w = arc.windowManager.createWindow({ title: 'MaxAI', appId: 'maxai' });
    arc.windowManager.focusWindow(w.id); const r = ai.processCommand('maximize');
    expect(r).toContain('maximized'); expect(w.maximized).toBe(true);
  });
  test('should route maximize command with no active window', () => {
    arc.windowManager.activeWindow = null; expect(ai.processCommand('maximize')).toContain('No active window');
  });
  test('should route close all command', () => {
    arc.windowManager.createWindow({ title: 'CA1', appId: 'ca1' });
    arc.windowManager.createWindow({ title: 'CA2', appId: 'ca2' });
    const r = ai.processCommand('close all'); expect(r).toContain('closed');
    expect(arc.windowManager.windows.size).toBe(0);
  });
  test('should route exit all windows command', () => {
    arc.windowManager.createWindow({ title: 'EA1', appId: 'ea1' });
    expect(ai.processCommand('exit all windows')).toContain('closed');
  });
  test('should route show notifications command', () => { expect(ai.processCommand('show notifications')).toContain('notifications'); });
  test('should route clear notifications command', () => {
    arc.notifications.notify('T', 'B', 'info');
    expect(ai.processCommand('clear notifications')).toContain('cleared');
    expect(arc.notifications.notifications.length).toBe(0);
  });
  test('should route send test notification', () => { expect(ai.processCommand('send notification')).toContain('sent'); });
  test('should route create notification', () => { expect(ai.processCommand('create notification')).toContain('sent'); });
  test('should route test notification', () => { expect(ai.processCommand('test notification')).toContain('sent'); });
  test('should route help command', () => {
    const r = ai.processCommand('help');
    expect(r).toContain('Apps'); expect(r).toContain('Themes'); expect(r).toContain('Windows');
  });
  test('should route what can you do command', () => { expect(ai.processCommand('what can you do')).toContain('Apps'); });
  test('should route commands command', () => { expect(ai.processCommand('commands')).toContain('Apps'); });
  test('should route system info command', () => { expect(ai.processCommand('system info')).toContain('System Info'); });
  test('should route device info command', () => { expect(ai.processCommand('device info')).toContain('System Info'); });
  test('should route what time command', () => { expect(ai.processCommand('what time')).toContain('Current time'); });
  test('should route current time command', () => { expect(ai.processCommand('current time')).toContain('Current time'); });
  test('should return smart response for unknown input', () => {
    const r = ai.processCommand('random gibberish xyz');
    expect(typeof r).toBe('string'); expect(r.length).toBeGreaterThan(0);
  });
  test('should get system info', () => { const i = ai.getSystemInfo(); expect(i).toContain('Platform'); expect(i).toContain('Language'); });
  test('should get help text', () => {
    const h = ai.getHelpText(); expect(h).toContain('Apps'); expect(h).toContain('Themes'); expect(h).toContain('open terminal');
  });
}

console.log('\nApp Launching');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should launch an app and create a window', () => {
    arc.launchApp('terminal'); const w = arc.windowManager.getWindowByAppId('terminal');
    expect(w).toBeDefined(); expect(w.config.title).toBe('Terminal');
  });
  test('should not launch unknown app', () => {
    arc.launchApp('nonexistent'); expect(arc.windowManager.getWindowByAppId('nonexistent')).toBeNull();
  });
  test('should focus existing window on second launch', () => {
    arc.launchApp('terminal'); const w1 = arc.windowManager.getWindowByAppId('terminal');
    arc.launchApp('terminal'); const w2 = arc.windowManager.getWindowByAppId('terminal');
    expect(w1.id).toBe(w2.id); expect(arc.windowManager.activeWindow).toBe(w1.id);
  });
  test('should restore minimized window on launch', () => {
    arc.launchApp('terminal'); const w = arc.windowManager.getWindowByAppId('terminal');
    arc.windowManager.minimizeWindow(w.id); expect(w.minimized).toBe(true);
    arc.launchApp('terminal'); expect(w.minimized).toBe(false);
  });
  test('should launch multiple different apps', () => {
    arc.launchApp('terminal'); arc.launchApp('browser'); arc.launchApp('text-editor');
    expect(arc.windowManager.getWindowByAppId('terminal')).toBeDefined();
    expect(arc.windowManager.getWindowByAppId('browser')).toBeDefined();
    expect(arc.windowManager.getWindowByAppId('text-editor')).toBeDefined();
  });
  test('should register running app in taskbar', () => {
    arc.launchApp('settings'); let found = false;
    arc.taskbar.runningApps.forEach((btn, wid) => {
      const w = arc.windowManager.windows.get(wid); if (w && w.config.appId === 'settings') found = true;
    });
    expect(found).toBe(true);
  });
}

console.log('\nWorkflow Engine');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should start with no workflows', () => { expect(arc.workflows.getWorkflows().length).toBe(0); });
  test('should create a workflow', () => {
    const wf = arc.workflows.createWorkflow('Test WF', [{ type: 'launch-app', appId: 'terminal' }, { type: 'notification', title: 'WF', message: 'Done' }]);
    expect(wf).toBeDefined(); expect(wf.name).toBe('Test WF');
    expect(wf.steps.length).toBe(2); expect(wf.enabled).toBe(true); expect(wf.runCount).toBe(0);
  });
  test('should persist workflows', () => { expect(arc.workflows.getWorkflows().length).toBeGreaterThan(0); });
  test('should delete a workflow', () => {
    const wf = arc.workflows.createWorkflow('Del', []); arc.workflows.deleteWorkflow(wf.id);
    expect(arc.workflows.getWorkflow(wf.id)).toBeNull();
  });
  test('should toggle workflow', () => {
    const wf = arc.workflows.createWorkflow('Toggle', []);
    expect(wf.enabled).toBe(true); arc.workflows.toggleWorkflow(wf.id);
    expect(wf.enabled).toBe(false); arc.workflows.toggleWorkflow(wf.id); expect(wf.enabled).toBe(true);
  });
  test('should get workflow by id', () => {
    const wf = arc.workflows.createWorkflow('Get', []);
    expect(arc.workflows.getWorkflow(wf.id)).toBeDefined(); expect(arc.workflows.getWorkflow(wf.id).name).toBe('Get');
  });
  test('should return null for nonexistent workflow', () => { expect(arc.workflows.getWorkflow(999999)).toBeNull(); });
}

console.log('\nIntegration Layer');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should get and set theme via UI bridge', () => {
    arc.integration.ArcanisUI.setTheme('light'); expect(arc.integration.ArcanisUI.getTheme()).toBe('light');
  });
  test('should get and set settings via UI bridge', () => {
    arc.integration.ArcanisUI.setSetting('testkey', 'testval'); expect(arc.integration.ArcanisUI.getSetting('testkey')).toBe('testval');
  });
  test('should open app via shell bridge', () => {
    arc.integration.ArcanisShell.openApp('terminal'); expect(arc.windowManager.getWindowByAppId('terminal')).toBeDefined();
  });
  test('should close app via shell bridge', () => {
    arc.launchApp('browser'); arc.launchApp('text-editor');
    arc.integration.ArcanisShell.closeApp('browser');
    expect(arc.windowManager.getWindowByAppId('browser')).toBeNull();
    expect(arc.windowManager.getWindowByAppId('text-editor')).toBeDefined();
  });
  test('should get open apps via shell bridge', () => {
    arc.windowManager.windows.clear(); arc.launchApp('terminal'); arc.launchApp('browser');
    const apps = arc.integration.ArcanisShell.getOpenApps();
    expect(apps.length).toBe(2);
    expect(apps.map(a => a.id)).toContain('terminal');
    expect(apps.map(a => a.id)).toContain('browser');
  });
  test('should minimize all via shell bridge', () => {
    arc.windowManager.windows.clear(); arc.launchApp('terminal'); arc.launchApp('browser');
    arc.integration.ArcanisShell.minimizeAll();
    arc.windowManager.windows.forEach(w => { expect(w.minimized).toBe(true); });
  });
  test('should close all via shell bridge', () => {
    arc.windowManager.windows.clear(); arc.launchApp('terminal'); arc.launchApp('browser');
    arc.integration.ArcanisShell.closeAll(); expect(arc.windowManager.windows.size).toBe(0);
  });
  test('should process command via brain bridge', () => { expect(arc.integration.ArcanisBrain.processCommand('help')).toContain('Apps'); });
  test('should get conversation history via brain bridge', () => { expect(Array.isArray(arc.integration.ArcanisBrain.getConversationHistory())).toBe(true); });
  test('should create workflow via brain bridge', () => {
    const wf = arc.integration.ArcanisBrain.createWorkflow('Bridge WF', []);
    expect(wf).toBeDefined(); expect(wf.name).toBe('Bridge WF');
  });
  test('should get workflows via brain bridge', () => { expect(arc.integration.ArcanisBrain.getWorkflows().length).toBeGreaterThan(0); });
  test('should get capabilities', () => {
    const c = arc.integration.getCapabilities();
    expect(c.ui.length).toBeGreaterThan(0); expect(c.shell.length).toBeGreaterThan(0); expect(c.brain.length).toBeGreaterThan(0);
    expect(c.ui).toContain('getTheme'); expect(c.ui).toContain('setTheme');
    expect(c.shell).toContain('openApp'); expect(c.shell).toContain('closeApp');
    expect(c.brain).toContain('processCommand'); expect(c.brain).toContain('createWorkflow');
  });
}

console.log('\nDesktop');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should render desktop icons', () => {
    const c = ctx.document.getElementById('desktop-icons');
    expect(c.innerHTML).toContain('Terminal'); expect(c.innerHTML).toContain('Files'); expect(c.innerHTML).toContain('Browser');
  });
  test('should have context menu element', () => { expect(ctx.document.getElementById('context-menu')).toBeDefined(); });
  test('should hide context menu', () => {
    const c = ctx.document.getElementById('context-menu'); c.classList.remove('hidden');
    arc.desktop.hideContextMenu(); expect(c.classList.contains('hidden')).toBe(true);
  });
}

console.log('\nWorkspace Manager');
{
  const { ctx } = createCtx();
  const arc = buildDesktop(ctx);

  test('should have default workspaces', () => {
    expect(arc.workspace.workspaces.length).toBe(3);
    expect(arc.workspace.workspaces[0].name).toBe('Desktop');
    expect(arc.workspace.workspaces[1].name).toBe('Work');
    expect(arc.workspace.workspaces[2].name).toBe('Personal');
  });
  test('should start at workspace 0', () => { expect(arc.workspace.currentWorkspace).toBe(0); });
  test('should get layout', () => {
    const l = arc.workspace.getLayout(); expect(l.currentWorkspace).toBe(0); expect(l.workspaces.length).toBe(3);
  });
  test('should add a workspace', () => {
    const ws = arc.workspace.addWorkspace('Custom'); expect(ws.name).toBe('Custom');
    expect(arc.workspace.workspaces.length).toBe(4);
  });
  test('should remove a workspace', () => {
    const ws = arc.workspace.addWorkspace('Removable'); expect(arc.workspace.removeWorkspace(ws.id)).toBe(true);
  });
  test('should not remove last workspace', () => {
    while (arc.workspace.workspaces.length > 1) arc.workspace.removeWorkspace(arc.workspace.workspaces[arc.workspace.workspaces.length - 1].id);
    expect(arc.workspace.removeWorkspace(arc.workspace.workspaces[0].id)).toBe(false);
  });
  test('should not remove current workspace', () => {
    arc.workspace.addWorkspace('Try');
    expect(arc.workspace.removeWorkspace(arc.workspace.currentWorkspace)).toBe(false);
  });
}

console.log('\n' + '='.repeat(50));
console.log(`Results: ${testsPassed} passed, ${testsFailed} failed`);
console.log('='.repeat(50));
if (testsFailed > 0) process.exit(1);
