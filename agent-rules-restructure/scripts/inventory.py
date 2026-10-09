#!/usr/bin/env python3
"""Read-only inventory of agent instruction files for Claude Code and Codex.

Usage: python3 inventory.py [project_dir]   (default: current folder)

Prints what each agent loads every session when started in project_dir,
sizes, and the common breakages: unscoped or globs: rule files, a CLAUDE.md
hiding AGENTS.md, missing imports, an AGENTS.override.md cutting Codex off,
and the Codex 32 KiB cap. Exit 0 always unless the folder does not exist.
"""
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
CODEX_HOME = os.environ.get("CODEX_HOME", os.path.join(HOME, ".codex"))
CODEX_CAP = 32768
IMPORT_DEPTH = 4
FENCE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)
IMPORT = re.compile(r"(?<![\w`'\"])@((?:\\ |[^\s`'\"])+)")
CODE_SPAN = re.compile(r"`[^`\n]*`")


def kib(n):
    return f"{n / 1024:.1f}"


def size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def row(path, label):
    with open(path, "rb") as f:
        lines = f.read().count(b"\n")
    print(f"  {path}\n      {lines} lines, {kib(size(path))} KiB, {label}")


def real(path):
    return os.path.realpath(path)


def imports_of(path):
    """@imports Claude Code would expand from this file (outside code fences)."""
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    text = CODE_SPAN.sub("", FENCE.sub("", text))
    out = []
    for m in IMPORT.finditer(text):
        raw = m.group(1).replace("\\ ", " ").rstrip(".,;:)")
        if "/" not in raw and "." not in raw:
            continue  # an @mention, not a path
        if raw.startswith("~/"):
            p = os.path.join(HOME, raw[2:])
        elif os.path.isabs(raw):
            p = raw
        else:
            p = os.path.join(os.path.dirname(path), raw)
        out.append((m.group(0), os.path.normpath(p)))
    return out


def walk_imports(path, seen, depth, problems):
    """Return [(file, importer)] for every import reachable within IMPORT_DEPTH hops."""
    found = []
    if depth >= IMPORT_DEPTH:
        return found
    for token, target in imports_of(path):
        if not os.path.isfile(target):
            problems.append(f"import {token} in {path} points to a missing file")
            continue
        key = real(target)
        if key in seen:
            continue
        seen.add(key)
        found.append((target, path))
        found += walk_imports(target, seen, depth + 1, problems)
    return found


def ancestors(start):
    d = start
    while True:
        yield d
        parent = os.path.dirname(d)
        if parent == d:
            return
        d = parent


def rule_files(base):
    seen_dirs, seen_files = set(), set()
    for root, dirs, files in os.walk(base, followlinks=True):
        key = real(root)
        if key in seen_dirs:
            dirs[:] = []  # symlink loop or repeated folder
            continue
        seen_dirs.add(key)
        for name in sorted(files):
            p = os.path.join(root, name)
            if name.endswith(".md") and real(p) not in seen_files:
                seen_files.add(real(p))
                yield p


