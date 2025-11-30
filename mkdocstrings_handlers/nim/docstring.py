"""Docstring parsing for Nim documentation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DocstringStyle(Enum):
    """Supported docstring styles."""
    RST = "rst"
    GOOGLE = "google"
    NUMPY = "numpy"


@dataclass
class ParamDoc:
    """Parsed parameter documentation."""
    name: str
    description: str = ""
    type: str = ""


@dataclass
class ReturnsDoc:
    """Parsed return value documentation."""
    description: str = ""
    type: str = ""


@dataclass
class RaisesDoc:
    """Parsed raises documentation."""
    type: str
    description: str = ""


@dataclass
class ParsedDocstring:
    """Parsed docstring with structured sections."""
    description: str = ""
    params: list[ParamDoc] = field(default_factory=list)
    returns: Optional[ReturnsDoc] = None
    raises: list[RaisesDoc] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


def parse_rst_docstring(doc: str) -> ParsedDocstring:
    """Parse RST-style docstring.

    Args:
        doc: Raw docstring text.

    Returns:
        Parsed docstring structure.
    """
    result = ParsedDocstring()

    lines = doc.strip().split("\n")
    description_lines = []
    in_description = True

    # Patterns for RST directives
    param_pattern = re.compile(r":param\s+(\w+):\s*(.*)")
    returns_pattern = re.compile(r":returns?:\s*(.*)")
    raises_pattern = re.compile(r":raises?\s+(\w+):\s*(.*)")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for RST directives
        param_match = param_pattern.match(line)
        returns_match = returns_pattern.match(line)
        raises_match = raises_pattern.match(line)

        if param_match:
            in_description = False
            result.params.append(ParamDoc(
                name=param_match.group(1),
                description=param_match.group(2).strip(),
            ))
        elif returns_match:
            in_description = False
            result.returns = ReturnsDoc(description=returns_match.group(1).strip())
        elif raises_match:
            in_description = False
            result.raises.append(RaisesDoc(
                type=raises_match.group(1),
                description=raises_match.group(2).strip(),
            ))
        elif in_description:
            if line or description_lines:  # Skip leading blank lines
                description_lines.append(line)

        i += 1

    # Clean up description
    result.description = "\n".join(description_lines).strip()

    return result


def parse_google_docstring(doc: str) -> ParsedDocstring:
    """Parse Google-style docstring.

    Args:
        doc: Raw docstring text.

    Returns:
        Parsed docstring structure.
    """
    result = ParsedDocstring()

    lines = doc.strip().split("\n")
    current_section = "description"
    description_lines = []

    section_pattern = re.compile(r"^(Args|Arguments|Parameters|Returns|Raises|Examples):\s*$", re.IGNORECASE)
    param_pattern = re.compile(r"^\s+(\w+):\s*(.*)")

    i = 0
    while i < len(lines):
        line = lines[i]

        section_match = section_pattern.match(line.strip())
        if section_match:
            section_name = section_match.group(1).lower()
            if section_name in ("args", "arguments", "parameters"):
                current_section = "params"
            elif section_name == "returns":
                current_section = "returns"
            elif section_name == "raises":
                current_section = "raises"
            else:
                current_section = section_name
        elif current_section == "description":
            description_lines.append(line)
        elif current_section == "params":
            param_match = param_pattern.match(line)
            if param_match:
                result.params.append(ParamDoc(
                    name=param_match.group(1),
                    description=param_match.group(2).strip(),
                ))
        elif current_section == "returns":
            if line.strip():
                result.returns = ReturnsDoc(description=line.strip())
                current_section = ""
        elif current_section == "raises":
            param_match = param_pattern.match(line)
            if param_match:
                result.raises.append(RaisesDoc(
                    type=param_match.group(1),
                    description=param_match.group(2).strip(),
                ))

        i += 1

    result.description = "\n".join(description_lines).strip()
    return result


def parse_docstring(doc: str, style: DocstringStyle = DocstringStyle.RST) -> ParsedDocstring:
    """Parse a docstring according to the specified style.

    Args:
        doc: Raw docstring text.
        style: Docstring style to use for parsing.

    Returns:
        Parsed docstring structure.
    """
    if not doc:
        return ParsedDocstring()

    if style == DocstringStyle.RST:
        return parse_rst_docstring(doc)
    elif style == DocstringStyle.GOOGLE:
        return parse_google_docstring(doc)
    else:
        # Default to RST
        return parse_rst_docstring(doc)
