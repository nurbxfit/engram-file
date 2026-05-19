# Architecture Issues & Technical Debt

Tracking document for improvements identified during the memory system redesign.
Each issue is a candidate for future implementation sessions.

---

## P0 — Structural (foundation)

### I-01: Agent discovery — no guaranteed activation
**Status**: open
**Area**: activation
**Priority**: high
**Description**: The chain is `AGENTS.md → "Read .agents/skills/memory.md" → agent reads → agent acts`. This is a convention, not a mechanism. No hook, pre-session script, or skill-load trigger forces the agent to consult memory. If the agent doesn't read `AGENTS.md`, memory is invisible.
**Proposed direction**: OpenCode skill registration or session-start hook.

### I-02: Retrieval is manual keyword-only matching
**Status**: open
**Area**: retrieval
**Priority**: high
**Description**: Workflow says "read all of index.jsonl, filter by topic/tags." The agent must guess the right keywords. No fuzzy matching, no semantic search, no fallback. A memory tagged `["db","connection"]` is missed if the task says "database pool."
**Proposed direction**: CLI digest command with fuzzy matching; later, vector/semantic search.

### I-03: Write-side guardrails — no validation on index.jsonl
**Status**: open
**Area**: data integrity
**Priority**: high
**Description**: `index.jsonl` is edited directly by the AI. No schema validation. A typo in `type: "decison"` silently orphans the entry. No uniqueness check on `topic`. Corruption risk.
**Proposed direction**: `engram add` / `engram validate` commands enforce schema.

### I-04: Archive.jsonl move vs. soft-delete semantics
**Status**: open
**Area**: data lifecycle
**Priority**: medium
**Description**: Superseded entries move to `archive.jsonl`. The new entry can't inline-reference what it superseded without an `id` field. Cross-file lookup needs CLI support.
**Proposed direction**: Add `id` field (UUID or slug-hash) to entries. CLI resolves supersedes chain across index + archive.

---

## P1 — Quality of Life

### I-05: No query interface — raw file ops are the only path
**Status**: open
**Area**: tooling
**Priority**: medium
**Description**: Every read/write operation requires the AI to grep, parse JSONL, filter, open detail files. High friction, error-prone.
**Proposed direction**: `engram` CLI handles query, add, archive, digest, sync-views.

### I-06: No eviction policy — unbounded index growth
**Status**: open
**Area**: scalability
**Priority**: medium
**Description**: Over dozens of sessions, `index.jsonl + archive.jsonl` grows linearly. No TTL, no archival, no summarization for stale entries. "Read all entries at session start" eventually becomes expensive.
**Proposed direction**: Archive rotation policy (e.g., auto-archive entries older than N months). Configurable digest depth.

### I-07: Cross-project memory silos
**Status**: open
**Area**: scope
**Priority**: low
**Description**: Each repo has its own `memory/`. An agent working across multiple projects can't cross-reference. Patterns from project A are invisible in project B.
**Proposed direction**: Optional shared memory index via `--global` flag in CLI or symlink farm.

### I-08: by-module/ — generated or maintained?
**Status**: open
**Area**: views
**Priority**: low
**Description**: `by-module/` is a proposed directory for filtered views. Symlinks are fragile across platforms and need upkeep. A generated approach avoids rot but needs tooling.
**Proposed direction**: `engram sync-views` CLI command generates/updates `by-module/` from the index.

### I-09: Empty bootstrap — no self-referential entry
**Status**: open
**Area**: onboarding
**Priority**: low
**Description**: `index.jsonl` starts empty. There's nothing in memory that says "this is how memory works." The agent must find and parse the skill doc externally.
**Proposed direction**: Seed `index.jsonl` with a self-referential entry pointing to `.agents/skills/memory.md` on CLI init.

---

## P2 — Polish

### I-10: Schema richness — limited matching dimensions
**Status**: open
**Area**: schema
**Priority**: low
**Description**: Entries have `topic` (one slug) + `tags` (array). Missing `module`, `layer` (e.g. "frontend", "db", "api"), `importance` fields. Requires manual tagging redundancy.
**Proposed direction**: Add optional `module` and `layer` fields to schema. CLI `digest` can filter on them.

### I-11: Token awareness in the skill doc itself
**Status**: open
**Area**: documentation
**Priority**: low
**Description**: The skill doc is 84 lines. It tells agents to be token-conscious but is itself always loaded. Could be slimmed down.
**Proposed direction**: Split into quick-reference usage (always-loaded) vs. detailed spec (loaded on demand).

### I-12: Detail filename convention
**Status**: open
**Area**: naming
**Priority**: low
**Description**: Current convention `{topic}-{subtopic}-{type}.md` repeats module info already encoded in the subdirectory. `details/auth/jwt-spec-guards.md` vs `details/auth/auth-jwt-spec-guards.md`.
**Proposed direction**: Drop module prefix when inside a module subdirectory. Keep convention for root-level detail files.

---

## Legend

| Marking | Meaning |
|---------|---------|
| **P0** | Blocks correct operation |
| **P1** | Quality-of-life, non-blocking |
| **P2** | Nice-to-have, polish |
| **open** | Not yet addressed |
| **in-progress** | Being worked on |
| **resolved** | Fixed, keep for audit |
