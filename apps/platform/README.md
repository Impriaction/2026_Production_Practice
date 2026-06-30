# ODPlatform Platform Package

This package contains the `od_platform` source code for the platform app.

## Install

```bash
pip install -e .
```

## CLI

After installation, the package exposes:

```bash
odp-init
odp-reset
```

## Reset Preview

```bash
odp-reset
```

Preview the default runtime reset scope without deleting anything.

## Execute Reset

```bash
odp-reset --execute
odp-reset --execute --scope runtime-plus-raw
odp-reset --execute --scope full --force --yes
```

Real reset creates a backup archive under `apps/platform/meta_logging/reset_backups`
and writes an audit record under `apps/platform/meta_logging/reset_audit`.
