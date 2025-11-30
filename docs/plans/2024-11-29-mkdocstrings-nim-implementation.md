# mkdocstrings-nim Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a mkdocstrings handler that generates API documentation from Nim source code.

**Architecture:** Two components - a Nim CLI (`nimdocinfo`) that extracts AST data to JSON, and a Python mkdocstrings handler that runs the CLI, parses docstrings, and renders HTML via Jinja templates.

**Tech Stack:** Nim (compiler APIs), Python (mkdocstrings, Jinja2), Material theme templates.

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `nimdocinfo.nimble`
- Create: `mkdocstrings_handlers/nim/__init__.py`
- Create: `src/nimdocinfo/nimdocinfo.nim`
- Create: `tests/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mkdocstrings-nim"
version = "0.1.0"
description = "A Nim handler for mkdocstrings"
readme = "README.md"
license = "MIT"
requires-python = ">=3.9"
authors = [
    { name = "Elijah Rutschman" }
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Documentation",
    "Topic :: Software Development :: Documentation",
]
dependencies = [
    "mkdocstrings>=0.20",
    "Jinja2>=3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "mkdocs-material",
]

[project.entry-points."mkdocstrings.handlers"]
nim = "mkdocstrings_handlers.nim:get_handler"

[tool.hatch.build.targets.wheel]
packages = ["mkdocstrings_handlers", "src"]
```

**Step 2: Create nimdocinfo.nimble**

```nim
# Package
version       = "0.1.0"
author        = "Elijah Rutschman"
description   = "Extract documentation data from Nim source files"
license       = "MIT"
srcDir        = "src"
bin           = @["nimdocinfo/nimdocinfo"]

# Dependencies
requires "nim >= 2.0.0"
```

**Step 3: Create handler __init__.py**

```python
"""Nim handler for mkdocstrings."""

from mkdocstrings_handlers.nim.handler import NimHandler, get_handler

__all__ = ["NimHandler", "get_handler"]
```

**Step 4: Create placeholder nimdocinfo.nim**

```nim
## nimdocinfo - Extract documentation from Nim source files
import std/[json, os]

when isMainModule:
  if paramCount() < 1:
    echo "Usage: nimdocinfo <file.nim>"
    quit(1)

  let filepath = paramStr(1)
  if not fileExists(filepath):
    echo "Error: File not found: ", filepath
    quit(1)

  # Placeholder - will implement extraction
  echo %*{
    "module": "placeholder",
    "file": filepath,
    "doc": "",
    "entries": []
  }
```

**Step 5: Create tests/__init__.py**

```python
"""Tests for mkdocstrings-nim."""
```

**Step 6: Verify structure**

Run: `find . -type f -name "*.py" -o -name "*.nim" -o -name "*.toml" -o -name "*.nimble" | grep -v __pycache__ | sort`

Expected:
```
./mkdocstrings_handlers/nim/__init__.py
./nimdocinfo.nimble
./pyproject.toml
./src/nimdocinfo/nimdocinfo.nim
./tests/__init__.py
```

**Step 7: Test Nim placeholder compiles**

Run: `nim c -r src/nimdocinfo/nimdocinfo.nim src/nimdocinfo/nimdocinfo.nim`

Expected: JSON output with placeholder data

**Step 8: Commit**

```bash
git init
git add -A
git commit -m "feat: initial project scaffolding"
```

---

## Task 2: nimdocinfo - Parse Nim AST

**Files:**
- Modify: `src/nimdocinfo/nimdocinfo.nim`
- Create: `src/nimdocinfo/extractor.nim`
- Create: `tests/fixtures/simple.nim`

**Step 1: Create test fixture**

```nim
## A simple test module for documentation extraction.
##
## This module contains examples of procs, types, and constants.

const
  MaxSize* = 100  ## Maximum allowed size

type
  MyObject* = object
    ## A simple object type.
    name*: string  ## The name field
    value*: int    ## The value field

proc greet*(name: string): string =
  ## Greet someone by name.
  ##
  ## :param name: The name to greet
  ## :returns: A greeting message
  result = "Hello, " & name & "!"

proc add*(a, b: int): int {.inline.} =
  ## Add two integers.
  ##
  ## :param a: First number
  ## :param b: Second number
  ## :returns: Sum of a and b
  result = a + b
```

**Step 2: Create extractor module**

