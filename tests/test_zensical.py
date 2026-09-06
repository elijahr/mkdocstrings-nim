"""Tests for Zensical support and asset generation in mkdocstrings-nim."""

import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mkdocstrings_handlers.nim.collector import NimEntry, NimModule, NimParam
from mkdocstrings_handlers.nim.handler import (
    NimHandler,
    _is_zensical,
    _setup_zensical_assets,
    get_handler,
)


@pytest.fixture
def mock_tool_config(tmp_path: Path):
    """Create a mock tool_config with config_file_path."""
    config = MagicMock()
    config.config_file_path = str(tmp_path / "mkdocs.yml")
    return config


def test_is_zensical_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test detection of Zensical environment via sys.modules."""
    monkeypatch.delitem(sys.modules, "zensical", raising=False)
    assert not _is_zensical()

    fake_zensical = types.ModuleType("zensical")
    monkeypatch.setitem(sys.modules, "zensical", fake_zensical)
    assert _is_zensical()


def test_setup_zensical_assets_hook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _setup_zensical_assets hooks get_inventory and writes CSS assets."""
    site_dir = tmp_path / "site"

    # Create mock zensical modules
    fake_zensical = types.ModuleType("zensical")
    fake_z_compat = types.ModuleType("zensical.compat")
    fake_z_compat_mk = types.ModuleType("zensical.compat.mkdocstrings")
    fake_z_config = types.ModuleType("zensical.config")

    fake_z_compat_mk.get_inventory = MagicMock(return_value=b"inventory-data")
    fake_z_config.get_config = MagicMock(
        return_value={
            "root_dir": str(tmp_path),
            "site_dir": str(site_dir),
        }
    )

    monkeypatch.setitem(sys.modules, "zensical", fake_zensical)
    monkeypatch.setitem(sys.modules, "zensical.compat", fake_z_compat)
    monkeypatch.setitem(sys.modules, "zensical.compat.mkdocstrings", fake_z_compat_mk)
    monkeypatch.setitem(sys.modules, "zensical.config", fake_z_config)

    handler = NimHandler(
        paths=["src"],
        base_dir=tmp_path,
        mdx=[],
        mdx_config={},
    )

    _setup_zensical_assets(handler)

    # get_inventory should now be wrapped
    assert fake_z_compat_mk.get_inventory != fake_z_compat_mk.get_inventory.__wrapped__  # type: ignore[attr-defined]

    # Execute hooked get_inventory
    result = fake_z_compat_mk.get_inventory(b"cached")
    assert result == b"inventory-data"

    # Verify that the CSS asset was written to site_dir
    expected_css = site_dir / "assets" / "stylesheets" / "mkdocstrings-nim.css"
    assert expected_css.exists()
    assert expected_css.read_text(encoding="utf-8") == handler.extra_css


