'use strict';

exports.handler = async function search(pm, args, options, logger) {
  if (args.length === 0) {
    logger.error('Usage: arcanis search <query>');
    process.exit(1);
  }

  const query = args.join(' ');
  logger.step(`Searching for "${query}"...`);

  const results = await pm.search(query);
  if (!results || results.length === 0) {
    logger.info('No packages found.');
    return;
  }

  logger.info(`\n  Found ${results.length} package(s):\n`);
  for (const pkg of results) {
    const name = pkg.name.padEnd(30);
    const version = (pkg.version || '').padEnd(12);
    const desc = pkg.description || '';
    logger.info(`  ${name} ${version} ${desc}`);
  }
};
