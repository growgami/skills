#!/usr/bin/env node
'use strict';

const { discover } = require('../lib/discover');
const { targetDir, installSkill } = require('../lib/install');
const { printList, interactivePick } = require('../lib/ui');

const dim = '\x1b[2m';
const green = '\x1b[32m';
const yellow = '\x1b[33m';
const red = '\x1b[31m';
const reset = '\x1b[0m';

function printHelp(target) {
  process.stdout.write('Usage: growgami-skills [--all | skill1 skill2 ...]\n');
  process.stdout.write('\n');
  process.stdout.write('  --all         Install all skills\n');
  process.stdout.write('  --list        List available skills\n');
  process.stdout.write('  skill1 ...    Install specific skills\n');
  process.stdout.write('  (no args)     Interactive picker\n');
  process.stdout.write('\n');
  process.stdout.write(
    `Target: ${target} (override with CLAUDE_SKILLS_DIR)\n`
  );
}

// Install a set of bare names, resolving each against discovered skills.
// Returns a non-zero exit code if any name is missing or collides.
function installNames(names, skills, collisions, target) {
  const byName = new Map(skills.map((s) => [s.name, s]));
  const collisionNames = new Set(collisions.map((c) => c.name));
  let status = 0;

  for (const name of names) {
    if (collisionNames.has(name)) {
      process.stdout.write(
        `  ${red}skip${reset} ${name} (name collision)\n`
      );
      status = 1;
      continue;
    }
    const skill = byName.get(name);
    if (!skill) {
      process.stdout.write(`  ${yellow}skip${reset} ${name} (not found)\n`);
      status = 1;
      continue;
    }
    try {
      installSkill(skill.name, skill.srcPath, target);
      process.stdout.write(`  ${green}+${reset} ${name}\n`);
    } catch (err) {
      process.stdout.write(
        `  ${red}skip${reset} ${name} (${err.message})\n`
      );
      status = 1;
    }
  }
  return status;
}

async function main() {
  const args = process.argv.slice(2);
  const target = targetDir();
  const { skills, collisions } = discover();

  if (args[0] === '--help' || args[0] === '-h') {
    printHelp(target);
    return 0;
  }

  if (args[0] === '--list') {
    for (const c of collisions) {
      process.stderr.write(
        `  ${red}skip${reset} ${c.name} (name collision)\n`
      );
    }
    printList(skills);
    return 0;
  }

  process.stdout.write(`\n  ${dim}Installing to ${target}${reset}\n\n`);

  let names;
  if (args[0] === '--all') {
    names = skills.map((s) => s.name);
  } else if (args.length > 0) {
    names = args;
  } else if (process.stdin.isTTY) {
    names = await interactivePick(skills);
  } else {
    printHelp(target);
    return 0;
  }

  const status = installNames(names, skills, collisions, target);
  process.stdout.write('\n');
  return status;
}

main()
  .then((code) => process.exit(code))
  .catch((err) => {
    process.stderr.write(`${err && err.stack ? err.stack : err}\n`);
    process.exit(1);
  });
