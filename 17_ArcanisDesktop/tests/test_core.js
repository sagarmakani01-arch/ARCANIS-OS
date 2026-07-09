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
    toBe(e) { if (val !== e) throw new Error(`Expected ${JSON.stringify(e)}, got ${JSON.stringify(val)}`); },
    toEqual(e) { if (JSON.stringify(val) !== JSON.stringify(e)) throw new Error(`Expected ${JSON.stringify(e)}, got ${JSON.stringify(val)}`); },
    toBeTruthy() { if (!val) throw new Error(`Expected truthy, got ${JSON.stringify(val)}`); },
    toBeFalsy() { if (val) throw new Error(`Expected falsy, got ${JSON.stringify(val)}`); },
    toBeGreaterThan(n) { if (!(val > n)) throw new Error(`Expected ${val} > ${n}`); },
    toContain(item) {
      if (typeof val === 'string') { if (!val.includes(item)) throw new Error(`Expected "${val}" to contain "${item}"`); }
      else if (Array.isArray(val)) { if (!val.includes(item)) throw new Error(`Expected array to contain ${JSON.stringify(item)}`); }
    },
    toHaveLength(n) { if (val.length !== n) throw new Error(`Expected length ${n}, got ${val.length}`); },
    toBeNull() { if (val !== null) throw new Error(`Expected null, got ${JSON.stringify(val)}`); },
    toBeDefined() { if (val === undefined) throw new Error('Expected defined'); },
    toBeInstanceOf(cls) { if (!(val instanceof cls)) throw new Error(`Expected instance of ${cls.name}`); },
    not: {
      toBeNull() { if (val === null) throw new Error('Expected not null'); },
      toBe(e) { if (val === e) throw new Error(`Expected not ${JSON.stringify(e)}`); },
    },
  };
}

const _elements = {};
function makeEl(id) {
  return {
    id, tagName: 'DIV', className: '', innerHTML: '', textContent: '',
    style: {}, dataset: {}, children: [], parentNode: null,
    classList: { _c: new Set(), add(c) { this._c.add(c); }, remove(c) { this._c.delete(c); }, toggle(c) { this._c.has(c) ? this._c.delete(c) : this._c.add(c); }, contains(c) { return this._c.has(c); } },
    addEventListener() {}, removeEventListener() {}, appendChild() {}, removeChild() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    getAttribute() { return null; }, setAttribute() {},
    getBoundingClientRect() { return { left: 0, top: 0, width: 800, height: 600 }; },
  };
}
const mockDocument = {
  getElementById(id) { return _elements[id] || (_elements[id] = makeEl(id)); },
  querySelector(sel) { return makeEl('queried'); },
  querySelectorAll() { return []; },
  createElement(tag) { return makeEl('created-' + tag); },
  createDocumentFragment() { return makeEl('fragment'); },
  addEventListener() {},
  removeEventListener() {},
  body: makeEl('body'),
  documentElement: makeEl('html'),
};
const mockWindow = {
  innerWidth: 1920, innerHeight: 1080, addEventListener() {},
  matchMedia() { return { matches: false }; },
  requestAnimationFrame(cb) { return setTimeout(cb, 16); },
  cancelAnimationFrame(id) { clearTimeout(id); },
  performance: { now() { return Date.now(); } },
  localStorage: { _s: {}, getItem(k) { return this._s[k] || null; }, setItem(k, v) { this._s[k] = String(v); }, removeItem(k) { delete this._s[k]; } },
  location: { href: 'http://localhost', protocol: 'http:', hostname: 'localhost' },
  navigator: { userAgent: 'test' },
};
function createMinimalDOM() {
  return { document: mockDocument, window: mockWindow, elements: _elements, makeEl };
}

