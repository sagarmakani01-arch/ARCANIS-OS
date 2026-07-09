class TerminalApp {
  constructor() {
    this.history = [];
    this.historyIndex = -1;
    this.cwd = '~';
    this.env = {
      USER: 'arcanis',
      HOME: '/home/arcanis',
      SHELL: 'arcanis-shell',
      TERM: 'arcanis-terminal',
      PATH: '/usr/local/bin:/usr/bin:/bin',
      PS1: '\\u@arcanis:\\w$ ',
    };
    this.filesystem = {
      '~': {
        type: 'dir',
        children: {
          'Documents': { type: 'dir', children: { 'notes.txt': { type: 'file', content: 'Welcome to ArcanisDesktop!' } } },
          'Downloads': { type: 'dir', children: {} },
          'Projects': { type: 'dir', children: {} },
          '.config': { type: 'dir', children: { 'settings.json': { type: 'file', content: '{"theme":"dark"}' } } },
          'readme.md': { type: 'file', content: '# ArcanisDesktop\nAI-native desktop experience.' },
        },
      },
    };
  }

  getContent() {
    return `
      <div class="terminal-app">
        <div class="terminal-output" id="term-output"></div>
        <div class="terminal-input-line">
          <span class="terminal-prompt">${this.getPrompt()}</span>
          <input class="terminal-input" id="term-input" type="text" autocomplete="off" spellcheck="false">
        </div>
      </div>
    `;
  }

  onReady(winElement, winId) {
    this.winId = winId;
    this.outputEl = winElement.querySelector('#term-output');
    this.inputEl = winElement.querySelector('#term-input');

    this.print('ArcanisTerminal v1.0 — Type "help" for commands.\n');
    this.inputEl.addEventListener('keydown', (e) => this.handleKey(e));
    this.inputEl.focus();
  }

  getPrompt() {
    return `${this.env.USER}@arcanis:${this.cwd}$ `;
  }

  handleKey(e) {
    if (e.key === 'Enter') {
      const cmd = this.inputEl.value.trim();
      this.print(`${this.getPrompt()}${cmd}\n`);
      if (cmd) {
        this.history.push(cmd);
        this.historyIndex = this.history.length;
        this.execute(cmd);
      }
      this.inputEl.value = '';
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (this.historyIndex > 0) {
        this.historyIndex--;
        this.inputEl.value = this.history[this.historyIndex];
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (this.historyIndex < this.history.length - 1) {
        this.historyIndex++;
        this.inputEl.value = this.history[this.historyIndex];
      } else {
        this.historyIndex = this.history.length;
        this.inputEl.value = '';
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      this.autocomplete();
    } else if (e.key === 'l' && e.ctrlKey) {
      e.preventDefault();
      this.outputEl.innerHTML = '';
    }
  }

  print(text) {
    this.outputEl.innerHTML += text;
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }

  execute(cmdStr) {
    const parts = cmdStr.split(/\s+/);
    const cmd = parts[0];
    const args = parts.slice(1);

    const commands = {
      help: () => `Available commands:\n  help        Show this help\n  ls          List directory\n  cd          Change directory\n  pwd         Print working directory\n  cat         Display file contents\n  echo        Print text\n  mkdir       Create directory\n  touch       Create file\n  clear       Clear terminal\n  whoami      Current user\n  date        Current date/time\n  uname       System info\n  theme       Change theme (dark/light/midnight)\n  open        Open application\n  neofetch    System info display\n  calc        Calculator\n  history     Command history\n  exit        Close terminal\n`,

      ls: () => {
        const dir = this.resolveDir(this.cwd);
        if (!dir || !dir.children) return `ls: cannot access '${this.cwd}': Not a directory\n`;
        return Object.entries(dir.children).map(([name, item]) => {
          const prefix = item.type === 'dir' ? '\x1b[34m' : '';
          const suffix = item.type === 'dir' ? '/\x1b[0m' : '';
          return `${prefix}${name}${suffix}`;
        }).join('  ') + '\n';
      },

      cd: () => {
        const target = args[0] || '~';
        if (target === '~' || target === '/') { this.cwd = '~'; return ''; }
        if (target === '..') {
          if (this.cwd !== '~') {
            const parts = this.cwd.split('/');
            parts.pop();
            this.cwd = parts.join('/') || '~';
          }
          return '';
        }
        const dir = this.resolveDir(this.cwd);
        if (dir && dir.children && dir.children[target] && dir.children[target].type === 'dir') {
          this.cwd = this.cwd === '~' ? `~/${target}` : `${this.cwd}/${target}`;
          return '';
        }
        return `cd: ${target}: No such directory\n`;
      },

      pwd: () => this.cwd.replace('~', this.env.HOME) + '\n',

      cat: () => {
        if (!args[0]) return 'cat: missing file operand\n';
        const file = this.resolveFile(args[0]);
        if (file && file.type === 'file') return file.content + '\n';
        return `cat: ${args[0]}: No such file\n`;
      },

      echo: () => args.join(' ') + '\n',

      mkdir: () => {
        if (!args[0]) return 'mkdir: missing operand\n';
        const dir = this.resolveDir(this.cwd);
        if (dir && dir.children) {
          dir.children[args[0]] = { type: 'dir', children: {} };
        }
        return '';
      },

      touch: () => {
        if (!args[0]) return 'touch: missing operand\n';
        const dir = this.resolveDir(this.cwd);
        if (dir && dir.children) {
          if (!dir.children[args[0]]) {
            dir.children[args[0]] = { type: 'file', content: '' };
          }
        }
        return '';
      },

      clear: () => { this.outputEl.innerHTML = ''; return ''; },
      whoami: () => this.env.USER + '\n',
      date: () => new Date().toString() + '\n',
      uname: () => 'ArcanisOS 1.0 arcanis-desktop x86_64\n',

      theme: () => {
        const theme = args[0] || 'dark';
        if (['dark', 'light', 'midnight'].includes(theme)) {
          document.documentElement.setAttribute('data-theme', theme);
          localStorage.setItem('arcanis-theme', theme);
          return `Theme set to ${theme}\n`;
        }
        return 'Usage: theme [dark|light|midnight]\n';
      },

      open: () => {
        const app = args[0] || 'terminal';
        window.arcanisDesktop.launchApp(app);
        return `Opening ${app}...\n`;
      },

      neofetch: () => {
        return `
\x1b[35m       _         _        \x1b[0m  ${this.env.USER}@arcanis
\x1b[35m      / \\   ___ / |       \x1b[0m  ─────────────────
\x1b[35m     / _ \\ / _ \\ |        \x1b[0m  OS: ArcanisOS 1.0
\x1b[35m    / ___ \\  __/ |___     \x1b[0m  Shell: ${this.env.SHELL}
\x1b[35m   /_/   \\_\\___|_____|    \x1b[0m  Terminal: ArcanisTerminal
\x1b[35m                          \x1b[0m  Theme: ${document.documentElement.getAttribute('data-theme')}
\x1b[35m                          \x1b[0m  Resolution: ${window.innerWidth}x${window.innerHeight}
`;
      },

      calc: () => {
        if (!args.length) return 'Usage: calc <expression>\n';
        try {
          const expr = args.join('').replace(/[^0-9+\-*/().]/g, '');
          const result = Function('"use strict"; return (' + expr + ')')();
          return result + '\n';
        } catch (e) {
          return 'calc: invalid expression\n';
        }
      },

      history: () => this.history.map((c, i) => `  ${i + 1}  ${c}`).join('\n') + '\n',

      exit: () => {
        window.arcanisDesktop.windowManager.closeWindow(this.winId);
        return '';
      },
    };

    const handler = commands[cmd];
    if (handler) {
      const output = handler();
      if (output) this.print(output);
    } else {
      this.print(`arcanis: command not found: ${cmd}\n`);
    }

    const promptEl = this.outputEl.parentElement?.querySelector('.terminal-prompt');
    if (promptEl) promptEl.textContent = this.getPrompt();
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

  resolveFile(name) {
    const dir = this.resolveDir(this.cwd);
    if (dir && dir.children && dir.children[name]) return dir.children[name];
    return null;
  }

  autocomplete() {
    const val = this.inputEl.value;
    const parts = val.split(/\s+/);
    const last = parts[parts.length - 1];
    const dir = this.resolveDir(this.cwd);
    if (!dir || !dir.children) return;
    const matches = Object.keys(dir.children).filter((n) => n.startsWith(last));
    if (matches.length === 1) {
      parts[parts.length - 1] = matches[0];
      this.inputEl.value = parts.join(' ');
    }
  }
}
