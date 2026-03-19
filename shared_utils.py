"""Shared utilities for the pqt_generator toolkit."""

from pathlib import Path
from typing import Dict, Optional

# Constants
PQT_VERSION = "1.0.0.0"

CONTENT_TYPES_XML = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="pq" ContentType="application/x-ms-m" />
</Types>'''


def parse_ws_filename(filename: str) -> Optional[Dict[str, str]]:
    """
    Parse a Fabric workspace export filename into metadata components.

    Expected format: WS__<workspace-id>__<item-id>__<name>__<type>.json
    Handles display names containing '__' by treating the last segment as the type.

    Args:
        filename: Name of the file to parse

    Returns:
        Dictionary with workspace_id, item_id, name, type keys, or None if parsing fails
    """
    stem = Path(filename).stem
    parts = stem.split('__')

    if len(parts) >= 5 and parts[0] == 'WS':
        return {
            'workspace_id': parts[1],
            'item_id': parts[2],
            'name': '__'.join(parts[3:-1]),
            'type': parts[-1]
        }
    return None


def parse_mapping_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse a line from item_mapping.txt, supporting both pipe and arrow formats.

    Pipe format: item_001 | WorkspaceID: xxx | ItemID: xxx | Name: xxx | Type: xxx | File: xxx
    Arrow format: item_001 -> filename.json

    Returns:
        Dictionary with item_id and available metadata, or None if parsing fails
    """
    line = line.strip()
    if not line:
        return None

    if ' | ' in line:
        segments = line.split(' | ')
        result = {'item_id': segments[0].strip()}
        for seg in segments[1:]:
            if ': ' in seg:
                key, value = seg.split(': ', 1)
                result[key.strip()] = value.strip()
        return result
    elif ' -> ' in line:
        parts = line.split(' -> ', 1)
        if len(parts) == 2:
            return {
                'item_id': parts[0].strip(),
                'File': parts[1].strip()
            }
    return None


def format_mapping_line(item_id: str, metadata: Optional[Dict[str, str]], filename: str) -> str:
    """
    Format a mapping line for item_mapping.txt in pipe-delimited format.

    Args:
        item_id: Directory name (e.g., 'item_001')
        metadata: Parsed metadata dict or None
        filename: Original filename

    Returns:
        Formatted mapping line string
    """
    if metadata:
        return (f"{item_id} | WorkspaceID: {metadata['workspace_id']} | "
                f"ItemID: {metadata['item_id']} | Name: {metadata['name']} | "
                f"Type: {metadata['type']} | File: {filename}\n")
    else:
        return f"{item_id} -> {filename}\n"
