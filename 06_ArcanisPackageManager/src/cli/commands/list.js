'use strict';

exports.handler = async function list(pm, args, options, logger) {
  logger.step('Installed packages:');
  const packages = await pm.list();

  if (packages.length === 0) {
    logger.info('  No packages installed.');
    return;
  }

  logger.info('');
  for (const pkg of packages) {
    const name = `${pkg.name}`.padEnd(30);
    const version = `${pkg.version}`.padEnd(12);
    const deps = pkg.dependencies ? Object.keys(pkg.dependencies).length : 0;
    const installed = pkg.installedAt ? new Date(pkg.installedAt).toLocaleDateString() : '?';
    logger.info(`  ${name} ${version} deps:${deps}  installed:${installed}`);
  }
  logger.info(`\n  Total: ${packages.length} package(s)`);
};
