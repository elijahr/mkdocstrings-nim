# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-04

### Added

- Type field documentation: Object and ref object types now display a **Fields** section
- Enum value documentation: Enum types now display a **Values** section with explicit values
- Case object (variant type) support with branch annotations (e.g., `[when kind = nkInt]`)
- Private field visibility controlled by `show_private` option
- `type_field_doc_style` config option: `inline` (default, Nim-native) or `docstring` (RST `:var:` style)
- Comprehensive integration tests for type field extraction

## [0.1.2] - 2025-12-03

### Fixed

- CI: Switch from iffy/install-nim to asdf-nim for more reliable Nim installation
- CI: Fix pyproject.toml structure (dependencies was incorrectly under [project.urls])

## [0.1.1] - 2025-12-02

### Added

- Strict linting with ruff and mypy
- Pre-commit hooks for code quality
- CI lint job that runs on all pushes and PRs
- Publish and docs workflows now depend on test and lint passing
- `show_private` option to include non-exported symbols (default: false)
- Attribution footer with link to mkdocstrings-nim
- Auto-detection of `source_ref` from git branch
- Validation of `source_url` configuration
- Source code links with GitHub/GitLab/Bitbucket support
- TOC integration using heading filter
- PyPI metadata: project URLs, keywords, license classifier
- Improved README with complete quickstart guide for Nim developers

### Fixed

- Live reload now works correctly with cache invalidation
- Heading levels properly integrate with MkDocs TOC
- Config options properly applied from mkdocs.yml

### Changed

- Improved test coverage to 87%

## [0.1.0] - 2025-11-29

### Added

- Initial release
- Nim handler for mkdocstrings
- Support for procs, funcs, templates, macros, types, and constants
- RST, Google, NumPy, and Epydoc docstring style parsing
- Pragma extraction and display
- Material theme templates
