# mkdocstrings-nim

A [mkdocstrings](https://mkdocstrings.github.io/) handler for [Nim](https://nim-lang.org/).

Parses Nim source files using the Nim compiler's AST to extract module docstrings, procedure signatures, parameter types, return types, and `{.raises.}` pragma annotations. Renders the extracted documentation as HTML within [MkDocs](https://www.mkdocs.org/) using the `::: module` directive syntax.

## Features

- **Automatic extraction** - Parses Nim source files using the Nim compiler's AST
- **Docstring support** - RST-style docstrings with parameter and return documentation
- **Pragma extraction** - Shows `{.raises.}` and other pragmas in docs
- **Material theme** - Full support for mkdocs-material theme
- **Versioned docs** - Works with mike for versioned documentation

## Requirements

- Python 3.9+
- Nim compiler (must be in PATH)
- MkDocs with mkdocstrings

## Quick Example

Given `src/math_utils.nim`:

```nim
## Math utilities module.

proc add*(a, b: int): int =
  ## Add two integers.
  ##
  ## :param a: First operand
  ## :param b: Second operand
  ## :returns: Sum of a and b
  result = a + b
```

Reference it in your markdown:

```markdown
::: math_utils
```

The handler generates formatted documentation with:

- Module description
- Function signatures
- Parameter types and descriptions
- Return type and description
- Source line references

## Next Steps

- [Getting Started](getting-started.md) - Installation and basic setup
- [Configuration](configuration.md) - All available options
- [Writing Docstrings](docstrings.md) - Docstring format reference
- [CI Integration](ci.md) - GitHub Actions workflows
