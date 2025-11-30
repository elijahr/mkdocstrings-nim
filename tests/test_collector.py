"""Tests for collector path resolution."""
import pytest
from pathlib import Path
from importlib.resources import as_file
from mkdocstrings_handlers.nim.collector import NimCollector


def test_nimdocinfo_path_exists():
    """Test that nimdocinfo source path resolves correctly."""
    collector = NimCollector(paths=["src"], base_dir=Path.cwd())
    # Use as_file to get actual path for checking
    with as_file(collector._nimdocinfo_source) as path:
        assert path.exists(), f"Path not found: {path}"
        assert path.name == "nimdocinfo.nim"
