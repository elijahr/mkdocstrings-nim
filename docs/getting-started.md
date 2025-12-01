# Getting Started

## Installation

```bash
pip install mkdocstrings-nim
```

Ensure the Nim compiler is installed and available in your PATH:

```bash
nim --version
```

If not installed, see [nim-lang.org/install](https://nim-lang.org/install.html).

## Basic Setup

### 1. Configure MkDocs

Add mkdocstrings with the Nim handler to your `mkdocs.yml`:

```yaml
plugins:
  - search
  - mkdocstrings:
      default_handler: nim
      handlers:
        nim:
          paths: [src]
          options:
            heading_level: 3  # Recommended for TOC integration
```

For the right-side table of contents to include API items, also configure:

```yaml
markdown_extensions:
  - toc:
      permalink: true
      toc_depth: 4  # Include h2, h3, h4 in TOC
```

### 2. Write Documented Nim Code

Create a Nim module with docstrings:

```nim
## mylib.nim - A sample library.

type
  Config* = object
    ## Configuration settings.
    name*: string
    debug*: bool

proc init*(cfg: Config): bool =
  ## Initialize the library.
  ##
  ## :param cfg: Configuration to use
  ## :returns: True if successful
  result = true
```

### 3. Reference in Markdown

Create `docs/api.md`:

```markdown
# API Reference

::: mylib
```

### 4. Build

```bash
mkdocs serve   # Development server
mkdocs build   # Production build
```

### 5. Enable Hot Reload for Source Files

By default, `mkdocs serve` only watches the `docs/` directory. To reload when Nim source files change, add `watch` to your `mkdocs.yml`:

```yaml
watch:
  - docs
  - src  # Reload when Nim source files change
```

## Project Structure

Recommended layout:

```
myproject/
├── src/
│   └── mylib.nim
├── docs/
│   ├── index.md
│   └── api.md
├── mkdocs.yml
└── mylib.nimble
```

## First Build

The first documentation build compiles the Nim extractor tool (~15 seconds). Subsequent builds use the cached binary and are fast.

## Troubleshooting

### "Nim compiler not found"

Ensure `nim` is in your PATH:

```bash
which nim
```

### "Could not find Nim file"

Check that `paths` in your handler config points to your source directory:

```yaml
handlers:
  nim:
    paths: [src]  # Adjust to match your layout
```

### Slow first build

Normal. The Nim extractor compiles on first use. The binary is cached in `/tmp/mkdocstrings-nim-cache/`.
