# Power Query Template (.pqt) Generator

This toolset automates the conversion of Microsoft Fabric Dataflow Gen2 exports into portable Power Query Template (.pqt) files.

## Overview

This repository contains scripts for processing Fabric Dataflow exports:

### Main Script (Recommended)

**`process_dataflows.py`** - Unified interface for complete workflow

### Individual Scripts

1. **`batch_decode_dataflows.py`** - Decodes base64-encoded Fabric dataflow exports
2. **`create_pqt_from_workspace.py`** - Converts decoded dataflows into .pqt template files

### Complete Workflow

```
Fabric Export (JSON) → process_dataflows.py --all → Decoded Files + .pqt Templates
```

Or run individually:
```
Fabric Export (JSON) → batch_decode_dataflows.py → Decoded Files → create_pqt_from_workspace.py → .pqt Templates
```

## Requirements

- **Python 3.6+** (minimum)
- **Python 3.8+** (recommended for best compatibility and performance)
- **Tested on:** Python 3.13
- No external dependencies (uses only standard library)

---

## Quick Start (Unified Script)

### Usage

```bash
# Complete workflow (decode + convert)
python process_dataflows.py --all <source_directory>

# Decode only
python process_dataflows.py --decode <source_directory>

# Convert only (already decoded)
python process_dataflows.py --convert <source_directory>

# With custom output directory
python process_dataflows.py --all <source_directory> --output <output_directory>
```

### Examples

```bash
# Run complete workflow on Fabric exports
python process_dataflows.py --all "PIE_WORKSPACES"

# Decode exports only
python process_dataflows.py --decode "PIE_WORKSPACES"

# Convert already-decoded dataflows to .pqt
python process_dataflows.py --convert "PIE_WORKSPACES"

# Complete workflow with custom output
python process_dataflows.py --all "PIE_WORKSPACES" --output "output/templates"
```

### Help

```bash
python process_dataflows.py --help
```

---

## Script 1: batch_decode_dataflows.py

### Purpose
Decodes base64-encoded Fabric Dataflow Gen2 export files into readable formats.

### Usage

```bash
python batch_decode_dataflows.py <source_directory>
```

**Examples:**
```bash
python batch_decode_dataflows.py "PIE_WORKSPACES"
python batch_decode_dataflows.py "C:\Fabric\Exports\Dataflows"
```

### What It Does

1. Scans the source directory for `.json` files (Fabric exports)
2. Creates numbered subdirectories (`item_001`, `item_002`, etc.) to avoid Windows MAX_PATH issues
3. Decodes base64 payloads from each export file
4. Extracts individual components:
   - `mashup.pq` - Power Query M code
   - `queryMetadata.json` - Query metadata
   - `.platform` - Fabric platform configuration
   - Other JSON/text files
5. Saves `definition_decoded.json` with all decoded content
6. Moves original file into the subdirectory
7. Creates `item_mapping.txt` to track which item corresponds to which original file

### Input Format

Fabric dataflow export files with this structure:
```json
{
  "definition": {
    "parts": [
      {
        "path": "mashup.pq",
        "payload": "base64_encoded_content...",
        "payloadType": "InlineBase64"
      },
      ...
    ]
  }
}
```

### Output Structure

```
source_directory/
├── item_001/
│   ├── mashup.pq                    # Decoded M code
│   ├── queryMetadata.json            # Decoded metadata
│   ├── .platform                     # Decoded config
│   ├── definition_decoded.json       # Complete decoded definition
│   └── WS__original_export.json      # Original file (moved here)
├── item_002/
│   └── ...
└── item_mapping.txt                  # Maps item_XXX to original filenames
```

### item_mapping.txt Format

Includes workspace ID, item ID, name, type, and original filename:

```
item_001 | WorkspaceID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee | ItemID: 11111111-2222-3333-4444-555555555555 | Name: DataflowName | Type: Dataflow | File: WS__aaaaaaaa-bbbb-cccc__11111111-2222-3333__DataflowName__Dataflow.json
item_002 | WorkspaceID: ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj | ItemID: 66666666-7777-8888-9999-aaaaaaaaaaaa | Name: FinanceRun | Type: Dataflow | File: WS__ffffffff-gggg-hhhh__66666666-7777-8888__FinanceRun__Dataflow.json
```

