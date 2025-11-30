# Packaging Fixes Design

## Problem

The mkdocstrings-nim handler has critical packaging issues that prevent it from working after `pip install`:

1. Templates/CSS not included in wheel
2. Nim extractor path resolution breaks outside dev environment
3. Nim source not bundled in package

## Solution

### Package Structure

```
mkdocstrings_handlers/
├── __init__.py              # Namespace package with extend_path
└── nim/
    ├── __init__.py
    ├── collector.py         # Modified path resolution
    ├── handler.py           # Add DocstringStyle validation
    ├── docstring.py
    ├── extractor/           # Moved from src/nimdocinfo/
    │   ├── extractor.nim
    │   └── nimdocinfo.nim
    └── templates/
        └── material/
            └── *.jinja
```

### Path Resolution

Use `importlib.resources` instead of relative path hacks:

```python
# Before (broken after install):
self._nimdocinfo_path = Path(__file__).parent.parent.parent / "src" / "nimdocinfo" / "nimdocinfo.nim"

# After (works everywhere):
from importlib.resources import files
self._nimdocinfo_path = files("mkdocstrings_handlers.nim.extractor").joinpath("nimdocinfo.nim")
```

### Compilation Strategy

Keep existing `nim c -r` approach - Nim handles its own compilation caching. No custom binary caching needed.

### pyproject.toml Configuration

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

### Error Handling

Fail fast with actionable error messages:

```python
raise CollectionError(
    "Nim compiler not found. Install from https://nim-lang.org/install.html\n"
    f"Then verify: nim c -r {source_path} {filepath}"
)
```

Add timeout to subprocess calls and validate DocstringStyle enum with fallback.

### Namespace Package

Explicit namespace using `extend_path`:

```python
# mkdocstrings_handlers/__init__.py
__path__ = __import__('pkgutil').extend_path(__path__, __name__)
```

## Files to Modify

1. `pyproject.toml` - packaging config
2. `mkdocstrings_handlers/__init__.py` - create namespace package
3. `mkdocstrings_handlers/nim/collector.py` - importlib.resources path resolution
4. `mkdocstrings_handlers/nim/handler.py` - DocstringStyle validation
5. Move `src/nimdocinfo/*.nim` → `mkdocstrings_handlers/nim/extractor/`
6. Delete `src/` directory

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Nim distribution | `nim c -r` at runtime | Users documenting Nim already have compiler |
| Path resolution | `importlib.resources` | Standard, works in all install scenarios |
| Binary caching | None | Nim compiler handles caching internally |
| Namespace package | Explicit `extend_path` | Maximum compatibility |
| Asset inclusion | Glob patterns | Simple, covers all file types |
