'use strict';

exports.handler = async function install(pm, args, options, logger) {
  if (args.length === 0) {
    logger.error('Usage: arcanis install <package> [version]');
    process.exit(1);
  }

  const packageName = args[0];
  const constraint = args[1] || '*';

  logger.step(`Resolving ${packageName}@${constraint}...`);
  const result = await pm.install(packageName, constraint, options);

  if (result.success) {
    const installed = result.installed || [];
    const count = installed.filter(i => i.status === 'installed').length;
    const skipped = installed.filter(i => i.status === 'already-installed').length;
    logger.success(`Installed ${count} package(s)` + (skipped > 0 ? ` (${skipped} already up-to-date)` : ''));
    if (result.tree) {
      const flat = pm.resolver.flatten(result.tree);
      logger.info(`\n  Dependency tree:`);
      for (const pkg of flat) {
        const indent = '  '.repeat(pkg.depth + 1);
        logger.info(`${indent}${pkg.name}@${pkg.version}`);
      }
    }
  } else {
    logger.error(`Installation failed: ${result.error}`);
    if (result.scanResult) {
      logger.warn('Security scan flagged the package:');
      for (const finding of result.scanResult.findings || []) {
        logger.warn(`  [${finding.severity}] ${finding.description} (${finding.file})`);
      }
    }
    process.exit(1);
  }
};
