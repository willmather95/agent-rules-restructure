# Proposal brief (fill the angle-bracket fields, give one copy to each proposal agent)

## Hard rule
Do not edit, move or create any file outside `<scratch>/<version>/`. Read anything. This step is proposals only.

## Sources
Snapshots in `<scratch>/src/`. Table of each file: original path, lines, KiB, when it loads (from `scripts/inventory.py`).

## Target
1. One shared root `AGENTS.md`, under 200 lines and under 32 KiB, loaded by Claude through `@<root path>` in `~/.claude/CLAUDE.md` and by Codex through a `~/.codex/AGENTS.md` symlink. State the root's location and why it will not double-load.
2. Folder-only rules move to that folder's `AGENTS.md` (say create or append; check whether it exists).
3. Other detail moves to separate files. Prefer an existing doc that already covers the topic. File-type rules become `.claude/rules` files with `paths:`.
4. The root has a pointer table: trigger, then file. No `@` imports for detail files.
5. Delete only: model defaults, facts the repo shows, hook restatements (confirm the hook exists), stale facts. Cite evidence.
6. Merge duplicates. List contradictions with both texts and file:line, plus a recommended pick. Do not resolve them silently.
7. Lose no useful rule.

## Aggressiveness
`<conservative | moderate | aggressive>`, root target `<line range>`.

## Deliverables in `<scratch>/<version>/`
- `AGENTS.md`, `CLAUDE.md` (show the import line), and `moved/` mirroring target paths (mark appends as APPEND).
- Report: summary; stats measured with `wc -lc` (root, each agent's every-session load, before and after); deleted (rule, reason, evidence); moved (rule, destination, create/append, when read); merged; contradictions; ledger of every source rule; risks (scripts or hooks that read these files, size limits, approval prompts).
- No em dashes; short imperative lines.

If you cannot write the report file, return it as text.
