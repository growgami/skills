'use strict';

const fs = require('fs');
const path = require('path');

// Root of this package (parent of lib/).
const PKG_ROOT = path.join(__dirname, '..');
const SKILLS_DIR = path.join(PKG_ROOT, 'skills');

function isSkillDir(dir) {
  return fs.existsSync(path.join(dir, 'SKILL.md'));
}

function listSubdirs(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => path.join(dir, e.name));
}

/**
 * Walk skills/ for skills at two depths:
 *   - Flat:   skills/<name>/SKILL.md
 *   - Nested: skills/<bundle>/skills/<name>/SKILL.md
 *
 * A directory counts as a skill only if it contains SKILL.md. A bundle's own
 * top-level README.md (with no SKILL.md) is never treated as a skill.
 *
 * Returns an object:
 *   { skills: Array<{ name, srcPath }>, collisions: Array<{ name, paths }> }
 * `skills` contains each bare name once (first source wins); any bare name
 * resolving to more than one source is reported in `collisions`.
 */
function discover() {
  const found = []; // { name, srcPath }

  for (const top of listSubdirs(SKILLS_DIR)) {
    if (isSkillDir(top)) {
      found.push({ name: path.basename(top), srcPath: top });
      continue;
    }
    const nestedSkillsDir = path.join(top, 'skills');
    if (fs.existsSync(nestedSkillsDir)) {
      for (const nested of listSubdirs(nestedSkillsDir)) {
        if (isSkillDir(nested)) {
          found.push({ name: path.basename(nested), srcPath: nested });
        }
      }
    }
  }

  const byName = new Map();
  for (const item of found) {
    if (!byName.has(item.name)) byName.set(item.name, []);
    byName.get(item.name).push(item.srcPath);
  }

  const skills = [];
  const collisions = [];
  for (const [name, paths] of byName) {
    if (paths.length > 1) {
      collisions.push({ name, paths });
    }
    skills.push({ name, srcPath: paths[0] });
  }

  skills.sort((a, b) => a.name.localeCompare(b.name));
  return { skills, collisions };
}

module.exports = { discover, SKILLS_DIR };
