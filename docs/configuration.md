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
            show_private: false
            heading_level: 2
            source_url: https://github.com/owner/repo
            source_ref: main
```

### Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `paths` | list | `["src"]` | Directories to search for Nim source files |
| `docstring_style` | string | `"rst"` | Docstring format: `rst`, `google`, `numpy`, `epydoc`, or `auto` |
| `show_source` | bool | `true` | Show source file and line number for each entry |
| `show_signature` | bool | `true` | Show full procedure signatures |
| `show_pragmas` | bool | `true` | Show pragma annotations |
| `show_private` | bool | `false` | Show non-exported (private) symbols |
| `show_attribution` | bool | `true` | Show "Generated with mkdocstrings-nim" footer |
| `heading_level` | int | `2` | Starting HTML heading level |
| `source_url` | string | `null` | Base URL for source links (e.g., `https://github.com/owner/repo`) |
| `source_ref` | string | auto-detected | Git branch or tag for source links (auto-detected from git if not set) |

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

## Source Links

Enable clickable links to source code on GitHub or GitLab:

```yaml
handlers:
  nim:
    paths: [src]
    options:
      show_source: true
      source_url: https://github.com/owner/repo
      # source_ref auto-detected from git branch
```

When `source_url` is set, the source location becomes a link to the file on GitHub/GitLab.

- `source_ref` is **auto-detected** from your current git branch if not set
- Override with a tag (e.g., `v1.0.0`) for versioned release documentation
- The handler warns if `source_url` format appears incorrect

## Private Symbols

By default, only exported symbols (marked with `*` in Nim) are documented. To include private symbols:

```yaml
handlers:
  nim:
    paths: [src]
    options:
      show_private: true
```

Override per-module to show private symbols for internal documentation:

```markdown
::: mymodule.internal
    options:
      show_private: true
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

## Footer Attribution

By default, each rendered module shows "Generated with mkdocstrings-nim" at the bottom. To move this to the site footer instead (alongside "Made with Material for MkDocs"):

### 1. Create the override template

Create `docs/overrides/main.html`:

```jinja
{% extends "base.html" %}

{% set extracopyright %}
  ·
  <a href="https://mkdocstrings.github.io/" target="_blank" rel="noopener">mkdocstrings</a>
  ·
  <a href="https://github.com/elijahr/mkdocstrings-nim" target="_blank" rel="noopener">mkdocstrings-nim</a>
{% endset %}
```

### 2. Configure MkDocs

In `mkdocs.yml`:

```yaml
theme:
  name: material
  custom_dir: docs/overrides

plugins:
  - mkdocstrings:
      handlers:
        nim:
          options:
            show_attribution: false  # Disable per-module attribution
```

This displays: **Made with Material for MkDocs · mkdocstrings · mkdocstrings-nim**
