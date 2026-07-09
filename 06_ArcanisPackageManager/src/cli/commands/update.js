'use strict';

exports.handler = async function update(pm, args, options, logger) {
  if (args.length === 0) {
    logger.error('Usage: arcanis update <package> [version]');
    process.exit(1);
  }

  const packageName = args[0];
  const constraint = args[1] || '*';

  logger.step(`Updating ${packageName} to ${constraint}...`);
  const result = await pm.update(packageName, constraint, options);

  if (result.success) {
    const installed = result.installed || [];
    const updated = installed.filter(i => i.status === 'installed').length;
    logger.success(`Updated ${packageName} (${updated} package(s) changed)`);
  } else {
    logger.error(`Update failed: ${result.error}`);
    process.exit(1);
  }
};