def frontmatter(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else ""


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    proj = os.path.abspath(os.path.expanduser(arg))
    if not os.path.isdir(proj):
        print(f"no such folder: {arg}", file=sys.stderr)
        return 1
    problems = []
    seen = set()

    # ---------------- Claude Code ----------------
    print(f"== Claude Code, every session when started in {proj}")
    total = 0
    claude_files = []
    user_claude = os.path.join(HOME, ".claude", "CLAUDE.md")
    if os.path.isfile(user_claude):
        claude_files.append((user_claude, "user level"))
    hiders = []
    for d in ancestors(proj):
        for name in ("CLAUDE.md", os.path.join(".claude", "CLAUDE.md"), "CLAUDE.local.md"):
            p = os.path.join(d, name)
            if os.path.isfile(p) and real(p) != real(user_claude):
                claude_files.append((p, "folder at or above project"))
                hiders.append(p)
    agents_fallback = []
    if not hiders:
        for d in ancestors(proj):
            for name in ("AGENTS.md", os.path.join(".claude", "AGENTS.md")):
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    agents_fallback.append((p, "AGENTS.md read directly (no CLAUDE.md present)"))
    for p, label in claude_files + agents_fallback:
        key = real(p)
        if key in seen:
            continue
        seen.add(key)
        row(p, label)
        total += size(p)
        for target, importer in walk_imports(p, seen, 0, problems):
            row(target, f"imported by {importer}")
            total += size(target)

    rule_dirs = [os.path.join(HOME, ".claude", "rules")]
    proj_rules = os.path.join(proj, ".claude", "rules")
    if real(proj_rules) != real(rule_dirs[0]):
        rule_dirs.append(proj_rules)
    for base in rule_dirs:
        if not os.path.isdir(base):
            continue
        for f in rule_files(base):
            fm = frontmatter(f)
            if re.search(r"^paths:", fm, re.M):
                row(f, "path-scoped: loads only on matching files")
            else:
                row(f, "UNSCOPED rule: loads every session")
                total += size(f)
                if re.search(r"^globs:", fm, re.M):
                    problems.append(f"{f} uses globs:, which Claude Code ignores. Rename it to paths:.")
    print(f"  Total every session: {kib(total)} KiB (auto memory MEMORY.md not counted)")

    # Is AGENTS.md hidden from Claude?
    for a in [os.path.join(d, n) for d in ancestors(proj)
              for n in ("AGENTS.md", os.path.join(".claude", "AGENTS.md"))]:
        if not os.path.isfile(a) or not hiders:
            continue
        imported = any(real(t) == real(a)
                       for h in hiders for _tok, t in imports_of(h))
        if not imported:
            problems.append(f"{a} is hidden from Claude: {hiders[0]} exists and nothing imports {a}.")

    # ---------------- Codex ----------------
    print()
    if not os.path.isdir(CODEX_HOME):
        print(f"== Codex: no {CODEX_HOME}; Codex steps do not apply")
    else:
        print(f"== Codex, every session when started in {proj}")
        ctotal = 0
        override = os.path.join(CODEX_HOME, "AGENTS.override.md")
        glob_file = os.path.join(CODEX_HOME, "AGENTS.md")
        if size(override) > 0:
            problems.append(f"{override} is not empty, so Codex reads it instead of {glob_file}.")
            glob_file = override
        if os.path.islink(glob_file):
            print(f"  {glob_file} is a symlink to {os.readlink(glob_file)}")
            if not os.path.exists(glob_file):
                problems.append(f"{glob_file} is a broken symlink, so Codex loads no global rules.")
        if size(glob_file) > 0:
            row(glob_file, "global")
            ctotal += size(glob_file)
        try:
            top = subprocess.run(["git", "-C", proj, "rev-parse", "--show-toplevel"],
                                 capture_output=True, text=True, timeout=10).stdout.strip() or proj
        except (OSError, subprocess.SubprocessError):
            top = proj
        chain = []
        for d in ancestors(proj):
            chain.append(d)
            if real(d) == real(top):
                break
        for d in reversed(chain):
            for name in ("AGENTS.override.md", "AGENTS.md"):
                p = os.path.join(d, name)
                if size(p) > 0:
                    if real(p) == real(glob_file):
                        problems.append(f"{p} loads twice in Codex: as the global file and on the project walk.")
                    row(p, "project chain")
                    ctotal += size(p)
                    break
        print(f"  Combined: {kib(ctotal)} KiB of the {kib(CODEX_CAP)} KiB cap")
        if ctotal >= CODEX_CAP:
            problems.append("Codex is over its 32 KiB cap and drops everything past it.")

    print()
    print("== Problems")
    if problems:
        for p in problems:
            print(f"  ! {p}")
    else:
        print("  none found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