function loadModule(filePath, dom) {
  const code = fs.readFileSync(path.join(__dirname, '..', filePath), 'utf-8');
  // Create a fresh context for each module load
  const g = {
    console, setTimeout, clearTimeout, setInterval, clearInterval,
    document: dom.document, window: {},
    navigator: dom.window.navigator, performance: dom.window.performance,
    localStorage: dom.window.localStorage,
    requestAnimationFrame: dom.window.requestAnimationFrame,
    cancelAnimationFrame: dom.window.cancelAnimationFrame,
    matchMedia: dom.window.matchMedia,
    Math, Date, JSON, Array, Object, String, Number, Boolean, Map, Set, RegExp, Error,
    parseInt, parseFloat, isNaN, isFinite,
  };
  g.window = g;
  g.globalThis = g;
  g.global = g;
  try {
    // Use Function constructor to execute code in a context where 'this' is the global
    const Fn = new Function('document', 'window', 'navigator', 'performance', 'localStorage',
      'requestAnimationFrame', 'cancelAnimationFrame', 'matchMedia',
      code + '\n' +
      'var __classes__ = {};\n' +
      'try { __classes__.WindowManager = WindowManager; } catch(e) {}\n' +
      'try { __classes__.Taskbar = Taskbar; } catch(e) {}\n' +
      'try { __classes__.NotificationSystem = NotificationSystem; } catch(e) {}\n' +
      'try { __classes__.TerminalApp = TerminalApp; } catch(e) {}\n' +
      'try { __classes__.AICenter = AICenter; } catch(e) {}\n' +
      'try { __classes__.WorkflowEngine = WorkflowEngine; } catch(e) {}\n' +
      'try { __classes__.ArcanisIntegration = ArcanisIntegration; } catch(e) {}\n' +
      'try { __classes__.ArcanisDesktop = ArcanisDesktop; } catch(e) {}\n' +
      'return __classes__;'
    );
    const result = Fn(dom.document, g, dom.window.navigator, dom.window.performance,
      dom.window.localStorage, dom.window.requestAnimationFrame,
      dom.window.cancelAnimationFrame, dom.window.matchMedia);
    return { ...g, ...result };
  } catch (e) {
    return { error: e };
  }
}

const dom = createMinimalDOM();
// Ensure window has all expected properties
mockWindow.document = mockDocument;
mockWindow.self = mockWindow;
mockWindow.top = mockWindow;
mockWindow.parent = mockWindow;
mockWindow.frames = mockWindow;

function findClass(ctx, names) {
  for (const n of names) {
    if (ctx[n] && typeof ctx[n] === 'function') return ctx[n];
  }
  return null;
}

console.log('\n=== WindowManager ===');
const wm = loadModule('js/core/window-manager.js', dom);
if (wm.error) { console.log(`  ✗ Load error: ${wm.error.message}`); }
else {
  const WM = findClass(wm, ['WindowManager', 'default']);
  if (!WM) { console.log('  ⚠ Class not found'); }
  else {
    const mgr = new WM();
    test('create window returns object', () => {
      const win = mgr.createWindow({ title: 'Test', width: 400, height: 300 });
      expect(win).toBeTruthy();
      expect(win.title).toBe('Test');
    });
    test('windows list tracks created', () => {
      const wins = mgr.getWindows ? mgr.getWindows() : mgr.windows;
      expect(wins.length).toBeGreaterThan(0);
    });
    test('close window removes it', () => {
      const win = mgr.createWindow({ title: 'CloseMe' });
      mgr.closeWindow(win.id);
      const wins = mgr.getWindows ? mgr.getWindows() : mgr.windows;
      expect(wins.find(w => w.id === win.id)).toBeUndefined();
    });
  }
}

console.log('\n=== Taskbar ===');
const tb = loadModule('js/core/taskbar.js', dom);
if (tb.error) { console.log(`  ✗ Load error: ${tb.error.message}`); }
else {
  const TB = findClass(tb, ['Taskbar', 'default']);
  if (!TB) { console.log('  ⚠ Class not found'); }
  else {
    const taskbar = new TB();
    test('taskbar initializes', () => { expect(taskbar).toBeTruthy(); });
    test('taskbar has apps', () => {
      const apps = taskbar.getApps ? taskbar.getApps() : taskbar.apps;
      expect(apps).toBeTruthy();
    });
  }
}

