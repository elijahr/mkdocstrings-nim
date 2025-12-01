# mkdocstrings-nim

[![PyPI](https://img.shields.io/pypi/v/mkdocstrings-nim)](https://pypi.org/project/mkdocstrings-nim/)
[![Python](https://img.shields.io/pypi/pyversions/mkdocstrings-nim)](https://pypi.org/project/mkdocstrings-nim/)
[![License](https://img.shields.io/github/license/elijahr/mkdocstrings-nim)](https://github.com/elijahr/mkdocstrings-nim/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-elijahr.github.io%2Fmkdocstrings--nim-blue)](https://elijahr.github.io/mkdocstrings-nim/)

A [mkdocstrings](https://mkdocstrings.github.io/) handler for [Nim](https://nim-lang.org/).

Parses Nim source files using the Nim compiler's AST to extract module docstrings, procedure signatures, parameter types, return types, and `{.raises.}` pragma annotations. Renders the extracted documentation as HTML within [MkDocs](https://www.mkdocs.org/) using the `::: module` directive syntax.

**[Documentation](https://elijahr.github.io/mkdocstrings-nim/)**

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
| `docstring_style` | `"rst"` | Docstring format: `rst`, `google`, `numpy`, `epydoc`, or `auto` |
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
git clone https://github.com/elijahr/mkdocstrings-nim
cd mkdocstrings-nim
pip install -e ".[dev]"
pytest
```

## License

MIT