---

## Script 2: create_pqt_from_workspace.py

### Purpose
Converts decoded dataflow directories into Power Query Template (.pqt) files for import into Power BI or Excel.

### Usage

**Basic (works in-place, no copying):**
```bash
python create_pqt_from_workspace.py <source_workspace_path>
```

This creates `.pqt` files and `with_dataflows/` directory directly in the source directory.

**Custom output location:**
```bash
python create_pqt_from_workspace.py <source_workspace_path> <output_directory>
```

This copies items to a new location before processing.

**Examples:**
```bash
# Work in-place (default)
python create_pqt_from_workspace.py "PIE_WORKSPACES_decoded"

# Copy to custom output location
python create_pqt_from_workspace.py "PIE_WORKSPACES_decoded" "output/pie_templates"
```

### What It Does

1. Identifies dataflow items (directories containing `mashup.pq`)
2. Works in-place by default (or copies to output directory if specified)
3. Creates `pqtzip` directory with transformed files:
   - `MashupDocument.pq` (copy of `mashup.pq`)
   - `MashupMetadata.json` (transformed from `queryMetadata.json`)
   - `Metadata.json` (extracted from `.platform`)
   - `[Content_Types].xml` (generated XML manifest)
4. Creates `.pqt` ZIP archives
5. Moves items with `.pqt` files to `with_dataflows/` subdirectory
6. Generates `item_mapping.txt` files:
   - In `with_dataflows/` - for items with dataflows (have .pqt files)
   - In main directory - for items without dataflows (no .pq files)

## Output Structure (create_pqt_from_workspace.py)

By default, the script works in-place and organizes the source directory:

```
source_workspace/                     # Your original decoded workspace
├── with_dataflows/                   # Items with .pqt files (have mashup.pq)
│   ├── item_001/
│   │   ├── mashup.pq                 # Original M query file
│   │   ├── queryMetadata.json        # Original metadata
│   │   ├── .platform                 # Original platform config
│   │   ├── WS__10ee8e5c...json       # Original workspace file
│   │   ├── pqtzip/                   # Template structure
│   │   │   ├── MashupDocument.pq     # Copy of mashup.pq
│   │   │   ├── MashupMetadata.json   # Transformed metadata
│   │   │   ├── Metadata.json         # Name/version info
│   │   │   └── [Content_Types].xml   # MIME type declarations
│   │   └── item_001.pqt              # Final ZIP archive
│   ├── item_002/
│   │   └── ...
│   └── item_mapping.txt              # Mapping for items with dataflows
├── item_003/                         # Items without .pq files remain here
│   └── ...
└── item_mapping.txt                  # Mapping for items without dataflows (if any)
```

### item_mapping.txt Format

Both scripts generate the same format with complete metadata:

```
item_001 | WorkspaceID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee | ItemID: 11111111-2222-3333-4444-555555555555 | Name: DataflowTest | Type: Dataflow | File: WS__aaaaaaaa-bbbb-cccc__11111111-2222-3333__DataflowTest__Dataflow.json
item_002 | WorkspaceID: ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj | ItemID: 66666666-7777-8888-9999-aaaaaaaaaaaa | Name: FinanceRun | Type: Dataflow | File: WS__ffffffff-gggg-hhhh__66666666-7777-8888__FinanceRun__Dataflow.json
```

Each entry includes:
- **Item Directory**: Local directory name (`item_XXX`)
- **WorkspaceID**: Fabric workspace GUID
- **ItemID**: Fabric item GUID
- **Name**: Display name of the item
- **Type**: Item type (typically "Dataflow")
- **File**: Original export filename

---

## Complete End-to-End Example

### Using the Unified Script (Recommended)

```bash
cd C:\Fabric\Exports
python process_dataflows.py --all "PIE_WORKSPACES"
```

