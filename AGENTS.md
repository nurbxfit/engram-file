# Project Instructions
This file contains behavioral rules for AI agents.

## Memory System
This project uses a file-based memory system.
- Read `.agents/skills/engram/SKILL.md` for behavior instructions.
- Read `memory/index.jsonl` at session start for active entries.
- Run `python scripts/engram.py digest` for a task-relevant memory summary.
- Use `python scripts/engram.py add` to save new entries (validated automatically).
- See `ISSUES.md` for known architecture gaps and planned improvements.
- Always consult memory before starting any task.

## Safety Rules
### Git Operations

- **NEVER push to `master` or `main` without explicit user confirmation.** Always ask first and state which branch + remote you're pushing to.
- **NEVER `git push --force` or `git push --force-with-lease` without explicit user confirmation.** Explain why a force push is needed.
- **NEVER `git push` after a rebase or amend without explicit warning.** State: "This rewrites history on the remote."
- **NEVER discard or delete work from other agents/users.** If you encounter unexpected changes, assume they're in-progress work from someone else.
- **NEVER use `--no-verify` to bypass hooks.** If a hook blocks an action, stop and ask the user.

### File Operations

- **NEVER run destructive commands** (`rm -rf`, `DROP TABLE`, `git reset --hard`) without explicit confirmation.
- **PREFER editing existing files over creating new ones.**

### Implementation Rules 
- **NEVER suppress type errors** with `as any`, `@ts-ignore`, or `@ts-expect-error`. 

## Git Rules
### Branches
- `main` - Stable, publish-ready. 
- `feature/*` - Work in progress, experimental features.

