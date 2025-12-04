"""Tests for type field extraction."""

from mkdocstrings_handlers.nim.collector import NimEntry, NimField


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


def test_nimentry_has_fields_and_values():
    """Test that NimEntry has fields and values attributes."""
    entry = NimEntry(
        name="MyType",
        kind="type",
        line=10,
        signature="type MyType = object",
    )
    assert hasattr(entry, "fields")
    assert hasattr(entry, "values")
    assert entry.fields == []
    assert entry.values == []


def test_nimentry_with_fields():
    """Test NimEntry with populated fields."""
    fields = [
        NimField(name="x", type="int", doc="X coordinate"),
        NimField(name="y", type="int", doc="Y coordinate"),
    ]
    entry = NimEntry(
        name="Point",
        kind="type",
        line=1,
        signature="type Point = object",
        fields=fields,
    )
    assert len(entry.fields) == 2
    assert entry.fields[0].name == "x"
