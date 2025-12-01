# Writing Docstrings

## Basic Format

Nim docstrings use `##` comments:

```nim
proc greet*(name: string): string =
  ## Single line description.
  result = "Hello, " & name
```

Multi-line descriptions:

```nim
proc process*(data: seq[int]): seq[int] =
  ## Process a sequence of integers.
  ##
  ## This function filters, transforms, and returns
  ## the processed data. Empty sequences return empty.
  result = data.filterIt(it > 0)
```

## Module Docstrings

Document modules at the top of the file:

```nim
## mymodule - Utilities for data processing.
##
## This module provides functions for filtering,
## transforming, and aggregating data sequences.

import std/sequtils

proc filter*[T](data: seq[T]): seq[T] =
  ## Filter the sequence.
  discard
```

## Parameters

Document parameters with `:param`:

```nim
proc connect*(host: string; port: int; timeout: float = 30.0): Connection =
  ## Connect to a remote server.
  ##
  ## :param host: Server hostname or IP address
  ## :param port: Port number (1-65535)
  ## :param timeout: Connection timeout in seconds
  result = newConnection(host, port, timeout)
```

## Return Values

Document return values with `:returns`:

```nim
proc calculate*(x, y: int): tuple[sum: int, product: int] =
  ## Calculate sum and product.
  ##
  ## :param x: First operand
  ## :param y: Second operand
  ## :returns: Tuple containing sum and product
  result = (sum: x + y, product: x * y)
```

## Exceptions

Document raised exceptions with `:raises`:

```nim
proc divide*(a, b: int): int =
  ## Divide two integers.
  ##
  ## :param a: Dividend
  ## :param b: Divisor
  ## :returns: Quotient
  ## :raises DivByZeroDefect: When b is zero
  if b == 0:
    raise newException(DivByZeroDefect, "division by zero")
  result = a div b
```

## Pragmas

The handler extracts pragmas automatically:

```nim
proc riskyOp*() {.raises: [IOError, ValueError].} =
  ## Operation that may fail.
  ##
  ## See Raises section for possible exceptions.
  discard
```

This displays a **Raises** section listing `IOError` and `ValueError`.

## Types

Document types and their fields:

```nim
type
  Config* = object
    ## Application configuration.
    host*: string    ## Server hostname
    port*: int       ## Server port
    debug*: bool     ## Enable debug mode
```

## Constants

```nim
const
  Version* = "1.0.0"
    ## Current library version.

  MaxConnections* = 100
    ## Maximum concurrent connections.
```

## Code Examples

Include code examples in docstrings:

```nim
proc factorial*(n: int): int =
  ## Calculate factorial of n.
  ##
  ## :param n: Non-negative integer
  ## :returns: n!
  ##
  ## Example:
  ##
  ## ```nim
  ## assert factorial(5) == 120
  ## assert factorial(0) == 1
  ## ```
  if n <= 1: 1
  else: n * factorial(n - 1)
```

## Docstring Styles

The `docstring_style` option controls how **structured sections** (parameters, returns, raises) are parsed:

- **RST** (default) - Uses `:param:`, `:returns:`, `:raises:` directives
- **Google** - Uses `Args:`, `Returns:`, `Raises:` sections
- **NumPy** - Uses section headers with underlines (`Parameters`, `Returns`, etc.)
- **Epydoc** - Uses `@param`, `@return`, `@raise` tags
- **Auto** - Automatically detects the style

Set the style in your `mkdocs.yml`:

```yaml
handlers:
  nim:
    options:
      docstring_style: google  # or "rst", "numpy", "epydoc", "auto"
```

See [Configuration](configuration.md#docstring-styles) for examples of each style.

## Markdown Content (Important)

While the `docstring_style` controls how structured sections are parsed, all **prose content** is rendered as Markdown. This is the same approach used by mkdocstrings-python.

Use Markdown formatting in your docstrings:

```nim
proc format*(text: string): string =
  ## Format text with **bold** and *italic*.
  ##
  ## Supports:
  ##
  ## - Bullet lists
  ## - `inline code`
  ## - [links](https://example.com)
  ##
  ## > Blockquotes work too.
  ##
  ## Code blocks use fences:
  ##
  ## ```nim
  ## let x = format("hello")
  ## ```
  result = text
```

### What Works

| Syntax | Example |
|--------|---------|
| Bold | `**bold**` |
| Italic | `*italic*` |
| Code | `` `code` `` |
| Links | `[text](url)` |
| Lists | `- item` or `1. item` |
| Headings | `## Heading` |
| Code blocks | ` ```nim ... ``` ` |
| Blockquotes | `> quote` |

### What Does NOT Work

RST-specific formatting is **not supported** for prose content:

```nim
# DON'T do this:
proc example*() =
  ## Example::            <-- RST code block syntax won't work
  ##
  ##   indented code      <-- Will render as plain text
  ##
  ## See :ref:`other`     <-- RST cross-references won't work
```

Instead, use Markdown:

```nim
# DO this:
proc example*() =
  ## Example:
  ##
  ## ```nim
  ## code here
  ## ```
  ##
  ## See [other](other.md)
```

### Summary

| Aspect | Format |
|--------|--------|
| Structured sections (`:param:`, `Args:`) | Determined by `docstring_style` |
| Prose content (descriptions, examples) | **Markdown** |