def test_render_zensical_includes_assets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test that render() includes asset link and styling when running under Zensical."""
    fake_zensical = types.ModuleType("zensical")
    monkeypatch.setitem(sys.modules, "zensical", fake_zensical)

    handler = NimHandler(
        paths=["src"],
        base_dir=tmp_path,
        mdx=[],
        mdx_config={},
    )

    def mock_heading(text: str, level: int, **kwargs: Any) -> str:
        html_id = kwargs.get("id", "")
        html_class = kwargs.get("class", "")
        return f'<h{level} id="{html_id}" class="{html_class}">{text}</h{level}>'

    handler.env.filters["heading"] = mock_heading

    module = NimModule(
        module="test_mod",
        file="test_mod.nim",
        entries=[
            NimEntry(
                name="myProc",
                kind="proc",
                line=1,
                signature="proc myProc(x: int): int",
                exported=True,
                params=[NimParam(name="x", type="int")],
                returns="int",
            )
        ],
    )

    rendered = handler.render(module, handler.get_options({}))
    assert 'href="assets/stylesheets/mkdocstrings-nim.css"' in rendered
    assert "<style>" in rendered
    assert ".doc-symbol-proc" in rendered


def test_render_standard_mkdocs_clean(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test that render() produces clean output without Zensical asset wrappers under standard MkDocs."""
    monkeypatch.delitem(sys.modules, "zensical", raising=False)

    handler = NimHandler(
        paths=["src"],
        base_dir=tmp_path,
        mdx=[],
        mdx_config={},
    )

    def mock_heading(text: str, level: int, **kwargs: Any) -> str:
        html_id = kwargs.get("id", "")
        html_class = kwargs.get("class", "")
        return f'<h{level} id="{html_id}" class="{html_class}">{text}</h{level}>'

    handler.env.filters["heading"] = mock_heading

    module = NimModule(
        module="test_mod",
        file="test_mod.nim",
        entries=[
            NimEntry(
                name="myProc",
                kind="proc",
                line=1,
                signature="proc myProc(x: int): int",
                exported=True,
                params=[NimParam(name="x", type="int")],
                returns="int",
            )
        ],
    )

    rendered = handler.render(module, handler.get_options({}))
    assert 'href="assets/stylesheets/mkdocstrings-nim.css"' not in rendered


def test_get_handler_triggers_zensical_setup(
    tmp_path: Path, mock_tool_config: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that get_handler automatically installs the Zensical asset hook when Zensical is active."""
    site_dir = tmp_path / "site"

    fake_zensical = types.ModuleType("zensical")
    fake_z_compat = types.ModuleType("zensical.compat")
    fake_z_compat_mk = types.ModuleType("zensical.compat.mkdocstrings")
    fake_z_config = types.ModuleType("zensical.config")

    fake_z_compat_mk.get_inventory = MagicMock(return_value=b"inv")
    fake_z_config.get_config = MagicMock(
        return_value={
            "root_dir": str(tmp_path),
            "site_dir": str(site_dir),
        }
    )

    monkeypatch.setitem(sys.modules, "zensical", fake_zensical)
    monkeypatch.setitem(sys.modules, "zensical.compat", fake_z_compat)
    monkeypatch.setitem(sys.modules, "zensical.compat.mkdocstrings", fake_z_compat_mk)
    monkeypatch.setitem(sys.modules, "zensical.config", fake_z_config)

    handler = get_handler(
        handler_config={"paths": ["src"]},
        tool_config=mock_tool_config,
        mdx=[],
        mdx_config={},
    )
    assert isinstance(handler, NimHandler)

    # Call get_inventory to verify hook was installed
    fake_z_compat_mk.get_inventory(None)
    css_file = site_dir / "assets" / "stylesheets" / "mkdocstrings-nim.css"
    assert css_file.exists()


def test_zensical_build_full_integration(tmp_path: Path) -> None:
    """End-to-end integration test with real zensical build."""
    try:
        import zensical
    except ImportError:
        pytest.skip("zensical not installed")

    src = tmp_path / "src"
    src.mkdir()
    (src / "maths.nim").write_text(
        "## Math utilities.\n\nproc multiply*(a, b: int): int =\n  ## Multiplies two integers.\n  result = a * b\n"
    )

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Math API\n\n::: maths\n    handler: nim\n")

    config = tmp_path / "zensical.toml"
    config.write_text(
        """[project]
site_name = "Integration Test"

[project.plugins.mkdocstrings]
default_handler = "nim"

[project.plugins.mkdocstrings.handlers.nim]
paths = ["src"]
"""
    )

    zensical.build(str(config), {"clean": True, "strict": False})

    site_dir = tmp_path / "site"
    assert (site_dir / "index.html").exists()
    html = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "multiply" in html
    assert "Multiplies two integers" in html

    # Verify that the CSS asset was written by our hook into site/
    css_file = site_dir / "assets" / "stylesheets" / "mkdocstrings-nim.css"
    assert css_file.exists()
    assert ".doc-symbol-proc" in css_file.read_text(encoding="utf-8")
