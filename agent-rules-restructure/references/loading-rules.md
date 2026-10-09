# How Claude Code and Codex find instruction files

Check the live docs when in doubt:
- Claude Code: https://code.claude.com/docs/en/memory and https://code.claude.com/docs/en/hooks
- Codex: https://learn.chatgpt.com/docs/agent-configuration/agents-md

## Claude Code
- Loads at launch: managed policy, `~/.claude/CLAUDE.md` (user level), and every `CLAUDE.md`, `.claude/CLAUDE.md` and `CLAUDE.local.md` from the working folder upward. Files in subfolders load on demand when Claude reads files there. Files over 4 MiB are skipped.
- **`AGENTS.md` fallback.** Recent versions read `AGENTS.md` (or `.claude/AGENTS.md`) directly when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working folder or above it. If one does exist, Claude reads only the `CLAUDE.md` files. The user-level `~/.claude/CLAUDE.md` does not count. So a stray `~/CLAUDE.md` hides every project `AGENTS.md` below the home folder.
- Three fixes for a hidden `AGENTS.md`: put `@AGENTS.md` in the `CLAUDE.md` that sits in the same folder, remove the stray `CLAUDE.md`, or set the Project instructions setting to read both files (`claude-md-and-agents-md`).
- `@path` imports expand at launch and cost context every session. They can appear anywhere in the text, recurse at most four hops, resolve relative to the importing file, and support `~`. Escape spaces with `\ `. A quoted path is not imported. Imports inside code fences are ignored. Use imports for the shared root only, never for detail files.
- `.claude/rules/` is read recursively. A rule file loads every session unless its frontmatter has `paths:`. **`globs:` is not read**, so a rule file using it loads everywhere.
- Auto memory (`MEMORY.md`) loads its first 200 lines or 25 KB. Do not duplicate it in instruction files.
- User-level imports outside the project load without an approval prompt in the CLI. Some surfaces, such as Cowork desktop sessions, skip imports that resolve outside the working folder, so check there with `/memory` or a probe.
- Hooks that exit 0: stdout from SessionStart is added to Claude's context, and JSON `systemMessage` is shown to the user. Stderr goes to the debug log only, and nobody sees it.

## Codex
- Global: `$CODEX_HOME` (default `~/.codex`). Reads `AGENTS.override.md` if it is non-empty, else `AGENTS.md`. Empty files are skipped.
- Then from the git root down to the working folder, one file per folder: `AGENTS.override.md`, then `AGENTS.md`, then any `project_doc_fallback_filenames` from config. Closer files win.
- **No import syntax.** Share a file by symlink.
- Combined instruction bytes cap at 32 KiB (`project_doc_max_bytes`), global file included. Content past the cap is dropped without an error.
- If the home folder is itself a git repo, `~/AGENTS.md` loads as a project file there. Put the shared root somewhere that is not on Codex's walk, such as `~/.agents/AGENTS.md`, or it loads twice.

## What belongs where
| Content | Home |
|---|---|
| Rules every session needs (safety, authority, done-criteria, voice) | Shared root |
| One line per review gate | Gate table in the shared root |
| Gate detail, checklists, incident history | Topic docs, listed in a pointer table with "read when" |
| Rules for one repo | That repo's `AGENTS.md` (plus `@AGENTS.md` in its `CLAUDE.md` if it has one) |
| Rules for one file type | `.claude/rules/*.md` with `paths:` |
| Multi-step procedures | Skills |
| Agent-specific rules | A labeled section ("Codex only") or the Claude wrapper file |

## What to delete
- Things the model does by default (read before editing, don't invent APIs).
- Facts the repo already shows (file lists, project tables that drift).
- Restatements of a hook that already blocks with its own message. Keep one line naming the hook if the other agent has no hooks.
- Stale facts: retired tools, dead projects, wrong paths.

Everything else is moved, not deleted.
