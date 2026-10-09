# agent-rules-restructure

A Claude Code and Codex skill that turns sprawling agent instruction files into one lean, shared rulebook without losing a rule.

If your `CLAUDE.md` has grown past a few hundred lines, your rules live in several places that disagree, or you run both Claude Code and Codex and keep two copies in sync by hand, this skill restructures it for you:

- `~/.agents/AGENTS.md` holds only the rules every session needs. Claude Code loads it with an `@import`; Codex loads it through a symlink.
- Checklists, gate detail and incident history move to separate files. A table in the root says where each one lives and when to read it.
- Nothing changes until you have compared a conservative, a moderate and an aggressive version side by side, each with measured before and after sizes and a rule-by-rule ledger.
- Fresh headless sessions of each agent quote lines back from their instructions, so you know what actually loaded.

On the setup it was built for, Claude Code's every-session instructions went from 65.8 KiB to about 16 KiB, and Codex's from 26.2 KiB to 13.7 KiB.

## Install

```bash
git clone https://github.com/mavericksolutions7/agent-rules-restructure.git ~/src/agent-rules-restructure

# Claude Code
mkdir -p ~/.claude/skills
ln -s ~/src/agent-rules-restructure/agent-rules-restructure ~/.claude/skills/agent-rules-restructure

# Codex (optional)
mkdir -p ~/.codex/skills
ln -s ~/src/agent-rules-restructure/agent-rules-restructure ~/.codex/skills/agent-rules-restructure
```

Start a new session afterwards, since skills load at session start.

## Use

In Claude Code, from your home folder, say something like:

> My CLAUDE.md is too big. Restructure my agent instructions.

Or run the read-only inventory on its own first:

```bash
python3 ~/.claude/skills/agent-rules-restructure/scripts/inventory.py ~/path/to/a/project
```

## What it checks for

These are the problems it found on a real setup:

- If any `CLAUDE.md` sits in or above the working folder, Claude Code reads `CLAUDE.md` files only, so project `AGENTS.md` files go unread.
- Rule files scoped with `globs:` load on every session, because Claude Code ignores `globs:` and only scopes rules with `paths:`.
- Codex reads at most 32 KiB of instructions and has no imports. Anything past the cap is dropped silently, and a shared file needs a symlink.
- Some scripts read instruction files as raw text. They break when text moves behind an import.
- A broken symlink fails silently. The included `instruction-guard.sh` warns at session start if the root is missing or the link has been replaced.

## What's inside

```
agent-rules-restructure/
  SKILL.md                     the workflow the agent follows
  references/loading-rules.md  how each agent discovers instruction files
  references/proposal-brief.md brief for the three proposal agents
  references/target-shape.md   file layout and root skeleton
  scripts/inventory.py         read-only inventory and breakage checks
  scripts/verify-load.sh       headless load probes for both agents
  scripts/instruction-guard.sh SessionStart guard, always exits 0
```

The inventory needs `python3`; the other two scripts are plain bash and work on macOS's bash 3.2. Read them before running, as you should with any skill.

## License

MIT
