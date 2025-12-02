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


class TestGoogleDocstring:
    """Tests for Google-style docstring parsing."""

    def test_parse_simple(self):
        """Test parsing a simple docstring."""
        doc = "A simple description."
        result = parse_docstring(doc, style=DocstringStyle.GOOGLE)

        assert result.description == "A simple description."
        assert result.params == []
        assert result.returns is None

    def test_parse_with_params(self):
        """Test parsing docstring with parameters."""
        doc = """Do something.

Args:
    name: The name to use
    value: The value to set
"""
        result = parse_docstring(doc, style=DocstringStyle.GOOGLE)

        assert "Do something." in result.description
        assert len(result.params) == 2
        assert result.params[0].name == "name"
        assert result.params[0].description == "The name to use"
        assert result.params[1].name == "value"
        assert result.params[1].description == "The value to set"

    def test_parse_with_returns(self):
        """Test parsing docstring with return value."""
        doc = """Calculate sum.

Args:
    a: First number

Returns:
    The sum of the numbers
"""
        result = parse_docstring(doc, style=DocstringStyle.GOOGLE)

        assert result.returns is not None
        assert result.returns.description == "The sum of the numbers"

    def test_parse_with_raises(self):
        """Test parsing docstring with raises."""
        doc = """Do risky thing.

Raises:
    ValueError: If value is invalid
    IOError: If file not found
"""
        result = parse_docstring(doc, style=DocstringStyle.GOOGLE)

        assert len(result.raises) == 2
        assert result.raises[0].type == "ValueError"
        assert result.raises[0].description == "If value is invalid"
        assert result.raises[1].type == "IOError"


class TestNumpyDocstring:
    """Tests for NumPy-style docstring parsing."""

    def test_parse_simple(self):
        """Test parsing a simple docstring."""
        doc = "A simple description."
        result = parse_docstring(doc, style=DocstringStyle.NUMPY)

        assert result.description == "A simple description."
        assert result.params == []
        assert result.returns is None

    def test_parse_with_params(self):
        """Test parsing docstring with parameters."""
        doc = """Do something.

Parameters
----------
name
    The name to use
value
    The value to set
"""
        result = parse_docstring(doc, style=DocstringStyle.NUMPY)

        assert "Do something." in result.description
        assert len(result.params) == 2
        assert result.params[0].name == "name"
        assert result.params[0].description == "The name to use"
        assert result.params[1].name == "value"
        assert result.params[1].description == "The value to set"

    def test_parse_with_returns(self):
        """Test parsing docstring with return value."""
        doc = """Calculate sum.

Parameters
----------
a
    First number

Returns
-------
int
    The sum of the numbers
"""
        result = parse_docstring(doc, style=DocstringStyle.NUMPY)

        assert result.returns is not None
        assert result.returns.type == "int"
        assert "sum" in result.returns.description.lower()

    def test_parse_with_raises(self):
        """Test parsing docstring with raises."""
        doc = """Do risky thing.

Raises
------
ValueError
    If value is invalid
"""
        result = parse_docstring(doc, style=DocstringStyle.NUMPY)

        assert len(result.raises) == 1
        assert result.raises[0].type == "ValueError"
        assert "invalid" in result.raises[0].description.lower()


class TestEpydocDocstring:
    """Tests for Epydoc-style docstring parsing."""

    def test_parse_simple(self):
        """Test parsing a simple docstring."""
        doc = "A simple description."
        result = parse_docstring(doc, style=DocstringStyle.EPYDOC)

        assert result.description == "A simple description."
        assert result.params == []
        assert result.returns is None

    def test_parse_with_params(self):
        """Test parsing docstring with parameters."""
        doc = """Do something.

@param name: The name to use
@param value: The value to set
"""
        result = parse_docstring(doc, style=DocstringStyle.EPYDOC)

        assert "Do something." in result.description
        assert len(result.params) == 2
        assert result.params[0].name == "name"
        assert result.params[0].description == "The name to use"
        assert result.params[1].name == "value"
        assert result.params[1].description == "The value to set"

    def test_parse_with_returns(self):
        """Test parsing docstring with return value."""
        doc = """Calculate sum.

@param a: First number
@return: The sum of the numbers
"""
        result = parse_docstring(doc, style=DocstringStyle.EPYDOC)

        assert result.returns is not None
        assert result.returns.description == "The sum of the numbers"

    def test_parse_with_raises(self):
        """Test parsing docstring with raises."""
        doc = """Do risky thing.

@raise ValueError: If value is invalid
@raise IOError: If file not found
"""
        result = parse_docstring(doc, style=DocstringStyle.EPYDOC)

        assert len(result.raises) == 2
        assert result.raises[0].type == "ValueError"
        assert result.raises[0].description == "If value is invalid"
        assert result.raises[1].type == "IOError"


class TestEdgeCases:
    """Tests for edge cases in docstring parsing."""

    def test_empty_docstring(self):
        """Test parsing empty docstring."""
        result = parse_docstring("", style=DocstringStyle.RST)

        assert result.description == ""
        assert result.params == []
        assert result.returns is None
        assert result.raises == []

    def test_whitespace_only_docstring(self):
        """Test parsing whitespace-only docstring."""
        result = parse_docstring("   \n\t  ", style=DocstringStyle.RST)

        # Should parse as description or empty
        assert result is not None

    def test_malformed_docstring_fallback(self):
        """Test that malformed docstrings fall back gracefully."""
        # This is intentionally malformed
        doc = """Description here.

:param missing closing
:returns but no colon
:raises: no type given
"""
        # Should not raise, should return something reasonable
        result = parse_docstring(doc, style=DocstringStyle.RST)
        assert "Description" in result.description

    def test_long_description(self):
        """Test docstring with short and long description."""
        doc = """Short description.

This is a longer description that spans
multiple lines and provides more detail.
"""
        result = parse_docstring(doc, style=DocstringStyle.RST)

        assert "Short description" in result.description
        assert "longer description" in result.description
