"""
Create Power Query Template (.pqt) files from decoded Fabric Dataflow workspace exports.

This script automates the process of:
1. Identifying dataflow items (those with mashup.pq files)
2. Creating pqtzip directory structures with required template files
3. Generating .pqt archive files
4. Creating item_mapping.txt for traceability

Usage:
    python create_pqt_from_workspace.py <source_workspace_path> [--output <output_directory>]

Example:
    python create_pqt_from_workspace.py "PIE_WORKSPACES_decoded"
    python create_pqt_from_workspace.py "PIE_WORKSPACES_decoded" --output "parse_out/with_pq/output"
"""

import argparse
import json
import logging
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Dict, List

from shared_utils import (
    CONTENT_TYPES_XML,
    PQT_VERSION,
    parse_mapping_line,
    parse_ws_filename,
)

logger = logging.getLogger(__name__)


def find_dataflow_items(workspace_path: Path) -> List[Path]:
    """
    Find all item directories that contain mashup.pq files (dataflows).

    Args:
        workspace_path: Path to the decoded workspace directory

    Returns:
        List of Path objects for directories containing mashup.pq
    """
    dataflow_items = []

    if not workspace_path.exists():
        logger.error(f"Error: Workspace path does not exist: {workspace_path}")
        return dataflow_items

    for item_dir in sorted(workspace_path.iterdir()):
        if item_dir.is_dir() and item_dir.name.startswith("item_"):
            mashup_file = item_dir / "mashup.pq"
            if mashup_file.exists():
                dataflow_items.append(item_dir)

    logger.info(f"Found {len(dataflow_items)} dataflow items in {workspace_path}")
    return dataflow_items


def read_item_mapping(workspace_path: Path) -> Dict[str, str]:
    """
    Read the original item_mapping.txt file to get item-to-workspace mappings.
    Supports both pipe-delimited and arrow formats.

    Args:
        workspace_path: Path to the workspace directory containing item_mapping.txt

    Returns:
        Dictionary mapping item directory names to workspace filenames
    """
    mapping_file = workspace_path / "item_mapping.txt"
    mappings: Dict[str, str] = {}

    if not mapping_file.exists():
        logger.warning(f"Warning: item_mapping.txt not found at {mapping_file}")
        return mappings

    with open(mapping_file, 'r', encoding='utf-8') as f:
        for line in f:
            parsed = parse_mapping_line(line)
            if parsed and 'File' in parsed:
                mappings[parsed['item_id']] = parsed['File']

    return mappings


def create_mashup_metadata(query_metadata_path: Path) -> Dict:
    """
    Transform queryMetadata.json to MashupMetadata.json format.

    Args:
        query_metadata_path: Path to queryMetadata.json file

    Returns:
        Dictionary in MashupMetadata.json format
    """
    with open(query_metadata_path, 'r', encoding='utf-8') as f:
        query_metadata = json.load(f)

    # Transform nested queriesMetadata object to QueriesMetadata array
    queries_metadata = []
    if "queriesMetadata" in query_metadata:
        for query_name, query_info in query_metadata["queriesMetadata"].items():
            query_entry = {"Name": query_name}
            if "isHidden" in query_info:
                query_entry["IsHidden"] = query_info["isHidden"]
            queries_metadata.append(query_entry)

    mashup_metadata = {
        "Version": PQT_VERSION,
        "QueriesMetadata": queries_metadata
    }

    return mashup_metadata


def create_metadata(platform_path: Path) -> Dict:
    """
    Create Metadata.json from .platform file.

    Args:
        platform_path: Path to the .platform file

    Returns:
        Dictionary in Metadata.json format
    """
    with open(platform_path, 'r', encoding='utf-8') as f:
        platform_data = json.load(f)

    display_name = platform_data.get("config", {}).get("displayName", "Dataflow")

    metadata = {
        "Name": display_name,
        "Description": "",
        "Version": PQT_VERSION
    }

    return metadata


