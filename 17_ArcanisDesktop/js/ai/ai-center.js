class AICenter {
  constructor() {
    this.panel = document.getElementById('ai-center');
    this.chat = document.getElementById('ai-chat');
    this.input = document.getElementById('ai-input');
    this.sendBtn = document.getElementById('ai-send');
    this.openBtn = document.getElementById('ai-center-btn');
    this.closeBtn = document.getElementById('ai-center-close');
    this.conversationHistory = [];
    this.init();
  }

  init() {
    this.openBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggle();
    });

    this.closeBtn.addEventListener('click', () => this.hide());

    this.sendBtn.addEventListener('click', () => this.sendMessage());

    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    document.addEventListener('click', (e) => {
      if (!this.panel.contains(e.target) && !this.openBtn.contains(e.target)) {
        this.hide();
      }
    });

    this.addAssistantMessage('Hello! I\'m ArcanisBrain, your AI assistant. I can help you manage your desktop, open applications, create workflows, and more. What would you like to do?');
  }

  toggle() {
    this.panel.classList.toggle('hidden');
    if (!this.panel.classList.contains('hidden')) {
      this.input.focus();
    }
  }

  show() {
    this.panel.classList.remove('hidden');
    this.input.focus();
  }

  hide() {
    this.panel.classList.add('hidden');
  }

  sendMessage() {
    const text = this.input.value.trim();
    if (!text) return;

    this.addUserMessage(text);
    this.input.value = '';

    this.conversationHistory.push({ role: 'user', content: text });

    this.showTyping();

    setTimeout(() => {
      this.removeTyping();
      const response = this.processCommand(text);
      this.addAssistantMessage(response);
      this.conversationHistory.push({ role: 'assistant', content: response });
    }, 600 + Math.random() * 800);
  }

  addUserMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'ai-message user';
    msg.innerHTML = `
      <div class="ai-avatar">U</div>
      <div class="ai-bubble">${this.escapeHtml(text)}</div>
    `;
    this.chat.appendChild(msg);
    this.scrollToBottom();
  }

  addAssistantMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'ai-message assistant';
    msg.innerHTML = `
      <div class="ai-avatar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
      </div>
      <div class="ai-bubble">${text}</div>
    `;
    this.chat.appendChild(msg);
    this.scrollToBottom();
  }

  showTyping() {
    const typing = document.createElement('div');
    typing.className = 'ai-message assistant';
    typing.id = 'ai-typing';
    typing.innerHTML = `
      <div class="ai-avatar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
      </div>
      <div class="ai-bubble"><div class="ai-typing"><span></span><span></span><span></span></div></div>
    `;
    this.chat.appendChild(typing);
    this.scrollToBottom();
  }

  removeTyping() {
    const typing = document.getElementById('ai-typing');
    if (typing) typing.remove();
  }

  scrollToBottom() {
    this.chat.scrollTop = this.chat.scrollHeight;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  processCommand(input) {
    const lower = input.toLowerCase().trim();

    // App launching
    if (lower.match(/^(open|launch|start|run)\s+(terminal|console|shell|cmd|powershell)/)) {
      window.arcanisDesktop.launchApp('terminal');
      return 'Opening Terminal for you.';
    }
    if (lower.match(/^(open|launch|start|run)\s+(file|files|manager|explorer|finder)/)) {
      window.arcanisDesktop.launchApp('file-manager');
      return 'Opening File Manager.';
    }
    if (lower.match(/^(open|launch|start|run)\s+(browser|web|chrome|firefox|edge)/)) {
      window.arcanisDesktop.launchApp('browser');
      return 'Opening Browser.';
    }
    if (lower.match(/^(open|launch|start|run)\s+(editor|text|notepad|code)/)) {
      window.arcanisDesktop.launchApp('text-editor');
      return 'Opening Text Editor.';
    }
    if (lower.match(/^(open|launch|start|run)\s+setting/)) {
      window.arcanisDesktop.launchApp('settings');
      return 'Opening Settings.';
    }

    // Theme switching
    if (lower.match(/(switch|change|set)\s+(theme|mode)\s+(to\s+)?(dark|midnight)/)) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('arcanis-theme', 'dark');
      return 'Theme changed to <code>dark</code>.';
    }
    if (lower.match(/(switch|change|set)\s+(theme|mode)\s+(to\s+)?light/)) {
      document.documentElement.setAttribute('data-theme', 'light');
      localStorage.setItem('arcanis-theme', 'light');
      return 'Theme changed to <code>light</code>.';
    }
    if (lower.match(/(switch|change|set)\s+(theme|mode)\s+(to\s+)?midnight/)) {
      document.documentElement.setAttribute('data-theme', 'midnight');
      localStorage.setItem('arcanis-theme', 'midnight');
      return 'Theme changed to <code>midnight</code>.';
    }

    // Notifications
    if (lower.match(/(show|open|view)\s+notif/)) {
      window.arcanisDesktop.notifications.togglePanel();
      return 'Showing notifications panel.';
    }
    if (lower.match(/clear\s+notif/)) {
      window.arcanisDesktop.notifications.clearAll();
      return 'All notifications cleared.';
    }
    if (lower.match(/(send|create|test)\s+notif/)) {
      window.arcanisDesktop.notifications.notify('Test Notification', 'This is a test from ArcanisBrain AI.', 'info');
      return 'Test notification sent!';
    }

    // Window management
    if (lower.match(/(minimize|hide)\s+(all|windows)/)) {
      window.arcanisDesktop.windowManager.windows.forEach((win, id) => {
        window.arcanisDesktop.windowManager.minimizeWindow(id);
      });
      return 'All windows minimized.';
    }
    if (lower.match(/(maximize|fullscreen)/)) {
      const wm = window.arcanisDesktop.windowManager;
      if (wm.activeWindow) {
        wm.toggleMaximize(wm.activeWindow);
        return 'Window maximized/restored.';
      }
      return 'No active window to maximize.';
    }
    if (lower.match(/(close|exit)\s+(all|windows)/)) {
      const ids = [...window.arcanisDesktop.windowManager.windows.keys()];
      ids.forEach((id) => window.arcanisDesktop.windowManager.closeWindow(id));
      return 'All windows closed.';
    }

    // Workspace
    if (lower.match(/(switch|go)\s+to\s+workspace\s+(\d)/)) {
      const num = parseInt(lower.match(/workspace\s+(\d)/)[1]) - 1;
      window.arcanisDesktop.workspace.switchWorkspace(num);
      return `Switched to Workspace ${num + 1}.`;
    }

    // Workflow
    if (lower.match(/(create|start|run|new)\s+workflow/)) {
      window.arcanisDesktop.workflows.showWorkflowCreator();
      return 'Opening Workflow Creator. You can build automated workflows from the dialog.';
    }
    if (lower.match(/(list|show)\s+workflow/)) {
      const wfs = window.arcanisDesktop.workflows.getWorkflows();
      if (wfs.length === 0) return 'No workflows created yet. Say <code>create workflow</code> to get started!';
      return `You have ${wfs.length} workflow(s): ${wfs.map((w) => `<code>${w.name}</code>`).join(', ')}.`;
    }

    // System info
    if (lower.match(/(system|device)\s+info/)) {
      const info = this.getSystemInfo();
      return `System Info:<br>${info}`;
    }
    if (lower.match(/what\s+time|current\s+time|what\'?s?\s+the\s+time/)) {
      return `Current time: <code>${new Date().toLocaleTimeString()}</code>`;
    }

    // Help
    if (lower.match(/^(help|what can you do|commands)/)) {
      return this.getHelpText();
    }

    // Workspace layout
    if (lower.match(/(show|get)\s+layout/)) {
      const layout = window.arcanisDesktop.workspace.getLayout();
      return `Current layout: Workspace "${this.workspaces?.[layout.currentWorkspace] || layout.currentWorkspace}" with open windows.`;
    }

    // Generic response
    return this.getSmartResponse(lower);
  }

  getHelpText() {
    return `Here's what I can do:<br><br>
    <strong>Apps:</strong> <code>open terminal</code>, <code>open files</code>, <code>open browser</code>, <code>open editor</code>, <code>open settings</code><br><br>
    <strong>Themes:</strong> <code>change theme to dark/light/midnight</code><br><br>
    <strong>Windows:</strong> <code>minimize all</code>, <code>maximize</code>, <code>close all</code><br><br>
    <strong>Workspaces:</strong> <code>switch to workspace 1-3</code><br><br>
    <strong>Workflows:</strong> <code>create workflow</code>, <code>list workflows</code><br><br>
    <strong>System:</strong> <code>system info</code>, <code>what time</code>, <code>show notifications</code>`;
  }

  getSystemInfo() {
    const nav = navigator;
    return `
      <code>Platform:</code> ${nav.platform}<br>
      <code>Language:</code> ${nav.language}<br>
      <code>Cores:</code> ${nav.hardwareConcurrency || 'Unknown'}<br>
      <code>Screen:</code> ${screen.width}x${screen.height}<br>
      <code>Theme:</code> ${document.documentElement.getAttribute('data-theme')}
    `;
  }

  getSmartResponse(input) {
    const responses = [
      `I understand you want to "${input}". Try <code>help</code> to see available commands.`,
      `I'm not sure how to handle that yet. Say <code>help</code> to see what I can do.`,
      `Interesting request! For now, I can help with app management, themes, workspaces, and workflows. Say <code>help</code> for details.`,
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  }
}
