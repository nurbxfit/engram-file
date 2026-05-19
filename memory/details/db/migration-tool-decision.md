# Database Migration Tool Decision

## Context

Evaluated Alembic vs. custom migration scripts for managing PostgreSQL schema changes.

## Decision

Use **Alembic** with auto-generation enabled.

## Reasons

- Auto-generation of migration scripts from model changes saves significant manual effort.
- Alembic's `downgrade` support is critical for rollback in CI/CD pipelines.
- Python-native (matches our stack), well-maintained, widely adopted.
- Built-in support for naming conventions for indexes/constraints.

## Conventions

- Each migration must have both `upgrade()` and `downgrade()`.
- Migration filenames follow `YYYY_MM_DD_{description}.py`.
- Run `alembic check` in CI to detect drift before deployment.
- Never edit a migration that has already been applied to production — create a new one instead.

## Trade-offs

Custom scripts would be simpler but lack auto-generation and community tooling. The added complexity of Alembic is worth the safety net.

## Status

Active. Applied since sprint 3.
