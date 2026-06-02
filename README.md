# Growgami Skills

Claude Code skills built from real operational experience.

## Install

**With npx (quickest):**

```bash
npx growgami-skills --all                  # everything
npx growgami-skills --list                 # list available skills (and bundles)
npx growgami-skills org-map                # specific skill(s)
npx growgami-skills neobank-seo-skills     # a whole bundle (all 7 SEO skills)
```

Installing a bundle name (e.g. `neobank-seo-skills`) installs every skill inside
it, each under its own bare name.

Installs into `~/.claude/skills/` (override with `CLAUDE_SKILLS_DIR`).

**Alternative — git clone + install script:**

```bash
git clone https://github.com/growgami/skills.git
cd skills
./install.sh              # interactive picker
./install.sh org-map      # specific skill
./install.sh --all        # everything
```

**Alternative — git clone + manual copy:**

```bash
git clone https://github.com/growgami/skills.git
cp -r skills/skills/org-map ~/.claude/skills/   # one skill
cp -r skills/skills/* ~/.claude/skills/         # all flat skills
```

## Skills

| Skill | What it does |
|---|---|
| [org-map](skills/org-map/) | Map your org's real operating model into a structured YAML ontology |
| [brand-guidelines](skills/brand-guidelines/) | Brand color and typography standards |
| [competitive-ads-extractor](skills/competitive-ads-extractor/) | Competitive ad intelligence extraction |
| [editor](skills/editor/) | Content editing |
| [frontend-design](skills/frontend-design/) | Frontend UI/UX design |
| [investor-materials](skills/investor-materials/) | Investor decks and materials |
| [lead-research-assistant](skills/lead-research-assistant/) | Lead research and qualification |
| [market-research-reports](skills/market-research-reports/) | Market research generation |
| [memory-management](skills/memory-management/) | Claude memory management |
| [neobank-lifecycle-sequence-generator](skills/neobank-lifecycle-sequence-generator/) | Neobank lifecycle sequences |
| [skill-creator](skills/skill-creator/) | Scaffold new Claude skills |
| [neobank-seo-skills](skills/neobank-seo-skills/) | Bundle of 7 nested SEO skills for neobank/fintech: seo-audit, ai-seo, programmatic-seo, competitor-pages, schema, aso, growgami-pdf |

## Structure

```
skills/
  skill-name/
    SKILL.md        # skill definition (YAML frontmatter + prompt)
    references/     # optional supporting files
  bundle-name/      # a bundle groups related skills
    skills/
      skill-name/
        SKILL.md
        references/
```

Both flat skills and nested bundle skills install under their bare name (e.g. `seo-audit`). Tooling discovers SKILL.md at both depths.

Compatible with vanilla Claude Code (`~/.claude/skills/`) and [skills.ws](https://skills.ws).
