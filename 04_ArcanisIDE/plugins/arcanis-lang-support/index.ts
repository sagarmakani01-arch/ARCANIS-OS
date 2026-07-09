import { PluginContext } from '../../src/api/types';
import { PluginAPI } from '../../src/api/PluginAPI';

interface ActivationContext extends PluginContext {
  api: PluginAPI;
}

export function activate(ctx: ActivationContext): void {
  ctx.log('ArcanisLang support activated!');

  ctx.globalState.set('arcanisLang.version', '0.1.0');
  ctx.globalState.set('arcanisLang.activatedAt', new Date().toISOString());

  const savedVersion = ctx.globalState.get<string>('arcanisLang.version');
  ctx.log(`Extension metadata saved: version=${savedVersion}`);

  ctx.subscriptions.push(
    ctx.api.commands.registerCommand('arcanisLang.defineSnippet', () => {
      ctx.log('Inserting ArcanisLang snippet...');
      ctx.api.ui.showNotification('ArcanisLang snippet template inserted.', 'info');
    })
  );

  ctx.subscriptions.push(
    ctx.api.commands.registerCommand('arcanisLang.formatDocument', () => {
      ctx.log('Formatting ArcanisLang document...');
      ctx.api.ui.showNotification('ArcanisLang document formatted.', 'info');
    })
  );

  ctx.subscriptions.push(
    ctx.api.commands.registerCommand('arcanisLang.runArcanisFile', () => {
      ctx.log('Running ArcanisLang file...');
      ctx.api.ui.showNotification('ArcanisLang file executed successfully.', 'info');
    })
  );
}

export function deactivate(): void {
  console.log('[ArcanisLang Support] Deactivated');
}
