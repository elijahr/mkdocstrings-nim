"""Collector for Nim documentation."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mkdocstrings import CollectionError


@dataclass
class NimParam:
    """A Nim parameter."""
    name: str
    type: str
    description: str = ""


@dataclass
class NimEntry:
    """A documented Nim entry (proc, type, const, etc.)."""
    name: str
    kind: str
    line: int
    signature: str
    doc: str = ""
    params: list[NimParam] = field(default_factory=list)
    returns: str = ""
    returns_doc: str = ""
    pragmas: list[str] = field(default_factory=list)
    raises: list[str] = field(default_factory=list)


@dataclass
class NimModule:
    """A documented Nim module."""
    module: str
    file: str
    doc: str = ""
    entries: list[NimEntry] = field(default_factory=list)


class NimCollector:
    """Collects documentation from Nim source files."""

    def __init__(self, paths: list[str], base_dir: Path):
        """Initialize the collector.

        Args:
            paths: Search paths for Nim source files.
            base_dir: Base directory of the project.
        """
        self.paths = paths
        self.base_dir = base_dir
        self._cache: dict[str, NimModule] = {}
        self._nimdocinfo_path = Path(__file__).parent.parent.parent / "src" / "nimdocinfo" / "nimdocinfo.nim"

    def _resolve_identifier(self, identifier: str) -> Path:
        """Resolve a module identifier to a file path.

        Args:
            identifier: Module identifier like 'lockfreequeues.ops'

        Returns:
            Path to the Nim source file.

        Raises:
            CollectionError: If the file cannot be found.
        """
        # Convert dots to path separators
        rel_path = identifier.replace(".", "/") + ".nim"

        for search_path in self.paths:
            full_path = self.base_dir / search_path / rel_path
            if full_path.exists():
                return full_path

        # Try without nested path (just filename)
        filename = identifier.split(".")[-1] + ".nim"
        for search_path in self.paths:
            full_path = self.base_dir / search_path / filename
            if full_path.exists():
                return full_path

        raise CollectionError(f"Could not find Nim file for identifier: {identifier}")

    def _run_nimdocinfo(self, filepath: Path) -> dict[str, Any]:
        """Run nimdocinfo on a Nim file.

        Args:
            filepath: Path to the Nim source file.

        Returns:
            Parsed JSON output from nimdocinfo.

        Raises:
            CollectionError: If nimdocinfo fails.
        """
        try:
            result = subprocess.run(
                ["nim", "c", "-r", str(self._nimdocinfo_path), str(filepath)],
                capture_output=True,
                text=True,
                cwd=str(self.base_dir),
            )

            if result.returncode != 0:
                raise CollectionError(f"nimdocinfo failed: {result.stderr}")

            # Parse JSON from stdout (skip compiler hints)
            lines = result.stdout.strip().split("\n")
            # Find the JSON output - it starts with { and ends with }
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("{"):
                    in_json = True
                if in_json:
                    json_lines.append(line)
                if in_json and line.strip().startswith("}") and len(json_lines) > 1:
                    # Check if this closes the main object
                    try:
                        return json.loads("\n".join(json_lines))
                    except json.JSONDecodeError:
                        continue

            if not json_lines:
                raise CollectionError(f"No JSON output from nimdocinfo: {result.stdout}")

            return json.loads("\n".join(json_lines))

        except FileNotFoundError:
            raise CollectionError("Nim compiler not found. Is Nim installed?")
        except json.JSONDecodeError as e:
            raise CollectionError(f"Invalid JSON from nimdocinfo: {e}")

    def _parse_module(self, data: dict[str, Any]) -> NimModule:
        """Parse JSON data into NimModule.

        Args:
            data: JSON data from nimdocinfo.

        Returns:
            Parsed NimModule.
        """
        entries = []
        for entry_data in data.get("entries", []):
            params = [
                NimParam(name=p["name"], type=p["type"])
                for p in entry_data.get("params", [])
            ]

            entries.append(NimEntry(
                name=entry_data["name"],
                kind=entry_data["kind"],
                line=entry_data["line"],
                signature=entry_data["signature"],
                doc=entry_data.get("doc", ""),
                params=params,
                returns=entry_data.get("returns", ""),
                pragmas=entry_data.get("pragmas", []),
            ))

        return NimModule(
            module=data["module"],
            file=data["file"],
            doc=data.get("doc", ""),
            entries=entries,
        )

    def collect(self, identifier: str) -> NimModule:
        """Collect documentation for a module identifier.

        Args:
            identifier: Module identifier like 'lockfreequeues.ops'

        Returns:
            NimModule with documentation.
        """
        if identifier in self._cache:
            return self._cache[identifier]

        filepath = self._resolve_identifier(identifier)
        data = self._run_nimdocinfo(filepath)
        module = self._parse_module(data)

        self._cache[identifier] = module
        return module
