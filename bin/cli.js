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

// Install one resolved skill, printing a "+ name" line on success.
// Returns 0 on success, 1 on failure.
function installOne(skill, target) {
  try {
    installSkill(skill.name, skill.srcPath, target);
    process.stdout.write(`  ${green}+${reset} ${skill.name}\n`);
    return 0;
  } catch (err) {
    process.stdout.write(
      `  ${red}skip${reset} ${skill.name} (${err.message})\n`
    );
    return 1;
  }
}

// Install a set of bare names, resolving each against discovered skills and
// bundles. A bundle name installs all of its member skills.
// Returns a non-zero exit code if any name is missing or collides.
function installNames(names, skills, bundles, collisions, target) {
  const byName = new Map(skills.map((s) => [s.name, s]));
  const byBundle = new Map(bundles.map((b) => [b.name, b]));
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
    const bundle = byBundle.get(name);
    // Prefer an individual skill over a bundle if both somehow match.
    if (skill) {
      if (bundle) {
        process.stdout.write(
          `  ${yellow}note${reset} ${name} matches both a skill and a bundle; installing the skill\n`
        );
      }
      status = installOne(skill, target) || status;
      continue;
    }
    if (bundle) {
      process.stdout.write(
        `  ${dim}bundle ${bundle.name} -> ${bundle.members.length} skills${reset}\n`
      );
      for (const member of bundle.members) {
        const memberSkill = byName.get(member);
        if (!memberSkill) {
          process.stdout.write(
            `  ${yellow}skip${reset} ${member} (not found)\n`
          );
          status = 1;
          continue;
        }
        status = installOne(memberSkill, target) || status;
      }
      continue;
    }
    process.stdout.write(`  ${yellow}skip${reset} ${name} (not found)\n`);
    status = 1;
  }
  return status;
}

async function main() {
  const args = process.argv.slice(2);
  const target = targetDir();
  const { skills, bundles, collisions } = discover();

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
    printList(skills, bundles);
    return 0;
  }

  process.stdout.write(`\n  ${dim}Installing to ${target}${reset}\n\n`);

  let names;
  if (args[0] === '--all') {
    names = skills.map((s) => s.name);
  } else if (args.length > 0) {
    names = args;
  } else if (process.stdin.isTTY) {
    names = await interactivePick(skills, bundles);
  } else {
    printHelp(target);
    return 0;
  }

  const status = installNames(names, skills, bundles, collisions, target);
  process.stdout.write('\n');
  return status;
}

main()
  .then((code) => process.exit(code))
  .catch((err) => {
    process.stderr.write(`${err && err.stack ? err.stack : err}\n`);
    process.exit(1);
  });