```nim
## AST extraction logic for nimdocinfo
import std/[json, strutils, sequtils]
import compiler/[ast, parser, idents, options, pathutils, lineinfos, msgs]
import compiler/[modulegraphs, passes, sem, passaux, condsyms]

type
  DocEntry* = object
    name*: string
    kind*: string
    line*: int
    signature*: string
    params*: seq[tuple[name, typ: string]]
    returns*: string
    pragmas*: seq[string]
    doc*: string

  ModuleDoc* = object
    module*: string
    file*: string
    doc*: string
    entries*: seq[DocEntry]

proc extractDocComment(n: PNode): string =
  ## Extract doc comment from a node
  if n == nil:
    return ""
  if n.comment.len > 0:
    return n.comment.strip
  return ""

proc extractPragmas(n: PNode): seq[string] =
  ## Extract pragma names from a pragma node
  result = @[]
  if n == nil or n.kind != nkPragma:
    return
  for child in n:
    if child.kind == nkIdent:
      result.add($child.ident.s)
    elif child.kind == nkExprColonExpr and child[0].kind == nkIdent:
      result.add($child[0].ident.s)

proc extractParams(n: PNode): seq[tuple[name, typ: string]] =
  ## Extract parameter list from formal params
  result = @[]
  if n == nil or n.kind != nkFormalParams:
    return
  # Skip first child (return type)
  for i in 1..<n.len:
    let param = n[i]
    if param.kind == nkIdentDefs:
      let typNode = param[^2]
      let typStr = if typNode.kind == nkEmpty: "auto" else: $typNode
      # All names except last two (type and default)
      for j in 0..<param.len - 2:
        if param[j].kind == nkIdent:
          result.add(($param[j].ident.s, typStr))

proc extractReturnType(n: PNode): string =
  ## Extract return type from formal params
  if n == nil or n.kind != nkFormalParams or n.len == 0:
    return ""
  let retNode = n[0]
  if retNode.kind == nkEmpty:
    return ""
  return $retNode

proc renderSignature(n: PNode, kind: string): string =
  ## Render full signature as string
  # Simplified - just use repr for now
  result = kind & " " & $n[0]  # name
  if n.len > 1 and n[1].kind == nkFormalParams:
    let params = n[1]
    var paramStrs: seq[string] = @[]
    for i in 1..<params.len:
      paramStrs.add($params[i])
    result &= "(" & paramStrs.join("; ") & ")"
    let ret = extractReturnType(n[1])
    if ret.len > 0:
      result &= ": " & ret

proc extractProc(n: PNode, kind: string): DocEntry =
  ## Extract documentation from a proc/func/etc definition
  result.name = $n[0].ident.s
  result.kind = kind
  result.line = n.info.line.int
  result.doc = extractDocComment(n)

  if n.len > 1:
    result.params = extractParams(n[1])
    result.returns = extractReturnType(n[1])

  # Find pragma node
  for child in n:
    if child.kind == nkPragma:
      result.pragmas = extractPragmas(child)
      break

  result.signature = renderSignature(n, kind)

proc extractType(n: PNode): DocEntry =
  ## Extract documentation from a type definition
  result.kind = "type"
  result.doc = extractDocComment(n)
  result.line = n.info.line.int

  if n[0].kind == nkIdent:
    result.name = $n[0].ident.s
  elif n[0].kind == nkPostfix and n[0][1].kind == nkIdent:
    result.name = $n[0][1].ident.s

  result.signature = "type " & result.name

proc extractConst(n: PNode): DocEntry =
  ## Extract documentation from a const definition
  result.kind = "const"
  result.doc = extractDocComment(n)
  result.line = n.info.line.int

  if n[0].kind == nkIdent:
    result.name = $n[0].ident.s
  elif n[0].kind == nkPostfix and n[0][1].kind == nkIdent:
    result.name = $n[0][1].ident.s

  result.signature = "const " & result.name

proc extractModule*(filepath: string): ModuleDoc =
  ## Extract all documentation from a Nim source file
  result.file = filepath
  result.module = filepath.splitFile.name
  result.entries = @[]

  # Parse the file
  var conf = newConfigRef()
  conf.verbosity = 0

  let fileIdx = fileInfoIdx(conf, AbsoluteFile(filepath))
  var parser: Parser

  let source = readFile(filepath)
  openParser(parser, fileIdx, llStreamOpen(source), newIdentCache(), conf)

  let ast = parseAll(parser)
  closeParser(parser)

  # Extract module doc comment
  if ast.len > 0 and ast[0].comment.len > 0:
    result.doc = ast[0].comment.strip

  # Walk AST
  proc walk(n: PNode) =
    if n == nil:
      return

    case n.kind
    of nkProcDef:
      result.entries.add extractProc(n, "proc")
    of nkFuncDef:
      result.entries.add extractProc(n, "func")
    of nkIteratorDef:
      result.entries.add extractProc(n, "iterator")
    of nkTemplateDef:
      result.entries.add extractProc(n, "template")
    of nkMacroDef:
      result.entries.add extractProc(n, "macro")
    of nkTypeDef:
      result.entries.add extractType(n)
    of nkConstDef:
      result.entries.add extractConst(n)
    else:
      for child in n:
        walk(child)

  walk(ast)

proc toJson*(doc: ModuleDoc): JsonNode =
  ## Convert module documentation to JSON
  result = %*{
    "module": doc.module,
    "file": doc.file,
    "doc": doc.doc,
    "entries": []
  }

  for entry in doc.entries:
    var entryJson = %*{
      "name": entry.name,
      "kind": entry.kind,
      "line": entry.line,
      "signature": entry.signature,
      "doc": entry.doc
    }

    if entry.params.len > 0:
      entryJson["params"] = %entry.params.mapIt(%*{"name": it.name, "type": it.typ})

    if entry.returns.len > 0:
      entryJson["returns"] = %entry.returns

    if entry.pragmas.len > 0:
      entryJson["pragmas"] = %entry.pragmas

    result["entries"].add entryJson
```

