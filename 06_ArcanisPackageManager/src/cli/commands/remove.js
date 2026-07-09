'use strict';

exports.handler = async function remove(pm, args, options, logger) {
  if (args.length === 0) {
    logger.error('Usage: arcanis remove <package>');
    process.exit(1);
  }

  const packageName = args[0];
  logger.step(`Removing ${packageName}...`);

  const result = await pm.remove(packageName);
  if (result.status === 'removed') {
    logger.success(`Removed ${packageName}`);
  } else if (result.status === 'not-found') {
    logger.warn(`Package "${packageName}" is not installed`);
  }
};
