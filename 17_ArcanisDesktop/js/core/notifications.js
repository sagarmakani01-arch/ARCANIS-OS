class NotificationSystem {
  constructor() {
    this.notifications = [];
    this.panel = document.getElementById('notifications-panel');
    this.listEl = document.getElementById('notifications-list');
    this.badgeEl = document.getElementById('notification-badge');
    this.btn = document.getElementById('notifications-btn');
    this.clearBtn = document.getElementById('clear-notifs');
    this.toastContainer = null;
    this.init();
  }

  init() {
    this.toastContainer = document.createElement('div');
    this.toastContainer.className = 'toast-container';
    document.getElementById('desktop').appendChild(this.toastContainer);

    this.btn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.togglePanel();
    });

    this.clearBtn.addEventListener('click', () => this.clearAll());

    document.addEventListener('click', (e) => {
      if (!this.panel.contains(e.target) && !this.btn.contains(e.target)) {
        this.hidePanel();
      }
    });
  }

  notify(title, body, type = 'info', options = {}) {
    const notif = {
      id: Date.now(),
      title,
      body,
      type,
      time: new Date(),
      read: false,
    };
    this.notifications.unshift(notif);
    this.updateBadge();
    this.renderList();

    if (options.toast !== false) {
      this.showToast(title, body, type);
    }
    return notif;
  }

  showToast(title, message, type = 'info') {
    const icons = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
      </div>
      <button class="toast-close">&times;</button>
    `;
    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.classList.add('removing');
      setTimeout(() => toast.remove(), 300);
    });
    this.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('removing');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  updateBadge() {
    const unread = this.notifications.filter((n) => !n.read).length;
    this.badgeEl.textContent = unread;
    this.badgeEl.classList.toggle('hidden', unread === 0);
  }

  renderList() {
    if (this.notifications.length === 0) {
      this.listEl.innerHTML = '<div class="notif-empty">No notifications</div>';
      return;
    }
    this.listEl.innerHTML = this.notifications.map((n) => {
      const timeStr = this.formatTime(n.time);
      return `
        <div class="notification-item" data-id="${n.id}">
          <div class="notif-icon ${n.type}">${this.getTypeIcon(n.type)}</div>
          <div class="notif-content">
            <div class="notif-title">${n.title}</div>
            <div class="notif-body">${n.body}</div>
            <div class="notif-time">${timeStr}</div>
          </div>
        </div>
      `;
    }).join('');

    this.listEl.querySelectorAll('.notification-item').forEach((el) => {
      el.addEventListener('click', () => {
        const id = parseInt(el.dataset.id);
        const notif = this.notifications.find((n) => n.id === id);
        if (notif) notif.read = true;
        this.updateBadge();
      });
    });
  }

  getTypeIcon(type) {
    const icons = { info: 'ℹ', success: '✓', warning: '!', error: '✕' };
    return icons[type] || icons.info;
  }

  formatTime(date) {
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  clearAll() {
    this.notifications = [];
    this.updateBadge();
    this.renderList();
  }

  togglePanel() {
    this.panel.classList.toggle('hidden');
    if (!this.panel.classList.contains('hidden')) {
      this.renderList();
    }
  }

  hidePanel() {
    this.panel.classList.add('hidden');
  }
}
