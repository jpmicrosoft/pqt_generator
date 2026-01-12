# Microsoft Fabric Dataflow Project Instructions

## Purpose
This instruction file provides guidance for working with Microsoft Fabric Dataflow Gen2 exports, converting them to Power Query Templates (.pqt), and understanding the structure and requirements for successful imports.

## Core Concepts

### 1. Fabric Dataflow Export Structure

Fabric dataflow exports are JSON files with the following structure:

```json
{
  "definition": {
    "parts": [
      {
        "path": "mashup.pq",
        "payload": "<base64-encoded-content>",
        "payloadType": "InlineBase64"
      },
      {
        "path": "queryMetadata.json",
        "payload": "<base64-encoded-content>",
        "payloadType": "InlineBase64"
      },
      {
        "path": ".platform",
        "payload": "<base64-encoded-content>",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

**Key Components:**
- **mashup.pq**: Power Query M code containing the dataflow queries
- **queryMetadata.json**: Query metadata including query names, IDs, and settings
- **.platform**: Fabric platform metadata (workspace ID, item ID, item type, display name)

### 2. Critical queryMetadata.json Structure

The queryMetadata.json file MUST contain a nested `queriesMetadata` object for .pqt conversion to work:

```json
{
  "formatVersion": "202502",
  "computeEngineSettings": {},
  "name": "DataflowName",
  "queryGroups": [],
  "documentLocale": "en-US",
  "queriesMetadata": {
    "QueryName1": {
      "queryId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "queryName": "QueryName1"
    },
    "QueryName2": {
      "queryId": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "queryName": "QueryName2"
    }
  }
}
```

**Common Error:** Missing the `queriesMetadata` object results in empty QueriesMetadata arrays in the generated .pqt files.

### 3. Workspace ID and Import Requirements

**Critical Understanding:**
- Toolkit creates valid .pqt files from Fabric exports ✓
- .pqt files can be imported successfully into the SAME workspace or workspaces with matching resources ✓
- Import failures occur when workspace IDs, Lakehouse IDs, or connection references don't exist in the target workspace ✗

**Workspace-Specific References in M Code:**
- `Lakehouse.Contents()` calls reference specific Lakehouse IDs
- Connection strings may include workspace-specific endpoints
- Workspace IDs in .platform metadata should match target environment

**Solution for Portable Demos:**
- Create dataflows with self-contained M code (no external dependencies)
- Use `Table.FromRows(Json.Document("[{...}]"))` pattern for inline data
- Avoid Lakehouse.Contents(), database connections, or workspace-specific functions

### 4. Power Query Template (.pqt) File Structure

A .pqt file is a ZIP archive containing:

```
.pqt (ZIP archive)
├── MashupDocument.pq          # Power Query M code
├── MashupMetadata.json        # Metadata with QueriesMetadata array
├── Metadata.json              # Name and version info
└── [Content_Types].xml        # MIME type declarations
```

**MashupMetadata.json Structure:**
```json
{
  "QueryGroups": [],
  "QueriesMetadata": [
    {
      "QueryId": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "QueryName": "QueryName1"
    }
  ]
}
```

## Workflow Guidelines

### Standard Workflow: Export → Decode → Convert → Import

1. **Export from Fabric**
   - Use Fabric REST API, Scanner API, or Portal export
   - Files named: `WS__<workspace-id>__<item-id>__<name>__Dataflow.json`

2. **Decode Exports**
   ```bash
   python batch_decode_dataflows.py <source_directory>
   ```
   - Creates `item_XXX/` directories
   - Decodes base64 payloads
   - Extracts mashup.pq, queryMetadata.json, .platform

3. **Convert to .pqt**
   ```bash
   python create_pqt_from_workspace.py <source_directory>
   ```
   - Creates pqtzip/ structure
   - Generates .pqt ZIP archives
   - Moves items to with_dataflows/

4. **Import .pqt**
   - Import into same workspace OR
   - Import into workspace with matching resources

### Unified Workflow (Recommended)

```bash
python process_dataflows.py --all <source_directory>
```

Performs both decode and convert operations in one command.

## Common Issues and Solutions

### Issue 1: .pqt Import Fails with Connection/Resource Errors

**Cause:** .pqt file contains references to workspace-specific resources (Lakehouses, connections) that don't exist in target workspace.

**Solution:**
- Import into the same workspace where exports originated
- OR create dataflows with self-contained M code
- OR ensure target workspace has matching resources

### Issue 2: Empty QueriesMetadata in Generated .pqt

**Cause:** queryMetadata.json missing the `queriesMetadata` object.

**Solution:**
- Verify queryMetadata.json has nested `queriesMetadata` object
- Check that query names match between queriesMetadata and M code
- Ensure queryIds are valid GUIDs

### Issue 3: Toolkit Decoding Fails - No Dataflow Items Found

**Cause:** Export file doesn't have correct `definition.parts` structure.

**Solution:**
- Verify export file has `definition.parts` array
- Check that parts include mashup.pq, queryMetadata.json, .platform
- Ensure payloads are base64-encoded

### Issue 4: Re-zipped .pqt Files Won't Import

**Cause:** This is misleading - the real issue is workspace/connection mismatch, not ZIP corruption.

**Solution:**
- Don't manually re-zip .pqt files unless necessary
- If needed, use toolkit to regenerate from source
- Focus on workspace/resource matching, not ZIP structure

## Best Practices

### For Production Migrations

1. **Export from source workspace**
   - Document workspace ID, Lakehouse IDs, connection strings
   - Export all dataflows at once for consistency

2. **Decode and inspect**
   - Review M code for workspace-specific references
   - Check queryMetadata.json structure
   - Verify .platform metadata

3. **Prepare target workspace**
   - Create matching Lakehouses (same names/IDs if possible)
   - Set up required connections
   - Ensure permissions are configured

4. **Convert and import**
   - Generate .pqt files
   - Import into target workspace
   - Test and validate queries

### For Demos and Presentations

1. **Create self-contained dataflows in Fabric**
   - Use inline data: `Table.FromRows(Json.Document("[{...}]"))`
   - Avoid Lakehouse.Contents() and external connections
   - Keep queries simple and focused

2. **Export and process**
   - Export from demo workspace
   - Process with toolkit
   - Verify .pqt files import successfully

3. **Test in clean environment**
   - Import into different workspace
   - Verify no connection/resource errors
   - Confirm queries execute correctly

### For Multi-Tenant Scenarios

1. **Export once, deploy many**
   - Create template dataflows
   - Use parameters for tenant-specific values
   - Document required resources per tenant

2. **Customize per tenant**
   - Update workspace IDs in .platform
   - Modify connection strings in M code
   - Adjust Lakehouse references

3. **Validate imports**
   - Test in one tenant workspace first
   - Verify all queries execute
   - Check for performance issues

## File Naming Conventions

### Export Files
```
WS__<workspace-id-prefix>__<item-id-prefix>__<dataflow-name>__Dataflow.json
```

Example:
```
WS__aaaaaaaa-bbbb-cccc__11111111-2222-3333__SalesData__Dataflow.json
```

### Decoded Directories
```
item_001, item_002, item_003, ...
```

### .pqt Files
```
item_001.pqt, item_002.pqt, item_003.pqt, ...
```

### Mapping Files
```
item_mapping.txt
```

Format:
```
item_001 | WorkspaceID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee | ItemID: 11111111-2222-3333-4444-555555555555 | Name: DataflowName | Type: Dataflow | File: WS__aaaaaaaa-bbbb-cccc__11111111-2222-3333__DataflowName__Dataflow.json
```

## Security and Compliance

### Protecting Sensitive Information

1. **Workspace and Item IDs**
   - These are GUIDs that identify resources
   - Not inherently sensitive but should be sanitized for public sharing
   - Use dummy GUIDs in documentation and examples

2. **Connection Strings**
   - May contain credentials or endpoint information
   - Always review M code before sharing
   - Sanitize or remove sensitive connections

3. **Data Content**
   - M code may contain inline data or references
   - Review for PII, credentials, or proprietary information
   - Use sample data for demonstrations

### Repository Cleanliness

When preparing code for public repositories:

1. **Search for company-specific references**
   ```bash
   grep -r "CompanyName|company-name" .
   ```

2. **Replace real IDs with dummy values**
   - Workspace IDs: `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`
   - Item IDs: `11111111-2222-3333-4444-555555555555`

3. **Review all documentation**
   - README files
   - Code comments
   - Example outputs

## Advanced Topics

### Custom M Code Patterns for Portability

**Inline Data Table:**
```m
let
    Source = Table.FromRows(
        Json.Document("[{""Product"":""Laptop"",""Sales"":1000,""Region"":""North""}]"),
        type table [Product = text, Sales = number, Region = text]
    )
