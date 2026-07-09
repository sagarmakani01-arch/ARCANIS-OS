'use strict';

const { PackageManager } = require('./core/PackageManager');
const { RegistryClient } = require('./core/RegistryClient');
const { DependencyResolver } = require('./core/DependencyResolver');
const { PackageInstaller } = require('./core/PackageInstaller');
const { ManifestValidator } = require('./core/ManifestValidator');
const { PackageVerifier } = require('./security/PackageVerifier');
const { MalwareScanner } = require('./security/MalwareScanner');
const { PermissionManager } = require('./security/PermissionManager');
const { TrustedSourceManager } = require('./security/TrustedSourceManager');
const { Logger } = require('./util/logger');

module.exports = {
  PackageManager,
  RegistryClient,
  DependencyResolver,
  PackageInstaller,
  ManifestValidator,
  PackageVerifier,
  MalwareScanner,
  PermissionManager,
  TrustedSourceManager,
  Logger
};
