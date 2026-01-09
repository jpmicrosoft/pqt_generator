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

import json
import base64
import os
import sys
from pathlib import Path


def decode_dataflow_definition(input_file, output_dir):
    """
    Decode base64-encoded dataflow definition.
    
    Args:
        input_file: Path to the encoded JSON file
        output_dir: Directory to save decoded files
    """
    # Read the encoded file
    with open(input_file, 'r', encoding='utf-8') as f:
        definition = json.load(f)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    decoded_parts = []
    
    # Decode each part
    for part in definition.get('definition', {}).get('parts', []):
        path = part.get('path')
        payload = part.get('payload')
        payload_type = part.get('payloadType')
        
        if payload_type == 'InlineBase64' and payload:
            try:
                # Decode base64
                decoded_bytes = base64.b64decode(payload)
                decoded_text = decoded_bytes.decode('utf-8')
                
                # Parse JSON if it's a .json file
                if path.endswith('.json'):
                    decoded_payload = json.loads(decoded_text)
                    new_payload_type = 'DecodedJSON'
                    
                    # Save as formatted JSON file
                    output_file = os.path.join(output_dir, path)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(decoded_payload, f, indent=2, ensure_ascii=False)
                    
                else:
                    # Keep as text (M code, etc.)
                    decoded_payload = decoded_text
                    new_payload_type = 'DecodedText'
                    
                    # Save as text file
                    output_file = os.path.join(output_dir, path)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(decoded_text)
                
                decoded_parts.append({
                    'path': path,
                    'payload': decoded_payload,
                    'payloadType': new_payload_type
                })
                
            except Exception as e:
                print(f"   ❌ Error decoding {path}: {e}")
                decoded_parts.append(part)
        else:
            decoded_parts.append(part)
    
    # Save complete decoded definition
    decoded_definition = {
        'definition': {
            'parts': decoded_parts
        }
    }
    
    output_file = os.path.join(output_dir, "definition_decoded.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(decoded_definition, f, indent=2, ensure_ascii=False)
    
    # Move original file to the directory
    import shutil
    moved_file = os.path.join(output_dir, os.path.basename(input_file))
    shutil.copy2(input_file, moved_file)
    
    return decoded_definition


def extract_metadata_from_filename(filename):
    """
    Extract metadata from filename.
    Expected format: WS__<workspace-id>__<item-id>__<name>__<type>.json
    
    Args:
        filename: Name of the file to extract metadata from
    
    Returns:
        Dictionary with workspace_id, item_id, name, type, or None if parsing fails
    """
    try:
        # Remove .json extension
        name_parts = filename.replace('.json', '')
        
        # Split by double underscore
        parts = name_parts.split('__')
        
        # Expected: WS, workspace-id, item-id, name, type
        if len(parts) >= 5 and parts[0] == 'WS':
            return {
                'workspace_id': parts[1],
                'item_id': parts[2],
                'name': parts[3],
                'type': parts[4]
            }
    except Exception:
        pass
    
    return None


def batch_decode_directory(source_dir):
    """
    Process all JSON files in a directory.
    For each file, create a subdirectory and decode into it.
    
    Args:
        source_dir: Directory containing encoded JSON files
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"❌ Directory not found: {source_dir}")
        return False
    
    # Get all JSON files
    json_files = list(source_path.glob("*.json"))
    
    print(f"\n{'='*70}")
    print(f"BATCH DECODING DATAFLOW DEFINITIONS")
    print(f"{'='*70}")
    print(f"Source Directory: {source_dir}")
    print(f"Found {len(json_files)} JSON files\n")
    
    if not json_files:
        print("❌ No JSON files found in the directory")
        return False
    
    success_count = 0
    error_count = 0
    
    for idx, json_file in enumerate(json_files, 1):
        # Use short numbered directory names to avoid Windows MAX_PATH issues
        # Format: item_001, item_002, etc.
        output_dir = source_path / f"item_{idx:03d}"
        
        # Create a mapping file to track which item corresponds to which file
        mapping_file = source_path / "item_mapping.txt"
        
        print(f"[{idx}/{len(json_files)}] Processing: {json_file.name}")
        
        try:
            # Decode the file
            decode_dataflow_definition(str(json_file), str(output_dir))
            
            # Extract metadata from filename
            metadata = extract_metadata_from_filename(json_file.name)
            
            # Create/append to mapping file with full metadata
            with open(mapping_file, 'a', encoding='utf-8') as f:
                if metadata:
                    f.write(f"item_{idx:03d} | WorkspaceID: {metadata['workspace_id']} | ItemID: {metadata['item_id']} | Name: {metadata['name']} | Type: {metadata['type']} | File: {json_file.name}\n")
                else:
                    f.write(f"item_{idx:03d} -> {json_file.name}\n")
            
            # Delete original file after successful decode
            json_file.unlink()
            
            print(f"   ✅ Decoded to: {output_dir}")
            print(f"   ✅ Original file moved to subdirectory\n")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            error_count += 1
    
    print(f"\n{'='*70}")
    print(f"BATCH DECODE COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {error_count}")
    print(f"\n💡 See 'item_mapping.txt' for file-to-folder mapping")
    print(f"{'='*70}\n")
    
    return success_count > 0


def main():
    """Command-line entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Missing required argument")
        print("Usage: python batch_decode_dataflows.py <source_directory>")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    success = batch_decode_directory(source_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
