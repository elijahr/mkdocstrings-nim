"""Nim handler for mkdocstrings."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any, ClassVar

from markupsafe import Markup
from mkdocstrings import BaseHandler, CollectorItem, HandlerOptions, get_logger
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers.nimrod import NimrodLexer

from mkdocstrings_handlers.nim.collector import NimCollector, NimEntry, NimModule
from mkdocstrings_handlers.nim.docstring import DocstringStyle, parse_docstring

_logger = get_logger(__name__)

# Pattern for valid source URLs (GitHub, GitLab, Bitbucket, etc.)
_SOURCE_URL_PATTERN = re.compile(
    r"^https?://[^/]+/[^/]+/[^/]+/?$"  # https://host/org/repo or https://host/org/repo/
)


class NimHandler(BaseHandler):
    """The Nim handler class."""

    name: ClassVar[str] = "nim"
    domain: ClassVar[str] = "nim"
    fallback_theme: ClassVar[str] = "material"

    # Shared lexer and formatter for Pygments highlighting
    _nim_lexer = NimrodLexer()
    _html_formatter = HtmlFormatter(nowrap=True)

    def __init__(
        self,
        paths: list[str],
        base_dir: Path,
        *,
        theme: str = "material",
        custom_templates: str | None = None,
        config_options: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the handler.

        Args:
            paths: Search paths for Nim source files.
            base_dir: Base directory of the project.
            theme: MkDocs theme name.
            custom_templates: Path to custom templates.
            config_options: Handler options from mkdocs.yml.
            **kwargs: Additional arguments for BaseHandler.
        """
        super().__init__(
            theme=theme,
            custom_templates=custom_templates,
            **kwargs,
        )
        self.paths = paths or ["src"]
        self.base_dir = base_dir
        self.config_options = self._validate_and_enhance_config(config_options or {}, base_dir)
        self.collector = NimCollector(self.paths, base_dir)

        # Register custom Jinja filters
        self.env.filters["highlight_nim"] = self._highlight_nim

    @staticmethod
    def _highlight_nim(code: str) -> Markup:
        """Highlight Nim code using Pygments.

        Args:
            code: Nim source code to highlight.

        Returns:
            Highlighted HTML wrapped in Markup for safe rendering.
        """
        highlighted = highlight(code, NimHandler._nim_lexer, NimHandler._html_formatter)
        return Markup(highlighted)

    @staticmethod
    def _detect_git_branch(base_dir: Path) -> str | None:
        """Detect the current git branch.

        Args:
            base_dir: Directory to run git command in.

        Returns:
            Branch name or None if not in a git repo or detection fails.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=base_dir,
                timeout=5,
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                if branch and branch != "HEAD":  # HEAD means detached state
                    return branch
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return None

    def _validate_and_enhance_config(
        self, config: dict[str, Any], base_dir: Path
    ) -> dict[str, Any]:
        """Validate configuration and auto-detect missing values.

        Args:
            config: Raw configuration options.
            base_dir: Project base directory.

        Returns:
            Enhanced configuration with auto-detected values.
        """
        config = config.copy()
        show_source = config.get("show_source", True)
        source_url = config.get("source_url")
        source_ref = config.get("source_ref")

        # Auto-detect source_ref from git if not set
        if source_ref is None:
            detected_branch = self._detect_git_branch(base_dir)
            if detected_branch:
                config["source_ref"] = detected_branch
                _logger.debug(f"Auto-detected source_ref: {detected_branch}")
            else:
                config["source_ref"] = "main"  # fallback default
                if show_source and source_url:
                    _logger.warning(
                        "mkdocstrings-nim: Could not auto-detect git branch for source_ref. "
                        "Defaulting to 'main'. Set source_ref explicitly if this is incorrect."
                    )

        # Validate source_url format
        if source_url:
            # Remove trailing slash for consistency
            source_url = source_url.rstrip("/")
            config["source_url"] = source_url

            if not _SOURCE_URL_PATTERN.match(source_url + "/"):
                _logger.warning(
                    f"mkdocstrings-nim: source_url '{source_url}' may be malformed. "
                    "Expected format: https://github.com/owner/repo (no trailing /blob/ or /tree/)"
                )

            # Check for common mistakes
            if "/blob/" in source_url or "/tree/" in source_url:
                _logger.warning(
                    "mkdocstrings-nim: source_url should not contain '/blob/' or '/tree/'. "
                    "Use the repository root URL instead: e.g., https://github.com/owner/repo"
                )

        # Warn if show_source is enabled but source_url is not set
        elif show_source:
            _logger.info(
                "mkdocstrings-nim: show_source is enabled but source_url is not set. "
                "Source locations will show file:line without clickable links. "
                "Set source_url (e.g., https://github.com/owner/repo) to enable source links."
            )

        return config

    def get_options(self, local_options: Mapping[str, Any]) -> HandlerOptions:
        """Get combined options.

        Merges defaults < config options < directive options (local_options).

        Args:
            local_options: Local options from the directive.

        Returns:
            Combined options.
        """
        defaults = {
            "show_source": True,
            "show_signature": True,
            "show_pragmas": True,
            "show_private": False,  # Hide non-exported symbols by default
            "show_attribution": True,  # Show "Generated with mkdocstrings-nim" footer
            "heading_level": 2,
            "docstring_style": "rst",
            "source_url": None,  # e.g., "https://github.com/owner/repo"
            "source_ref": None,  # auto-detected from git, or set explicitly
            "type_field_doc_style": "inline",  # "inline" or "docstring"
        }
        return {**defaults, **self.config_options, **local_options}

    def _parse_entry_docstring(self, entry: NimEntry, style: DocstringStyle) -> None:
        """Parse docstring and update entry with structured documentation.

        Args:
            entry: The entry to update.
            style: Docstring style to use.
        """
        if not entry.doc:
            return

        parsed = parse_docstring(entry.doc, style)

        # Replace raw docstring with just the description (without field lists)
        entry.doc = parsed.description

        # Update params with descriptions from docstring
        for param in entry.params:
            for doc_param in parsed.params:
                if param.name == doc_param.name:
                    param.description = doc_param.description
                    break

        # Add returns description
        if parsed.returns:
            entry.returns_doc = parsed.returns.description

    def collect(self, identifier: str, options: HandlerOptions) -> CollectorItem:
        """Collect documentation for an identifier.

        Args:
            identifier: Module or item identifier.
            options: Collection options.

        Returns:
            Collected documentation data.
        """
        _logger.debug(f"Collecting {identifier}")
        module = self.collector.collect(identifier)

        # Filter non-exported entries unless show_private is True
        show_private = options.get("show_private", False)
        if not show_private:
            module.entries = [e for e in module.entries if e.exported]

        # Parse docstrings with configured style
        style_str = options.get("docstring_style", "rst")
        try:
            style = DocstringStyle(style_str)
        except ValueError:
            _logger.warning(
                f"Unknown docstring_style '{style_str}', falling back to 'rst'. "
                f"Valid options: {[s.value for s in DocstringStyle]}"
            )
            style = DocstringStyle.RST
        for entry in module.entries:
            self._parse_entry_docstring(entry, style)

        return module

    def render(
        self,
        data: CollectorItem,
        options: HandlerOptions,
        *,
        locale: str | None = None,  # noqa: ARG002
    ) -> str:
        """Render collected data to HTML.

        Args:
            data: Collected documentation data.
            options: Rendering options.

        Returns:
            Rendered HTML string.
        """
        if not isinstance(data, NimModule):
            raise TypeError(f"Expected NimModule, got {type(data)}")

        template = self.env.get_template("module.html.jinja")
        rendered = template.render(
            module=data,
            config=options,
            heading_level=options.get("heading_level", 2),
            root=True,
        )

        if _is_zensical() and self.extra_css:
            asset_link = '<link rel="stylesheet" href="assets/stylesheets/mkdocstrings-nim.css">'
            style_tag = f"<style>\n{self.extra_css}\n</style>"
            return f"{asset_link}\n{style_tag}\n{rendered}"

        return rendered


def _is_zensical() -> bool:
    """Check whether execution is running under the Zensical SSG environment."""
    return "zensical" in sys.modules


def _setup_zensical_assets(handler: NimHandler) -> None:
    """Register a post-build asset hook in Zensical to write handler CSS and media.

    Zensical runs builds through a Rust core (zrx) and does not invoke legacy
    MkDocs plugin hooks (like on_post_build). Instead, Zensical invokes
    `zensical.compat.mkdocstrings.get_inventory()` at the conclusion of the build
    to extract `objects.inv`. Hooking this callback allows writing handler-specific
    stylesheets and assets directly into the final `site/` distribution.
    """
    if not _is_zensical():
        return

    try:
        import zensical.compat.mkdocstrings as z_compat
        import zensical.config as z_config
    except ImportError:
        return

    if getattr(z_compat, "_nim_assets_hooked", False):
        return
    setattr(z_compat, "_nim_assets_hooked", True)  # noqa: B010

    original_get_inventory = z_compat.get_inventory

    def get_inventory_with_nim_assets(cached: bytes | None) -> bytes:
        result: bytes = original_get_inventory(cached)
        try:
            cfg = z_config.get_config()
            root_dir = Path(cfg.get("root_dir", ".")) if cfg else Path(".")
            site_dir = Path(cfg.get("site_dir", "site")) if cfg else Path("site")
            if not site_dir.is_absolute():
                site_dir = root_dir / site_dir

            # 1. Write handler extra_css to site/assets/stylesheets/mkdocstrings-nim.css
            if handler.extra_css:
                css_file = site_dir / "assets" / "stylesheets" / "mkdocstrings-nim.css"
                css_file.parent.mkdir(parents=True, exist_ok=True)
                css_file.write_text(handler.extra_css, encoding="utf-8")
                _logger.debug(f"Wrote mkdocstrings-nim stylesheet to {css_file}")

            # 2. Copy any extra media/asset files from templates if present
            searchpaths = getattr(handler.env.loader, "searchpath", [])
            for template_dir in searchpaths:
                assets_src = Path(template_dir) / "assets"
                if assets_src.is_dir():
                    assets_dest = site_dir / "assets" / "mkdocstrings-nim"
                    shutil.copytree(assets_src, assets_dest, dirs_exist_ok=True)
                    _logger.debug(
                        f"Copied mkdocstrings-nim template assets from {assets_src} to {assets_dest}"
                    )
        except Exception as err:
            _logger.warning(f"mkdocstrings-nim: Failed to write Zensical assets: {err}")

        return result

    setattr(get_inventory_with_nim_assets, "__wrapped__", original_get_inventory)  # noqa: B010
    z_compat.get_inventory = get_inventory_with_nim_assets


def get_handler(
    handler_config: MutableMapping[str, Any],
    tool_config: Any,
    **kwargs: Any,
) -> NimHandler:
    """Return a NimHandler instance.

    Args:
        handler_config: Handler configuration from mkdocs.yml.
        tool_config: MkDocs configuration.
        **kwargs: Additional arguments.

    Returns:
        NimHandler instance.
    """
    base_dir = Path(getattr(tool_config, "config_file_path", "./mkdocs.yml")).parent
    paths = handler_config.get("paths", ["src"])
    options = handler_config.get("options", {})

    handler = NimHandler(
        paths=paths,
        base_dir=base_dir,
        config_options=options,
        **kwargs,
    )

    if _is_zensical():
        _setup_zensical_assets(handler)

    return handler
