# Backup All Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `backup-all` capability that backs up every occupied VM slot, skips empty slots, continues after individual failures, and exposes the behavior through both CLI and SDK.

**Architecture:** Extend the existing backup service with a batch orchestration method that filters the VM list to occupied entries and reuses `backup_vm()` for each VM. Keep CLI and SDK thin by routing both through the new service method and adding only parser and formatter support.

**Tech Stack:** Python 3.10+, `argparse`, `unittest`, existing `MytApp` service layer

---

### Task 1: Add failing tests for batch backup behavior

**Files:**
- Modify: `tests/test_backup_service.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing service tests**

```python
def test_backup_all_vms_skips_empty_slots_and_continues_after_failures(self):
    ...
```

```python
def test_sdk_exposes_backup_all_vms(self):
    ...
```

- [ ] **Step 2: Write the failing CLI tests**

```python
def test_build_parser_supports_backup_all_command(self):
    ...
```

```python
def test_format_output_renders_backup_all_summary(self):
    ...
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m unittest tests.test_backup_service tests.test_cli`
Expected: FAIL because batch backup support does not exist yet

### Task 2: Implement batch backup in the service and SDK

**Files:**
- Modify: `myt_cli/services/backup_service.py`
- Modify: `myt_cli/api.py`

- [ ] **Step 1: Add `backup_all_vms()` to `BackupService`**

```python
def backup_all_vms(self) -> Dict[str, Any]:
    ...
```

- [ ] **Step 2: Add occupied-slot filtering helper**

```python
def _is_occupied_vm(self, item: Dict[str, Any]) -> bool:
    ...
```

- [ ] **Step 3: Expose `backup_all_vms()` from `MytApp`**

```python
def backup_all_vms(self) -> Dict:
    return self.backup_service.backup_all_vms()
```

- [ ] **Step 4: Run tests to verify service and SDK pass**

Run: `python -m unittest tests.test_backup_service`
Expected: PASS

### Task 3: Add CLI command and formatter

**Files:**
- Modify: `myt_cli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `backup-all` parser support**

```python
subparsers.add_parser("backup-all", help="Back up all occupied VM slots")
```

- [ ] **Step 2: Dispatch the new command**

```python
elif args.command == "backup-all":
    result = app.backup_all_vms()
```

- [ ] **Step 3: Add formatter for batch summary**

```python
def _format_backup_all_result(result: Dict[str, object]) -> str:
    ...
```

- [ ] **Step 4: Run tests to verify CLI passes**

Run: `python -m unittest tests.test_cli`
Expected: PASS

### Task 4: Document CLI and SDK usage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add CLI usage example**

```text
myt-cli --config config.yaml backup-all
```

- [ ] **Step 2: Add SDK usage example**

```python
summary = app.backup_all_vms()
print(summary)
```

- [ ] **Step 3: Document skip-and-continue behavior**

Note that the command skips empty slots and keeps running after individual VM backup failures.

### Task 5: Verify the completed change

**Files:**
- Verify: `tests/test_backup_service.py`
- Verify: `tests/test_cli.py`
- Verify: `tests/test_config.py`
- Verify: `tests/test_vm_service.py`

- [ ] **Step 1: Run the targeted suite**

Run: `python -m unittest tests.test_backup_service tests.test_cli tests.test_config tests.test_vm_service`
Expected: PASS
