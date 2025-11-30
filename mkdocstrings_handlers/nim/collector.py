"""Collector for Nim documentation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from importlib.resources import files, as_file
from pathlib import Path
from typing import Any

from mkdocstrings import CollectionError

# Cache directory for compiled nimdocinfo binary
_CACHE_DIR = Path(tempfile.gettempdir()) / "mkdocstrings-nim-cache"


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
        # Use importlib.resources for reliable path resolution
        extractor_files = files("mkdocstrings_handlers.nim").joinpath("extractor")
        self._nimdocinfo_source = extractor_files.joinpath("nimdocinfo.nim")

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

    def _ensure_nimdocinfo_compiled(self) -> Path:
        """Ensure nimdocinfo is compiled and return path to binary.

        Copies Nim source files to a cache directory and compiles them there.
        This avoids writing to the installed package directory.

        Returns:
            Path to the compiled nimdocinfo binary.

        Raises:
            CollectionError: If compilation fails.
        """
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Get the extractor package files
        extractor_pkg = files("mkdocstrings_handlers.nim").joinpath("extractor")

        # Copy source files to cache if needed
        with as_file(extractor_pkg.joinpath("nimdocinfo.nim")) as src_main:
            with as_file(extractor_pkg.joinpath("extractor.nim")) as src_extractor:
                cache_main = _CACHE_DIR / "nimdocinfo.nim"
                cache_extractor = _CACHE_DIR / "extractor.nim"
                cache_binary = _CACHE_DIR / "nimdocinfo"

                # Check if we need to recompile (source newer than binary)
                needs_compile = not cache_binary.exists()
                if not needs_compile:
                    binary_mtime = cache_binary.stat().st_mtime
                    if src_main.stat().st_mtime > binary_mtime:
                        needs_compile = True
                    elif src_extractor.stat().st_mtime > binary_mtime:
                        needs_compile = True

                if needs_compile:
                    # Copy source files
                    shutil.copy2(src_main, cache_main)
                    shutil.copy2(src_extractor, cache_extractor)

                    # Compile (first run is slow, ~15s; subsequent runs use cache)
                    result = subprocess.run(
                        ["nim", "c", "--outdir:" + str(_CACHE_DIR), str(cache_main)],
                        capture_output=True,
                        text=True,
                        timeout=120,  # First compile can be slow
                    )

                    if result.returncode != 0:
                        raise CollectionError(
                            f"Failed to compile nimdocinfo:\n{result.stderr}"
                        )

                return cache_binary

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
            binary_path = self._ensure_nimdocinfo_compiled()

            result = subprocess.run(
                [str(binary_path), str(filepath)],
                capture_output=True,
                text=True,
                cwd=str(self.base_dir),
                timeout=60,
            )

            if result.returncode != 0:
                raise CollectionError(
                    f"nimdocinfo failed:\n{result.stderr}\n\n"
                    f"To debug, run manually:\n"
                    f"  {binary_path} {filepath}"
                )

            # Parse JSON from stdout
            lines = result.stdout.strip().split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("{"):
                    in_json = True
                if in_json:
                    json_lines.append(line)
                if in_json and line.strip().startswith("}") and len(json_lines) > 1:
                    try:
                        return json.loads("\n".join(json_lines))
                    except json.JSONDecodeError:
                        continue

            if not json_lines:
                raise CollectionError(f"No JSON output from nimdocinfo: {result.stdout}")

            return json.loads("\n".join(json_lines))

        except FileNotFoundError:
            raise CollectionError(
                "Nim compiler not found. Install from https://nim-lang.org/install.html\n"
                "Then verify installation: nim --version"
            )
        except subprocess.TimeoutExpired:
            raise CollectionError(
                f"nimdocinfo timed out processing {filepath}. "
                "The file may be too complex or have circular imports."
            )
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
                raises=entry_data.get("raises", []),
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
