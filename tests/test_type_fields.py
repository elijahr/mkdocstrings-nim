"""Tests for type field extraction."""

from mkdocstrings_handlers.nim.collector import NimField


def test_nimfield_dataclass_exists():
    """Test that NimField dataclass exists with correct fields."""
    field = NimField(
        name="test",
        type="int",
        doc="A test field",
        exported=True,
        branch="",
    )
    assert field.name == "test"
    assert field.type == "int"
    assert field.doc == "A test field"
    assert field.exported is True
    assert field.branch == ""


def test_nimfield_defaults():
    """Test NimField default values."""
    field = NimField(name="x", type="string")
    assert field.doc == ""
    assert field.exported is True
    assert field.branch == ""
