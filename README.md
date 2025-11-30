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
