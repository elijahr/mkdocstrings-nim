"""Tests for docstring parsing."""

import pytest
from mkdocstrings_handlers.nim.docstring import parse_docstring, DocstringStyle


class TestRstDocstring:
    """Tests for RST-style docstring parsing."""

    def test_parse_simple(self):
        """Test parsing a simple docstring."""
        doc = "A simple description."
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert result.description == "A simple description."
        assert result.params == []
        assert result.returns is None

    def test_parse_with_params(self):
        """Test parsing docstring with parameters."""
        doc = """Do something.

        :param name: The name to use
        :param value: The value to set
        """
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert result.description == "Do something."
        assert len(result.params) == 2
        assert result.params[0].name == "name"
        assert result.params[0].description == "The name to use"

    def test_parse_with_returns(self):
        """Test parsing docstring with return value."""
        doc = """Calculate sum.

        :param a: First number
        :returns: The sum
        """
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert result.returns.description == "The sum"

    def test_parse_with_raises(self):
        """Test parsing docstring with raises."""
        doc = """Do risky thing.

        :raises ValueError: If value is invalid
        """
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert len(result.raises) == 1
        assert result.raises[0].type == "ValueError"
        assert result.raises[0].description == "If value is invalid"