def create_pqtzip_structure(item_dir: Path) -> bool:
    """
    Create pqtzip directory with all required template files.

    Args:
        item_dir: Path to the item directory

    Returns:
        True if structure was created successfully, False otherwise
    """
    pqtzip_dir = item_dir / "pqtzip"
    pqtzip_dir.mkdir(exist_ok=True)

    try:
        # 1. Copy mashup.pq to MashupDocument.pq
        mashup_src = item_dir / "mashup.pq"
        mashup_dest = pqtzip_dir / "MashupDocument.pq"
        shutil.copy2(mashup_src, mashup_dest)

        # 2. Create MashupMetadata.json from queryMetadata.json
        query_metadata_path = item_dir / "queryMetadata.json"
        if query_metadata_path.exists():
            mashup_metadata = create_mashup_metadata(query_metadata_path)
        else:
            logger.warning(f"  ⚠️ {item_dir.name}: queryMetadata.json not found, using empty metadata")
            mashup_metadata = {"Version": PQT_VERSION, "QueriesMetadata": []}
        with open(pqtzip_dir / "MashupMetadata.json", 'w', encoding='utf-8') as f:
            json.dump(mashup_metadata, f, indent=2)

        # 3. Create Metadata.json from .platform
        platform_path = item_dir / ".platform"
        if platform_path.exists():
            metadata = create_metadata(platform_path)
        else:
            logger.warning(f"  ⚠️ {item_dir.name}: .platform not found, using directory name as display name")
            metadata = {"Name": item_dir.name, "Description": "", "Version": PQT_VERSION}
        with open(pqtzip_dir / "Metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        # 4. Create [Content_Types].xml
        with open(pqtzip_dir / "[Content_Types].xml", 'w', encoding='utf-8') as f:
            f.write(CONTENT_TYPES_XML)

        return True

    except Exception as e:
        logger.error(f"Error creating pqtzip for {item_dir.name}: {e}")
        return False


def create_pqt_archive(item_dir: Path) -> bool:
    """
    Create .pqt archive file from pqtzip directory.

    Args:
        item_dir: Path to the item directory containing a pqtzip subdirectory

    Returns:
        True if archive was created successfully, False otherwise
    """
    pqtzip_dir = item_dir / "pqtzip"
    pqt_file = item_dir / f"{item_dir.name}.pqt"

    if not pqtzip_dir.exists():
        logger.error(f"Error: pqtzip directory does not exist for {item_dir.name}")
        return False

    try:
        with zipfile.ZipFile(pqt_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in pqtzip_dir.iterdir():
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)

        return True

    except Exception as e:
        logger.error(f"Error creating .pqt archive for {item_dir.name}: {e}")
        return False


def create_output_mapping(dataflow_items: List[Path], original_mappings: Dict[str, str], output_path: Path) -> bool:
    """
    Create item_mapping.txt in the output directory with workspace IDs and metadata.

    Args:
        dataflow_items: List of item directory Paths
        original_mappings: Dictionary of item_id -> workspace filename
        output_path: Directory to write item_mapping.txt

    Returns:
        True if mapping file was created successfully, False otherwise
    """
    mapping_file = output_path / "item_mapping.txt"

    try:
        with open(mapping_file, 'w', encoding='utf-8') as f:
            for item_dir in sorted(dataflow_items, key=lambda x: x.name):
                item_id = item_dir.name

                # Find the WS__*.json file to extract workspace information
                ws_files = list(item_dir.glob("WS__*.json"))

                if ws_files:
                    ws_filename = ws_files[0].name
                    metadata = parse_ws_filename(ws_filename)

                    if metadata:
                        f.write(f"{item_id} | WorkspaceID: {metadata['workspace_id']} | "
                                f"ItemID: {metadata['item_id']} | Name: {metadata['name']} | "
                                f"Type: {metadata['type']} | File: {ws_filename}\n")
                    else:
                        # Fallback to original format if parsing fails
                        workspace_file = original_mappings.get(item_id, "Unknown")
                        f.write(f"{item_id} -> {workspace_file}\n")
                else:
                    # Fallback to original format if no WS__ file found
                    workspace_file = original_mappings.get(item_id, "Unknown")
                    f.write(f"{item_id} -> {workspace_file}\n")

        logger.info(f"\nCreated item_mapping.txt with {len(dataflow_items)} entries at {mapping_file}")
        return True

    except Exception as e:
        logger.error(f"Error creating item_mapping.txt: {e}")
        return False


def copy_dataflow_items(dataflow_items: List[Path], output_path: Path) -> List[Path]:
    """
    Copy dataflow item directories to output location.

    Args:
        dataflow_items: List of item directory Paths to copy
        output_path: Destination directory

    Returns:
        List of Paths to the copied (or in-place) item directories
    """
    if not dataflow_items:
        return []

    # If output path is the same as source, don't copy - work in place
    if output_path == dataflow_items[0].parent:
        logger.info("Working in place (source directory)")
        return dataflow_items

    # Otherwise, copy to the new location
    output_path.mkdir(parents=True, exist_ok=True)
    copied_items = []

    for item_dir in dataflow_items:
        dest_dir = output_path / item_dir.name

        # Copy the entire item directory if it doesn't exist
        if not dest_dir.exists():
            shutil.copytree(item_dir, dest_dir)
            copied_items.append(dest_dir)
        else:
            copied_items.append(dest_dir)

    return copied_items


def process_workspace(source_workspace: str, output_directory: str = None) -> bool:
    """
    Main processing function to convert workspace dataflows to .pqt files.

    Args:
        source_workspace: Path to the decoded workspace directory
        output_directory: Optional output directory. If not provided, works in-place in the source directory

    Returns:
        True if successful, False otherwise
    """
    workspace_path = Path(source_workspace).resolve()

    if not workspace_path.exists():
        logger.error(f"Error: Workspace path does not exist: {workspace_path}")
        return False

    # Determine output directory
    if output_directory:
        output_path = Path(output_directory).resolve()
    else:
        # Default: use the same source workspace directory
        output_path = workspace_path

    logger.info(f"\n{'=' * 70}")
    logger.info(f"Processing workspace: {workspace_path}")
    logger.info(f"Output directory: {output_path}")
    logger.info(f"{'=' * 70}\n")

    # Step 1: Find dataflow items
    dataflow_items = find_dataflow_items(workspace_path)
    if not dataflow_items:
        logger.info("No dataflow items found. Exiting.")
        return False

    # Step 2: Read original item mappings
    original_mappings = read_item_mapping(workspace_path)

    # Step 3: Copy dataflow items to output directory
    if output_path != workspace_path:
        logger.info(f"\nCopying {len(dataflow_items)} dataflow items to {output_path}...")
    copied_items = copy_dataflow_items(dataflow_items, output_path)

    # Step 4: Create pqtzip structures and Step 5: Create .pqt archive files
    # Wrapped in try/finally to ensure temporary pqtzip directories are always cleaned up
    try:
        logger.info("\nCreating pqtzip structures...")
        success_count = 0
        for item_dir in copied_items:
            if create_pqtzip_structure(item_dir):
                success_count += 1
                logger.info(f"  ✓ {item_dir.name}")
            else:
                logger.error(f"  ✗ {item_dir.name} - Failed")

        logger.info(f"\nSuccessfully created {success_count}/{len(copied_items)} pqtzip structures")

        logger.info("\nCreating .pqt archive files...")
        pqt_success_count = 0
        for item_dir in copied_items:
            if create_pqt_archive(item_dir):
                pqt_success_count += 1
                logger.info(f"  ✓ {item_dir.name}.pqt")
            else:
                logger.error(f"  ✗ {item_dir.name}.pqt - Failed")

        logger.info(f"\nSuccessfully created {pqt_success_count}/{len(copied_items)} .pqt files")
    finally:
        # Clean up temporary pqtzip directories if they still exist
        for item_dir in copied_items:
            pqtzip_path = item_dir / "pqtzip"
            if pqtzip_path.exists():
                shutil.rmtree(pqtzip_path, ignore_errors=True)

    # Step 6: Move items with .pqt files to with_dataflows directory
    with_dataflows_path = output_path / "with_dataflows"
    with_dataflows_path.mkdir(exist_ok=True)

    moved_items = []
    failed_moves = []
    logger.info("\nMoving items with .pqt files to with_dataflows...")

    for item_dir in copied_items:
        pqt_file = item_dir / f"{item_dir.name}.pqt"
        if pqt_file.exists():
            dest_dir = with_dataflows_path / item_dir.name

            # Try to move with retry logic for Windows file locking issues
            max_retries = 3
            retry_delay = 0.5

            for attempt in range(max_retries):
                try:
                    # Remove destination if it exists
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)

                    # Move the entire directory
                    shutil.move(str(item_dir), str(dest_dir))
                    moved_items.append(dest_dir)
                    logger.info(f"  ✓ Moved {item_dir.name} to with_dataflows/")
                    break

                except PermissionError as e:
                    if attempt < max_retries - 1:
                        # Wait and retry
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Final attempt failed, log and continue
                        logger.error(f"  ✗ Failed to move {item_dir.name}: {e}")
                        failed_moves.append(item_dir.name)
                        break
                except Exception as e:
                    logger.error(f"  ✗ Error moving {item_dir.name}: {e}")
                    failed_moves.append(item_dir.name)
                    break

    logger.info(f"\nSuccessfully moved {len(moved_items)}/{pqt_success_count} items to with_dataflows/")
    if failed_moves:
        logger.error(f"Failed to move {len(failed_moves)} items: {', '.join(failed_moves)}")
        logger.info("These items remain in the main output directory.")

    # Step 7: Create item_mapping.txt in with_dataflows directory
    if moved_items:
        create_output_mapping(moved_items, original_mappings, with_dataflows_path)

    # Step 8: Create item_mapping.txt in main output directory for remaining items
    remaining_items = [item for item in copied_items if (output_path / item.name).exists()]
    if remaining_items:
        logger.info(f"\nCreating item_mapping.txt for {len(remaining_items)} items in main directory...")
        create_output_mapping(remaining_items, original_mappings, output_path)

    # Final summary
    logger.info(f"\n{'=' * 70}")
    logger.info("PROCESSING COMPLETE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Total items processed: {len(copied_items)}")
    logger.info(f"Items with dataflows (.pq files): {len(dataflow_items)}")
    logger.info(f"  - pqtzip structures created: {success_count}")
    logger.info(f"  - .pqt archives created: {pqt_success_count}")
    logger.info(f"  - Moved to with_dataflows/: {len(moved_items)}")
    logger.info(f"Items remaining in source directory: {len(remaining_items)}")
    logger.info(f"\nOutput location: {output_path}")
    if moved_items:
        logger.info(f"Dataflows location: {with_dataflows_path}")
    logger.info(f"{'=' * 70}\n")

    return success_count > 0 and pqt_success_count > 0


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Create Power Query Template (.pqt) files from decoded Fabric Dataflow workspace exports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "PIE_WORKSPACES_decoded"
  %(prog)s "PIE_WORKSPACES_decoded" --output "parse_out/with_pq/output"
        """
    )
    parser.add_argument(
        'source_workspace',
        type=str,
        help='Path to the decoded workspace directory'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        dest='output_directory',
        help='Output directory for .pqt files (default: works in-place)'
    )

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    success = process_workspace(args.source_workspace, args.output_directory)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
