# Packaging Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix critical packaging issues so mkdocstrings-nim works after `pip install`.

**Architecture:** Move Nim extractor source into Python package, use `importlib.resources` for path resolution, configure hatch to include non-Python files.

**Tech Stack:** Python 3.9+, hatchling, importlib.resources

---

### Task 1: Move Nim Extractor Into Python Package

**Files:**
- Create: `mkdocstrings_handlers/nim/extractor/` directory
- Move: `src/nimdocinfo/extractor.nim` → `mkdocstrings_handlers/nim/extractor/extractor.nim`
- Move: `src/nimdocinfo/nimdocinfo.nim` → `mkdocstrings_handlers/nim/extractor/nimdocinfo.nim`
- Delete: `src/` directory

**Step 1: Create extractor directory**

```bash
mkdir -p mkdocstrings_handlers/nim/extractor
```

**Step 2: Move Nim source files**

```bash
mv src/nimdocinfo/extractor.nim mkdocstrings_handlers/nim/extractor/
mv src/nimdocinfo/nimdocinfo.nim mkdocstrings_handlers/nim/extractor/
```

**Step 3: Remove old src directory**

```bash
rm -rf src/
```

**Step 4: Verify files are in place**

```bash
ls -la mkdocstrings_handlers/nim/extractor/
```

Expected: `extractor.nim` and `nimdocinfo.nim` present

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: move Nim extractor into Python package"
```

---

### Task 2: Create Namespace Package Init

**Files:**
- Create: `mkdocstrings_handlers/__init__.py`

**Step 1: Create namespace package file**

Create `mkdocstrings_handlers/__init__.py`:

```python
"""mkdocstrings handlers namespace package."""
__path__ = __import__("pkgutil").extend_path(__path__, __name__)
```

**Step 2: Verify syntax**

```bash
python -c "import mkdocstrings_handlers; print('OK')"
```

Expected: `OK` (no import errors)

**Step 3: Commit**

```bash
git add mkdocstrings_handlers/__init__.py
git commit -m "feat: add explicit namespace package init"
```

---

### Task 3: Update pyproject.toml Packaging Config

**Files:**
- Modify: `pyproject.toml`

**Step 1: Update hatch build configuration**

Replace lines 41-42 in `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["mkdocstrings_handlers"]

