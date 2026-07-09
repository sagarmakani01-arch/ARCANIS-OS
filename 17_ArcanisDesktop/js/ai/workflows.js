class WorkflowEngine {
  constructor() {
    this.workflows = [];
    this.loadWorkflows();
  }

  loadWorkflows() {
    const saved = localStorage.getItem('arcanis-workflows');
    if (saved) {
      try {
        this.workflows = JSON.parse(saved);
      } catch (e) {
        this.workflows = [];
      }
    }
  }

  saveWorkflows() {
    localStorage.setItem('arcanis-workflows', JSON.stringify(this.workflows));
  }

  createWorkflow(name, steps) {
    const workflow = {
      id: Date.now(),
      name,
      steps,
      created: new Date().toISOString(),
      enabled: true,
      runCount: 0,
    };
    this.workflows.push(workflow);
    this.saveWorkflows();
    return workflow;
  }

  deleteWorkflow(id) {
    this.workflows = this.workflows.filter((w) => w.id !== id);
    this.saveWorkflows();
  }

  toggleWorkflow(id) {
    const wf = this.workflows.find((w) => w.id === id);
    if (wf) {
      wf.enabled = !wf.enabled;
      this.saveWorkflows();
    }
  }

  async runWorkflow(id) {
    const wf = this.workflows.find((w) => w.id === id);
    if (!wf || !wf.enabled) return;

    wf.runCount++;
    this.saveWorkflows();

    for (const step of wf.steps) {
      await this.executeStep(step);
      if (step.delay) {
        await new Promise((r) => setTimeout(r, step.delay));
      }
    }

    window.arcanisDesktop.notifications.notify(
      'Workflow Complete',
      `"${wf.name}" finished successfully.`,
      'success'
    );
  }

  async executeStep(step) {
    const desktop = window.arcanisDesktop;
    switch (step.type) {
      case 'launch-app':
        desktop.launchApp(step.appId);
        break;
      case 'notification':
        desktop.notifications.notify(step.title || 'Workflow', step.message || '', step.notifType || 'info');
        break;
      case 'set-theme':
        document.documentElement.setAttribute('data-theme', step.theme);
        localStorage.setItem('arcanis-theme', step.theme);
        break;
      case 'close-all':
        desktop.windowManager.windows.forEach((_, id) => desktop.windowManager.closeWindow(id));
        break;
      case 'minimize-all':
        desktop.windowManager.windows.forEach((_, id) => desktop.windowManager.minimizeWindow(id));
        break;
      case 'ai-command':
        if (desktop.aiCenter) {
          desktop.aiCenter.processCommand(step.command);
        }
        break;
      case 'wait':
        await new Promise((r) => setTimeout(r, step.duration || 1000));
        break;
    }
  }

  getWorkflows() {
    return this.workflows;
  }

  getWorkflow(id) {
    return this.workflows.find((w) => w.id === id);
  }

  showWorkflowCreator() {
    const existing = document.getElementById('workflow-creator');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'workflow-creator';
    overlay.style.cssText = `
      position: fixed; inset: 0; background: rgba(0,0,0,0.5);
      z-index: 5000; display: flex; align-items: center; justify-content: center;
    `;

    const dialog = document.createElement('div');
    dialog.style.cssText = `
      background: var(--bg-secondary); border: 1px solid var(--border-color);
      border-radius: var(--radius-lg); width: 520px; max-height: 80vh;
      overflow-y: auto; padding: 24px; box-shadow: var(--shadow-lg);
    `;

    dialog.innerHTML = `
      <h2 style="font-size:18px;margin-bottom:16px;color:var(--text-primary)">Create Workflow</h2>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:13px;color:var(--text-secondary);margin-bottom:6px">Workflow Name</label>
        <input id="wf-name" type="text" placeholder="My Workflow" style="
          width:100%;padding:10px 12px;background:var(--bg-tertiary);border:1px solid var(--border-color);
          border-radius:var(--radius-md);color:var(--text-primary);font-size:13px;outline:none;
          font-family:var(--font-primary);
        ">
      </div>
      <div id="wf-steps" style="margin-bottom:16px">
        <label style="display:block;font-size:13px;color:var(--text-secondary);margin-bottom:8px">Steps</label>
      </div>
      <button id="wf-add-step" style="
        padding:8px 16px;background:var(--bg-tertiary);border:1px solid var(--border-color);
        border-radius:var(--radius-md);color:var(--text-secondary);cursor:pointer;font-size:12px;
        margin-bottom:16px;font-family:var(--font-primary);
      ">+ Add Step</button>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button id="wf-cancel" style="
          padding:8px 16px;background:var(--bg-tertiary);border:1px solid var(--border-color);
          border-radius:var(--radius-md);color:var(--text-secondary);cursor:pointer;font-size:13px;
          font-family:var(--font-primary);
        ">Cancel</button>
        <button id="wf-save" style="
          padding:8px 16px;background:var(--accent-gradient);border:none;
          border-radius:var(--radius-md);color:white;cursor:pointer;font-size:13px;font-weight:500;
          font-family:var(--font-primary);
        ">Create Workflow</button>
      </div>
    `;

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);

    let stepCount = 0;
    const stepsContainer = dialog.querySelector('#wf-steps');
    const addStepBtn = dialog.querySelector('#wf-add-step');

    const addStep = () => {
      stepCount++;
      const stepEl = document.createElement('div');
      stepEl.style.cssText = 'display:flex;gap:8px;margin-bottom:8px;align-items:center;';
      stepEl.innerHTML = `
        <select class="wf-step-type" style="
          flex:1;padding:8px;background:var(--bg-tertiary);border:1px solid var(--border-color);
          border-radius:var(--radius-sm);color:var(--text-primary);font-size:12px;
          font-family:var(--font-primary);
        ">
          <option value="launch-app">Launch App</option>
          <option value="notification">Send Notification</option>
          <option value="set-theme">Set Theme</option>
          <option value="close-all">Close All Windows</option>
          <option value="minimize-all">Minimize All</option>
          <option value="wait">Wait</option>
        </select>
        <input class="wf-step-config" type="text" placeholder="Config..." style="
          flex:2;padding:8px;background:var(--bg-tertiary);border:1px solid var(--border-color);
          border-radius:var(--radius-sm);color:var(--text-primary);font-size:12px;outline:none;
          font-family:var(--font-primary);
        ">
        <button class="wf-step-remove" style="
          width:28px;height:28px;background:transparent;border:1px solid var(--border-color);
          border-radius:var(--radius-sm);color:var(--text-muted);cursor:pointer;font-size:14px;
        ">&times;</button>
      `;
      stepEl.querySelector('.wf-step-remove').addEventListener('click', () => stepEl.remove());
      stepsContainer.appendChild(stepEl);
    };

    addStepBtn.addEventListener('click', addStep);
    addStep();

    dialog.querySelector('#wf-cancel').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });

    dialog.querySelector('#wf-save').addEventListener('click', () => {
      const name = dialog.querySelector('#wf-name').value.trim() || 'Untitled Workflow';
      const steps = [];
      stepsContainer.querySelectorAll('.wf-step-type').forEach((sel, i) => {
        const config = stepsContainer.querySelectorAll('.wf-step-config')[i].value.trim();
        const step = { type: sel.value };
        if (step.type === 'launch-app') step.appId = config || 'terminal';
        else if (step.type === 'notification') { step.title = 'Workflow'; step.message = config || 'Step executed'; }
        else if (step.type === 'set-theme') step.theme = config || 'dark';
        else if (step.type === 'wait') step.duration = parseInt(config) || 1000;
        steps.push(step);
      });
      this.createWorkflow(name, steps);
      overlay.remove();
      window.arcanisDesktop.notifications.notify('Workflow Created', `"${name}" is ready to run.`, 'success');
    });
  }
}
