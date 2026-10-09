# Target shape

```
~/.agents/AGENTS.md           shared root, every session, both agents
~/.codex/AGENTS.md  -> ../.agents/AGENTS.md   (symlink)
~/.claude/CLAUDE.md           @~/.agents/AGENTS.md + Claude-only lines
~/.claude/docs/*.md           detail, read when a pointer row fires
~/.claude/rules/*.md          file-type rules with paths: frontmatter
<repo>/AGENTS.md              repo-only rules (plus @AGENTS.md in <repo>/CLAUDE.md)
```

## Root skeleton

```markdown
# <Name>'s agent rules (shared by Claude Code and Codex)

Canonical file: `~/.agents/AGENTS.md`. Project files win on conflict.

## Standard
<how work is delivered; definition of done>

## Completion gates
<numbered checks required before saying done>

## Domain gates
| Trigger | Run | Blocks on |
|---|---|---|

## Safety and authority
<ask-first list; secrets; protected files; git rules>

## External systems
<pre-flight reads; monitoring rules>

## Voice and stance

## Codex only (Claude ignores this section)

## Where detail lives (read when the trigger fires; never @-import)
| Trigger | Read |
|---|---|
```

## Claude wrapper

```markdown
# Claude Code layer

@~/.agents/AGENTS.md

Claude-only rules below.
```

## Path-scoped rule

```markdown
---
paths:
  - "**/app/**/*.{ts,tsx}"
---
# Next.js
- ...
```
