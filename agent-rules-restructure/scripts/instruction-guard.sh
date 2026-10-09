#!/usr/bin/env bash
# SessionStart guard for a shared instruction root. Never blocks: always exits 0.
# Prints nothing when healthy. On a problem it prints JSON: systemMessage is shown
# to the user and additionalContext reaches Claude. (Stderr from a hook that exits 0
# goes only to the debug log, so it is not used.)
# Override paths with AGENT_RULES_ROOT and CODEX_HOME.
root="${AGENT_RULES_ROOT:-${HOME}/.agents/AGENTS.md}"
codex_home="${CODEX_HOME:-${HOME}/.codex}"
codex="${codex_home}/AGENTS.md"
msgs=""
# Escape for JSON as messages are added; "\\n" is a JSON newline.
add() {
  local e
  e=$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
  msgs="${msgs}instruction-guard: ${e}\\n"
}

if [ ! -f "$root" ]; then
  add "shared root $root is missing; agents are running on almost no rules."
else
  bytes=$(wc -c < "$root" | tr -d ' ')
  [ "$bytes" -ge 29000 ] && add "$root is $bytes bytes; Codex drops content past 32768 combined."
fi
if [ -d "$codex_home" ]; then
  if [ -s "${codex_home}/AGENTS.override.md" ]; then
    add "${codex_home}/AGENTS.override.md is not empty, so Codex reads it instead of the shared root."
  fi
  if [ ! -L "$codex" ] || [ ! "$codex" -ef "$root" ]; then
    add "$codex is not a symlink to $root. Keep any new rules from it, then: mv \"$codex\" \"$codex.bak.\$(date +%s)\" && ln -s \"$root\" \"$codex\""
  fi
fi

[ -z "$msgs" ] && exit 0
printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%sTell the user about this at the start of your first reply."}}\n' "$msgs" "$msgs"
exit 0
