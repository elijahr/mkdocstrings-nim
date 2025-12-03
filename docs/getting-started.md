# Getting Started

This guide gets you from zero to a running documentation server for your Nim project.

## Prerequisites

- **Nim** compiler installed and in PATH ([install Nim](https://nim-lang.org/install.html))
- **Python 3.9+** ([install Python](https://www.python.org/downloads/))

Verify Nim is installed:

```bash
nim --version
```

## 1. Install the tools

```bash
pip install mkdocs mkdocs-material mkdocstrings-nim
```

## 2. Create mkdocs.yml

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
            heading_level: 3  # Recommended for TOC integration

markdown_extensions:
  - toc:
      permalink: true
      toc_depth: 4  # Include h2, h3, h4 in TOC

watch:
  - docs
  - src  # Reload when Nim source files change
```

## 3. Create your docs

Create a `docs/` directory with documentation files:

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

## 4. Write documented Nim code

Create a Nim module with docstrings using `##` comments:

**src/mymodule.nim:**
```nim
## This module provides greeting utilities.

type
  Config* = object
    ## Configuration settings.
    name*: string  ## The name to use
    debug*: bool   ## Enable debug mode

proc greet*(name: string): string =
  ## Greet someone by name.
  ##
  ## :param name: The name to greet
  ## :returns: A greeting message
  result = "Hello, " & name & "!"

proc init*(cfg: Config): bool =
  ## Initialize the library.
  ##
  ## :param cfg: Configuration to use
  ## :returns: True if successful
  result = true
```

## 5. Run the docs server

```bash
mkdocs serve
```

Open http://127.0.0.1:8000 to see your documentation.

## 6. Build for deployment

```bash
mkdocs build
```

This creates a `site/` directory with static HTML ready to deploy to GitHub Pages, Netlify, or any static host.

## Project Structure

Recommended layout:

```
myproject/
├── src/
│   └── mymodule.nim
├── docs/
│   ├── index.md
│   └── api.md
├── mkdocs.yml
└── myproject.nimble
```

## First Build Note

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