**Step 3: Update nimdocinfo.nim main**

```nim
## nimdocinfo - Extract documentation from Nim source files
import std/[json, os]
import extractor

when isMainModule:
  if paramCount() < 1:
    echo "Usage: nimdocinfo <file.nim>"
    quit(1)

  let filepath = paramStr(1)
  if not fileExists(filepath):
    echo "Error: File not found: ", filepath
    quit(1)

  let doc = extractModule(filepath)
  echo doc.toJson.pretty
```

**Step 4: Test extraction on fixture**

Run: `nim c -r src/nimdocinfo/nimdocinfo.nim tests/fixtures/simple.nim`

Expected: JSON with module, doc, and entries for MaxSize, MyObject, greet, add

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement nimdocinfo AST extraction"
```

---

## Task 3: Python Handler - Basic Structure

**Files:**
- Create: `mkdocstrings_handlers/nim/handler.py`
- Create: `mkdocstrings_handlers/nim/collector.py`
- Create: `tests/test_handler.py`

**Step 1: Create collector.py**

```python
"""Collector for Nim documentation."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mkdocstrings import CollectionError


@dataclass
class NimParam:
    """A Nim parameter."""
    name: str
    type: str
    description: str = ""


@dataclass
class NimEntry:
    """A documented Nim entry (proc, type, const, etc.)."""
    name: str
    kind: str
    line: int
    signature: str
    doc: str = ""
    params: list[NimParam] = field(default_factory=list)
    returns: str = ""
    returns_doc: str = ""
    pragmas: list[str] = field(default_factory=list)
    raises: list[str] = field(default_factory=list)


@dataclass
class NimModule:
    """A documented Nim module."""
    module: str
    file: str
    doc: str = ""
    entries: list[NimEntry] = field(default_factory=list)


class NimCollector:
    """Collects documentation from Nim source files."""

    def __init__(self, paths: list[str], base_dir: Path):
        """Initialize the collector.

        Args:
            paths: Search paths for Nim source files.
            base_dir: Base directory of the project.
        """
        self.paths = paths
        self.base_dir = base_dir
        self._cache: dict[str, NimModule] = {}
        self._nimdocinfo_path = Path(__file__).parent.parent.parent / "src" / "nimdocinfo" / "nimdocinfo.nim"

    def _resolve_identifier(self, identifier: str) -> Path:
        """Resolve a module identifier to a file path.

        Args:
            identifier: Module identifier like 'lockfreequeues.ops'

        Returns:
            Path to the Nim source file.

        Raises:
            CollectionError: If the file cannot be found.
        """
        # Convert dots to path separators
        rel_path = identifier.replace(".", "/") + ".nim"

        for search_path in self.paths:
            full_path = self.base_dir / search_path / rel_path
            if full_path.exists():
                return full_path

        # Try without nested path (just filename)
        filename = identifier.split(".")[-1] + ".nim"
        for search_path in self.paths:
            full_path = self.base_dir / search_path / filename
            if full_path.exists():
                return full_path

        raise CollectionError(f"Could not find Nim file for identifier: {identifier}")

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
            result = subprocess.run(
                ["nim", "c", "-r", str(self._nimdocinfo_path), str(filepath)],
                capture_output=True,
                text=True,
                cwd=str(self.base_dir),
            )

            if result.returncode != 0:
                raise CollectionError(f"nimdocinfo failed: {result.stderr}")

            # Parse JSON from stdout (skip compiler hints)
            lines = result.stdout.strip().split("\n")
            json_line = next((l for l in reversed(lines) if l.startswith("{")), None)

            if not json_line:
                raise CollectionError(f"No JSON output from nimdocinfo: {result.stdout}")

            return json.loads(json_line)

        except FileNotFoundError:
            raise CollectionError("Nim compiler not found. Is Nim installed?")
        except json.JSONDecodeError as e:
            raise CollectionError(f"Invalid JSON from nimdocinfo: {e}")

    def _parse_module(self, data: dict[str, Any]) -> NimModule:
        """Parse JSON data into NimModule.

        Args:
            data: JSON data from nimdocinfo.

        Returns:
            Parsed NimModule.
        """
        entries = []
        for entry_data in data.get("entries", []):
            params = [
                NimParam(name=p["name"], type=p["type"])
                for p in entry_data.get("params", [])
            ]

            entries.append(NimEntry(
                name=entry_data["name"],
                kind=entry_data["kind"],
                line=entry_data["line"],
                signature=entry_data["signature"],
                doc=entry_data.get("doc", ""),
                params=params,
                returns=entry_data.get("returns", ""),
                pragmas=entry_data.get("pragmas", []),
            ))

        return NimModule(
            module=data["module"],
            file=data["file"],
            doc=data.get("doc", ""),
            entries=entries,
        )

    def collect(self, identifier: str) -> NimModule:
        """Collect documentation for a module identifier.

        Args:
            identifier: Module identifier like 'lockfreequeues.ops'

        Returns:
            NimModule with documentation.
        """
        if identifier in self._cache:
            return self._cache[identifier]

        filepath = self._resolve_identifier(identifier)
        data = self._run_nimdocinfo(filepath)
        module = self._parse_module(data)

        self._cache[identifier] = module
        return module
```

**Step 2: Create handler.py**

```python
"""Nim handler for mkdocstrings."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, MutableMapping

