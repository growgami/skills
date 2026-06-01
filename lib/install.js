'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

function targetDir() {
  return (
    process.env.CLAUDE_SKILLS_DIR ||
    path.join(os.homedir(), '.claude', 'skills')
  );
}

/**
 * Copy a single skill's entire source directory (including references/) into
 * <target>/<name>/ recursively. Replaces any existing install of that name.
 */
function installSkill(name, srcPath, target) {
  const dest = path.join(target, name);
  fs.rmSync(dest, { recursive: true, force: true });
  fs.mkdirSync(dest, { recursive: true });
  fs.cpSync(srcPath, dest, { recursive: true });
}

module.exports = { targetDir, installSkill };
