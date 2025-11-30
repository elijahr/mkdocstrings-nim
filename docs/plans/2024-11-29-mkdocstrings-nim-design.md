# mkdocstrings-nim Design Document

## Overview

A mkdocstrings handler for Nim that generates API documentation from Nim source code. Users write `::: module.name` directives in their markdown, and the handler renders beautiful API docs.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   nimdocinfo    │     │  Python Handler  │     │ Jinja Templates │
│   (Nim tool)    │ ──► │  (collect/render)│ ──► │   (HTML output) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
   Extracts AST            Parses docstrings        Renders final
   + raw docstrings        (RST/Google/etc)         HTML for page
```

## Components

### 1. nimdocinfo (Nim Tool)

A Nim CLI that extracts documentation data from source files using Nim's compiler AST APIs.

**Usage:**
```bash
nimdocinfo src/lockfreequeues/ops.nim > ops.json
```

**Output JSON Schema:**
```json
{
  "module": "lockfreequeues/ops",
  "file": "src/lockfreequeues/ops.nim",
  "doc": "Module description from doc comment.",
  "entries": [
    {
      "name": "validateHeadOrTail",
      "kind": "proc",
      "line": 10,
      "signature": "proc validateHeadOrTail(value: int; capacity: int): bool",
      "params": [
        {"name": "value", "type": "int"},
        {"name": "capacity", "type": "int"}
      ],
      "returns": "bool",
      "pragmas": ["inline"],
      "raises": [],
      "doc": ":param value: The value to check\n:param capacity: Queue capacity\n:returns: True if valid"
    },
    {
      "name": "Sipsic",
      "kind": "type",
      "line": 50,
      "signature": "type Sipsic[T] = object",
      "generics": [{"name": "T", "constraint": null}],
      "fields": [
        {"name": "head", "type": "Atomic[int]", "doc": "Consumer position"}
      ],
      "doc": "Single-producer single-consumer queue."
    }
  ]
}
```

**Supported kinds:**
- `proc`, `func`, `iterator`, `template`, `macro`
- `type` (object, enum, distinct, alias)
- `const`, `let`, `var`

**Key design decisions:**
- Raw docstrings returned as-is (Python parses them)
- Type info extracted from AST (not docstrings)
- Pragmas, raises, generics all captured

### 2. Python Handler

Located in `mkdocstrings_handlers/nim/`.

**Files:**
- `__init__.py` - Handler class, `get_handler()` entry point
- `collector.py` - Runs nimdocinfo, parses JSON, resolves identifiers
- `docstring.py` - Parses RST/Google/NumPy docstring formats
- `renderer.py` - Renders data to HTML via Jinja

**Handler Interface:**
```python
class NimHandler(BaseHandler):
    def collect(self, identifier: str, options: dict) -> CollectorItem:
        # 1. Resolve identifier to file path
        # 2. Run: nimdocinfo <path>
        # 3. Parse JSON
        # 4. Return data structure

    def render(self, data: CollectorItem, options: dict) -> str:
        # 1. Parse docstrings (RST/Google/etc)
        # 2. Merge param descriptions with AST types
        # 3. Apply Jinja template
        # 4. Return HTML string
```

**Identifier Format:**
```markdown
::: lockfreequeues.ops                    # Whole module
::: lockfreequeues.ops.validateHeadOrTail # Specific proc
::: lockfreequeues.sipsic.Sipsic          # Specific type
```

### 3. Jinja Templates

Located in `mkdocstrings_handlers/nim/templates/material/`.

**Template structure:**
```
templates/material/
├── _base/
│   ├── module.html.jinja
│   ├── proc.html.jinja
│   ├── func.html.jinja
│   ├── iterator.html.jinja
│   ├── template.html.jinja
│   ├── macro.html.jinja
│   ├── type.html.jinja
│   ├── const.html.jinja
│   ├── children.html.jinja
│   ├── signature.html.jinja
│   ├── labels.html.jinja
│   └── docstring/
│       ├── parameters.html.jinja
│       ├── returns.html.jinja
│       ├── raises.html.jinja
│       └── examples.html.jinja
├── summary/
│   ├── procs.html.jinja
│   ├── types.html.jinja
│   └── consts.html.jinja
├── module.html.jinja      # extends _base
├── proc.html.jinja
├── type.html.jinja
└── style.css
```

**Templates output HTML** (not markdown). Example rendered proc:
```html
<div class="doc doc-object doc-proc">
  <h3 id="validateHeadOrTail">
    <code>proc validateHeadOrTail(value: int; capacity: int): bool</code>
    <span class="doc-label">inline</span>
  </h3>
  <div class="doc doc-contents">
    <p>Assert that the given value is in the range 0..&lt;2*capacity.</p>
    <div class="doc-section doc-parameters">
      <h4>Parameters</h4>
      <ul>
        <li><code>value</code> (int) – The value to check</li>
        <li><code>capacity</code> (int) – Queue capacity</li>
      </ul>
    </div>
    <div class="doc-section doc-returns">
      <h4>Returns</h4>
      <p>bool – True if valid</p>
    </div>
  </div>