from mkdocstrings import BaseHandler, CollectorItem, HandlerOptions, get_logger

from mkdocstrings_handlers.nim.collector import NimCollector, NimModule

_logger = get_logger(__name__)


class NimHandler(BaseHandler):
    """The Nim handler class."""

    name: ClassVar[str] = "nim"
    domain: ClassVar[str] = "nim"
    fallback_theme: ClassVar[str] = "material"

    def __init__(
        self,
        paths: list[str],
        base_dir: Path,
        **kwargs: Any,
    ) -> None:
        """Initialize the handler.

        Args:
            paths: Search paths for Nim source files.
            base_dir: Base directory of the project.
            **kwargs: Additional arguments for BaseHandler.
        """
        super().__init__(**kwargs)
        self.paths = paths or ["src"]
        self.base_dir = base_dir
        self.collector = NimCollector(self.paths, base_dir)

    def get_options(self, local_options: MutableMapping[str, Any]) -> HandlerOptions:
        """Get combined options.

        Args:
            local_options: Local options from the directive.

        Returns:
            Combined options.
        """
        defaults = {
            "show_source": True,
            "show_signature": True,
            "show_pragmas": True,
            "heading_level": 2,
            "docstring_style": "rst",
        }
        return {**defaults, **local_options}

    def collect(self, identifier: str, options: HandlerOptions) -> CollectorItem:
        """Collect documentation for an identifier.

        Args:
            identifier: Module or item identifier.
            options: Collection options.

        Returns:
            Collected documentation data.
        """
        _logger.debug(f"Collecting {identifier}")
        return self.collector.collect(identifier)

    def render(self, data: CollectorItem, options: HandlerOptions) -> str:
        """Render collected data to HTML.

        Args:
            data: Collected documentation data.
            options: Rendering options.

        Returns:
            Rendered HTML string.
        """
        if not isinstance(data, NimModule):
            raise TypeError(f"Expected NimModule, got {type(data)}")

        template = self.env.get_template("module.html.jinja")
        return template.render(
            module=data,
            config=options,
            heading_level=options.get("heading_level", 2),
            root=True,
        )


def get_handler(
    handler_config: MutableMapping[str, Any],
    tool_config: Any,
    **kwargs: Any,
) -> NimHandler:
    """Return a NimHandler instance.

    Args:
        handler_config: Handler configuration from mkdocs.yml.
        tool_config: MkDocs configuration.
        **kwargs: Additional arguments.

    Returns:
        NimHandler instance.
    """
    base_dir = Path(getattr(tool_config, "config_file_path", "./mkdocs.yml")).parent
    paths = handler_config.get("paths", ["src"])

    return NimHandler(
        paths=paths,
        base_dir=base_dir,
        **kwargs,
    )
```

**Step 3: Write handler test**

```python
"""Tests for the Nim handler."""

import pytest
from pathlib import Path

from mkdocstrings_handlers.nim.handler import NimHandler, get_handler
from mkdocstrings_handlers.nim.collector import NimCollector, NimModule


class TestNimCollector:
    """Tests for NimCollector."""

    def test_resolve_identifier_simple(self, tmp_path: Path):
        """Test resolving a simple identifier."""
        # Create test file
        src = tmp_path / "src"
        src.mkdir()
        (src / "mymodule.nim").write_text("## Test module")

        collector = NimCollector(["src"], tmp_path)
        path = collector._resolve_identifier("mymodule")

        assert path == src / "mymodule.nim"

    def test_resolve_identifier_nested(self, tmp_path: Path):
        """Test resolving a nested identifier."""
        # Create nested structure
        src = tmp_path / "src" / "package"
        src.mkdir(parents=True)
        (src / "submodule.nim").write_text("## Test module")

        collector = NimCollector(["src"], tmp_path)
        path = collector._resolve_identifier("package.submodule")

        assert path == src / "submodule.nim"


class TestNimHandler:
    """Tests for NimHandler."""

    def test_get_options_defaults(self):
        """Test default options."""
        handler = NimHandler(paths=["src"], base_dir=Path("."))
        options = handler.get_options({})

        assert options["show_source"] is True
        assert options["heading_level"] == 2

    def test_get_options_override(self):
        """Test option override."""
        handler = NimHandler(paths=["src"], base_dir=Path("."))
        options = handler.get_options({"show_source": False})

        assert options["show_source"] is False
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_handler.py -v`

Expected: Tests pass (some may skip if nimdocinfo not compiled)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement Python handler and collector"
```

---

## Task 4: Adapt Templates for Nim

**Files:**
- Modify: `mkdocstrings_handlers/nim/templates/material/_base/function.html.jinja` → rename to `proc.html.jinja`
- Create: `mkdocstrings_handlers/nim/templates/material/_base/func.html.jinja`
- Create: `mkdocstrings_handlers/nim/templates/material/_base/iterator.html.jinja`
- Create: `mkdocstrings_handlers/nim/templates/material/_base/const.html.jinja`
- Modify: `mkdocstrings_handlers/nim/templates/material/_base/module.html.jinja`
- Modify: `mkdocstrings_handlers/nim/templates/material/module.html.jinja`

