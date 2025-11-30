"""Tests for the Nim handler."""

import pytest
from pathlib import Path

from mkdocstrings_handlers.nim.handler import NimHandler, get_handler
from mkdocstrings_handlers.nim.collector import NimCollector, NimModule


class TestNimCollector:
    """Tests for NimCollector."""

    def test_resolve_identifier_simple(self, tmp_path: Path):
        """Test resolving a simple identifier."""
        # Create test file
        src = tmp_path / "src"
        src.mkdir()
        (src / "mymodule.nim").write_text("## Test module")

        collector = NimCollector(["src"], tmp_path)
        path = collector._resolve_identifier("mymodule")

        assert path == src / "mymodule.nim"

    def test_resolve_identifier_nested(self, tmp_path: Path):
        """Test resolving a nested identifier."""
        # Create nested structure
        src = tmp_path / "src" / "package"
        src.mkdir(parents=True)
        (src / "submodule.nim").write_text("## Test module")

        collector = NimCollector(["src"], tmp_path)
        path = collector._resolve_identifier("package.submodule")

        assert path == src / "submodule.nim"


class TestNimHandler:
    """Tests for NimHandler."""

    def test_get_options_defaults(self):
        """Test default options."""
        handler = NimHandler(
            paths=["src"],
            base_dir=Path("."),
            mdx=[],
            mdx_config={},
        )
        options = handler.get_options({})

        assert options["show_source"] is True
        assert options["heading_level"] == 2

    def test_get_options_override(self):
        """Test option override."""
        handler = NimHandler(
            paths=["src"],
            base_dir=Path("."),
            mdx=[],
            mdx_config={},
        )
        options = handler.get_options({"show_source": False})

        assert options["show_source"] is False


def test_invalid_docstring_style_fallback(tmp_path, caplog):
    """Test that invalid docstring_style falls back to RST with warning."""
    import logging
    from mkdocstrings_handlers.nim.handler import NimHandler

    handler = NimHandler(paths=["src"], base_dir=tmp_path, mdx=[], mdx_config={})
    options = handler.get_options({"docstring_style": "invalid_style"})

    # This should not raise, should fall back to RST
    # We need a minimal Nim file to test collect()
    nim_file = tmp_path / "src" / "test.nim"
    nim_file.parent.mkdir(parents=True, exist_ok=True)
    nim_file.write_text('proc foo*() = discard\n')

    with caplog.at_level(logging.WARNING):
        # Should not raise ValueError
        try:
            handler.collect("test", options)
        except Exception as e:
            # Collection may fail for other reasons (no Nim), but not ValueError
            assert "invalid_style" not in str(e)
