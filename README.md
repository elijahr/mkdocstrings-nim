# mkdocstrings-nim

[![PyPI](https://img.shields.io/pypi/v/mkdocstrings-nim)](https://pypi.org/project/mkdocstrings-nim/)
[![Python](https://img.shields.io/pypi/pyversions/mkdocstrings-nim)](https://pypi.org/project/mkdocstrings-nim/)
[![License](https://img.shields.io/github/license/elijahr/mkdocstrings-nim)](https://github.com/elijahr/mkdocstrings-nim/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-elijahr.github.io%2Fmkdocstrings--nim-blue)](https://elijahr.github.io/mkdocstrings-nim/)

Generate API documentation for your Nim projects with [MkDocs](https://www.mkdocs.org/) or [Zensical](https://zensical.org/).

mkdocstrings-nim extracts documentation from Nim source files using the Nim compiler's AST, including module docstrings, procedure signatures, parameter types, return types, and pragma annotations. It renders the documentation as HTML using **mkdocstrings** with either **MkDocs** (and `mkdocs-material`) or **Zensical** (the next-generation MkDocs successor).

**[Full Documentation](https://elijahr.github.io/mkdocstrings-nim/)** | **[Changelog](https://github.com/elijahr/mkdocstrings-nim/blob/main/CHANGELOG.md)**

## Quick Start

### Prerequisites

- **Nim** compiler installed and in PATH ([install Nim](https://nim-lang.org/install.html))
- **Python 3.9+** ([install Python](https://www.python.org/downloads/))

---

### Using with Zensical (Recommended)

[Zensical](https://zensical.org/) is the high-performance successor to MkDocs by the creators of Material for MkDocs. mkdocstrings-nim supports Zensical out-of-the-box, automatically generating required CSS and media assets in `site/` during build.

#### 1. Install

```bash
pip install zensical mkdocstrings-nim
```

#### 2. Configure `zensical.toml`

```toml
[project]
site_name = "My Nim Project"

[project.plugins.mkdocstrings]
default_handler = "nim"

[project.plugins.mkdocstrings.handlers.nim]
paths = ["src"]
```

#### 3. Run

```bash
zensical serve    # local dev server
zensical build    # build static site
```

---

### Using with MkDocs

#### 1. Install

```bash
pip install mkdocs mkdocs-material mkdocstrings-nim
```

#### 2. Configure `mkdocs.yml`

In your Nim project root, create `mkdocs.yml`:

```yaml
site_name: My Nim Project
theme:
  name: material

plugins:
  - search
  - mkdocstrings:
      handlers:
        nim:
          paths: [src]  # Where your .nim files are
          options:
            show_source: true
            docstring_style: rst
```

#### 3. Run

```bash
mkdocs serve    # local dev server
mkdocs build    # build static site
```

---

### Documenting Your Code

Create a `docs/` directory with an `index.md`:

```bash
mkdir docs
```

**docs/index.md:**
```markdown
# My Nim Project

Welcome to my project documentation.

## API Reference

::: mymodule
```

The `::: mymodule` directive tells mkdocstrings to extract and render documentation from `src/mymodule.nim`.

Open http://127.0.0.1:8000 to see your documentation.

### 5. Build for deployment

```bash
mkdocs build
```

This creates a `site/` directory with static HTML ready to deploy to GitHub Pages, Netlify, or any static host.

## Writing Nim Docstrings

Use `##` comments to document your Nim code:

```nim
## This module provides greeting utilities.

proc greet*(name: string): string =
  ## Greet someone by name.
  ##
  ## :param name: The name to greet
  ## :returns: A greeting message
  result = "Hello, " & name & "!"

type
  Config* = object
    ## Configuration for the greeter.
    prefix*: string  ## The greeting prefix
    suffix*: string  ## The greeting suffix
```

Supported docstring styles: `rst` (default), `google`, `numpy`, `epydoc`.

## Configuration Options

Configure in `mkdocs.yml` under `plugins > mkdocstrings > handlers > nim > options`:

| Option | Default | Description |
|--------|---------|-------------|
| `paths` | `["src"]` | Search paths for Nim source files |
| `docstring_style` | `"rst"` | Docstring format: `rst`, `google`, `numpy`, `epydoc`, `auto` |
| `show_source` | `true` | Show source file and line numbers |
| `show_signature` | `true` | Show full procedure signatures |
| `show_pragmas` | `true` | Show pragma annotations like `{.raises.}` |
| `show_private` | `false` | Include non-exported (private) symbols |
| `heading_level` | `2` | Starting heading level for entries |
| `source_url` | `null` | Repository URL for source links (e.g., `https://github.com/user/repo`) |

See the [full documentation](https://elijahr.github.io/mkdocstrings-nim/) for more details.

## Projects Using mkdocstrings-nim

- [nim-typestates](https://github.com/elijahr/nim-typestates) - Compile-time state machine verification
- [lockfreequeues](https://github.com/elijahr/lockfreequeues) - Lock-free data structures for Nim

## License

MIT
