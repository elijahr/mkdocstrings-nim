# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `show_private` option to include non-exported (private) symbols in documentation
- `source_url` and `source_ref` options for clickable source links to GitHub/GitLab
- `exported` field tracking for Nim symbols (detects `*` export marker)
- Documentation for source links, private symbols, and all handler options

### Changed

- Cache now invalidates when source files are modified (fixes live reload with `mkdocs serve`)
- Documented objects now appear in right-side TOC using mkdocstrings heading filter
- Handler options from `mkdocs.yml` are now properly applied

### Fixed

- Live reload now works correctly when Nim source files change
- TOC integration: documented procs/types now appear in table of contents
- Config options cascade correctly: defaults < config < directive options

## [0.1.0] - 2025-11-30

### Added

- Initial release
- Nim source file parsing using compiler AST
- Docstring style support: RST, Google, NumPy, Epydoc, and Auto detection
- Parameter and return value documentation
- Raises pragma extraction and display
- Material theme templates
- Markdown rendering in docstrings
- Compile-time caching of Nim extractor binary
- Module, proc, func, iterator, template, macro, type, and const support
- CI integration with GitHub Actions
- Comprehensive test suite (24 tests)
