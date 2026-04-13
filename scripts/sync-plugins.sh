#!/usr/bin/env bash
# sync-plugins.sh — Sync all PretInnov plugins from local source into Claude Code caches
# Run this whenever you update plugin manifests, skills, hooks, or agents locally.
# Usage: bash scripts/sync-plugins.sh [--dry-run]

set -euo pipefail

MARKETPLACE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_PLUGINS="${HOME}/.claude/plugins"
MARKETPLACE_CACHE="${CLAUDE_PLUGINS}/marketplaces/pretinnov-plugins/plugins"
INSTALL_CACHE="${CLAUDE_PLUGINS}/cache/pretinnov-plugins"
REGISTRY="${CLAUDE_PLUGINS}/installed_plugins.json"
DRY_RUN=false

[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

log()  { echo "  $*"; }
ok()   { echo "  ✓ $*"; }
warn() { echo "  ⚠ $*"; }
info() { echo ""; echo "── $* ──"; }

echo "════════════════════════════════════════════"
echo "  PretInnov Plugin Sync"
echo "  Source: ${MARKETPLACE_ROOT}/plugins"
echo "  Dry-run: ${DRY_RUN}"
echo "════════════════════════════════════════════"

# Always sync the marketplace index first — this controls the "available" count in /plugin UI
info "marketplace.json (available count)"
if $DRY_RUN; then
    log "[dry-run] would copy .claude-plugin/marketplace.json to cache"
else
    mkdir -p "${HOME}/.claude/plugins/marketplaces/pretinnov-plugins/.claude-plugin"
    cp "${MARKETPLACE_ROOT}/.claude-plugin/marketplace.json" \
       "${HOME}/.claude/plugins/marketplaces/pretinnov-plugins/.claude-plugin/marketplace.json"
    ok "marketplace.json synced ($(python3 -c "import json; d=json.load(open('${MARKETPLACE_ROOT}/.claude-plugin/marketplace.json')); print(len(d['plugins']),'plugins listed')"))"
fi

PLUGINS=( $(ls "${MARKETPLACE_ROOT}/plugins/") )

for plugin in "${PLUGINS[@]}"; do
    src="${MARKETPLACE_ROOT}/plugins/${plugin}"
    manifest="${src}/.claude-plugin/plugin.json"

    [[ ! -f "$manifest" ]] && warn "Skipping ${plugin}: no plugin.json" && continue

    version=$(python3 -c "import json; print(json.load(open('${manifest}'))['version'])" 2>/dev/null || echo "unknown")

    info "${plugin} v${version}"

    # 1. Sync marketplace cache (what /plugin list reads)
    mc_dir="${MARKETPLACE_CACHE}/${plugin}"
    if $DRY_RUN; then
        log "[dry-run] would rsync ${src}/ -> ${mc_dir}/"
    else
        mkdir -p "${mc_dir}"
        rsync -a --delete \
            --exclude="data/*.jsonl" \
            --exclude="data/*-cache.*" \
            --exclude="*.pyc" \
            "${src}/" "${mc_dir}/"
        ok "marketplace cache updated"
    fi

    # 2. Sync install cache at the exact version path (what Claude Code loads)
    ic_dir="${INSTALL_CACHE}/${plugin}/${version}"
    if [[ -d "${ic_dir}" ]]; then
        if $DRY_RUN; then
            log "[dry-run] would rsync ${src}/ -> ${ic_dir}/"
        else
            rsync -a \
                --exclude="data/*.jsonl" \
                --exclude="data/*-cache.*" \
                --exclude="*.pyc" \
                "${src}/" "${ic_dir}/"
            ok "install cache (v${version}) updated"
        fi
    else
        # Not installed at this version — create and register
        if $DRY_RUN; then
            log "[dry-run] would install ${plugin} v${version}"
        else
            mkdir -p "${ic_dir}"
            rsync -a \
                --exclude="data/*.jsonl" \
                --exclude="data/*-cache.*" \
                --exclude="*.pyc" \
                "${src}/" "${ic_dir}/"
            # Register in installed_plugins.json
            python3 - <<PYEOF
import json, datetime

registry_path = '${REGISTRY}'
with open(registry_path) as f:
    reg = json.load(f)

key = '${plugin}@pretinnov-plugins'
now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
entry = {
    "scope": "user",
    "installPath": "${ic_dir}",
    "version": "${version}",
    "installedAt": now,
    "lastUpdated": now
}

# Remove stale entries for this plugin, keep entries from other scopes/projects
existing = reg['plugins'].get(key, [])
existing_non_user = [e for e in existing if e.get('scope') != 'user']
reg['plugins'][key] = existing_non_user + [entry]

with open(registry_path, 'w') as f:
    json.dump(reg, f, indent=2)
print('    registered in installed_plugins.json')
PYEOF
            ok "installed and registered ${plugin} v${version}"
        fi
    fi

done

echo ""
echo "════════════════════════════════════════════"
echo "  Sync complete. Restart Claude Code to"
echo "  pick up plugin changes."
echo "════════════════════════════════════════════"