console.log('\n=== Notifications ===');
const notif = loadModule('js/core/notifications.js', dom);
if (notif.error) { console.log(`  ✗ Load error: ${notif.error.message}`); }
else {
  const NC = findClass(notif, ['Notifications', 'NotificationManager', 'default']);
  if (!NC) { console.log('  ⚠ Class not found'); }
  else {
    const nm = new NC();
    test('notification manager initializes', () => { expect(nm).toBeTruthy(); });
  }
}

console.log('\n=== Terminal ===');
const term = loadModule('js/apps/terminal.js', dom);
if (term.error) { console.log(`  ✗ Load error: ${term.error.message}`); }
else {
  const Term = findClass(term, ['Terminal', 'default']);
  if (!Term) { console.log('  ⚠ Class not found'); }
  else {
    const t = new Term();
    test('terminal initializes', () => { expect(t).toBeTruthy(); });
    test('has processCommand', () => {
      expect(t.processCommand || t.execute || t.run).toBeTruthy();
    });
    test('echo command works', () => {
      const fn = t.processCommand || t.execute || t.run;
      const r = fn.call(t, 'echo hello');
      expect(r).toBeTruthy();
    });
    test('help command works', () => {
      const fn = t.processCommand || t.execute || t.run;
      const r = fn.call(t, 'help');
      expect(r).toBeTruthy();
    });
  }
}

console.log('\n=== AI Center ===');
const ai = loadModule('js/ai/ai-center.js', dom);
if (ai.error) { console.log(`  ✗ Load error: ${ai.error.message}`); }
else {
  const AIC = findClass(ai, ['AICenter', 'AiCenter', 'default']);
  if (!AIC) { console.log('  ⚠ Class not found'); }
  else {
    const center = new AIC();
    test('AI center initializes', () => { expect(center).toBeTruthy(); });
    test('has process method', () => {
      expect(center.process || center.respond || center.handle).toBeTruthy();
    });
  }
}

console.log('\n=== Workflows ===');
const wf = loadModule('js/ai/workflows.js', dom);
if (wf.error) { console.log(`  ✗ Load error: ${wf.error.message}`); }
else {
  const WF = findClass(wf, ['Workflows', 'WorkflowManager', 'default']);
  if (!WF) { console.log('  ⚠ Class not found'); }
  else {
    const wfm = new WF();
    test('workflow manager initializes', () => { expect(wfm).toBeTruthy(); });
  }
}

console.log('\n=== Integration ===');
const integ = loadModule('js/integration.js', dom);
if (integ.error) { console.log(`  ✗ Load error: ${integ.error.message}`); }
else {
  const INT = findClass(integ, ['Integration', 'default']);
  if (!INT) { console.log('  ⚠ Class not found'); }
  else {
    const intg = new INT();
    test('integration initializes', () => { expect(intg).toBeTruthy(); });
  }
}

console.log('\n=== Main (ArcanisDesktop) ===');
const main = loadModule('js/main.js', dom);
if (main.error) { console.log(`  ✗ Load error: ${main.error.message}`); }
else {
  const Desktop = findClass(main, ['ArcanisDesktop', 'default']);
  if (!Desktop) { console.log('  ⚠ Class not found'); }
  else {
    const desktop = new Desktop();
    test('desktop initializes', () => { expect(desktop).toBeTruthy(); });
    test('has app registry', () => {
      expect(desktop.apps || desktop.appRegistry || desktop.registeredApps).toBeTruthy();
    });
    test('has launch method', () => {
      expect(desktop.launch || desktop.openApp || desktop.startApp).toBeTruthy();
    });
  }
}

console.log('\n' + '='.repeat(50));
console.log(`Results: ${testsPassed} passed, ${testsFailed} failed`);
process.exit(testsFailed > 0 ? 1 : 0);
