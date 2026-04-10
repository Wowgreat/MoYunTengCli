# Backup Mapping Design

Date: 2026-04-09

## Goal

Persist a local append-only record of successful backups so the project can track VM names and backup archive names outside the box API.

## Scope

- Store backup records in `artifacts/backup-mapping.json`
- Append one record after each successful single-VM backup
- Append one record per successful VM during `backup-all`
- Create the file automatically when missing
- Reject invalid existing file content instead of silently overwriting it

Out of scope:

- Using the mapping file for restore lookup
- User-defined aliases
- Deduplication or cleanup

## File format

The file is a JSON array. Each entry is an object:

```json
[
  {
    "vm_name": "1775617170315_1_T0001",
    "backup_name": "1775617170315_1_T0001-20260409103000.tar.gz",
    "created_at": "2026-04-09T10:30:00+08:00"
  }
]
```

## Behavior

### Successful single backup

After `backup_vm()` gets the final `export_name`, append a record to the mapping file.

### Successful batch backup

`backup-all` reuses `backup_vm()`, so each successful VM backup appends its own record. Failed items do not write entries.

### Missing file

If `artifacts/backup-mapping.json` does not exist, create its parent directory and initialize it as an empty array before appending.

### Invalid file

If the file exists but is not valid JSON or is not a JSON array, raise a `ConfigError`. Do not overwrite it.

## Architecture

- Add a small storage helper module for JSON-array persistence
- Inject it into `BackupService`
- Keep the write path inside the existing success path for `backup_vm()`

## Testing

- Single backup writes a new entry
- Two successful backups append two entries
- Invalid existing mapping file raises an error
- Batch backup only records successful items
