---
name: agent-rules-restructure
description: 'Restructure a person''s Claude Code and Codex instruction files (CLAUDE.md, AGENTS.md, .claude/rules) into one lean shared root plus on-demand detail, losing no rule. Use when someone says "my CLAUDE.md is too big", "clean up my agent instructions", "share rules between Claude and Codex", "set up AGENTS.md", "why is Claude ignoring my AGENTS.md", or wants a leaner agent setup. Differentiator: rule-by-rule ledger, three proposals before any edit, load verified in both agents.'
---

# Agent rules restructure

Turns sprawling, duplicated agent instructions into one shared root file plus on-demand detail. Works for Claude Code alone, Codex alone, or both.

Read `references/loading-rules.md` before Step 1. Every decision below depends on how each agent discovers files, and most broken setups come from getting one of those rules wrong.

Run every script from this skill's folder. `SKILL_DIR` below means that folder.

## Step 0 - Inventory (no edits)

```bash
python3 "$SKILL_DIR/scripts/inventory.py" ~                 # home view
python3 "$SKILL_DIR/scripts/inventory.py" ~/path/to/project # one real project, since project files change what loads
```

It prints what each agent loads every session (imports and the `AGENTS.md` fallback included), sizes, unscoped or `globs:` rule files, any file that hides `AGENTS.md` from Claude, an `AGENTS.override.md` that cuts Codex off, and the Codex 32 KiB total. Show the person the totals.

Branch on what is installed: no `~/.codex` means skip every Codex step; no `~/.claude` means skip every Claude step (Codex-only setups use the symlink alone).

## Step 1 - Three proposals, no file changes

Snapshot every source file into a scratch folder with paths preserved (`tar -cf "$scratch/src.tar" <files>`). Then spawn three independent subagents (or write three versions yourself if subagents are unavailable), each given `references/proposal-brief.md` with its fields filled in and a different aggressiveness:

| Version | Root target | Keeps in root |
|---|---|---|
| Conservative | 170-199 lines | Original wording; deletes only duplicates, stale facts, hook restatements |
| Moderate | 110-140 lines | One-line imperatives, a gate table, a pointer table; rationale moves out |
| Aggressive | 50-90 lines | Identity, safety, unhooked completion gates, pointer table |

Each returns drafts plus a report: stats measured with `wc -lc` (never estimated), deleted, moved, merged, contradictions, and a ledger mapping every source rule to KEPT / MERGED / MOVED(dest) / DELETED(reason).

Present the three side by side with measured before and after numbers. Recommend one and say why. Ask the person to pick one and to decide each contradiction.

## Step 2 - Check nothing useful was lost

Grep the chosen drafts for 30 to 60 distinctive phrases taken from the source rules (numbers, tool names, unusual verbs). Every miss must appear in the ledger as a justified deletion. If it doesn't, restore it.

## Step 3 - Apply with backups

```bash
backup=~/.agent-rules-backup/$(date +%Y%m%d-%H%M%S)
mkdir -p "$backup" && tar -cf "$backup/before.tar" -C / <absolute paths of every file you will touch, without the leading slash>
tar -tf "$backup/before.tar" | wc -l      # must equal the number of files you meant to back up
```

Never move on if the counts differ. Then:

- If `~/.agents/AGENTS.md` already exists, treat it as one more source and merge it in. Never overwrite it.
- Write the shared root and the Claude wrapper (layout in `references/target-shape.md`). Move removed files into `$backup/removed/` instead of deleting them.
- Codex (`${CODEX_HOME:-~/.codex}`): if `AGENTS.md` there is a regular file, it is already backed up and its rules are in the proposal. Move it into `$backup/removed/` (a plain `ln -s` would fail on it), then `ln -s ~/.agents/AGENTS.md "${CODEX_HOME:-$HOME/.codex}/AGENTS.md"`. If `AGENTS.override.md` there is non-empty, Codex reads it instead of `AGENTS.md`. Fold its rules in and move it to the backup too, with the person's OK.
- Find anything that reads instruction files as raw text, because it breaks when text moves behind an import:

```bash
grep -rlI --exclude-dir=sessions --exclude-dir=projects --exclude-dir=log --exclude-dir=node_modules \
  -e 'CLAUDE\.md' -e 'AGENTS\.md' ~/.claude/hooks ~/.claude/bin ~/.claude/scripts ~/.codex/hooks 2>/dev/null
```

- Repoint stale references to removed files with the same grep, using the removed file names.

Rollback: `tar -xf "$backup/before.tar" -C /`, then remove the files the change created (list them in the report).

## Step 4 - Independent review

Run a reviewer in a fresh context, with no access to your reasoning. Give it the source snapshot, the new live files and the ledger. Its main job is a rule-loss audit: walk every source rule and confirm where it landed. Fix P0 and P1 findings, then review the changed files once more.

## Step 5 - Prove both agents load it

This step spends one model call per agent.

```bash
bash "$SKILL_DIR/scripts/verify-load.sh" "<a distinctive phrase from the shared root>" "<a Claude-only phrase>" ~/path/to/project
```

Pass: Claude reports both phrases FOUND, and Codex reports the shared phrase FOUND and the Claude-only phrase ABSENT. If an agent returns nothing, the script prints its error output. Fix login or install before trusting the result. ABSENT for the shared phrase means the import or symlink is broken; fix it before going further.

## Step 6 - Guard against silent breakage (Claude Code)

```bash
mkdir -p ~/.claude/hooks && cp "$SKILL_DIR/scripts/instruction-guard.sh" ~/.claude/hooks/
```

Register it under `hooks.SessionStart` in `~/.claude/settings.json` with the command `bash ~/.claude/hooks/instruction-guard.sh`. Merge it into any existing SessionStart entries; never replace them. It prints a JSON warning that the person sees and Claude reads when the root is missing, when the Codex symlink was replaced, or when the root nears the Codex cap. It prints nothing when all is well, and it always exits 0. Test it once:

```bash
bash ~/.claude/hooks/instruction-guard.sh; echo "exit=$?"    # healthy setup: no output, exit=0
```

## Step 7 - Ship

Instruction files often live in several git repos: home, dotfiles, each project. Ask before committing or pushing. Build each pull request from a clean branch off the remote default branch, applying only this change as a patch, so unrelated uncommitted work stays out.

## Output

Report the measured before and after every-session load for each agent, where each moved rule now lives, the contradictions still open, files created, and the backup path with its rollback command.
