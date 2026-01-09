"""
Process Fabric Dataflows - Complete Workflow Tool

This script provides a unified interface to decode Fabric dataflow exports
and convert them to Power Query Template (.pqt) files.

Usage:
    # Decode only
    python process_dataflows.py --decode <source_directory>
    
    # Convert only (assumes already decoded)
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
from pathlib import Path

# Import functions from other scripts
sys.path.insert(0, str(Path(__file__).parent))
from batch_decode_dataflows import batch_decode_directory
from create_pqt_from_workspace import process_workspace


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
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate source directory exists
    source_path = Path(args.source_directory)
    if not source_path.exists():
        print(f"❌ Error: Source directory does not exist: {args.source_directory}")
        sys.exit(1)
    
    # Track overall success
    overall_success = True
    
    # Execute based on operation mode
    if args.decode or args.all:
        print("\n" + "="*70)
        print("STEP 1: DECODING DATAFLOW EXPORTS")
        print("="*70)
        
        decode_success = batch_decode_directory(str(source_path))
        
        if not decode_success:
            print("\n❌ Decode step failed")
            overall_success = False
            
            # If running --all and decode failed, don't proceed to convert
            if args.all:
                print("❌ Stopping workflow due to decode failure")
                sys.exit(1)
    
    if args.convert or args.all:
        print("\n" + "="*70)
        print("STEP 2: CONVERTING TO .PQT FILES")
        print("="*70)
        
        # Use the source directory for convert (it's now decoded)
        convert_source = str(source_path)
        convert_output = args.output if args.output else None
        
        convert_success = process_workspace(convert_source, convert_output)
        
        if not convert_success:
            print("\n❌ Convert step failed")
            overall_success = False
    
    # Final summary
    print("\n" + "="*70)
    print("WORKFLOW SUMMARY")
    print("="*70)
    
    if args.decode:
        print("Operation: Decode only")
    elif args.convert:
        print("Operation: Convert only")
    elif args.all:
        print("Operation: Complete workflow (decode + convert)")
    
    print(f"Source directory: {source_path}")
    if args.output:
        print(f"Output directory: {args.output}")
    
    if overall_success:
        print("\n✅ All operations completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Some operations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
