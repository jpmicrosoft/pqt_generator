"""
Process Fabric Dataflows - Complete Workflow Tool

This script provides a unified interface to decode Fabric dataflow exports
and convert them to Power Query Template (.pqt) files.

Usage:
    # Decode only
    python process_dataflows.py --decode <source_directory>

    # Convert only
    python process_dataflows.py --convert <source_directory>

    # Both decode and convert (complete workflow)
    python process_dataflows.py --all <source_directory>

    # Specify custom output directory for convert step
    python process_dataflows.py --all <source_directory> --output <output_directory>

Examples:
    # Complete workflow (decode + convert)
    python process_dataflows.py --all "PIE_WORKSPACES"

    # Decode exported JSON files only
    python process_dataflows.py --decode "PIE_WORKSPACES"

    # Convert already-decoded dataflows to .pqt files
    python process_dataflows.py --convert "PIE_WORKSPACES_decoded"

    # Complete workflow with custom output
    python process_dataflows.py --all "PIE_WORKSPACES" --output "output/templates"
"""

import sys
import argparse
import logging
from pathlib import Path

# Import functions from other scripts
from batch_decode_dataflows import batch_decode_directory
from create_pqt_from_workspace import process_workspace

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the unified dataflow processor."""
    parser = argparse.ArgumentParser(
        description='Process Fabric Dataflow exports - Decode and/or convert to .pqt files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all "PIE_WORKSPACES"
  %(prog)s --decode "PIE_WORKSPACES"
  %(prog)s --convert "PIE_WORKSPACES"
  %(prog)s --all "PIE_WORKSPACES" --output "custom_output"
        """
    )

    # Operation mode (mutually exclusive)
    operation_group = parser.add_mutually_exclusive_group(required=True)
    operation_group.add_argument(
        '--decode',
        action='store_true',
        help='Decode base64-encoded Fabric dataflow exports only'
    )
    operation_group.add_argument(
        '--convert',
        action='store_true',
        help='Convert decoded dataflows to .pqt files only'
    )
    operation_group.add_argument(
        '--all',
        action='store_true',
        help='Run complete workflow (decode + convert)'
    )

    # Required source directory
    parser.add_argument(
        'source_directory',
        type=str,
        help='Source directory containing Fabric exports or decoded dataflows'
    )

    # Optional output directory
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default=None,
        help='Output directory for .pqt files (default: works in-place)'
    )

    # Verbose flag
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose/debug output'
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(message)s'
    )

    # Validate source directory exists
    source_path = Path(args.source_directory)
    if not source_path.exists():
        logger.error(f"❌ Error: Source directory does not exist: {args.source_directory}")
        sys.exit(1)

    # Track overall success
    overall_success = True

    # Dynamic step numbering
    step_num = 1

    # Execute based on operation mode
    if args.decode or args.all:
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP {step_num}: DECODING DATAFLOW EXPORTS")
        logger.info("=" * 70)
        step_num += 1

        decode_success = batch_decode_directory(str(source_path))

        if not decode_success:
            logger.error("\n❌ Decode step failed")
            overall_success = False

            # If running --all and decode failed, don't proceed to convert
            if args.all:
                logger.error("❌ Stopping workflow due to decode failure")
                sys.exit(1)

    if args.convert or args.all:
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP {step_num}: CONVERTING TO .PQT FILES")
        logger.info("=" * 70)

        # Use the source directory for convert (it's now decoded)
        convert_source = str(source_path)
        convert_output = args.output if args.output else None

        convert_success = process_workspace(convert_source, convert_output)

        if not convert_success:
            logger.error("\n❌ Convert step failed")
            overall_success = False

    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("WORKFLOW SUMMARY")
    logger.info("=" * 70)

    if args.decode:
        logger.info("Operation: Decode only")
    elif args.convert:
        logger.info("Operation: Convert only")
    elif args.all:
        logger.info("Operation: Complete workflow (decode + convert)")

    logger.info(f"Source directory: {source_path}")
    if args.output:
        logger.info(f"Output directory: {args.output}")

    if overall_success:
        logger.info("\n✅ All operations completed successfully")
        sys.exit(0)
    else:
        logger.error("\n❌ Some operations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
