"""Tests for template rendering of type fields and values."""

import pytest

from mkdocstrings_handlers.nim.handler import get_handler


class MockToolConfig:
    """Mock MkDocs tool config."""

    def __init__(self, tmp_path):
        self.config_file_path = str(tmp_path / "mkdocs.yml")


@pytest.fixture
def handler(tmp_path):
    """Create a handler with test setup."""
    src = tmp_path / "src"
    src.mkdir()
    handler = get_handler(
        handler_config={"paths": ["src"]},
        tool_config=MockToolConfig(tmp_path),
        mdx=[],
        mdx_config={},
    )

    # Mock filters for testing
    handler.env.filters["convert_markdown"] = lambda text, *_args, **_kwargs: text

    def mock_heading(text, level, **kwargs):
        html_id = kwargs.get("id", "")
        html_class = kwargs.get("class", "")
        return f'<h{level} id="{html_id}" class="{html_class}">{text}</h{level}>'

    handler.env.filters["heading"] = mock_heading

    return handler


class TestFieldsRendering:
    """Tests for object fields rendering."""

    def test_fields_section_renders_for_object_types(self, handler, tmp_path):
        """Test that fields section renders for object types."""
        src = tmp_path / "src"
        (src / "test.nim").write_text(
            """
type Point* = object
  ## A simple point type.
  x*: int  ## X coordinate
  y*: int  ## Y coordinate
"""
        )

        options = handler.get_options({})
        data = handler.collect("test", options)
        result = handler.render(data, options)

        assert "doc-section-fields" in result
        assert "Fields" in result
        assert "doc-field-name" in result
        assert ">x<" in result
        assert ">y<" in result
        assert "int" in result

    def test_private_fields_hidden_when_show_private_false(self, handler, tmp_path):
        """Test that private fields are hidden when show_private=False."""
        src = tmp_path / "src"
        (src / "test.nim").write_text(
            """
type Counter* = object
  count*: int
  max: int
"""
        )

        options = handler.get_options({"show_private": False})
        data = handler.collect("test", options)
        result = handler.render(data, options)

        assert ">count<" in result
        assert ">max<" not in result

    def test_private_fields_show_with_label_when_show_private_true(self, handler, tmp_path):
        """Test that private fields show with label when show_private=True."""
        src = tmp_path / "src"
        (src / "test.nim").write_text(
            """
type Counter* = object
  count*: int
  max: int
"""
        )

        options = handler.get_options({"show_private": True})
        data = handler.collect("test", options)
        result = handler.render(data, options)

        assert ">count<" in result
        assert ">max<" in result
        assert "doc-field-private" in result
        assert "private" in result

    def test_branch_annotations_render_for_case_objects(self, handler, tmp_path):
        """Test that branch annotations render for case objects."""
        src = tmp_path / "src"
        (src / "test.nim").write_text(
            """
type NodeKind* = enum
  nkInt, nkString

type Node* = object
  case kind*: NodeKind
  of nkInt:
    intVal*: int
  of nkString:
    strVal*: string
"""
        )

        options = handler.get_options({})
        data = handler.collect("test", options)
        result = handler.render(data, options)

        assert "doc-field-branch" in result
        assert "[when nkInt]" in result
        assert "[when nkString]" in result


class TestValuesRendering:
    """Tests for enum values rendering."""

    def test_values_section_renders_for_enum_types(self, handler, tmp_path):
        """Test that values section renders for enum types."""
        src = tmp_path / "src"
        (src / "test.nim").write_text(
            """
type Color* = enum
  Red = 0    ## The color red
  Green = 1  ## The color green
  Blue = 2   ## The color blue
"""
        )

        options = handler.get_options({})
        data = handler.collect("test", options)
        result = handler.render(data, options)

        assert "doc-section-values" in result
        assert "Values" in result
        assert "doc-value-name" in result
        assert ">Red<" in result
        assert ">Green<" in result
        assert ">Blue<" in result
        assert "The color red" in result

    def test_enum_explicit_values_render(self, handler, tmp_path):
        """Test that explicit enum values render."""
        src = tmp_path / "src"
        (src / "test.nim").write_text(
            """
type Status* = enum
  Active = 100
  Inactive = 200
"""
        )

        options = handler.get_options({})
        data = handler.collect("test", options)
        result = handler.render(data, options)

        assert "= <code>100</code>" in result
        assert "= <code>200</code>" in result

    def test_enum_without_explicit_values(self, handler, tmp_path):
        """Test rendering of enum without explicit values."""
        src = tmp_path / "src"
        (src / "test.nim").write_text(
            """
type NodeKind* = enum
  nkInt, nkFloat, nkString
"""
        )

        options = handler.get_options({})
        data = handler.collect("test", options)
        result = handler.render(data, options)

        assert ">nkInt<" in result
        assert ">nkFloat<" in result
        assert ">nkString<" in result
        # Should not show "= <code>" for implicit values
        assert "= <code></code>" not in result
