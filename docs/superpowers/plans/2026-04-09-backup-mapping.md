# Backup Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist successful backup results into `artifacts/backup-mapping.json` so VM names and backup archive names are recorded locally.

**Architecture:** Add a focused JSON-array storage helper and wire it into `BackupService` so both single and batch backups reuse the same append logic. Keep file validation strict and fail loudly on invalid existing content.

**Tech Stack:** Python 3.10+, `json`, `pathlib`, `unittest`, existing service layer

---

### Task 1: Add failing tests for mapping persistence

**Files:**
- Modify: `tests/test_backup_service.py`

- [ ] **Step 1: Write failing tests for successful appends**

```python
def test_backup_vm_appends_mapping_record(self):
    ...
```

```python
def test_backup_all_vms_records_only_successful_items(self):
    ...
```

- [ ] **Step 2: Write failing test for invalid file content**

```python
def test_backup_vm_rejects_invalid_mapping_file(self):
    ...
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m unittest tests.test_backup_service`
Expected: FAIL because mapping persistence does not exist yet

### Task 2: Implement mapping storage and integrate it

**Files:**
- Create: `myt_cli/services/backup_mapping_store.py`
- Modify: `myt_cli/services/backup_service.py`

- [ ] **Step 1: Add JSON-array append helper**

```python
class BackupMappingStore:
    def append(self, *, vm_name: str, backup_name: str) -> None:
        ...
```

- [ ] **Step 2: Integrate store into `BackupService.backup_vm()`**

```python
self._mapping_store.append(...)
```

- [ ] **Step 3: Run tests to verify service passes**

Run: `python -m unittest tests.test_backup_service`
Expected: PASS

### Task 3: Document the mapping file

**Files:**
- Modify: `README.md`
- Modify: `config.example.yaml`

- [ ] **Step 1: Document `artifacts/backup-mapping.json`**

Explain that successful backups append VM name and backup name records there.

- [ ] **Step 2: Clarify batch behavior**

Document that `backup-all` writes one entry per successful VM and skips failed items.

### Task 4: Verify the completed change

**Files:**
- Verify: `tests/test_backup_service.py`
- Verify: `tests/test_cli.py`
- Verify: `tests/test_config.py`
- Verify: `tests/test_vm_service.py`

- [ ] **Step 1: Run the targeted suite**

Run: `python -m unittest tests.test_backup_service tests.test_cli tests.test_config tests.test_vm_service`
Expected: PASS
