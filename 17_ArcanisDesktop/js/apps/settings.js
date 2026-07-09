class SettingsApp {
  constructor() {
    this.currentSection = 'appearance';
  }

  getContent() {
    return `
      <div class="settings-app">
        <div class="settings-sidebar">
          <div class="settings-nav-item active" data-section="appearance">
            <span>🎨</span> Appearance
          </div>
          <div class="settings-nav-item" data-section="desktop">
            <span>🖥️</span> Desktop
          </div>
          <div class="settings-nav-item" data-section="notifications">
            <span>🔔</span> Notifications
          </div>
          <div class="settings-nav-item" data-section="ai">
            <span>🤖</span> AI Assistant
          </div>
          <div class="settings-nav-item" data-section="workspaces">
            <span>📐</span> Workspaces
          </div>
          <div class="settings-nav-item" data-section="about">
            <span>ℹ️</span> About
          </div>
        </div>
        <div class="settings-content" id="settings-content"></div>
      </div>
    `;
  }

  onReady(winElement) {
    this.winElement = winElement;
    this.contentEl = winElement.querySelector('#settings-content');

    winElement.querySelectorAll('.settings-nav-item').forEach((item) => {
      item.addEventListener('click', () => {
        winElement.querySelectorAll('.settings-nav-item').forEach((i) => i.classList.remove('active'));
        item.classList.add('active');
        this.currentSection = item.dataset.section;
        this.renderSection();
      });
    });

    this.renderSection();
  }

  renderSection() {
    const sections = {
      appearance: this.renderAppearance.bind(this),
      desktop: this.renderDesktop.bind(this),
      notifications: this.renderNotifications.bind(this),
      ai: this.renderAI.bind(this),
      workspaces: this.renderWorkspaces.bind(this),
      about: this.renderAbout.bind(this),
    };
    const renderer = sections[this.currentSection];
    if (renderer) this.contentEl.innerHTML = renderer();
    this.setupToggleEvents();
  }

  renderAppearance() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    return `
      <div class="settings-section">
        <h2>Appearance</h2>
        <p>Customize the look and feel of your desktop.</p>

        <div class="setting-row">
          <div>
            <div class="setting-label">Theme</div>
            <div class="setting-desc">Choose your preferred color scheme</div>
          </div>
        </div>
        <div class="theme-grid">
          <div class="theme-option ${currentTheme === 'dark' ? 'active' : ''}" data-theme="dark">
            <div class="theme-preview" style="background:linear-gradient(135deg,#0a0a0f,#1a1a2e)"></div>
            <div class="theme-name">Dark</div>
          </div>
          <div class="theme-option ${currentTheme === 'light' ? 'active' : ''}" data-theme="light">
            <div class="theme-preview" style="background:linear-gradient(135deg,#f0f0f5,#e8e8f0)"></div>
            <div class="theme-name">Light</div>
          </div>
          <div class="theme-option ${currentTheme === 'midnight' ? 'active' : ''}" data-theme="midnight">
            <div class="theme-preview" style="background:linear-gradient(135deg,#000000,#111118)"></div>
            <div class="theme-name">Midnight</div>
          </div>
        </div>

        <div class="setting-row" style="margin-top:20px">
          <div>
            <div class="setting-label">Accent Color</div>
            <div class="setting-desc">Primary accent throughout the UI</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;margin-top:12px">
          <div class="color-swatch" style="width:32px;height:32px;border-radius:50%;background:#7c5cff;cursor:pointer;border:2px solid var(--border-active)" data-color="#7c5cff"></div>
          <div class="color-swatch" style="width:32px;height:32px;border-radius:50%;background:#e74c3c;cursor:pointer;border:2px solid transparent" data-color="#e74c3c"></div>
          <div class="color-swatch" style="width:32px;height:32px;border-radius:50%;background:#2ecc71;cursor:pointer;border:2px solid transparent" data-color="#2ecc71"></div>
          <div class="color-swatch" style="width:32px;height:32px;border-radius:50%;background:#f39c12;cursor:pointer;border:2px solid transparent" data-color="#f39c12"></div>
          <div class="color-swatch" style="width:32px;height:32px;border-radius:50%;background:#3498db;cursor:pointer;border:2px solid transparent" data-color="#3498db"></div>
        </div>
      </div>
    `;
  }

  renderDesktop() {
    return `
      <div class="settings-section">
        <h2>Desktop</h2>
        <p>Configure desktop behavior and layout.</p>

        <div class="setting-row">
          <div>
            <div class="setting-label">Show Desktop Icons</div>
            <div class="setting-desc">Display icons on the desktop</div>
          </div>
          <div class="toggle active" data-setting="show-icons"></div>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Icon Size</div>
            <div class="setting-desc">Size of desktop icons</div>
          </div>
          <select style="padding:6px 10px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:var(--radius-sm);color:var(--text-primary);font-size:12px">
            <option>Small</option>
            <option selected>Medium</option>
            <option>Large</option>
          </select>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Wallpaper</div>
            <div class="setting-desc">Change desktop background</div>
          </div>
          <button style="padding:6px 12px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:var(--radius-sm);color:var(--text-secondary);cursor:pointer;font-size:12px;font-family:var(--font-primary)">Choose</button>
        </div>
      </div>
    `;
  }

  renderNotifications() {
    return `
      <div class="settings-section">
        <h2>Notifications</h2>
        <p>Manage notification preferences.</p>

        <div class="setting-row">
          <div>
            <div class="setting-label">Enable Notifications</div>
            <div class="setting-desc">Show system notifications</div>
          </div>
          <div class="toggle active" data-setting="enable-notifs"></div>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Toast Notifications</div>
            <div class="setting-desc">Show toast popups for events</div>
          </div>
          <div class="toggle active" data-setting="toast-notifs"></div>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Sound</div>
            <div class="setting-desc">Play sound for notifications</div>
          </div>
          <div class="toggle" data-setting="notif-sound"></div>
        </div>
      </div>
    `;
  }

  renderAI() {
    return `
      <div class="settings-section">
        <h2>AI Assistant</h2>
        <p>Configure ArcanisBrain AI settings.</p>

        <div class="setting-row">
          <div>
            <div class="setting-label">AI Command Center</div>
            <div class="setting-desc">Enable natural language commands</div>
          </div>
          <div class="toggle active" data-setting="ai-enabled"></div>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Smart Suggestions</div>
            <div class="setting-desc">AI-powered contextual suggestions</div>
          </div>
          <div class="toggle active" data-setting="ai-suggestions"></div>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Automated Workflows</div>
            <div class="setting-desc">Allow AI to run workflow automations</div>
          </div>
          <div class="toggle active" data-setting="ai-workflows"></div>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Voice Input</div>
            <div class="setting-desc">Use microphone for AI commands</div>
          </div>
          <div class="toggle" data-setting="ai-voice"></div>
        </div>
      </div>
    `;
  }

  renderWorkspaces() {
    return `
      <div class="settings-section">
        <h2>Workspaces</h2>
        <p>Manage virtual desktops.</p>

        <div class="setting-row">
          <div>
            <div class="setting-label">Workspace Count</div>
            <div class="setting-desc">Number of virtual desktops (1-9)</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <button class="ws-count-btn" data-action="decrease" style="width:28px;height:28px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:var(--radius-sm);color:var(--text-primary);cursor:pointer;font-size:14px">−</button>
            <span id="ws-count" style="font-size:14px;min-width:20px;text-align:center">3</span>
            <button class="ws-count-btn" data-action="increase" style="width:28px;height:28px;background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:var(--radius-sm);color:var(--text-primary);cursor:pointer;font-size:14px">+</button>
          </div>
        </div>
        <div class="setting-row">
          <div>
            <div class="setting-label">Switch Animations</div>
            <div class="setting-desc">Animate workspace transitions</div>
          </div>
          <div class="toggle active" data-setting="ws-animations"></div>
        </div>
      </div>
    `;
  }

  renderAbout() {
    return `
      <div class="settings-section">
        <h2>About ArcanisDesktop</h2>
        <p>AI-native desktop experience.</p>

        <div style="text-align:center;padding:32px 0">
          <div style="font-size:48px;margin-bottom:16px">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" stroke-width="1.5"><polygon points="12,2 22,12 12,22 2,12"/></svg>
          </div>
          <h3 style="font-size:20px;margin-bottom:4px">ArcanisDesktop</h3>
          <p style="color:var(--text-muted);font-size:13px">Version 1.0.0</p>
          <p style="color:var(--text-muted);font-size:12px;margin-top:8px">AI-native desktop experience powered by ArcanisBrain</p>
        </div>

        <div class="setting-row">
          <div class="setting-label">Components</div>
          <div style="font-size:13px;color:var(--text-secondary)">
            <div>ArcanisUI v1.0</div>
            <div>ArcanisShell v1.0</div>
            <div>ArcanisBrain v1.0</div>
          </div>
        </div>
        <div class="setting-row">
          <div class="setting-label">Platform</div>
          <div style="font-size:13px;color:var(--text-secondary)">${navigator.platform}</div>
        </div>
      </div>
    `;
  }

  setupToggleEvents() {
    this.contentEl.querySelectorAll('.toggle').forEach((toggle) => {
      toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        const setting = toggle.dataset.setting;
        const value = toggle.classList.contains('active');
        localStorage.setItem(`arcanis-${setting}`, value);
        window.arcanisDesktop?.notifications.notify('Settings', `${setting} ${value ? 'enabled' : 'disabled'}`, 'info', { toast: true });
      });
    });

    this.contentEl.querySelectorAll('.theme-option').forEach((opt) => {
      opt.addEventListener('click', () => {
        const theme = opt.dataset.theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('arcanis-theme', theme);
        this.contentEl.querySelectorAll('.theme-option').forEach((o) => o.classList.remove('active'));
        opt.classList.add('active');
        window.arcanisDesktop?.notifications.notify('Theme', `Changed to ${theme}`, 'info', { toast: true });
      });
    });

    this.contentEl.querySelectorAll('.color-swatch').forEach((swatch) => {
      swatch.addEventListener('click', () => {
        const color = swatch.dataset.color;
        document.documentElement.style.setProperty('--accent-primary', color);
        this.contentEl.querySelectorAll('.color-swatch').forEach((s) => s.style.borderColor = 'transparent');
        swatch.style.borderColor = 'var(--border-active)';
      });
    });
  }
}
