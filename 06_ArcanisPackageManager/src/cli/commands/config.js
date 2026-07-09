'use strict';

exports.handler = async function config(pm, args, options, logger) {
  if (args.length === 0) {
    logger.info('\n  Current configuration:');
    logger.info(`  ${JSON.stringify(pm.config, null, 4)}`);
    return;
  }

  if (args.length === 2) {
    const [key, value] = args;
    const keys = key.split('.');

    let target = pm.config;
    for (let i = 0; i < keys.length - 1; i++) {
      if (!target[keys[i]]) target[keys[i]] = {};
      target = target[keys[i]];
    }

    try {
      target[keys[keys.length - 1]] = JSON.parse(value);
    } catch {
      target[keys[keys.length - 1]] = value;
    }

    const fs = require('fs');
    const path = require('path');
    const configPath = path.join(pm.projectRoot, '.arcanis', 'config.json');
    fs.writeFileSync(configPath, JSON.stringify(pm.config, null, 2), 'utf-8');
    logger.success(`Set ${key} = ${target[keys[keys.length - 1]]}`);
    return;
  }

  logger.error('Usage: arcanis config <key> <value>');
  logger.info('  Examples:');
  logger.info('    arcanis config registry.default https://my-registry.com');
  logger.info('    arcanis config security.strictMode true');
};