**Step 1: Rename function.html.jinja to proc.html.jinja**

Run:
```bash
mv mkdocstrings_handlers/nim/templates/material/_base/function.html.jinja mkdocstrings_handlers/nim/templates/material/_base/proc.html.jinja
mv mkdocstrings_handlers/nim/templates/material/function.html.jinja mkdocstrings_handlers/nim/templates/material/proc.html.jinja
```

**Step 2: Update proc.html.jinja extends**

Edit `mkdocstrings_handlers/nim/templates/material/proc.html.jinja`:
```jinja
{% extends "_base/proc.html.jinja" %}
```

**Step 3: Create simplified _base/proc.html.jinja**

Replace `mkdocstrings_handlers/nim/templates/material/_base/proc.html.jinja` with:

```jinja
{#- Template for Nim procs/funcs/iterators/etc.

Context:
  entry (NimEntry): The entry to render.
  root (bool): Whether this is the root object.
  heading_level (int): The HTML heading level to use.
  config (dict): The configuration options.
-#}

<div class="doc doc-object doc-{{ entry.kind }}">
  {% set html_id = entry.name %}

  {% if root or config.show_root_heading %}
    <h{{ heading_level }} id="{{ html_id }}" class="doc doc-heading">
      {% if config.show_symbol_type_heading %}
        <code class="doc-symbol doc-symbol-heading doc-symbol-{{ entry.kind }}"></code>
      {% endif %}
      <span class="doc doc-object-name doc-{{ entry.kind }}-name">{{ entry.name }}</span>
      {% if entry.pragmas %}
        {% for pragma in entry.pragmas %}
          <span class="doc-label" data-label="{{ pragma }}">{{ pragma }}</span>
        {% endfor %}
      {% endif %}
    </h{{ heading_level }}>
  {% endif %}

  {% if config.show_signature %}
    <div class="doc-signature highlight">
      <pre><code class="language-nim">{{ entry.signature }}</code></pre>
    </div>
  {% endif %}

  <div class="doc doc-contents {% if root %}first{% endif %}">
    {% if entry.doc %}
      <div class="doc-description">
        <p>{{ entry.doc }}</p>
      </div>
    {% endif %}

    {% if entry.params %}
      <div class="doc-section doc-section-parameters">
        <h{{ heading_level + 1 }}>Parameters</h{{ heading_level + 1 }}>
        <ul>
          {% for param in entry.params %}
            <li>
              <code>{{ param.name }}</code>
              (<code>{{ param.type }}</code>)
              {% if param.description %} – {{ param.description }}{% endif %}
            </li>
          {% endfor %}
        </ul>
      </div>
    {% endif %}

    {% if entry.returns %}
      <div class="doc-section doc-section-returns">
        <h{{ heading_level + 1 }}>Returns</h{{ heading_level + 1 }}>
        <p><code>{{ entry.returns }}</code>{% if entry.returns_doc %} – {{ entry.returns_doc }}{% endif %}</p>
      </div>
    {% endif %}

    {% if config.show_source and entry.line %}
      <div class="doc-source">
        <span class="doc-source-label">Source:</span>
        <code>line {{ entry.line }}</code>
      </div>
    {% endif %}
  </div>
</div>
```

**Step 4: Create func.html.jinja, iterator.html.jinja (symlinks to proc)**

```bash
cd mkdocstrings_handlers/nim/templates/material/_base
ln -s proc.html.jinja func.html.jinja
ln -s proc.html.jinja iterator.html.jinja
ln -s proc.html.jinja template.html.jinja
ln -s proc.html.jinja macro.html.jinja
cd ../../../../..
```

**Step 5: Create const.html.jinja**

Create `mkdocstrings_handlers/nim/templates/material/_base/const.html.jinja`:

```jinja
{#- Template for Nim constants.

Context:
  entry (NimEntry): The entry to render.
  root (bool): Whether this is the root object.
  heading_level (int): The HTML heading level to use.
  config (dict): The configuration options.
-#}

<div class="doc doc-object doc-const">
  {% set html_id = entry.name %}

  <h{{ heading_level }} id="{{ html_id }}" class="doc doc-heading">
    <code class="doc-symbol doc-symbol-heading doc-symbol-const"></code>
    <span class="doc doc-object-name doc-const-name">{{ entry.name }}</span>
  </h{{ heading_level }}>

  {% if config.show_signature %}
    <div class="doc-signature highlight">
      <pre><code class="language-nim">{{ entry.signature }}</code></pre>
    </div>
  {% endif %}

  <div class="doc doc-contents">
    {% if entry.doc %}
      <div class="doc-description">
        <p>{{ entry.doc }}</p>
      </div>
    {% endif %}
  </div>
</div>
```

**Step 6: Create simplified module.html.jinja**

Replace `mkdocstrings_handlers/nim/templates/material/_base/module.html.jinja`:

