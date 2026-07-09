import { PluginContext, IDisposable } from '../../src/api/types';
import { PluginAPI } from '../../src/api/PluginAPI';

interface ActivationContext extends PluginContext {
  api: PluginAPI;
}

export function activate(ctx: ActivationContext): void {
  ctx.log('Sample plugin activated!');

  ctx.workspaceState.set('sample.greeting', 'Hello');
  const greeting = ctx.workspaceState.get<string>('sample.greeting');
  ctx.log(`Retrieved greeting from workspace state: ${greeting}`);

  ctx.subscriptions.push(
    ctx.api.commands.registerCommand('sample.helloWorld', () => {
      ctx.api.ui.showNotification('Hello from Sample Plugin!', 'info');
      ctx.log('Executed sample.helloWorld command');
    })
  );

  ctx.subscriptions.push(
    ctx.api.commands.registerCommand('sample.showTime', () => {
      const now = new Date().toLocaleTimeString();
      ctx.api.ui.showNotification(`Current time: ${now}`, 'info');
      ctx.log(`Current time: ${now}`);
    })
  );

  ctx.subscriptions.push(
    ctx.api.commands.registerCommand('sample.countLines', () => {
      ctx.log('Counting lines...');
      const doc = ctx.api.editor.getActiveDocument();
      if (doc) {
        ctx.api.ui.showNotification(`Active document "${doc.fileName}" has ${doc.lineCount} lines.`, 'info');
      } else {
        ctx.api.ui.showNotification('No active document open.', 'warning');
      }
    })
  );

  const disposable = ctx.api.events.on('plugin:loaded', (payload) => {
    ctx.log(`Other plugin loaded: ${payload.name} v${payload.version}`);
  });
  ctx.subscriptions.push(disposable);
}

export function deactivate(): void {
  console.log('[Sample Plugin] Deactivated — releasing resources');
}
