# CI Integration

## GitHub Actions

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

      - uses: iffy/install-nim@v5
        with:
          version: stable

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

## Versioned Documentation with Mike

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

      - uses: iffy/install-nim@v5
        with:
          version: stable

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

## Requirements

CI environments need:

1. **Python 3.9+** - For mkdocstrings-nim
2. **Nim compiler with compiler modules** - The handler uses Nim's internal compiler API to parse source files. Use [`iffy/install-nim@v5`](https://github.com/iffy/install-nim) which properly sets up access to compiler modules. Alternatives like `jiro4989/setup-nim-action` or `nim-lang/setup-nimble-action` may not include the required compiler sources.
3. **Dependencies** - Install via pip or a requirements file

Example `docs-requirements.txt`:

```
mkdocs>=1.5
mkdocstrings-nim>=0.1.0
mkdocs-material>=9.0
mike>=2.0
```
