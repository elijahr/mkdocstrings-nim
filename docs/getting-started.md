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

## CI Integration

### GitHub Actions

Example workflow for building and deploying docs:

```yaml
name: docs

on:
  push:
    branches: [main]
  pull_request:

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - uses: jiro4989/setup-nim-action@v2
        with:
          nim-version: 'stable'

      - name: Install dependencies
        run: pip install mkdocs mkdocstrings-nim mkdocs-material

      - name: Build docs
        run: mkdocs build

      - name: Deploy to GitHub Pages
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
```

### Versioned Documentation with Mike

For versioned docs using [mike](https://github.com/jimporter/mike):

```yaml
name: docs

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - uses: jiro4989/setup-nim-action@v2
        with:
          nim-version: 'stable'

      - name: Install dependencies
        run: pip install mkdocs mkdocstrings-nim mkdocs-material mike

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Deploy dev docs
        if: github.ref == 'refs/heads/main'
        run: |
          mike deploy --push dev
          mike set-default --push dev

      - name: Deploy versioned docs
        if: startsWith(github.ref, 'refs/tags/v')
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          mike deploy --push --update-aliases $VERSION latest
          mike set-default --push latest
```

### Requirements

CI environments need:

1. **Python 3.9+** - For mkdocstrings-nim
2. **Nim compiler** - Use `jiro4989/setup-nim-action@v2` or `nim-lang/setup-nimble-action@v1` on GitHub Actions
3. **Dependencies** - Install via pip or a requirements file

Example `docs-requirements.txt`:

```
mkdocs>=1.5
mkdocstrings-nim>=0.1.0
mkdocs-material>=9.0
mike>=2.0
```
