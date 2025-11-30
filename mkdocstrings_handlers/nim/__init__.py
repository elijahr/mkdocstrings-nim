"""Nim handler for mkdocstrings."""

from mkdocstrings_handlers.nim.handler import NimHandler, get_handler
from mkdocstrings_handlers.nim.collector import NimCollector, NimModule, NimEntry, NimParam
from mkdocstrings_handlers.nim.docstring import (
    parse_docstring,
    DocstringStyle,
    ParsedDocstring,
    ParamDoc,
    ReturnsDoc,
    RaisesDoc,
)

__all__ = [
    "NimHandler",
    "get_handler",
    "NimCollector",
    "NimModule",
    "NimEntry",
    "NimParam",
    "parse_docstring",
    "DocstringStyle",
    "ParsedDocstring",
    "ParamDoc",
    "ReturnsDoc",
    "RaisesDoc",
]