```jinja
{#- Template for Nim modules.

Context:
  module (NimModule): The module to render.
  root (bool): Whether this is the root object.
  heading_level (int): The HTML heading level to use.
  config (dict): The configuration options.
-#}

<div class="doc doc-object doc-module">
  {% set html_id = module.module %}

  <h{{ heading_level }} id="{{ html_id }}" class="doc doc-heading">
    <code class="doc-symbol doc-symbol-heading doc-symbol-module"></code>
    <span class="doc doc-object-name doc-module-name">{{ module.module }}</span>
  </h{{ heading_level }}>

  <div class="doc doc-contents first">
    {% if module.doc %}
      <div class="doc-description">
        {{ module.doc }}
      </div>
    {% endif %}

    {% for entry in module.entries %}
      {% set template_name = entry.kind ~ ".html.jinja" %}
      {% include template_name %}
    {% endfor %}
  </div>
</div>
```

**Step 7: Update top-level module.html.jinja**

Edit `mkdocstrings_handlers/nim/templates/material/module.html.jinja`:

```jinja
{% extends "_base/module.html.jinja" %}
```

**Step 8: Commit**

```bash
git add -A
git commit -m "feat: adapt templates for Nim (proc, func, iterator, const, module)"
```

---

## Task 5: Docstring Parser

**Files:**
- Create: `mkdocstrings_handlers/nim/docstring.py`
- Create: `tests/test_docstring.py`

**Step 1: Write docstring parser test**

```python
"""Tests for docstring parsing."""

import pytest
from mkdocstrings_handlers.nim.docstring import parse_docstring, DocstringStyle


class TestRstDocstring:
    """Tests for RST-style docstring parsing."""

    def test_parse_simple(self):
        """Test parsing a simple docstring."""
        doc = "A simple description."
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert result.description == "A simple description."
        assert result.params == []
        assert result.returns is None

    def test_parse_with_params(self):
        """Test parsing docstring with parameters."""
        doc = """Do something.

        :param name: The name to use
        :param value: The value to set
        """
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert result.description == "Do something."
        assert len(result.params) == 2
        assert result.params[0].name == "name"
        assert result.params[0].description == "The name to use"

    def test_parse_with_returns(self):
        """Test parsing docstring with return value."""
        doc = """Calculate sum.

        :param a: First number
        :returns: The sum
        """
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert result.returns.description == "The sum"

    def test_parse_with_raises(self):
        """Test parsing docstring with raises."""
        doc = """Do risky thing.

        :raises ValueError: If value is invalid
        """
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert len(result.raises) == 1
        assert result.raises[0].type == "ValueError"
        assert result.raises[0].description == "If value is invalid"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_docstring.py -v`

Expected: FAIL with "No module named 'mkdocstrings_handlers.nim.docstring'"

**Step 3: Implement docstring parser**

Create `mkdocstrings_handlers/nim/docstring.py`:

```python
"""Docstring parsing for Nim documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DocstringStyle(Enum):
    """Supported docstring styles."""
    RST = "rst"
    GOOGLE = "google"
    NUMPY = "numpy"


@dataclass
class ParamDoc:
    """Parsed parameter documentation."""
    name: str
    description: str = ""
    type: str = ""


@dataclass
class ReturnsDoc:
    """Parsed return value documentation."""
    description: str = ""
    type: str = ""


@dataclass
class RaisesDoc:
    """Parsed raises documentation."""
    type: str
    description: str = ""


@dataclass
class ParsedDocstring:
    """Parsed docstring with structured sections."""
    description: str = ""
    params: list[ParamDoc] = field(default_factory=list)
    returns: Optional[ReturnsDoc] = None
    raises: list[RaisesDoc] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


def parse_rst_docstring(doc: str) -> ParsedDocstring:
    """Parse RST-style docstring.

    Args:
        doc: Raw docstring text.

    Returns:
        Parsed docstring structure.
    """
    result = ParsedDocstring()

    lines = doc.strip().split("\n")
    description_lines = []
    in_description = True

    # Patterns for RST directives
    param_pattern = re.compile(r":param\s+(\w+):\s*(.*)")
    returns_pattern = re.compile(r":returns?:\s*(.*)")
    raises_pattern = re.compile(r":raises?\s+(\w+):\s*(.*)")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for RST directives
        param_match = param_pattern.match(line)
        returns_match = returns_pattern.match(line)
        raises_match = raises_pattern.match(line)

        if param_match:
            in_description = False
            result.params.append(ParamDoc(
                name=param_match.group(1),
                description=param_match.group(2).strip(),
            ))
        elif returns_match:
            in_description = False
            result.returns = ReturnsDoc(description=returns_match.group(1).strip())
        elif raises_match:
            in_description = False
            result.raises.append(RaisesDoc(
                type=raises_match.group(1),
                description=raises_match.group(2).strip(),
            ))
        elif in_description:
            if line or description_lines:  # Skip leading blank lines
                description_lines.append(line)

        i += 1

    # Clean up description
    result.description = "\n".join(description_lines).strip()

    return result


def parse_google_docstring(doc: str) -> ParsedDocstring:
    """Parse Google-style docstring.

    Args:
        doc: Raw docstring text.

    Returns:
        Parsed docstring structure.
    """
    result = ParsedDocstring()

    lines = doc.strip().split("\n")
    current_section = "description"
    description_lines = []

    section_pattern = re.compile(r"^(Args|Arguments|Parameters|Returns|Raises|Examples):\s*$", re.IGNORECASE)
    param_pattern = re.compile(r"^\s+(\w+):\s*(.*)")

    i = 0
    while i < len(lines):
        line = lines[i]

        section_match = section_pattern.match(line.strip())
        if section_match:
            section_name = section_match.group(1).lower()
            if section_name in ("args", "arguments", "parameters"):
                current_section = "params"
            elif section_name == "returns":
                current_section = "returns"
            elif section_name == "raises":
                current_section = "raises"
            else:
                current_section = section_name
        elif current_section == "description":
            description_lines.append(line)
        elif current_section == "params":
            param_match = param_pattern.match(line)
            if param_match:
                result.params.append(ParamDoc(
                    name=param_match.group(1),
                    description=param_match.group(2).strip(),
                ))
        elif current_section == "returns":
            if line.strip():
                result.returns = ReturnsDoc(description=line.strip())
                current_section = ""
        elif current_section == "raises":
            param_match = param_pattern.match(line)
            if param_match:
                result.raises.append(RaisesDoc(
                    type=param_match.group(1),
                    description=param_match.group(2).strip(),
                ))

        i += 1

    result.description = "\n".join(description_lines).strip()
    return result


def parse_docstring(doc: str, style: DocstringStyle = DocstringStyle.RST) -> ParsedDocstring:
    """Parse a docstring according to the specified style.

    Args:
        doc: Raw docstring text.
        style: Docstring style to use for parsing.

    Returns:
        Parsed docstring structure.
    """
    if not doc:
        return ParsedDocstring()

    if style == DocstringStyle.RST:
        return parse_rst_docstring(doc)
    elif style == DocstringStyle.GOOGLE:
        return parse_google_docstring(doc)
    else:
        # Default to RST
        return parse_rst_docstring(doc)
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_docstring.py -v`

