# ADR-001: Adopt Monorepo with `apps/` Layout

| Item | Content |
|---|---|
| Status | Accepted |
| Date | 2026-06-30 |

## Context

ODPlatform currently starts from a single platform application, but the repository is expected to grow into multiple apps such as desktop, web backend, and web frontend. We need a layout that supports shared code, shared tooling, and future expansion with low migration cost.

## Options Considered

### Option A: Flat repository layout

Keep everything under one direct source tree without app boundaries.

### Option B: Monorepo with `apps/` layout

Group each application under `apps/`, while keeping shared workspace-level assets at the repository root.

### Option C: Multi-repo split

Create separate repositories for platform, backend, frontend, and desktop.

## Decision

Adopt **Option B: Monorepo with `apps/` layout**.

## Rationale

1. It creates clear boundaries for multiple applications.
2. Shared code and tooling remain easy to reuse.
3. Cross-app refactors can happen atomically in one repository.
4. Workspace-level assets such as `data`, `models`, `runs`, and `docs` stay naturally centralized.
5. It matches the expected growth path of ODPlatform better than a flat or split repository.

## Consequences

### Positive

- Easier multi-app expansion
- Shared infrastructure is simpler to maintain
- Cross-app testing and documentation have a natural home

### Negative

- Repository structure is slightly deeper
- Requires stronger path and packaging conventions

### Neutral

- Workspace root detection needs an explicit marker file such as `.odp-workspace`
- App-local packaging needs its own `pyproject.toml`

## Review Trigger

Revisit this decision if:

- the repository becomes too large to manage effectively, or
- team and release boundaries strongly diverge between applications