This single command will:
1. Decode all base64-encoded export files
2. Create .pqt templates
3. Organize output into `with_dataflows/` directory

**Output:**
```
======================================================================
STEP 1: DECODING DATAFLOW EXPORTS
======================================================================
BATCH DECODING DATAFLOW DEFINITIONS
Source Directory: PIE_WORKSPACES
Found 45 JSON files
...
✅ Successful: 45

======================================================================
STEP 2: CONVERTING TO .PQT FILES
======================================================================
Processing workspace: C:\Fabric\Exports\PIE_WORKSPACES
...
Successfully created 45/45 .pqt files
Successfully moved 45/45 items to with_dataflows/

======================================================================
WORKFLOW SUMMARY
======================================================================
Operation: Complete workflow (decode + convert)
Source directory: PIE_WORKSPACES

✅ All operations completed successfully
```

---

### Using Individual Scripts (Advanced)

If you prefer to run steps separately:

### Step 1: Export Dataflows from Fabric
Export your dataflows using the Fabric REST API. You'll get JSON files with base64-encoded content.

### Step 2: Decode the Exports

```bash
cd C:\Fabric\Exports
python batch_decode_dataflows.py "PIE_WORKSPACES"
```

**Output:**
```
======================================================================
BATCH DECODING DATAFLOW DEFINITIONS
======================================================================
Source Directory: PIE_WORKSPACES
Found 45 JSON files

[1/45] Processing: WS__10ee8e5c__2523106f__DataflowTest__Dataflow.json
   ✅ Decoded to: PIE_WORKSPACES\item_001
   ✅ Original file moved to subdirectory

[2/45] Processing: WS__22b3514d__5fce0e6a__FinanceRun__Dataflow.json
   ✅ Decoded to: PIE_WORKSPACES\item_002
   ✅ Original file moved to subdirectory

...

======================================================================
BATCH DECODE COMPLETE
======================================================================
✅ Successful: 45
❌ Failed: 0

💡 See 'item_mapping.txt' for file-to-folder mapping
======================================================================
```

### Step 3: Generate .pqt Templates

```bash
python create_pqt_from_workspace.py "PIE_WORKSPACES"
```

**Output:**

### MashupMetadata.json
Transforms `queryMetadata.json` from Fabric format to Power Query format:

**Input (queryMetadata.json):**
```json
{
  "queriesMetadata": {
    "Query1": {"isHidden": false},
    "Query2": {"isHidden": true}
  }
}
```

**Output (MashupMetadata.json):**
```json
{
  "Version": "1.0.0.0",
  "QueriesMetadata": [
    {"Name": "Query1", "IsHidden": false},
    {"Name": "Query2", "IsHidden": true}
  ]
}
```

### Metadata.json
Extracts dataflow name from `.platform` file:

```json
{
  "Name": "Finance_Monthly_Run",
  "Description": "",
  "Version": "1.0.0.0"
}
```

### [Content_Types].xml
Standard MIME type declarations for .pqt package:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="pq" ContentType="application/x-ms-m" />
</Types>
```

```
======================================================================
Processing workspace: C:\Fabric\Exports\PIE_WORKSPACES
Output directory: C:\Fabric\Exports\PIE_WORKSPACES
======================================================================

Found 45 dataflow items in PIE_WORKSPACES

Working in place (source directory)

Creating pqtzip structures...
  ✓ item_001
  ✓ item_002
  ...
  ✓ item_045

Successfully created 45/45 pqtzip structures

Creating .pqt archive files...
  ✓ item_001.pqt
  ✓ item_002.pqt
  ...
  ✓ item_045.pqt

Successfully created 45/45 .pqt files

Moving items with .pqt files to with_dataflows...
  ✓ Moved item_001 to with_dataflows/
  ✓ Moved item_002 to with_dataflows/
  ...
  ✓ Moved item_045 to with_dataflows/

Successfully moved 45/45 items to with_dataflows/

Created item_mapping.txt with 45 entries at with_dataflows\item_mapping.txt

