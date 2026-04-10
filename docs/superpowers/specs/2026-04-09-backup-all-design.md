# Backup All Design

Date: 2026-04-09

## Goal

Add a batch backup capability that backs up every occupied VM slot on the box, skips empty slots, continues after individual failures, and reports a final summary.

## Scope

- Add a new CLI command: `backup-all`
- Expose the same behavior from the Python API
- Reuse the existing single-VM backup flow for each VM
- Skip entries that do not represent an occupied VM
- Continue processing after per-VM failures
- Return and print a structured summary

Out of scope:

- Parallel backups
- Retry logic
- Scheduled execution changes

## Behavior

### Input

- No per-VM name argument
- Uses the current box configuration and current VM list

### Occupied VM detection

An item from `list_vms()` is treated as occupied when it has a non-empty VM name. Items without a usable `name` are treated as empty slots and skipped.

### Execution flow

1. Read the VM list from the existing VM service
2. Filter to occupied VMs only
3. Run `backup_vm()` sequentially for each VM
4. Catch per-VM exceptions and continue
5. Return a summary with success and failure details

### Result shape

```python
{
    "total": 2,
    "success_count": 1,
    "failure_count": 1,
    "skipped_count": 1,
    "successes": [
        {"vm_name": "001", "vm_id": "vm-1", "status": "running", "export_name": "001.zip"}
    ],
    "failures": [
        {"vm_name": "002", "error": "Request failed"}
    ],
}
```

## Architecture

- `myt_cli/services/backup_service.py`
  - Owns batch backup orchestration and occupied-slot filtering
- `myt_cli/api.py`
  - Exposes `backup_all_vms()` for SDK parity
- `myt_cli/cli.py`
  - Adds `backup-all` command and summary rendering
- `tests/test_backup_service.py`
  - Covers sequential processing, skip behavior, and failure continuation
- `tests/test_cli.py`
  - Covers parser and output rendering

## Error handling

- A failure on one VM must not abort the rest of the batch
- The CLI command should complete normally and print the summary when at least one per-VM failure occurs
- Top-level failures before iteration starts, such as `list_vms()` failing, still surface as command failure

## Testing

- Service test for skipping empty slots
- Service test for continuing after one VM backup fails
- SDK test for exposing the new method
- CLI parser test for `backup-all`
- CLI formatter test for batch backup summaries
