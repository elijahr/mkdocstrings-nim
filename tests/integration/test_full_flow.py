"""End-to-end integration tests.

Test Coverage Strategy
----------------------
The Nim extractor (nimdocinfo.nim, extractor.nim) does not have direct unit tests.
Instead, coverage is provided through Python integration tests that:

1. Compile and run the Nim extractor on fixture files
2. Verify the JSON output contains expected structure and data
3. Test edge cases through various Nim source patterns in fixtures

This approach was chosen because:
- The extractor's correctness is validated by the Python tests
- Adding Nim unit tests would require a separate test framework
- Integration tests catch issues at the interface where they matter

The Python tests cover:
- Module-level documentation extraction
- Proc/func/template/macro signatures
- Parameter and return type extraction
- Docstring parsing and formatting
- Error handling for invalid inputs
"""

import pytest
from pathlib import Path
from mkdocstrings_handlers.nim.handler import get_handler
from mkdocstrings_handlers.nim.collector import NimModule


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "sample_project"


class MockToolConfig:
    """Mock MkDocs tool config."""
    config_file_path = str(FIXTURE_DIR / "mkdocs.yml")


@pytest.fixture
def handler():
    """Create a handler for testing."""
    return get_handler(
        handler_config={"paths": ["src"]},
        tool_config=MockToolConfig(),
        mdx=[],
        mdx_config={},
    )


class TestFullFlow:
    """End-to-end tests."""

    @pytest.mark.skipif(
        not (FIXTURE_DIR / "src" / "mylib.nim").exists(),
        reason="Fixture not found"
    )
    def test_collect_module(self, handler):
        """Test collecting a full module."""
        options = handler.get_options({})
        module = handler.collect("mylib", options)

        assert isinstance(module, NimModule)
        assert module.module == "mylib"
        assert "sample library" in module.doc.lower()

        # Check entries
        entry_names = [e.name for e in module.entries]
        assert "Version" in entry_names
        assert "Config" in entry_names
        assert "initialize" in entry_names
        assert "process" in entry_names

    @pytest.mark.skipif(
        not (FIXTURE_DIR / "src" / "mylib.nim").exists(),
        reason="Fixture not found"
    )
    def test_collect_parses_docstrings(self, handler):
        """Test that docstrings are parsed for parameter descriptions."""
        options = handler.get_options({})
        module = handler.collect("mylib", options)

        # Find the initialize proc
        initialize = next((e for e in module.entries if e.name == "initialize"), None)
        assert initialize is not None
        assert len(initialize.params) == 1
        assert initialize.params[0].name == "cfg"
        assert initialize.params[0].description == "Configuration to use"
        assert initialize.returns_doc == "True if successful"

    @pytest.mark.skipif(
        not (FIXTURE_DIR / "src" / "mylib.nim").exists(),
        reason="Fixture not found"
    )
    def test_render_module(self, handler):
        """Test rendering a module to HTML."""
        # Mock the convert_markdown filter to return input unchanged
        # This allows testing template rendering without full MkDocs infrastructure
        handler.env.filters["convert_markdown"] = lambda text, *args, **kwargs: text

        # Mock the heading filter to just wrap content in a heading tag
        def mock_heading(text, level, **kwargs):
            html_id = kwargs.get("id", "")
            html_class = kwargs.get("class", "")
            return f'<h{level} id="{html_id}" class="{html_class}">{text}</h{level}>'
        handler.env.filters["heading"] = mock_heading

        options = handler.get_options({})
        module = handler.collect("mylib", options)
        html = handler.render(module, options)

        # Verify HTML structure
        assert '<div class="doc doc-object doc-module">' in html
        assert "mylib" in html
        assert "initialize" in html
        assert "Config" in html
        # Verify docstring content is present
        assert "sample library" in html.lower()