======================================================================
PROCESSING COMPLETE
======================================================================
Total items processed: 45
Items with dataflows (.pq files): 45
  - pqtzip structures created: 45
  - .pqt archives created: 45
  - Moved to with_dataflows/: 45
Items without dataflows: 0

Output location: C:\Fabric\Exports\PIE_WORKSPACES
Dataflows location: C:\Fabric\Exports\PIE_WORKSPACES\with_dataflows
======================================================================
```

### Step 4: Use the .pqt Files

The `.pqt` files are now in `PIE_WORKSPACES\with_dataflows\item_XXX\item_XXX.pqt`

Import into Power BI Desktop:
1. Open Power BI Desktop
2. Home → Get Data → Power Query Template
3. Select the `.pqt` file
4. Update connection parameters as needed

---

## Command Reference

### process_dataflows.py (Unified Script)

| Flag | Description | Example |
|------|-------------|---------|
| `--all` | Run complete workflow (decode + convert) | `python process_dataflows.py --all "source"` |
| `--decode` | Decode exports only | `python process_dataflows.py --decode "source"` |
| `--convert` | Convert to .pqt only | `python process_dataflows.py --convert "source"` |
| `--output <dir>` | Custom output directory | `python process_dataflows.py --all "source" --output "out"` |
| `--help` | Show help message | `python process_dataflows.py --help` |

### Individual Scripts

**batch_decode_dataflows.py:**
```bash
python batch_decode_dataflows.py <source_directory>
```

**create_pqt_from_workspace.py:**
```bash
# In-place (default)
python create_pqt_from_workspace.py <source_directory>

# Custom output
python create_pqt_from_workspace.py <source_directory> <output_directory>
```

---

## File Transformations

## Troubleshooting

### batch_decode_dataflows.py

**No JSON files found**
- Verify the source directory path is correct
- Ensure JSON files are directly in the source directory (not in subdirectories)
- Check file extensions are `.json`

**Decoding errors**
- Ensure files are valid Fabric dataflow exports
- Check file encoding is UTF-8
- Verify JSON structure matches expected format

### create_pqt_from_workspace.py

**No dataflow items found**
- Ensure workspace was decoded with `batch_decode_dataflows.py` first
- Verify `item_XXX` directories contain `mashup.pq` files
- Check the source path points to the correct decoded directory

**Missing files in pqtzip**
- Ensure source items have `queryMetadata.json` and `.platform` files
- Re-run `batch_decode_dataflows.py` if files are missing

**.pqt archive creation fails**
- Verify sufficient disk space
- Check write permissions in output directory
- Ensure no files are open/locked in the source directories

## Technical Details

### Fabric Dataflow Export Format
Fabric exports dataflows as JSON files with base64-encoded parts:
```json
{
  "definition": {
    "parts": [
      {"path": "mashup.pq", "payload": "base64...", "payloadType": "InlineBase64"},
      {"path": "queryMetadata.json", "payload": "base64...", "payloadType": "InlineBase64"}
    ]
  }
}
```

### Power Query Template (.pqt) Format
A `.pqt` file is a ZIP archive containing exactly 4 files:
1. `MashupDocument.pq` - The Power Query M code
2. `MashupMetadata.json` - Query metadata (names, visibility)
3. `Metadata.json` - Template name, description, version
4. `[Content_Types].xml` - MIME type declarations

### Metadata Transformation
The script converts Fabric's nested `queriesMetadata` object to Power Query's flat `QueriesMetadata` array, preserving query names and visibility settings.

### Windows MAX_PATH Workaround
The tools use short numbered directory names (`item_001`, `item_002`) to avoid Windows 260-character path length limitations, especially important when working with deeply nested workspace structures.

## Use Cases

- **Template Distribution**: Create portable .pqt files for sharing dataflows across teams
- **Version Control**: Store decoded M code in source control systems
- **Migration**: Move dataflows between Fabric workspaces or tenants
- **Backup**: Archive dataflow definitions outside of Fabric
- **Development**: Edit dataflows in external tools before re-importing

## License

This tool is provided as-is for internal use with Microsoft Fabric and Power Query workflows.
