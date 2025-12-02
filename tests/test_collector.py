"""Tests for collector path resolution."""
import pytest
from pathlib import Path
from importlib.resources import as_file
from mkdocstrings import CollectionError
from mkdocstrings_handlers.nim.collector import NimCollector, _JSON_START_MARKER, _JSON_END_MARKER


def test_nimdocinfo_path_exists():
    """Test that nimdocinfo source path resolves correctly."""
    collector = NimCollector(paths=["src"], base_dir=Path.cwd())
    # Use as_file to get actual path for checking
    with as_file(collector._nimdocinfo_source) as path:
        assert path.exists(), f"Path not found: {path}"
        assert path.name == "nimdocinfo.nim"


class TestResolveIdentifier:
    """Tests for identifier resolution."""

    def test_resolve_identifier_not_found(self, tmp_path):
        """Test that CollectionError is raised for non-existent module."""
        collector = NimCollector(["src"], tmp_path)
        (tmp_path / "src").mkdir()

        with pytest.raises(CollectionError, match="Could not find Nim file"):
            collector._resolve_identifier("nonexistent")

    def test_resolve_identifier_fallback_filename(self, tmp_path):
        """Test fallback to just filename when nested path doesn't exist."""
        src = tmp_path / "src"
        src.mkdir()
        # Create file without nested structure
        (src / "mymodule.nim").write_text("## Test")

        collector = NimCollector(["src"], tmp_path)
        # This would first try src/some/nested/mymodule.nim, then fall back to src/mymodule.nim
        path = collector._resolve_identifier("some.nested.mymodule")

        assert path == src / "mymodule.nim"


class TestExtractJson:
    """Tests for JSON extraction from nimdocinfo output."""

    def test_extract_json_success(self, tmp_path):
        """Test successful JSON extraction."""
        collector = NimCollector(["src"], tmp_path)
        stdout = f'{_JSON_START_MARKER}{{"module": "test", "file": "test.nim", "entries": []}}{_JSON_END_MARKER}'

        result = collector._extract_json(stdout, Path("test.nim"))

        assert result["module"] == "test"
        assert result["entries"] == []

    def test_extract_json_missing_markers(self, tmp_path):
        """Test error when markers are missing."""
        collector = NimCollector(["src"], tmp_path)
        stdout = '{"module": "test"}'  # No markers

        with pytest.raises(CollectionError, match="Could not find JSON markers"):
            collector._extract_json(stdout, Path("test.nim"))

    def test_extract_json_invalid_json(self, tmp_path):
        """Test error when JSON is invalid."""
        collector = NimCollector(["src"], tmp_path)
        stdout = f'{_JSON_START_MARKER}{{invalid json}}{_JSON_END_MARKER}'

        with pytest.raises(CollectionError, match="Invalid JSON"):
            collector._extract_json(stdout, Path("test.nim"))


class TestParseModule:
    """Tests for module parsing."""

    def test_parse_module_missing_required_fields(self, tmp_path):
        """Test error when required fields are missing."""
        collector = NimCollector(["src"], tmp_path)
        data = {"module": "test"}  # Missing 'file' and 'entries'

        with pytest.raises(CollectionError, match="missing required fields"):
            collector._parse_module(data)

    def test_parse_module_missing_entry_fields(self, tmp_path):
        """Test error when entry is missing required fields."""
        collector = NimCollector(["src"], tmp_path)
        data = {
            "module": "test",
            "file": "test.nim",
            "entries": [{"name": "foo"}]  # Missing kind, line, signature
        }

        with pytest.raises(CollectionError, match="Entry 0 missing required fields"):
            collector._parse_module(data)

    def test_parse_module_with_all_fields(self, tmp_path):
        """Test parsing module with all optional fields."""
        collector = NimCollector(["src"], tmp_path)
        data = {
            "module": "test",
            "file": str(tmp_path / "test.nim"),
            "doc": "Module doc",
            "entries": [{
                "name": "foo",
                "kind": "proc",
                "line": 10,
                "signature": "proc foo()",
                "doc": "Proc doc",
                "params": [{"name": "x", "type": "int"}],
                "returns": "string",
                "pragmas": ["inline"],
                "raises": ["ValueError"],
                "exported": True,
            }]
        }

        module = collector._parse_module(data)

        assert module.module == "test"
        assert module.doc == "Module doc"
        assert len(module.entries) == 1
        assert module.entries[0].name == "foo"
        assert module.entries[0].params[0].name == "x"
        assert module.entries[0].returns == "string"
        assert module.entries[0].pragmas == ["inline"]
        assert module.entries[0].raises == ["ValueError"]
        assert module.entries[0].exported is True
