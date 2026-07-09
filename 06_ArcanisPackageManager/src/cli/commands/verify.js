'use strict';

exports.handler = async function verify(pm, args, options, logger) {
  if (args.length === 0) {
    const list = await pm.list();
    if (list.length === 0) {
      logger.info('No packages installed.');
      return;
    }
    logger.step('Verifying all installed packages...');
    let allValid = true;
    for (const pkg of list) {
      const result = await pm.verify(pkg.name);
      const status = result.valid ? '[OK]' : '[FAIL]';
      const extra = !result.valid && result.errors ? ` - ${result.errors.join(', ')}` : '';
      logger.info(`  ${status} ${pkg.name}@${pkg.version}${extra}`);
      if (!result.valid) allValid = false;
    }
    if (!allValid) process.exit(1);
    return;
  }

  const packageName = args[0];
  logger.step(`Verifying ${packageName}...`);

  const result = await pm.verify(packageName);
  if (result.valid) {
    logger.success(`${packageName} integrity verified`);
    if (result.warnings && result.warnings.length > 0) {
      for (const w of result.warnings) {
        logger.warn(`  ${w}`);
      }
    }
  } else {
    logger.error(`Verification failed for ${packageName}`);
    for (const err of result.errors || []) {
      logger.error(`  - ${err}`);
    }
    for (const w of result.warnings || []) {
      logger.warn(`  ${w}`);
    }
    process.exit(1);
  }
};