Expected: All tests pass

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement docstring parser (RST and Google styles)"
```

---

## Task 6: Integrate Docstring Parsing into Handler

**Files:**
- Modify: `mkdocstrings_handlers/nim/handler.py`
- Modify: `mkdocstrings_handlers/nim/collector.py`

**Step 1: Update collector to parse docstrings**

Add to `collector.py`:

```python
from mkdocstrings_handlers.nim.docstring import parse_docstring, DocstringStyle

# In NimCollector._parse_module, after creating entry:
            parsed_doc = parse_docstring(entry_data.get("doc", ""), DocstringStyle.RST)

            # Update params with descriptions from docstring
            for param in entries[-1].params:
                for doc_param in parsed_doc.params:
                    if param.name == doc_param.name:
                        param.description = doc_param.description
                        break

            # Add returns description
            if parsed_doc.returns:
                entries[-1].returns_doc = parsed_doc.returns.description
```

**Step 2: Update handler to pass docstring_style option**

Add to handler options processing:

```python
    def collect(self, identifier: str, options: HandlerOptions) -> CollectorItem:
        """Collect documentation for an identifier."""
        _logger.debug(f"Collecting {identifier}")
        module = self.collector.collect(identifier)

        # Parse docstrings with configured style
        style = DocstringStyle(options.get("docstring_style", "rst"))
        for entry in module.entries:
            self._parse_entry_docstring(entry, style)

        return module
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: integrate docstring parsing into handler"
```

---

## Task 7: End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_full_flow.py`
- Create: `tests/integration/fixtures/sample_project/src/mylib.nim`
- Create: `tests/integration/fixtures/sample_project/mkdocs.yml`
- Create: `tests/integration/fixtures/sample_project/docs/index.md`

**Step 1: Create sample Nim project**

Create `tests/integration/fixtures/sample_project/src/mylib.nim`:

```nim
## A sample library for testing mkdocstrings-nim.
##
## This module demonstrates documentation generation.

const
  Version* = "1.0.0"  ## Library version

type
  Config* = object
    ## Configuration settings.
    name*: string  ## Config name
    debug*: bool   ## Debug mode flag

proc initialize*(cfg: Config): bool =
  ## Initialize the library with given config.
  ##
  ## :param cfg: Configuration to use
  ## :returns: True if successful
  result = true

proc process*(data: string; count: int = 1): seq[string] {.inline.} =
  ## Process data and return results.
  ##
  ## :param data: Input data to process
  ## :param count: Number of times to process
  ## :returns: Processed results
  ## :raises ValueError: If data is empty
  result = @[data]
```

**Step 2: Create sample mkdocs.yml**

Create `tests/integration/fixtures/sample_project/mkdocs.yml`:

```yaml
site_name: Sample Lib Docs
theme:
  name: material

plugins:
  - mkdocstrings:
      handlers:
        nim:
          paths: [src]
          docstring_style: rst

nav:
  - Home: index.md
  - API: api.md
```

**Step 3: Create sample docs**

Create `tests/integration/fixtures/sample_project/docs/index.md`:

```markdown
# Sample Library

Welcome to the sample library documentation.

## API Reference

::: mylib
```

