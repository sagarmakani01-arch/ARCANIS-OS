#!/usr/bin/env node

'use strict';

const path = require('path');
const { PackageManager } = require('../core/PackageManager');
const { Logger } = require('../util/logger');
const { ManifestValidator } = require('../core/ManifestValidator');

const logger = new Logger('info');

const commands = {
  install: require('./commands/install'),
  remove: require('./commands/remove'),
  update: require('./commands/update'),
  publish: require('./commands/publish'),
  search: require('./commands/search'),
  verify: require('./commands/verify'),
  list: require('./commands/list'),
  config: require('./commands/config')
};

function showHelp() {
  console.log(`
  Arcanis Package Manager v1.0.0

  Usage: arcanis <command> [options]

  Commands:
    install   <package> [version]    Install a package
    remove    <package>              Remove a package
    update    <package> [version]    Update a package
    list                             List installed packages
    publish   [directory]            Publish a package
    search    <query>                Search the registry
    verify    <package>              Verify package integrity
    config    <key> <value>          Set configuration

  Options:
    --source <url>       Specify registry source
    --force              Force operation
    --verbose            Enable verbose logging
    --help               Show this help
    --version            Show version

  Examples:
    arcanis install @arcanis/core
    arcanis install lodash ^4.0.0 --source https://my-registry.com
    arcanis publish ./my-package
    arcanis verify @arcanis/core
    arcanis search "ai skill"
`);
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
    showHelp();
    return;
  }

  if (args[0] === '--version' || args[0] === '-v') {
    const pkg = require('../../package.json');
    console.log(pkg.version);
    return;
  }

  const command = args[0];
  const commandArgs = args.slice(1).filter(a => !a.startsWith('--'));
  const options = {};

  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--source' && args[i + 1]) {
      options.source = args[++i];
    } else if (args[i] === '--force') {
      options.force = true;
    } else if (args[i] === '--verbose') {
      logger.setLevel('debug');
    }
  }

  if (!commands[command]) {
    logger.error(`Unknown command: ${command}`);
    console.log(`\n  Run "arcanis --help" for available commands.\n`);
    process.exit(1);
  }

  try {
    const pm = new PackageManager({ projectRoot: process.cwd() });
    await commands[command].handler(pm, commandArgs, options, logger);
  } catch (err) {
    logger.error(`${err.name || 'Error'}: ${err.message}`);
    if (err.details) {
      logger.debug('Details:', JSON.stringify(err.details, null, 2));
    }
    process.exit(1);
  }
}

if (require.main === module) {
  main().catch(err => {
    logger.error('Fatal:', err.message);
    process.exit(1);
  });
}

module.exports = { main, commands, showHelp };