[tool.hatch.build]
include = [
    "mkdocstrings_handlers/**/*.py",
    "mkdocstrings_handlers/**/*.jinja",
    "mkdocstrings_handlers/**/*.css",
    "mkdocstrings_handlers/**/*.nim",
]
```

**Step 2: Build wheel and verify contents**

```bash
pip install build
python -m build --wheel
unzip -l dist/*.whl | grep -E '\.(py|jinja|css|nim)$'
```

Expected: Should show `.py`, `.jinja`, `.css`, and `.nim` files from `mkdocstrings_handlers/`

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "fix: configure hatch to include templates and Nim source"
```

---

### Task 4: Update Collector Path Resolution

**Files:**
- Modify: `mkdocstrings_handlers/nim/collector.py:50-60`
- Test: `tests/test_collector.py` (new test)

**Step 1: Write failing test for path resolution**

Create/update `tests/test_collector.py`:

```python
"""Tests for collector path resolution."""
import pytest
from pathlib import Path
from mkdocstrings_handlers.nim.collector import NimCollector


def test_nimdocinfo_path_exists():
    """Test that nimdocinfo source path resolves correctly."""
    collector = NimCollector(paths=["src"], base_dir=Path.cwd())
    assert collector._nimdocinfo_path.exists(), f"Path not found: {collector._nimdocinfo_path}"
    assert collector._nimdocinfo_path.name == "nimdocinfo.nim"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_collector.py::test_nimdocinfo_path_exists -v
```

Expected: FAIL (path doesn't exist with old resolution)

**Step 3: Update collector.py imports**

Add at top of `mkdocstrings_handlers/nim/collector.py` (after existing imports):

```python
from importlib.resources import files, as_file
```

**Step 4: Update path resolution in __init__**

Replace line 60 in `mkdocstrings_handlers/nim/collector.py`:

Old:
```python
self._nimdocinfo_path = Path(__file__).parent.parent.parent / "src" / "nimdocinfo" / "nimdocinfo.nim"
```

New:
```python
# Use importlib.resources for reliable path resolution
extractor_files = files("mkdocstrings_handlers.nim").joinpath("extractor")
self._nimdocinfo_source = extractor_files.joinpath("nimdocinfo.nim")
```

**Step 5: Update _run_nimdocinfo to use new path**

Replace the subprocess call in `_run_nimdocinfo` (around line 103-109):

```python
def _run_nimdocinfo(self, filepath: Path) -> dict[str, Any]:
    """Run nimdocinfo on a Nim file.

    Args:
        filepath: Path to the Nim source file.

    Returns:
        Parsed JSON output from nimdocinfo.

    Raises:
        CollectionError: If nimdocinfo fails.
    """
    try:
        # Use context manager to get actual filesystem path
        with as_file(self._nimdocinfo_source) as nimdocinfo_path:
            result = subprocess.run(
                ["nim", "c", "-r", str(nimdocinfo_path), str(filepath)],
                capture_output=True,
                text=True,
                cwd=str(self.base_dir),
                timeout=60,
            )

            if result.returncode != 0:
                raise CollectionError(
                    f"nimdocinfo failed:\n{result.stderr}\n\n"
                    f"To debug, run manually:\n"
                    f"  nim c -r {nimdocinfo_path} {filepath}"
                )

            # Parse JSON from stdout (skip compiler hints)
            lines = result.stdout.strip().split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("{"):
                    in_json = True
                if in_json:
                    json_lines.append(line)
                if in_json and line.strip().startswith("}") and len(json_lines) > 1:
                    try:
                        return json.loads("\n".join(json_lines))
                    except json.JSONDecodeError:
                        continue

            if not json_lines:
                raise CollectionError(f"No JSON output from nimdocinfo: {result.stdout}")

            return json.loads("\n".join(json_lines))

    except FileNotFoundError:
        raise CollectionError(
            "Nim compiler not found. Install from https://nim-lang.org/install.html\n"
            "Then verify installation: nim --version"
        )
    except subprocess.TimeoutExpired:
        raise CollectionError(
            f"nimdocinfo timed out processing {filepath}. "
            "The file may be too complex or have circular imports."
        )
    except json.JSONDecodeError as e:
        raise CollectionError(f"Invalid JSON from nimdocinfo: {e}")
```

**Step 6: Update test to match new attribute name**

Update `tests/test_collector.py`:

```python
def test_nimdocinfo_path_exists():
    """Test that nimdocinfo source path resolves correctly."""
    collector = NimCollector(paths=["src"], base_dir=Path.cwd())
    # Use as_file to get actual path for checking
    from importlib.resources import as_file
    with as_file(collector._nimdocinfo_source) as path:
        assert path.exists(), f"Path not found: {path}"
        assert path.name == "nimdocinfo.nim"
```

**Step 7: Run test to verify it passes**

```bash
pytest tests/test_collector.py::test_nimdocinfo_path_exists -v
```

Expected: PASS

**Step 8: Run full test suite**

```bash
pytest -v
```

Expected: All tests pass

**Step 9: Commit**

```bash
git add mkdocstrings_handlers/nim/collector.py tests/test_collector.py
git commit -m "fix: use importlib.resources for nimdocinfo path resolution"
```

---

### Task 5: Add DocstringStyle Validation

**Files:**
- Modify: `mkdocstrings_handlers/nim/handler.py:105-106`
- Test: `tests/test_handler.py`

**Step 1: Write failing test for invalid style**

Add to `tests/test_handler.py`:

```python
def test_invalid_docstring_style_fallback(tmp_path, caplog):
    """Test that invalid docstring_style falls back to RST with warning."""
    import logging
    from mkdocstrings_handlers.nim.handler import NimHandler

    handler = NimHandler(paths=["src"], base_dir=tmp_path)
    options = handler.get_options({"docstring_style": "invalid_style"})

    # This should not raise, should fall back to RST
    # We need a minimal Nim file to test collect()
    nim_file = tmp_path / "src" / "test.nim"
    nim_file.parent.mkdir(parents=True, exist_ok=True)
    nim_file.write_text('proc foo*() = discard\n')

    with caplog.at_level(logging.WARNING):
        # Should not raise ValueError
        try:
            handler.collect("test", options)
        except Exception as e:
            # Collection may fail for other reasons (no Nim), but not ValueError
            assert "invalid_style" not in str(e)
```

**Step 2: Run test to verify current behavior**

```bash
pytest tests/test_handler.py::test_invalid_docstring_style_fallback -v
```

Expected: FAIL (ValueError raised for invalid enum value)

**Step 3: Update handler.py with validation**

Replace lines 104-106 in `mkdocstrings_handlers/nim/handler.py`:

Old:
```python
style_str = options.get("docstring_style", "rst")
style = DocstringStyle(style_str)
```

New:
```python
style_str = options.get("docstring_style", "rst")
try:
    style = DocstringStyle(style_str)
except ValueError:
    _logger.warning(
        f"Unknown docstring_style '{style_str}', falling back to 'rst'. "
        f"Valid options: {[s.value for s in DocstringStyle]}"
    )
    style = DocstringStyle.RST
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_handler.py::test_invalid_docstring_style_fallback -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add mkdocstrings_handlers/nim/handler.py tests/test_handler.py
git commit -m "fix: validate DocstringStyle with fallback and warning"
```

---

### Task 6: Clean Up and Final Verification

**Files:**
- Delete: `nimdocinfo.nimble` (if exists, was for separate Nim project)
- Verify: Full test suite passes
- Verify: Package builds and installs correctly

**Step 1: Remove nimble file if present**

```bash
rm -f nimdocinfo.nimble
```

**Step 2: Run full test suite**

```bash
pytest -v
```

Expected: All tests pass

**Step 3: Build and test install**

```bash
pip install build
python -m build
pip install dist/*.whl --force-reinstall
```

**Step 4: Test import after install**

```bash
python -c "from mkdocstrings_handlers.nim import get_handler; print('Import OK')"
```

Expected: `Import OK`

**Step 5: Commit cleanup**

```bash
git add -A
git commit -m "chore: clean up packaging artifacts"
```

---

## Verification Checklist

After all tasks complete:

- [ ] `pytest -v` passes all tests
- [ ] `python -m build` creates wheel without errors
- [ ] Wheel contains `.nim`, `.jinja`, `.css` files
- [ ] Fresh `pip install dist/*.whl` works
- [ ] `from mkdocstrings_handlers.nim import get_handler` works after install
- [ ] Handler can collect docs from a Nim file (requires Nim installed)
