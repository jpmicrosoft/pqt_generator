"""
Batch Decode Dataflow Definitions
Decodes all dataflow definition files in a directory,
creating a subdirectory for each file with decoded parts

Usage:
    python batch_decode_dataflows.py <source_directory>

Example:
    python batch_decode_dataflows.py "C:\\path\\to\\dataflows"
    python batch_decode_dataflows.py "PIE_WORKSPACES"
"""

import argparse
import base64
import json
import logging
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import List

from shared_utils import parse_ws_filename, format_mapping_line

logger = logging.getLogger(__name__)

# Maximum payload size to decode (100MB)
MAX_PAYLOAD_SIZE = 100 * 1024 * 1024

# Maximum input file size (500MB)
MAX_INPUT_FILE_SIZE = 500 * 1024 * 1024

# Maximum number of parts in a definition
MAX_PARTS = 10_000


def decode_dataflow_definition(input_file: Path, output_dir: Path) -> bool:
    """
    Decode base64-encoded dataflow definition.

    Args:
        input_file: Path to the encoded JSON file
        output_dir: Directory to save decoded files

    Returns:
        True if decoding succeeded, False otherwise
    """
    # Check input file size
    input_size = input_file.stat().st_size
    if input_size > MAX_INPUT_FILE_SIZE:
        logger.warning(f"   ⚠️ Skipping {input_file.name}: file size ({input_size:,} bytes) exceeds {MAX_INPUT_FILE_SIZE:,} byte limit")
        return False

    # Read the encoded file
    with open(input_file, 'r', encoding='utf-8') as f:
        definition = json.load(f)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    decoded_parts: List[dict] = []
    resolved_output_dir = output_dir.resolve()

    # Decode each part
    parts = definition.get('definition', {}).get('parts', [])
    if len(parts) > MAX_PARTS:
        logger.warning(f"   ⚠️ Skipping {input_file.name}: {len(parts):,} parts exceeds {MAX_PARTS:,} limit")
        return False

    for part in parts:
        path = part.get('path')
        payload = part.get('payload')
        payload_type = part.get('payloadType')

        logger.debug(f"Processing part: {path}")

        # Guard against None/empty path values
        if not path:
            logger.warning("   ⚠️ Skipping part with missing or empty path")
            decoded_parts.append(part)
            continue

        # Sanitize path: strip directory components to prevent path traversal
        path = Path(path).name

        # Block Unicode control characters (RTL override, etc.)
        if any(unicodedata.category(c).startswith('C') for c in path):
            logger.warning(f"   ⚠️ Skipping part with suspicious Unicode characters in path: {repr(path)}")
            continue

        if payload_type == 'InlineBase64' and payload:
            # Check payload size before decoding
            if len(payload) > MAX_PAYLOAD_SIZE:
                logger.warning(f"   ⚠️ Skipping {path}: payload exceeds {MAX_PAYLOAD_SIZE // (1024 * 1024)}MB limit")
                decoded_parts.append(part)
                continue

            try:
                # Decode base64
                decoded_bytes = base64.b64decode(payload)
                decoded_text = decoded_bytes.decode('utf-8')

                # Build and validate output path
                output_file = output_dir / path
                if not output_file.resolve().as_posix().startswith(resolved_output_dir.as_posix()):
                    logger.warning(f"   ⚠️ Skipping {path}: resolved path escapes output directory")
                    decoded_parts.append(part)
                    continue

                # Create parent dirs for nested paths (defense-in-depth)
                if output_file.parent != output_dir:
                    output_file.parent.mkdir(parents=True, exist_ok=True)

                # Parse JSON if it's a .json file
                if path.endswith('.json'):
                    decoded_payload = json.loads(decoded_text)
                    new_payload_type = 'DecodedJSON'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(decoded_payload, f, indent=2, ensure_ascii=False)
                else:
                    # Keep as text (M code, etc.)
                    decoded_payload = decoded_text
                    new_payload_type = 'DecodedText'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(decoded_text)

                decoded_parts.append({
                    'path': path,
                    'payload': decoded_payload,
                    'payloadType': new_payload_type
                })

            except (ValueError, json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
                logger.error(f"   ❌ Error decoding {path}: {e}")
                decoded_parts.append(part)
        else:
            decoded_parts.append(part)

    # Save complete decoded definition
    decoded_definition = {
        'definition': {
            'parts': decoded_parts
        }
    }

    definition_file = output_dir / "definition_decoded.json"
    with open(definition_file, 'w', encoding='utf-8') as f:
        json.dump(decoded_definition, f, indent=2, ensure_ascii=False)

    # Copy original file into the output directory
    moved_file = output_dir / input_file.name
    shutil.copy2(input_file, moved_file)

    # Verify backup exists before we return (caller deletes original)
    if not moved_file.exists():
        logger.warning(f"   ⚠️ Backup copy not found at {moved_file}")
        return False

    return True


def batch_decode_directory(source_dir: str) -> bool:
    """
    Process all JSON files in a directory.
    For each file, create a subdirectory and decode into it.

    Args:
        source_dir: Directory containing encoded JSON files

    Returns:
        True if at least one file was successfully decoded, False otherwise
    """
    source_path = Path(source_dir)

    if not source_path.exists():
        logger.error(f"❌ Directory not found: {source_dir}")
        return False

    # Get all JSON files (sorted for deterministic numbering)
    json_files = sorted(source_path.glob("*.json"))

    logger.info(f"\n{'=' * 70}")
    logger.info("BATCH DECODING DATAFLOW DEFINITIONS")
    logger.info(f"{'=' * 70}")
    logger.info(f"Source Directory: {source_dir}")
    logger.info(f"Found {len(json_files)} JSON files\n")

    if not json_files:
        logger.error("❌ No JSON files found in the directory")
        return False

    success_count = 0
    error_count = 0
    mapping_lines: List[str] = []

    for idx, json_file in enumerate(json_files, 1):
        # Use short numbered directory names to avoid Windows MAX_PATH issues
        item_id = f"item_{idx:03d}"
        output_dir = source_path / item_id

        logger.info(f"[{idx}/{len(json_files)}] Processing: {json_file.name}")

        try:
            # Decode the file
            success = decode_dataflow_definition(json_file, output_dir)

            if not success:
                raise RuntimeError("decode_dataflow_definition returned failure")

            # Build mapping line using shared utility
            metadata = parse_ws_filename(json_file.name)
            mapping_lines.append(format_mapping_line(item_id, metadata, json_file.name))

            # Verify backup exists before deleting original
            moved_file = output_dir / json_file.name
            if moved_file.exists():
                json_file.unlink()
            else:
                logger.warning(f"   ⚠️ Backup not verified, keeping original: {json_file.name}")

            logger.info(f"   ✅ Decoded to: {output_dir}")
            logger.info("   ✅ Original file moved to subdirectory\n")
            success_count += 1

        except (ValueError, json.JSONDecodeError, UnicodeDecodeError, OSError, RuntimeError) as e:
            logger.error(f"   ❌ Error: {e}\n")
            error_count += 1

    # Write all mapping lines at once (not append mode)
    if mapping_lines:
        mapping_file = source_path / "item_mapping.txt"
        with open(mapping_file, 'w', encoding='utf-8') as f:
            f.writelines(mapping_lines)

    logger.info(f"\n{'=' * 70}")
    logger.info("BATCH DECODE COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"✅ Successful: {success_count}")
    logger.info(f"❌ Failed: {error_count}")
    logger.info("\n💡 See 'item_mapping.txt' for file-to-folder mapping")
    logger.info(f"{'=' * 70}\n")

    return success_count > 0


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Batch decode base64-encoded Fabric dataflow definition files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "C:\\path\\to\\dataflows"
  %(prog)s "PIE_WORKSPACES"
        """
    )
    parser.add_argument(
        'source_directory',
        type=str,
        help='Directory containing encoded JSON dataflow files'
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    success = batch_decode_directory(args.source_directory)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