in
    Source
```

**Date Table Generator:**
```m
let
    StartDate = #date(2024, 1, 1),
    EndDate = #date(2024, 12, 31),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    Source = List.Dates(StartDate, DayCount, #duration(1,0,0,0)),
    TableFromList = Table.FromList(Source, Splitter.SplitByNothing()),
    ChangedType = Table.TransformColumnTypes(TableFromList, {{"Column1", type date}}),
    RenamedColumns = Table.RenameColumns(ChangedType, {{"Column1", "Date"}})
in
    RenamedColumns
```

**Parameter-Based Configuration:**
```m
let
    EnvironmentConfig = [
        Dev = [WorkspaceId = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"],
        Prod = [WorkspaceId = "ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj"]
    ],
    CurrentEnvironment = "Dev",
    Config = Record.Field(EnvironmentConfig, CurrentEnvironment)
in
    Config
```

### Batch Processing Multiple Workspaces

When processing exports from multiple workspaces:

1. **Organize by workspace**
   ```
   exports/
   ├── workspace_A/
   ├── workspace_B/
   └── workspace_C/
   ```

2. **Process each workspace**
   ```bash
   python process_dataflows.py --all exports/workspace_A
   python process_dataflows.py --all exports/workspace_B
   python process_dataflows.py --all exports/workspace_C
   ```

3. **Merge item_mapping.txt files**
   - Combine mappings for tracking
   - Note workspace origins
   - Document dependencies

### Version Control Integration

1. **Track decoded files**
   - Commit mashup.pq for code review
   - Commit queryMetadata.json for structure review
   - Include .platform for reference tracking

2. **Exclude large binary files**
   ```.gitignore
   *.pqt
   *_decoded.json
   WS__*.json
   ```

3. **Document changes**
   - Use meaningful commit messages
   - Note M code modifications
   - Track metadata updates

## Troubleshooting Checklist

When .pqt imports fail:

- [ ] Verify workspace ID matches target environment
- [ ] Check for Lakehouse.Contents() calls requiring specific Lakehouse IDs
- [ ] Review connection strings for workspace-specific endpoints
- [ ] Confirm queryMetadata.json has queriesMetadata object
- [ ] Validate M code syntax
- [ ] Check for missing parameters
- [ ] Verify all referenced queries exist
- [ ] Test in source workspace first

When toolkit processing fails:

- [ ] Verify export file has definition.parts structure
- [ ] Check base64 encoding is valid
- [ ] Ensure all three parts exist (mashup.pq, queryMetadata.json, .platform)
- [ ] Verify JSON structure is valid
- [ ] Check file permissions
- [ ] Ensure Python 3.6+ is installed
- [ ] Review error messages for specific issues

## Reference Resources

### Official Microsoft Documentation

- **Microsoft Fabric Documentation**: https://learn.microsoft.com/fabric/
  - Complete Fabric platform documentation covering dataflows, workspaces, and features

- **Power Query M Language Reference**: https://learn.microsoft.com/powerquery-m/
  - Complete M language reference including functions, operators, and expressions

- **Power BI REST API Reference**: https://learn.microsoft.com/rest/api/power-bi/
  - Power BI REST API documentation for admin operations, datasets, reports, and workspaces

- **Power BI Admin API Endpoint**: https://api.powerbi.com/v1.0/myorg/admin
  - Base endpoint for Power BI Admin REST APIs including Scanner API

- **Fabric Scanner API Documentation**: https://learn.microsoft.com/rest/api/power-bi/admin/workspace-info-get-scan-result
  - Scanner API for performing tenant-wide workspace and item metadata scans

- **Fabric Dataflow Definition API**: https://learn.microsoft.com/rest/api/fabric/dataflow/items/get-dataflow-definition
  - API for retrieving Fabric dataflow definitions including mashup.pq and metadata

- **Scanner API Setup Guide**: https://learn.microsoft.com/power-bi/admin/service-admin-metadata-scanning
  - Setup guide for enabling and configuring metadata scanning in Power BI Admin Portal

- **Service Principal Setup**: https://learn.microsoft.com/power-bi/developer/embedded/embed-service-principal
  - Guide to configuring service principals for automated Power BI/Fabric API access

- **Power BI Admin REST API**: https://learn.microsoft.com/rest/api/power-bi/admin
  - Complete Power BI Admin REST API reference for tenant administration

### Development Tools

- **Git Credential Manager**: https://github.com/git-ecosystem/git-credential-manager
  - Secure Git credential storage for authenticating with GitHub repositories

- **Python zipfile Module**: https://docs.python.org/3/library/zipfile.html
  - Python standard library documentation for creating and manipulating ZIP archives

## Quick Reference Commands

```bash
# Complete workflow
python process_dataflows.py --all <directory>

# Decode only
python process_dataflows.py --decode <directory>

# Convert only
python process_dataflows.py --convert <directory>

# Individual scripts
python batch_decode_dataflows.py <directory>
python create_pqt_from_workspace.py <directory>

# Help
python process_dataflows.py --help
```

## Version History

- **Version 1.0** (2026-01-09): Initial instruction file based on session learnings
  - Documented Fabric export structure
  - Explained queryMetadata requirements
  - Clarified workspace ID importance
  - Provided troubleshooting guidance
