"""Nim handler for mkdocstrings."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, MutableMapping

from mkdocstrings import BaseHandler, CollectorItem, HandlerOptions, get_logger

from mkdocstrings_handlers.nim.collector import NimCollector, NimModule, NimEntry
from mkdocstrings_handlers.nim.docstring import parse_docstring, DocstringStyle

_logger = get_logger(__name__)


class NimHandler(BaseHandler):
    """The Nim handler class."""

    name: ClassVar[str] = "nim"
    domain: ClassVar[str] = "nim"
    fallback_theme: ClassVar[str] = "material"

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
        self.config_options = config_options or {}
        self.collector = NimCollector(self.paths, base_dir)

    def get_options(self, local_options: MutableMapping[str, Any]) -> HandlerOptions:
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
            "heading_level": 2,
            "docstring_style": "rst",
            "source_url": None,  # e.g., "https://github.com/owner/repo"
            "source_ref": "main",  # branch or tag
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

    def render(self, data: CollectorItem, options: HandlerOptions) -> str:
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
        return template.render(
            module=data,
            config=options,
            heading_level=options.get("heading_level", 2),
            root=True,
        )


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

    return NimHandler(
        paths=paths,
        base_dir=base_dir,
        config_options=options,
        **kwargs,
    )
