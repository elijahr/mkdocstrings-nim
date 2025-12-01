# Configuration

## Handler Options

Configure the Nim handler in `mkdocs.yml`:

```yaml
plugins:
  - mkdocstrings:
      default_handler: nim
      handlers:
        nim:
          paths: [src]
          options:
            docstring_style: rst
            show_source: true
            show_signature: true
            show_pragmas: true
            heading_level: 2
```

### Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `paths` | list | `["src"]` | Directories to search for Nim source files |
| `docstring_style` | string | `"rst"` | Docstring format: `rst`, `google`, `numpy`, `epydoc`, or `auto` |
| `show_source` | bool | `true` | Show source file line numbers |
| `show_signature` | bool | `true` | Show full procedure signatures |
| `show_pragmas` | bool | `true` | Show pragma annotations |
| `heading_level` | int | `2` | Starting HTML heading level |

## Per-Object Options

Override options for specific objects:

```markdown
::: mymodule
    options:
      show_source: false
      heading_level: 3
```

## Multiple Source Paths

Search multiple directories:

```yaml
handlers:
  nim:
    paths:
      - src
      - lib
      - vendor/nimble
```

## Docstring Styles

### RST (default)

```nim
proc example*(x: int): string =
  ## Brief description.
  ##
  ## :param x: Parameter description
  ## :returns: Return value description
  ## :raises ValueError: When x is negative
```

### Google

```nim
proc example*(x: int): string =
  ## Brief description.
  ##
  ## Args:
  ##   x: Parameter description
  ##
  ## Returns:
  ##   Return value description
  ##
  ## Raises:
  ##   ValueError: When x is negative
```

### NumPy

```nim
proc example*(x: int): string =
  ## Brief description.
  ##
  ## Parameters
  ## ----------
  ## x : int
  ##     Parameter description
  ##
  ## Returns
  ## -------
  ## string
  ##     Return value description
```

## Identifier Syntax

Reference modules and nested paths:

```markdown
<!-- Module -->
::: mymodule

<!-- Nested module -->
::: mypackage.submodule

<!-- Specific item (planned) -->
::: mymodule.MyType
```

## Theme Support

The handler includes templates for the Material theme. Other themes use fallback templates.

For custom templates, set:

```yaml
handlers:
  nim:
    custom_templates: path/to/templates
```
