#!/usr/bin/env bash
# Prove which instructions each agent actually loaded, using fresh headless sessions.
# Spends one model call per installed agent.
# Usage: verify-load.sh "<phrase from the shared root>" "<Claude-only phrase>" [project_dir]
# Pass: Claude reports both FOUND; Codex reports phrase 1 FOUND and phrase 2 ABSENT.
[ $# -ge 2 ] || { echo "usage: verify-load.sh \"<shared phrase>\" \"<Claude-only phrase>\" [project_dir]" >&2; exit 2; }
shared="$1"; claude_only="$2"; dir="${3:-$PWD}"
cd "$dir" 2>/dev/null || { echo "no such folder: $dir" >&2; exit 2; }
q="Answer from your loaded instructions only. Use no tools. For each phrase below, reply FOUND and quote the full line that contains it, or reply ABSENT.
1: $shared
2: $claude_only"
err=$(mktemp "${TMPDIR:-/tmp}/verify-load.XXXXXX"); trap 'rm -f "$err"' EXIT

echo "== Claude Code ($dir)"
if command -v claude >/dev/null; then
  out=$(claude -p "$q" --no-session-persistence --max-turns 1 2>"$err")
  if printf '%s' "$out" | grep -qE 'FOUND|ABSENT'; then printf '%s\n' "$out" | sed 's/^/  /'
  else echo "  no answer; error output:"; sed 's/^/    /' "$err"; fi
else echo "  claude CLI not found, skipped"; fi

echo "== Codex ($dir)"
if command -v codex >/dev/null; then
  out=$(codex exec --skip-git-repo-check "$q" 2>"$err")
  if printf '%s' "$out" | grep -qE 'FOUND|ABSENT'; then printf '%s\n' "$out" | grep -E 'FOUND|ABSENT' | sed 's/^/  /'
  else echo "  no answer; error output:"; sed 's/^/    /' "$err"; fi
else echo "  codex CLI not found, skipped"; fi
