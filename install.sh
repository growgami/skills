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

# Discover bundles and emit "bundle<TAB>member1,member2,..." lines.
# A bundle = a dir directly under skills/ with NO SKILL.md of its own that
# contains a skills/ subdir holding one or more <name>/SKILL.md.
discover_bundles() {
  local d nested name members
  for d in "$SKILLS_DIR"/*/; do
    [ -d "$d" ] || continue
    [ -f "$d/SKILL.md" ] && continue
    [ -d "$d/skills" ] || continue
    name="$(basename "$d")"
    members=""
    for nested in "$d"skills/*/; do
      [ -d "$nested" ] || continue
      [ -f "$nested/SKILL.md" ] || continue
      if [ -n "$members" ]; then
        members="$members,$(basename "$nested")"
      else
        members="$(basename "$nested")"
      fi
    done
    [ -n "$members" ] || continue
    printf '%s\t%s\n' "$name" "$members"
  done
}

# Resolve a bundle name to its comma-separated member list.
# Prints members on success; returns 1 if not a bundle.
resolve_bundle() {
  local want="$1" name members
  while IFS=$'\t' read -r name members; do
    if [ "$name" = "$want" ]; then
      printf '%s' "$members"
      return 0
    fi
  done < <(discover_bundles)
  return 1
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

# Copy one resolved skill (name + source dir) into the target.
copy_skill() {
  local name="$1" src="$2"
  rm -rf "${TARGET:?}/$name"
  mkdir -p "$TARGET/$name"
  cp -r "$src"/* "$TARGET/$name/"
  echo -e "  ${green}+${reset} $name"
}

# Install a single skill by bare name. Returns 1 if not found, 2 on collision.
install_one() {
  local name="$1" src rc
  set +e
  src="$(resolve_src "$name")"
  rc=$?
  set -e
  if [ "$rc" -eq 1 ]; then
    return 1
  elif [ "$rc" -eq 2 ]; then
    echo -e "  ${red}skip${reset} $name (name collision)"
    return 2
  fi
  copy_skill "$name" "$src"
}

# Install by name: an individual skill if it matches, else a bundle (all
# members), else not found. Prefers an individual skill over a bundle.
install_skill() {
  local name="$1" members member status=0
  # Detect skill vs bundle up front to handle the (guarded) collision case.
  local is_skill=0 is_bundle=0
  set +e
  resolve_src "$name" >/dev/null 2>&1 && is_skill=1
  members="$(resolve_bundle "$name")" && is_bundle=1
  set -e

  if [ "$is_skill" -eq 1 ]; then
    if [ "$is_bundle" -eq 1 ]; then
      echo -e "  ${yellow}note${reset} $name matches both a skill and a bundle; installing the skill"
    fi
    install_one "$name"
    return $?
  fi

  if [ "$is_bundle" -eq 1 ]; then
    local count
    count="$(echo "$members" | tr ',' '\n' | grep -c . || true)"
    echo -e "  ${dim}bundle $name -> $count skills${reset}"
    IFS=',' read -ra _members <<< "$members"
    for member in "${_members[@]}"; do
      install_one "$member" || status=$?
    done
    return "$status"
  fi

  echo -e "  ${yellow}skip${reset} $name (not found)"
  return 1
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
  bundles="$(discover_bundles)"
  if [ -n "$bundles" ]; then
    echo ""
    echo "Bundles (install the whole set by name):"
    while IFS=$'\t' read -r bname bmembers; do
      [ -n "$bname" ] || continue
      printf '  %s  (%s)\n' "$bname" "$(echo "$bmembers" | sed 's/,/, /g')"
    done < <(printf '%s\n' "$bundles")
  fi
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
picker_bundles="$(discover_bundles)"
if [ -n "$picker_bundles" ]; then
  echo ""
  echo "  Bundles (install the whole set by name):"
  while IFS=$'\t' read -r bname bmembers; do
    [ -n "$bname" ] || continue
    printf '    %s  (%s)\n' "$bname" "$(echo "$bmembers" | sed 's/,/, /g')"
  done < <(printf '%s\n' "$picker_bundles")
fi
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
