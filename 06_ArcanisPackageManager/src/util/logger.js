'use strict';

const LOG_LEVELS = { silent: 0, error: 1, warn: 2, info: 3, debug: 4 };

class Logger {
  constructor(level = 'info') {
    this.level = LOG_LEVELS[level] ?? LOG_LEVELS.info;
  }

  setLevel(level) {
    this.level = LOG_LEVELS[level] ?? this.level;
  }

  error(...args) {
    if (this.level >= LOG_LEVELS.error) {
      console.error(`[ERROR]`, ...args);
    }
  }

  warn(...args) {
    if (this.level >= LOG_LEVELS.warn) {
      console.warn(`[WARN]`, ...args);
    }
  }

  info(...args) {
    if (this.level >= LOG_LEVELS.info) {
      console.log(...args);
    }
  }

  debug(...args) {
    if (this.level >= LOG_LEVELS.debug) {
      console.debug(`[DEBUG]`, ...args);
    }
  }

  success(...args) {
    if (this.level >= LOG_LEVELS.info) {
      console.log(`[OK]`, ...args);
    }
  }

  step(message) {
    if (this.level >= LOG_LEVELS.info) {
      console.log(`\n  >> ${message}`);
    }
  }
}

module.exports = { Logger, LOG_LEVELS };
