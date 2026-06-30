# Reset Project Runbook

## Purpose

Use `odp-reset` to clean generated project artifacts while preserving source code
and protected assets.

## Preview First

```bash
odp-reset
```

This shows:

- selected reset scope
- target directories
- file and directory counts
- estimated total size
- large cleanup warnings

## Real Execution

```bash
odp-reset --execute
```

Optional scopes:

```bash
odp-reset --execute --scope runtime-plus-raw
odp-reset --execute --scope full --force
```

For non-interactive usage:

```bash
odp-reset --execute --scope runtime --yes
odp-reset --execute --scope full --force --yes
```

## Safety Notes

- Backup zip files are written to `apps/platform/meta_logging/reset_backups`.
- Audit JSON files are written to `apps/platform/meta_logging/reset_audit`.
- Protected directories are never removed by the reset workflow.
- Always run the preview first before using `--execute`.

## Suggested Manual Validation

1. Generate dirty data with `scripts/make_disaster_data.ps1`.
2. Run `odp-reset` and review the preview.
3. Run `odp-reset --execute --yes`.
4. Confirm runtime directories are emptied and recreated.
5. Confirm backup and audit files were created.
