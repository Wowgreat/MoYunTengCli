# CLI And SDK Backup Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backup-listing capability that is available consistently from both the CLI and the Python SDK, while keeping backup and restore behavior aligned across both interfaces.

**Architecture:** Extend the existing backup service to own backup-list parsing and expose it through both `MytApp` and a new CLI subcommand. Keep the implementation thin by reusing `MytClient.list_backups()` and adding only formatting and documentation layers on top.

**Tech Stack:** Python 3.10+, `argparse`, `unittest`, existing `MytClient` / service layer

---

### Task 1: Add backup listing to the service and SDK

**Files:**
- Modify: `myt_cli/services/backup_service.py`
- Modify: `myt_cli/api.py`
- Test: `tests/test_backup_service.py`

- [ ] **Step 1: Write the failing test**

```python
def test_list_backups_returns_parsed_backup_items(self):
    client = StubClient(backups_response={"list": [{"name": "b1.tar.gz"}]})
    service = BackupService(client, StubVmService(), BackupConfig())
    assert service.list_backups() == [{"name": "b1.tar.gz"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_backup_service`
Expected: FAIL because `BackupService` does not yet expose `list_backups`

- [ ] **Step 3: Write minimal implementation**

```python
def list_backups(self, name: Optional[str] = None) -> List[Dict[str, Any]]:
    data = self._client.list_backups(name=name)
    return self._extract_items(data)
```

- [ ] **Step 4: Expose the method from `MytApp`**

```python
def list_backups(self, name: Optional[str] = None) -> List[Dict]:
    return self.backup_service.list_backups(name=name)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m unittest tests.test_backup_service`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add myt_cli/services/backup_service.py myt_cli/api.py tests/test_backup_service.py
git commit -m "feat: expose backup listing in sdk"
```

### Task 2: Add the `backups` CLI command and output formatting

**Files:**
- Modify: `myt_cli/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_format_output_renders_backup_list(self):
    rendered = _format_output([{"name": "b1.tar.gz"}])
    assert "b1.tar.gz" in rendered
```

```python
def test_build_parser_supports_backups_command(self):
    args = build_parser().parse_args(["backups"])
    assert args.command == "backups"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_cli`
Expected: FAIL because the command and formatter do not exist

- [ ] **Step 3: Write minimal implementation**

```python
backups_parser = subparsers.add_parser("backups", help="List backup archives")
backups_parser.add_argument("--name", help="Filter by backup file name")
```

```python
elif args.command == "backups":
    result = app.list_backups(args.name)
```

```python
def _format_backup_list(result: List[Dict[str, object]]) -> str:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_cli`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add myt_cli/cli.py tests/test_cli.py
git commit -m "feat: add backups cli command"
```

### Task 3: Document CLI and SDK parity for backups

**Files:**
- Modify: `README.md`
- Modify: `config.example.yaml` (only if examples need alignment)

- [ ] **Step 1: Add CLI usage example**

```text
myt-cli --config config.yaml backups
myt-cli --config config.yaml backups --name 1775617170315_1_T0001-2026040812-lD23Ug.tar.gz
```

- [ ] **Step 2: Add SDK usage example**

```python
from myt_cli import create_app_from_path

app = create_app_from_path("config.yaml")
print(app.list_backups())
```

- [ ] **Step 3: Clarify parity**

Document that backup listing is available from both CLI and SDK, and that backup naming still comes from the box export API.

- [ ] **Step 4: Commit**

```bash
git add README.md config.example.yaml
git commit -m "docs: document backup listing parity"
```

### Task 4: Run final verification and package smoke checks

**Files:**
- Verify: `tests/test_backup_service.py`
- Verify: `tests/test_cli.py`
- Verify: `tests/test_config.py`
- Verify: `tests/test_vm_service.py`

- [ ] **Step 1: Run the targeted test suite**

Run: `python -m unittest tests.test_backup_service tests.test_cli tests.test_config tests.test_vm_service`
Expected: PASS

- [ ] **Step 2: Build packages**

Run: `python -m build`
Expected: sdist and wheel created under `dist/`

- [ ] **Step 3: Check built packages**

Run: `python -m twine check dist/moyuntengcli-0.1.4.tar.gz dist/moyuntengcli-0.1.4-py3-none-any.whl`
Expected: PASSED

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: align backup listing across cli and sdk"
```
