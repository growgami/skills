'use strict';

const readline = require('readline');

function printList(skills, bundles) {
  for (const s of skills) {
    process.stdout.write(s.name + '\n');
  }
  if (bundles && bundles.length > 0) {
    process.stdout.write('\nBundles (install the whole set by name):\n');
    for (const b of bundles) {
      process.stdout.write(`  ${b.name}  (${b.members.join(', ')})\n`);
    }
  }
}

/**
 * Interactive numbered picker. Resolves with an array of selected bare names
 * (raw strings; the caller validates them against discovered skills).
 * Accepts comma-separated numbers and/or names, or "all".
 */
function interactivePick(skills, bundles) {
  return new Promise((resolve) => {
    process.stdout.write('  Available skills:\n\n');
    skills.forEach((s, i) => {
      const n = String(i + 1).padStart(2, ' ');
      process.stdout.write(`  ${n}) ${s.name}\n`);
    });
    if (bundles && bundles.length > 0) {
      process.stdout.write('\n  Bundles (install the whole set by name):\n');
      for (const b of bundles) {
        process.stdout.write(`    ${b.name}  (${b.members.join(', ')})\n`);
      }
    }
    process.stdout.write('\n');

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    rl.question(
      "  Enter numbers or names (comma-separated), or 'all': ",
      (answer) => {
        rl.close();
        const choice = answer.trim();
        if (choice === 'all') {
          resolve(skills.map((s) => s.name));
          return;
        }
        const picks = choice
          .split(',')
          .map((p) => p.trim())
          .filter((p) => p.length > 0)
          .map((p) => {
            if (/^[0-9]+$/.test(p)) {
              const idx = parseInt(p, 10) - 1;
              if (idx >= 0 && idx < skills.length) return skills[idx].name;
            }
            return p;
          });
        resolve(picks);
      }
    );
  });
}

module.exports = { printList, interactivePick };
