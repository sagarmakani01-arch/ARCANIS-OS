'use strict';

const path = require('path');

exports.handler = async function publish(pm, args, options, logger) {
  const packageDir = args[0] ? path.resolve(args[0]) : process.cwd();

  logger.step(`Preparing package from ${packageDir}...`);
  const result = await pm.publish(packageDir, options);

  if (result.success === false) {
    logger.error(`Publish failed: ${result.error}`);
    if (result.details) {
      for (const detail of result.details) {
        logger.error(`  - ${detail}`);
      }
    }
    process.exit(1);
  }

  logger.success(`Published ${result.name}@${result.version}`);
  logger.info(`  Registry: ${options.source || pm.config.registry?.default}`);
};
