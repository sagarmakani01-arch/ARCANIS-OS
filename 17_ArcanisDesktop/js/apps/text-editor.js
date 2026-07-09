class TextEditorApp {
  constructor() {
    this.content = '';
    this.fileName = 'untitled.txt';
    this.modified = false;
  }

  getContent() {
    return `
      <div class="text-editor">
        <div class="te-toolbar">
          <button class="te-toolbar-btn" title="New File" onclick="window.arcanisDesktop.launchApp('text-editor')">📄</button>
          <button class="te-toolbar-btn te-save" title="Save">💾</button>
          <div class="te-toolbar-sep"></div>
          <button class="te-toolbar-btn te-undo" title="Undo">↩</button>
          <button class="te-toolbar-btn te-redo" title="Redo">↪</button>
          <div class="te-toolbar-sep"></div>
          <button class="te-toolbar-btn te-cut" title="Cut">✂</button>
          <button class="te-toolbar-btn te-copy" title="Copy">📋</button>
          <button class="te-toolbar-btn te-paste" title="Paste">📌</button>
          <div class="te-toolbar-sep"></div>
          <button class="te-toolbar-btn te-find" title="Find">🔍</button>
          <div style="flex:1"></div>
          <span class="te-filename" style="font-size:12px;color:var(--text-muted)">untitled.txt</span>
        </div>
        <textarea class="te-editor" id="te-editor" spellcheck="false" placeholder="Start typing..."></textarea>
        <div class="te-statusbar">
          <span class="te-pos">Ln 1, Col 1</span>
          <span class="te-info">UTF-8 | LF</span>
        </div>
      </div>
    `;
  }

  onReady(winElement, winId) {
    this.winId = winId;
    this.editor = winElement.querySelector('#te-editor');
    this.posEl = winElement.querySelector('.te-pos');
    this.filenameEl = winElement.querySelector('.te-filename');

    this.editor.addEventListener('input', () => {
      this.modified = true;
      this.updateTitle();
    });

    this.editor.addEventListener('keyup', () => this.updatePosition());
    this.editor.addEventListener('click', () => this.updatePosition());

    this.editor.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.editor.selectionStart;
        const end = this.editor.selectionEnd;
        this.editor.value = this.editor.value.substring(0, start) + '  ' + this.editor.value.substring(end);
        this.editor.selectionStart = this.editor.selectionEnd = start + 2;
      }
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        this.save();
      }
    });

    winElement.querySelector('.te-save').addEventListener('click', () => this.save());
    winElement.querySelector('.te-find').addEventListener('click', () => this.showFindDialog());

    this.editor.focus();
  }

  updatePosition() {
    const val = this.editor.value.substring(0, this.editor.selectionStart);
    const lines = val.split('\n');
    const ln = lines.length;
    const col = lines[lines.length - 1].length + 1;
    this.posEl.textContent = `Ln ${ln}, Col ${col}`;
  }

  updateTitle() {
    const prefix = this.modified ? '● ' : '';
    const title = `${prefix}${this.fileName}`;
    this.filenameEl.textContent = title;
    window.arcanisDesktop?.taskbar.updateTitle(this.winId, title);
  }

  save() {
    this.modified = false;
    this.updateTitle();
    const blob = new Blob([this.editor.value], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = this.fileName;
    a.click();
    URL.revokeObjectURL(a.href);
    window.arcanisDesktop?.notifications.notify('File Saved', `${this.fileName} saved successfully`, 'success');
  }

  showFindDialog() {
    const existing = document.getElementById('find-dialog');
    if (existing) existing.remove();

    const dialog = document.createElement('div');
    dialog.id = 'find-dialog';
    dialog.style.cssText = `
      position:absolute;top:40px;right:16px;background:var(--bg-elevated);
      border:1px solid var(--border-color);border-radius:var(--radius-md);
      padding:12px;display:flex;gap:8px;z-index:100;box-shadow:var(--shadow-md);
    `;
    dialog.innerHTML = `
      <input type="text" id="find-input" placeholder="Find..." style="
        padding:6px 10px;background:var(--bg-tertiary);border:1px solid var(--border-color);
        border-radius:var(--radius-sm);color:var(--text-primary);font-size:12px;outline:none;
        width:180px;font-family:var(--font-mono);
      ">
      <button id="find-next" style="
        padding:6px 10px;background:var(--accent-primary);border:none;
        border-radius:var(--radius-sm);color:white;cursor:pointer;font-size:12px;
      ">Find</button>
      <button id="find-close" style="
        padding:6px;background:transparent;border:1px solid var(--border-color);
        border-radius:var(--radius-sm);color:var(--text-muted);cursor:pointer;font-size:12px;
      ">&times;</button>
    `;

    this.winElement.querySelector('.text-editor').appendChild(dialog);

    const input = dialog.querySelector('#find-input');
    input.focus();

    dialog.querySelector('#find-next').addEventListener('click', () => this.findNext(input.value));
    dialog.querySelector('#find-close').addEventListener('click', () => dialog.remove());
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.findNext(input.value);
      if (e.key === 'Escape') dialog.remove();
    });
  }

  findNext(query) {
    if (!query) return;
    const idx = this.editor.value.indexOf(query, this.editor.selectionEnd);
    if (idx !== -1) {
      this.editor.selectionStart = idx;
      this.editor.selectionEnd = idx + query.length;
      this.editor.focus();
    }
  }
}