**Step 4: Create integration test**

Create `tests/integration/test_full_flow.py`:

```python
"""End-to-end integration tests."""

import pytest
from pathlib import Path
from mkdocstrings_handlers.nim.handler import get_handler
from mkdocstrings_handlers.nim.collector import NimModule


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_project"


class MockToolConfig:
    """Mock MkDocs tool config."""
    config_file_path = str(FIXTURE_DIR / "mkdocs.yml")


@pytest.fixture
def handler():
    """Create a handler for testing."""
    return get_handler(
        handler_config={"paths": ["src"]},
        tool_config=MockToolConfig(),
    )


class TestFullFlow:
    """End-to-end tests."""

    @pytest.mark.skipif(
        not (FIXTURE_DIR / "src" / "mylib.nim").exists(),
        reason="Fixture not found"
    )
    def test_collect_module(self, handler):
        """Test collecting a full module."""
        options = handler.get_options({})
        module = handler.collect("mylib", options)

        assert isinstance(module, NimModule)
        assert module.module == "mylib"
        assert "sample library" in module.doc.lower()

        # Check entries
        entry_names = [e.name for e in module.entries]
        assert "Version" in entry_names
        assert "Config" in entry_names
        assert "initialize" in entry_names
        assert "process" in entry_names

    @pytest.mark.skipif(
        not (FIXTURE_DIR / "src" / "mylib.nim").exists(),
        reason="Fixture not found"
    )
    def test_render_module(self, handler):
        """Test rendering a module to HTML."""
        options = handler.get_options({})
        module = handler.collect("mylib", options)
        html = handler.render(module, options)

        assert "<div class=\"doc doc-object doc-module\">" in html
        assert "mylib" in html
        assert "initialize" in html
```

**Step 5: Run integration tests**

Run: `python -m pytest tests/integration/ -v`

Expected: Tests pass (or skip if Nim not available)

**Step 6: Commit**

```bash
git add -A
git commit -m "test: add end-to-end integration tests"
```

---

## Task 8: Update __init__.py exports

**Files:**
- Modify: `mkdocstrings_handlers/nim/__init__.py`

**Step 1: Update exports**

```python
"""Nim handler for mkdocstrings."""

from mkdocstrings_handlers.nim.handler import NimHandler, get_handler
from mkdocstrings_handlers.nim.collector import NimCollector, NimModule, NimEntry, NimParam
from mkdocstrings_handlers.nim.docstring import (
    parse_docstring,
    DocstringStyle,
    ParsedDocstring,
    ParamDoc,
    ReturnsDoc,
    RaisesDoc,
)

__all__ = [
    "NimHandler",
    "get_handler",
    "NimCollector",
    "NimModule",
    "NimEntry",
    "NimParam",
    "parse_docstring",
    "DocstringStyle",
    "ParsedDocstring",
    "ParamDoc",
    "ReturnsDoc",
    "RaisesDoc",
]
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: update module exports"
```

---

## Task 9: Create README

**Files:**
- Create: `README.md`

**Step 1: Write README**

```markdown
# mkdocstrings-nim

A [mkdocstrings](https://mkdocstrings.github.io/) handler for [Nim](https://nim-lang.org/).

Generate beautiful API documentation for your Nim projects, integrated into your MkDocs site.

## Installation

```bash
pip install mkdocstrings-nim
```

**Requirements:** Nim compiler must be installed and available in PATH.

## Quick Start

1. Add to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocstrings:
      handlers:
        nim:
          paths: [src]
```

2. Use in your markdown:

```markdown
# API Reference

::: mymodule
```

3. Build your docs:

```bash
mkdocs build
```

## Configuration

### Handler Options

| Option | Default | Description |
|--------|---------|-------------|
| `paths` | `["src"]` | Search paths for Nim source files |
| `docstring_style` | `"rst"` | Docstring format: `rst`, `google`, or `numpy` |
| `show_source` | `true` | Show source line numbers |
| `show_signature` | `true` | Show full signatures |
| `show_pragmas` | `true` | Show pragma annotations |

### Docstring Format

Use RST-style docstrings in your Nim code:

```nim
proc greet*(name: string): string =
  ## Greet someone by name.
  ##
  ## :param name: The name to greet
  ## :returns: A greeting message
  result = "Hello, " & name & "!"
```

## Development

```bash
# Clone the repo
git clone https://github.com/you/mkdocstrings-nim
cd mkdocstrings-nim

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## Summary

| Task | Description | Estimated Time |
|------|-------------|----------------|
| 1 | Project scaffolding | 10 min |
| 2 | nimdocinfo AST extraction | 30 min |
| 3 | Python handler structure | 20 min |
| 4 | Adapt templates for Nim | 20 min |
| 5 | Docstring parser | 15 min |
| 6 | Integrate docstring parsing | 10 min |
| 7 | End-to-end tests | 15 min |
| 8 | Update exports | 5 min |
| 9 | README | 10 min |

**Total: ~2.5 hours**

After completing these tasks, you'll have a working mkdocstrings-nim handler that can:
- Extract documentation from Nim source files
- Parse RST and Google-style docstrings
- Render beautiful API docs with the Material theme