</div>
```

## Configuration

**mkdocs.yml:**
```yaml
plugins:
  - mkdocstrings:
      handlers:
        nim:
          paths: [src]              # Where to find .nim files
          docstring_style: rst      # rst | google | numpy
          show_source: true         # Link to source lines
          show_signature: true
          show_pragmas: true
```

**Per-directive options:**
```markdown
::: lockfreequeues.ops
    options:
      show_source: false
      members: [validateHeadOrTail, used]
```

## Project Structure

```
mkdocstrings-nim/
├── src/
│   └── nimdocinfo/
│       ├── nimdocinfo.nim       # CLI entry point
│       └── extractor.nim        # AST extraction logic
├── mkdocstrings_handlers/
│   └── nim/
│       ├── __init__.py          # Handler class
│       ├── collector.py         # Runs nimdocinfo
│       ├── docstring.py         # Docstring parser
│       ├── renderer.py          # Jinja rendering
│       └── templates/
│           └── material/        # Material theme templates
├── tests/
│   ├── test_collector.py
│   ├── test_docstring.py
│   └── fixtures/                # Sample Nim files
├── pyproject.toml               # Python package config
└── nimdocinfo.nimble            # Nim package config
```

## User Workflow

1. **Install:**
   ```bash
   pip install mkdocstrings-nim
   ```
   (nimdocinfo binary bundled with Python package)

2. **Configure mkdocs.yml:**
   ```yaml
   plugins:
     - mkdocstrings:
         handlers:
           nim:
             paths: [src]
   ```

3. **Write markdown:**
   ```markdown
   # API Reference

   ## Operations Module

   ::: lockfreequeues.ops
   ```

4. **Build:**
   ```bash
   mkdocs build   # or mkdocs serve
   ```

5. **Customize templates (optional):**
   ```yaml
   plugins:
     - mkdocstrings:
         custom_templates: templates/
   ```
   Then create `templates/nim/material/proc.html.jinja` to override.

## Docstring Format

Nim docstrings use RST (or Google/NumPy style if configured):

```nim
proc validateHeadOrTail*(value: int; capacity: int): bool {.inline.} =
  ## Assert that the given value is in the range 0..<2*capacity.
  ##
  ## :param value: The value to check
  ## :param capacity: Queue capacity
  ## :returns: True if valid, false otherwise
  ## :raises ValueError: If capacity is negative
  result = value >= 0 and value < 2 * capacity
```

Python parses these into structured data:
```python
{
  "description": "Assert that the given value is in the range 0..<2*capacity.",
  "params": [
    {"name": "value", "description": "The value to check"},
    {"name": "capacity", "description": "Queue capacity"}
  ],
  "returns": {"description": "True if valid, false otherwise"},
  "raises": [{"type": "ValueError", "description": "If capacity is negative"}]
}
```

Type info comes from AST (not docstrings), so `:type value: int` is not needed.

## Implementation Phases

### Phase 1: Core (MVP)
- [ ] nimdocinfo extracts procs, types, consts
- [ ] Python handler collect/render basics
- [ ] Templates for proc, type, const, module
- [ ] RST docstring parsing
- [ ] Basic Material theme support

### Phase 2: Polish
- [ ] iterators, templates, macros
- [ ] Google/NumPy docstring styles
- [ ] Cross-references between items
- [ ] Source code links
- [ ] TOC/summary tables

### Phase 3: Advanced
- [ ] Generics with constraints
- [ ] Effect system (raises, tags)
- [ ] Examples/runnableExamples extraction
- [ ] Search integration
- [ ] Additional themes

## Resolved Design Decisions

### 1. Binary Distribution
**Decision:** No bundling needed. Users have Nim installed (they're documenting Nim projects).

Python handler runs:
```bash
nim c -r /path/to/nimdocinfo.nim <source_file>
```

The nimdocinfo source is bundled with the Python package, compiled on first use.

### 2. Identifier Resolution
**Decision:** Convention-based (like Crystal handler), with future macro enhancement.

**Phase 1 (Simple):**
- Config `paths: [src]`
- Identifier `lockfreequeues.ops` → `src/lockfreequeues/ops.nim`
- Dots become directory separators

**Phase 2 (Advanced, if needed):**
Use Nim macro to resolve imports via compiler:
```nim
macro getModulePath(m: typed): string =
  result = newLit(m.getImpl.lineInfoObj.filename)

import lockfreequeues.ops
const path = getModulePath(ops)  # → actual file path
```

This handles nimble packages, complex setups, etc.

### 3. Cross-References
Build full module index on first access, cache it. Link types/procs across modules.

## References

- [mkdocstrings documentation](https://mkdocstrings.github.io/)
- [mkdocstrings-python handler](https://github.com/mkdocstrings/python)
- [mkdocstrings-crystal handler](https://github.com/mkdocstrings/crystal)
- [Nim compiler API](https://nim-lang.org/docs/compiler.html)
