class BrowserApp {
  constructor() {
    this.tabs = [{ id: 1, title: 'New Tab', url: '' }];
    this.activeTab = 1;
    this.nextTabId = 2;
    this.history = [];
  }

  getContent() {
    return `
      <div class="browser-app">
        <div class="browser-toolbar">
          <button class="browser-nav-btn" id="browser-back" title="Back">◀</button>
          <button class="browser-nav-btn" id="browser-forward" title="Forward">▶</button>
          <button class="browser-nav-btn" id="browser-refresh" title="Refresh">⟳</button>
          <button class="browser-nav-btn" id="browser-home" title="Home">🏠</button>
          <div class="browser-url-bar">
            <span style="color:var(--text-muted)">🔒</span>
            <input type="text" id="browser-url" placeholder="Search or enter URL...">
          </div>
          <button class="browser-nav-btn" id="browser-new-tab" title="New Tab">+</button>
        </div>
        <div class="browser-content" id="browser-content">
          <div class="browser-blank">
            <div class="browser-blank-logo">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            </div>
            <div class="browser-blank-search">
              <input type="text" id="browser-search" placeholder="Search the web or enter URL...">
            </div>
          </div>
        </div>
      </div>
    `;
  }

  onReady(winElement) {
    this.winElement = winElement;
    this.contentEl = winElement.querySelector('#browser-content');
    this.urlInput = winElement.querySelector('#browser-url');
    this.searchInput = winElement.querySelector('#browser-search');

    winElement.querySelector('#browser-back').addEventListener('click', () => this.goBack());
    winElement.querySelector('#browser-forward').addEventListener('click', () => this.goForward());
    winElement.querySelector('#browser-refresh').addEventListener('click', () => this.refresh());
    winElement.querySelector('#browser-home').addEventListener('click', () => this.goHome());
    winElement.querySelector('#browser-new-tab').addEventListener('click', () => this.newTab());

    const navigate = (input) => {
      const url = input.value.trim();
      if (url) this.navigate(url);
      input.value = '';
    };

    this.urlInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') navigate(this.urlInput);
    });
    this.searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') navigate(this.searchInput);
    });
  }

  navigate(input) {
    let url = input;
    if (!url.match(/^https?:\/\//)) {
      if (url.includes('.') && !url.includes(' ')) {
        url = 'https://' + url;
      } else {
        url = `https://www.google.com/search?q=${encodeURIComponent(url)}`;
      }
    }

    this.urlInput.value = url;
    this.history.push(url);
    this.contentEl.innerHTML = `<iframe src="${url}" sandbox="allow-same-origin allow-scripts allow-forms allow-popups"></iframe>`;
  }

  goBack() {
    if (this.history.length > 1) {
      this.history.pop();
      const url = this.history[this.history.length - 1];
      this.urlInput.value = url;
      this.contentEl.innerHTML = `<iframe src="${url}" sandbox="allow-same-origin allow-scripts allow-forms allow-popups"></iframe>`;
    }
  }

  goForward() {
  }

  refresh() {
    const url = this.urlInput.value;
    if (url) {
      this.contentEl.innerHTML = `<iframe src="${url}" sandbox="allow-same-origin allow-scripts allow-forms allow-popups"></iframe>`;
    }
  }

  goHome() {
    this.urlInput.value = '';
    this.contentEl.innerHTML = `
      <div class="browser-blank">
        <div class="browser-blank-logo">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        </div>
        <div class="browser-blank-search">
          <input type="text" id="browser-search" placeholder="Search the web or enter URL...">
        </div>
      </div>
    `;
    this.searchInput = this.contentEl.querySelector('#browser-search');
    this.searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.navigate(this.searchInput.value);
    });
  }

  newTab() {
    this.goHome();
  }
}
