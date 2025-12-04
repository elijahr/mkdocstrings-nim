"""Integration tests for type field extraction."""

from pathlib import Path

import pytest

from mkdocstrings_handlers.nim.collector import NimCollector


@pytest.fixture
def collector():
    """Create collector with test fixtures."""
    base_dir = Path(__file__).parent.parent.parent
    return NimCollector(["tests/fixtures"], base_dir)


class TestObjectFieldExtraction:
    """Tests for object field extraction."""

    def test_simple_object_fields(self, collector):
        """Test extraction of simple object fields."""
        module = collector.collect("types_with_fields")

        simple_obj = next(e for e in module.entries if e.name == "SimpleObject")

        assert len(simple_obj.fields) == 3

        x_field = next(f for f in simple_obj.fields if f.name == "x")
        assert x_field.type == "int"
        assert x_field.doc == "X coordinate"
        assert x_field.exported is True

        z_field = next(f for f in simple_obj.fields if f.name == "z")
        assert z_field.exported is False

    def test_ref_object_fields(self, collector):
        """Test extraction of ref object fields."""
        module = collector.collect("types_with_fields")

        ref_obj = next(e for e in module.entries if e.name == "RefCounter")

        assert len(ref_obj.fields) == 2
        assert any(f.name == "count" and f.exported for f in ref_obj.fields)
        assert any(f.name == "max" and not f.exported for f in ref_obj.fields)

    def test_empty_object_no_fields(self, collector):
        """Test that empty objects have no fields."""
        module = collector.collect("types_with_fields")

        empty = next(e for e in module.entries if e.name == "Empty")

        assert len(empty.fields) == 0


class TestEnumValueExtraction:
    """Tests for enum value extraction."""

    def test_enum_with_values_and_docs(self, collector):
        """Test extraction of enum values with documentation."""
        module = collector.collect("types_with_fields")

        color = next(e for e in module.entries if e.name == "Color")

        assert len(color.values) == 3

        red = next(v for v in color.values if v.name == "Red")
        assert red.type == "0"
        assert red.doc == "The color red"

    def test_simple_enum_without_values(self, collector):
        """Test extraction of simple enum without explicit values."""
        module = collector.collect("types_with_fields")

        node_kind = next(e for e in module.entries if e.name == "NodeKind")

        assert len(node_kind.values) == 3
        assert any(v.name == "nkInt" for v in node_kind.values)


class TestCaseObjectExtraction:
    """Tests for case/variant object extraction."""

    def test_case_object_discriminator(self, collector):
        """Test extraction of case object discriminator."""
        module = collector.collect("types_with_fields")

        node = next(e for e in module.entries if e.name == "Node")

        # Should have discriminator
        kind_field = next((f for f in node.fields if f.name == "kind"), None)
        assert kind_field is not None
        assert kind_field.type == "NodeKind"
        assert kind_field.branch == ""  # Discriminator has no branch

    def test_case_object_branch_fields(self, collector):
        """Test extraction of case object branch fields."""
        module = collector.collect("types_with_fields")

        node = next(e for e in module.entries if e.name == "Node")

        # Check branch annotations
        int_val = next((f for f in node.fields if f.name == "intVal"), None)
        assert int_val is not None
        assert "nkInt" in int_val.branch

        str_val = next((f for f in node.fields if f.name == "strVal"), None)
        assert str_val is not None
        assert "nkString" in str_val.branch
