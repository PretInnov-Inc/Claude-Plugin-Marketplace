#!/usr/bin/env bash
# Sentinel SessionStart Hook — Output Mode Injector (Category C)
#
# Fires at every session start. Reads the active output style from
# sentinel-config.json and loads the corresponding output-styles/*.md file,
# injecting its content into Claude's system prompt as additionalContext.
#
# This is the single source of truth for output mode — no more conflicting
# learning-output-style + explanatory-output-style plugins fighting each other.
# Change the active style via /sentinel:style-engine and it takes effect
# on the NEXT session start.
#
# Styles available: focused | learning | verbose
# Config key: output_style.active in sentinel-config.json

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
DATA_DIR="${PLUGIN_ROOT}/data"
STYLES_DIR="${PLUGIN_ROOT}/output-styles"
CONFIG_FILE="${DATA_DIR}/sentinel-config.json"

# Default style
ACTIVE_STYLE="focused"

# Read active style from config
if [ -f "$CONFIG_FILE" ]; then
  ACTIVE_STYLE=$(python3 -c "
import json, sys
try:
  d = json.load(open('$CONFIG_FILE'))
  style = d.get('output_style', {}).get('active', 'focused')
  inject = d.get('output_style', {}).get('inject_on_session_start', True)
  if not inject:
    sys.exit(1)
  print(style)
except Exception:
  print('focused')
" 2>/dev/null) || exit 0
fi

# Find and read the style file
STYLE_FILE="${STYLES_DIR}/${ACTIVE_STYLE}.md"
if [ ! -f "$STYLE_FILE" ]; then
  # Silently skip if style file not found
  exit 0
fi

# Extract style body (skip YAML frontmatter)
python3 << PYEOF
import json, sys

style_file = "${STYLE_FILE}"
active_style = "${ACTIVE_STYLE}"

try:
    with open(style_file, "r") as f:
        content = f.read()

    # Strip YAML frontmatter (--- ... ---)
    lines = content.split("\n")
    body_lines = []
    in_frontmatter = False
    frontmatter_done = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip() == "---":
            in_frontmatter = True
            continue
        if in_frontmatter and line.strip() == "---":
            in_frontmatter = False
            frontmatter_done = True
            continue
        if not in_frontmatter:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    if not body:
        sys.exit(0)

    style_label = {
        "focused": "focused (code-first, minimal)",
        "learning": "learning (educational + interactive)",
        "verbose": "verbose (detailed explanations)"
    }.get(active_style, active_style)

    context_text = f"# Active Output Style: {style_label}\n\n{body}"

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context_text
        }
    }
    print(json.dumps(output))
except Exception as e:
    sys.exit(0)
PYEOF

exit 0
