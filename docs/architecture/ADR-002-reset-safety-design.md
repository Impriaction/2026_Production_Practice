# ADR-002 Reset Safety Design

## Status

Accepted

## Context

ODPlatform needs a project reset command that can clean generated artifacts
without risking source code, configs, documentation, scripts, or audit data.
The command must be safe enough for local development and scriptable enough
for CI or repeatable environment setup.

## Decision

We add `odp-reset` with the following safety model:

1. Default behavior is preview only.
2. Real deletion requires `--execute`.
3. High-risk `full` scope additionally requires `--force`.
4. Interactive execution requires explicit confirmation unless `--yes` is used.
5. Real execution creates a timestamped zip backup before deletion.
6. Every run writes an audit record under `apps/platform/meta_logging/reset_audit`.
7. Reset targets are limited by allowlist scope rules from `od_platform.common.paths`.
8. Protected paths are never removed, including source, docs, configs, scripts,
   pretrained models, workspace marker, and meta logging.

## Consequences

- Developers get a reversible and inspectable reset workflow.
- Default usage is safe for first-time users because it only previews.
- Full reset remains possible, but only behind stronger confirmation.
- The implementation stays aligned with the current monorepo path model.
