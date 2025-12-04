"""Tests for type field extraction."""

from mkdocstrings_handlers.nim.collector import NimCollector, NimEntry, NimField


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


def test_parse_module_with_fields(tmp_path):
    """Test parsing module data with fields."""
    collector = NimCollector(["src"], tmp_path)
    data = {
        "module": "test",
        "file": str(tmp_path / "test.nim"),
        "entries": [
            {
                "name": "Point",
                "kind": "type",
                "line": 1,
                "signature": "type Point = object",
                "fields": [
                    {"name": "x", "type": "int", "doc": "X coord", "exported": True, "branch": ""},
                    {"name": "y", "type": "int", "doc": "Y coord", "exported": True, "branch": ""},
                ],
            }
        ],
    }

    module = collector._parse_module(data)

    assert len(module.entries) == 1
    assert len(module.entries[0].fields) == 2
    assert module.entries[0].fields[0].name == "x"
    assert module.entries[0].fields[0].type == "int"
    assert module.entries[0].fields[0].doc == "X coord"


def test_parse_module_with_enum_values(tmp_path):
    """Test parsing module data with enum values."""
    collector = NimCollector(["src"], tmp_path)
    data = {
        "module": "test",
        "file": str(tmp_path / "test.nim"),
        "entries": [
            {
                "name": "Color",
                "kind": "type",
                "line": 1,
                "signature": "type Color = enum",
                "values": [
                    {"name": "Red", "type": "", "doc": "Red color", "exported": True, "branch": ""},
                    {"name": "Green", "type": "1", "doc": "", "exported": True, "branch": ""},
                ],
            }
        ],
    }

    module = collector._parse_module(data)

    assert len(module.entries) == 1
    assert len(module.entries[0].values) == 2
    assert module.entries[0].values[0].name == "Red"
    assert module.entries[0].values[1].type == "1"
