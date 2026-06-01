#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"
TARGET="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

green="\033[32m" dim="\033[2m" yellow="\033[33m" red="\033[31m" reset="\033[0m"

# Discover all skills at both depths and emit "name<TAB>srcdir" lines.
# Flat:   skills/<name>/SKILL.md
# Nested: skills/<bundle>/skills/<name>/SKILL.md
# A dir counts as a skill only if it contains SKILL.md. A bundle's own
# top-level README.md (no SKILL.md) is never a skill.
discover_skills() {
  local d nested name
  for d in "$SKILLS_DIR"/*/; do
    [ -d "$d" ] || continue
    if [ -f "$d/SKILL.md" ]; then
      # Flat skill
      name="$(basename "$d")"
      printf '%s\t%s\n' "$name" "${d%/}"
    elif [ -d "$d/skills" ]; then
      # Nested bundle: look one level deeper
      for nested in "$d"skills/*/; do
        [ -d "$nested" ] || continue
        [ -f "$nested/SKILL.md" ] || continue
        name="$(basename "$nested")"
        printf '%s\t%s\n' "$name" "${nested%/}"
      done
    fi
  done
}

# Bare skill names, one per line, deduped is NOT applied here so callers can
# detect collisions; for listing we surface collisions explicitly.
list_skills() {
  local seen=" " name src
  while IFS=$'\t' read -r name src; do
    [ -n "$name" ] || continue
    if [[ "$seen" == *" $name "* ]]; then
      echo -e "  ${red}skip${reset} $name (name collision)" >&2
      continue
    fi
    seen="$seen$name "
    echo "$name"
  done < <(discover_skills)
}

# Resolve a bare skill name to its source dir. Detects collisions.
# Prints the source dir on success; returns 1 if not found, 2 on collision.
resolve_src() {
  local want="$1" name src matches=""
  while IFS=$'\t' read -r name src; do
    [ "$name" = "$want" ] || continue
    matches="$matches$src"$'\n'
  done < <(discover_skills)
  local count
  count="$(printf '%s' "$matches" | grep -c . || true)"
  if [ "$count" -eq 0 ]; then
    return 1
  elif [ "$count" -gt 1 ]; then
    return 2
  fi
  printf '%s' "$matches" | head -n1
}

install_skill() {
  local name="$1" src rc
  set +e
  src="$(resolve_src "$name")"
  rc=$?
  set -e
  if [ "$rc" -eq 1 ]; then
    echo -e "  ${yellow}skip${reset} $name (not found)"
    return 1
  elif [ "$rc" -eq 2 ]; then
    echo -e "  ${red}skip${reset} $name (name collision)"
    return 2
  fi
  rm -rf "${TARGET:?}/$name"
  mkdir -p "$TARGET/$name"
  cp -r "$src"/* "$TARGET/$name/"
  echo -e "  ${green}+${reset} $name"
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  echo "Usage: ./install.sh [--all | skill1 skill2 ...]"
  echo ""
  echo "  --all         Install all skills"
  echo "  --list        List available skills"
  echo "  skill1 ...    Install specific skills"
  echo "  (no args)     Interactive picker"
  echo ""
  echo "Target: $TARGET (override with CLAUDE_SKILLS_DIR)"
  exit 0
fi

if [ "${1:-}" = "--list" ]; then
  list_skills
  exit 0
fi

mkdir -p "$TARGET"
echo -e "\n  ${dim}Installing to $TARGET${reset}\n"

status=0

if [ "${1:-}" = "--all" ]; then
  while IFS= read -r name; do
    install_skill "$name" || status=$?
  done < <(list_skills)
  echo ""
  exit "$status"
fi

if [ $# -gt 0 ]; then
  for name in "$@"; do
    install_skill "$name" || status=$?
  done
  echo ""
  exit "$status"
fi

# Interactive picker
mapfile -t skills < <(list_skills)
echo "  Available skills:"
echo ""
for i in "${!skills[@]}"; do
  printf "  %2d) %s\n" $((i+1)) "${skills[$i]}"
done
echo ""
read -rp "  Enter numbers or names (comma-separated), or 'all': " choice

if [ "$choice" = "all" ]; then
  for name in "${skills[@]}"; do
    install_skill "$name" || status=$?
  done
else
  IFS=',' read -ra picks <<< "$choice"
  for pick in "${picks[@]}"; do
    pick="$(echo "$pick" | xargs)"
    if [[ "$pick" =~ ^[0-9]+$ ]] && [ "$pick" -ge 1 ] && [ "$pick" -le "${#skills[@]}" ]; then
      install_skill "${skills[$((pick-1))]}" || status=$?
    else
      install_skill "$pick" || status=$?
    fi
  done
fi
echo ""
exit "$status"
