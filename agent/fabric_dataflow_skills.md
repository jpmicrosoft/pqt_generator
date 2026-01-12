# Microsoft Fabric Dataflow Technical Skills

## Reference Resources

### Official Microsoft Documentation

- **Microsoft Fabric Documentation**: https://learn.microsoft.com/fabric/
- **Power Query M Language Reference**: https://learn.microsoft.com/powerquery-m/
- **Power BI REST API Reference**: https://learn.microsoft.com/rest/api/power-bi/
- **Power BI Admin API Endpoint**: https://api.powerbi.com/v1.0/myorg/admin
- **Fabric Scanner API Documentation**: https://learn.microsoft.com/rest/api/power-bi/admin/workspace-info-get-scan-result
- **Fabric Dataflow Definition API**: https://learn.microsoft.com/rest/api/fabric/dataflow/items/get-dataflow-definition
- **Scanner API Setup Guide**: https://learn.microsoft.com/power-bi/admin/service-admin-metadata-scanning
- **Service Principal Setup**: https://learn.microsoft.com/power-bi/developer/embedded/embed-service-principal
- **Power BI Admin REST API**: https://learn.microsoft.com/rest/api/power-bi/admin
- **Git Credential Manager**: https://github.com/git-ecosystem/git-credential-manager
- **Python zipfile Module**: https://docs.python.org/3/library/zipfile.html

---

## Skill Category: Fabric Export Structure Analysis

### Skill: Identify Fabric Export File Structure

**When to Use:**
- Analyzing JSON files exported from Microsoft Fabric
- Validating export file structure before processing
- Troubleshooting export format issues

**How to Execute:**

1. **Check for definition.parts structure:**
   ```python
   import json
   
   with open('export_file.json', 'r', encoding='utf-8') as f:
       data = json.load(f)
   
   if 'definition' in data and 'parts' in data['definition']:
       print(f"Found {len(data['definition']['parts'])} parts")
       for part in data['definition']['parts']:
           print(f"- {part['path']}")
   else:
       print("Invalid structure: missing definition.parts")
   ```

2. **Expected parts:**
   - `mashup.pq` - Power Query M code
   - `queryMetadata.json` - Query metadata
   - `.platform` - Platform metadata

3. **Validate payload encoding:**
   ```python
   import base64
   
   for part in data['definition']['parts']:
       if part['payloadType'] == 'InlineBase64':
           try:
               decoded = base64.b64decode(part['payload'])
               print(f"{part['path']}: {len(decoded)} bytes")
           except Exception as e:
               print(f"{part['path']}: Invalid base64 - {e}")
   ```

**Expected Output:**
```
Found 3 parts
- mashup.pq
- queryMetadata.json
- .platform
```

### Skill: Decode Base64 Payloads from Fabric Exports

**When to Use:**
- Converting base64-encoded content to readable format
- Extracting M code and metadata from exports
- Preparing files for manual inspection or editing

**How to Execute:**

```python
import base64
import json

def decode_fabric_export(export_file_path, output_dir):
    with open(export_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for part in data['definition']['parts']:
        payload = part['payload']
        path = part['path']
        
        # Decode base64
        decoded = base64.b64decode(payload)
        
        # Determine encoding (UTF-8 for text files)
        try:
            content = decoded.decode('utf-8')
            mode = 'w'
            write_content = content
        except UnicodeDecodeError:
            # Binary file
            mode = 'wb'
            write_content = decoded
        
        # Write to file
        output_path = os.path.join(output_dir, path)
        with open(output_path, mode, encoding='utf-8' if mode == 'w' else None) as out:
            out.write(write_content)
        
        print(f"Decoded: {path}")
```

**Key Points:**
- Always use UTF-8 encoding for text files
- Handle both text and binary payloads
- Preserve file structure and naming

---

## Skill Category: queryMetadata.json Structure Validation

### Skill: Validate queriesMetadata Object Presence

**When to Use:**
- Before converting to .pqt files
- Troubleshooting empty QueriesMetadata in .pqt
- Validating export quality

**How to Execute:**

```python
import json

def validate_query_metadata(metadata_path):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Check for queriesMetadata object
    if 'queriesMetadata' not in metadata:
        print("❌ Missing queriesMetadata object")
        return False
    
    if not isinstance(metadata['queriesMetadata'], dict):
        print("❌ queriesMetadata is not an object/dict")
        return False
    
    # Validate structure
    queries = metadata['queriesMetadata']
    if len(queries) == 0:
        print("⚠️  queriesMetadata is empty")
        return True  # Valid but empty
    
    print(f"✅ Found {len(queries)} queries:")
    for query_name, query_info in queries.items():
        if 'queryId' in query_info and 'queryName' in query_info:
            print(f"  - {query_name}: {query_info['queryId']}")
        else:
            print(f"  ❌ {query_name}: Missing queryId or queryName")
            return False
    
    return True
```

**Expected Structure:**
```json
{
  "formatVersion": "202502",
  "queriesMetadata": {
    "QueryName1": {
      "queryId": "guid-here",
      "queryName": "QueryName1"
    }
  }
}
```

**Common Error Pattern (Wrong):**
```json
{
  "name": "DataflowName",
  "description": "Some description"
}
```

### Skill: Transform queryMetadata to MashupMetadata

**When to Use:**
- Converting queryMetadata.json to .pqt format
- Creating MashupMetadata.json for .pqt files

**How to Execute:**

```python
import json

def create_mashup_metadata(query_metadata_path, output_path):
    with open(query_metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Initialize MashupMetadata structure
    mashup_metadata = {
        "QueryGroups": [],
        "QueriesMetadata": []
    }
    
    # Extract queriesMetadata if present
    if 'queriesMetadata' in metadata:
        for query_name, query_info in metadata['queriesMetadata'].items():
            mashup_metadata['QueriesMetadata'].append({
                "QueryId": query_info.get('queryId', ''),
                "QueryName": query_info.get('queryName', query_name)
            })
    
    # Write MashupMetadata.json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mashup_metadata, f, indent=2)
    
    print(f"Created MashupMetadata.json with {len(mashup_metadata['QueriesMetadata'])} queries")
```

**Key Points:**
- QueriesMetadata is an array, not an object
- Each entry needs QueryId and QueryName
- QueryGroups is usually empty

---

## Skill Category: Power Query M Code Analysis

### Skill: Identify Workspace-Specific References in M Code

**When to Use:**
- Before importing .pqt into different workspace
- Assessing portability of dataflows
- Planning migrations

**How to Execute:**

```python
import re

def analyze_m_code_dependencies(mashup_pq_path):
    with open(mashup_pq_path, 'r', encoding='utf-8') as f:
        m_code = f.read()
    
    dependencies = {
        'lakehouse_calls': [],
        'workspace_refs': [],
        'connection_strings': [],
        'external_sources': []
    }
    
    # Check for Lakehouse.Contents()
    lakehouse_pattern = r'Lakehouse\.Contents\([^)]+\)'
    dependencies['lakehouse_calls'] = re.findall(lakehouse_pattern, m_code)
    
    # Check for workspace IDs (GUID pattern)
    guid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    dependencies['workspace_refs'] = re.findall(guid_pattern, m_code, re.IGNORECASE)
    
    # Check for connection strings
    conn_pattern = r'Data Source=|Server=|Database='
    if re.search(conn_pattern, m_code, re.IGNORECASE):
        dependencies['connection_strings'] = ['Found connection string references']
    
    # Check for common external sources
    external_sources = [
        'Sql.Database', 'Sql.Databases', 'Oracle.Database',
        'PostgreSQL.Database', 'SharePoint.', 'Web.Contents',
        'AzureStorage.', 'Databricks.', 'Snowflake.'
    ]
    
    for source in external_sources:
        if source in m_code:
            dependencies['external_sources'].append(source)
    
    return dependencies

def print_dependency_report(dependencies):
    print("M Code Dependency Analysis:")
    print("=" * 50)
    
    if dependencies['lakehouse_calls']:
        print(f"⚠️  Lakehouse References: {len(dependencies['lakehouse_calls'])}")
        for call in dependencies['lakehouse_calls'][:3]:
            print(f"   {call}")
    
    if dependencies['workspace_refs']:
        print(f"⚠️  Workspace IDs Found: {len(dependencies['workspace_refs'])}")
    
    if dependencies['connection_strings']:
        print(f"⚠️  Connection Strings: {len(dependencies['connection_strings'])}")
    
    if dependencies['external_sources']:
        print(f"⚠️  External Sources: {', '.join(dependencies['external_sources'])}")
    
    if not any(dependencies.values()):
        print("✅ No workspace-specific dependencies found - likely portable")
```

**Portability Assessment:**
- **Portable**: Uses Table.FromRows(), List.*, Table.* functions only
- **Workspace-Specific**: Contains Lakehouse.Contents(), specific workspace IDs
- **Connection-Dependent**: References databases, SharePoint, web services

### Skill: Create Self-Contained M Code for Demos

**When to Use:**
- Creating portable demo dataflows
- Testing .pqt workflow without dependencies
- Training and presentations

**How to Execute:**

**Pattern 1: Inline Data Table**
```m
let
    // Define data inline as JSON
    Source = Table.FromRows(
        Json.Document("
        [
            {""Product"":""Laptop"",""Price"":1200,""Category"":""Electronics""},
            {""Product"":""Mouse"",""Price"":25,""Category"":""Electronics""},
            {""Product"":""Desk"",""Price"":350,""Category"":""Furniture""}
        ]
        "),
        type table [Product = text, Price = number, Category = text]
    ),
    // Transform as needed
    FilteredRows = Table.SelectRows(Source, each [Price] > 100)
in
    FilteredRows
```

**Pattern 2: Generated Date Table**
```m
let
    StartDate = #date(2024, 1, 1),
    EndDate = #date(2024, 12, 31),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    ToTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    ChangedType = Table.TransformColumnTypes(ToTable, {{"Date", type date}}),
    AddedYear = Table.AddColumn(ChangedType, "Year", each Date.Year([Date]), Int64.Type),
    AddedMonth = Table.AddColumn(AddedYear, "Month", each Date.MonthName([Date]), type text),
    AddedQuarter = Table.AddColumn(AddedMonth, "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text)
in
    AddedQuarter
```

**Pattern 3: Filtered Reference Data**
```m
let
    AllCustomers = Table.FromRows(
        Json.Document("
        [
            {""CustomerID"":1,""Name"":""Acme Corp"",""Status"":""Active""},
            {""CustomerID"":2,""Name"":""TechCo"",""Status"":""Inactive""},
            {""CustomerID"":3,""Name"":""DataWorks"",""Status"":""Active""}
        ]
        "),
        type table [CustomerID = number, Name = text, Status = text]
    ),
    ActiveOnly = Table.SelectRows(AllCustomers, each [Status] = "Active")
in
    ActiveOnly
```

**Benefits:**
- No external dependencies
- Imports into any workspace
- Easy to modify and test
- Ideal for training materials

---

## Skill Category: .pqt File Creation and Validation

### Skill: Create .pqt ZIP Archive Structure

**When to Use:**
- Converting decoded dataflows to .pqt format
- Manual .pqt creation for testing
- Customizing .pqt files

**How to Execute:**

```python
import zipfile
import os
import json

def create_pqt_file(source_dir, output_pqt_path):
    """
    Create .pqt ZIP archive from pqtzip directory structure
    
    Required files in source_dir:
    - MashupDocument.pq
    - MashupMetadata.json
    - Metadata.json
    - [Content_Types].xml
    """
    
    required_files = [
        'MashupDocument.pq',
        'MashupMetadata.json',
        'Metadata.json',
        '[Content_Types].xml'
    ]
    
    # Validate all required files exist
    for filename in required_files:
        filepath = os.path.join(source_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Required file missing: {filename}")
    
    # Create ZIP archive
    with zipfile.ZipFile(output_pqt_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in required_files:
            filepath = os.path.join(source_dir, filename)
            # Add to ZIP with just the filename (no path)
            zipf.write(filepath, arcname=filename)
    
    print(f"Created .pqt file: {output_pqt_path}")
    return True
```

**Key Points:**
- Files must be at root level in ZIP (no subdirectories)
- Use ZIP_DEFLATED compression
- All 4 files are required
- File order doesn't matter

### Skill: Generate [Content_Types].xml

**When to Use:**
- Creating .pqt files from scratch
- Missing [Content_Types].xml in source

**How to Execute:**

```python
def generate_content_types_xml():
    """Generate [Content_Types].xml for .pqt file"""
    
    content = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="pq" ContentType="application/x-ms-m" />
    <Default Extension="json" ContentType="application/json" />
</Types>'''
    
    return content

# Usage
xml_content = generate_content_types_xml()
with open('[Content_Types].xml', 'w', encoding='utf-8') as f:
    f.write(xml_content)
```

### Skill: Validate .pqt File Structure

**When to Use:**
- Before importing .pqt files
- Troubleshooting import failures
- Quality assurance

**How to Execute:**

```python
import zipfile
import json

def validate_pqt_file(pqt_path):
    """Validate .pqt file structure and content"""
    
    print(f"Validating: {pqt_path}")
    
    required_files = {
        'MashupDocument.pq': 'text',
        'MashupMetadata.json': 'json',
        'Metadata.json': 'json',
        '[Content_Types].xml': 'xml'
    }
    
    with zipfile.ZipFile(pqt_path, 'r') as zipf:
        # Check file list
        files_in_zip = zipf.namelist()
        print(f"\nFiles in ZIP: {len(files_in_zip)}")
        
        for filename in files_in_zip:
            print(f"  - {filename}")
        
        # Validate required files
        missing = []
        for required_file in required_files.keys():
            if required_file not in files_in_zip:
                missing.append(required_file)
        
        if missing:
            print(f"\n❌ Missing required files: {', '.join(missing)}")
            return False
        
        # Validate MashupMetadata.json structure
        metadata_content = zipf.read('MashupMetadata.json').decode('utf-8')
        metadata = json.loads(metadata_content)
        
        if 'QueriesMetadata' not in metadata:
            print("\n❌ MashupMetadata.json missing QueriesMetadata array")
            return False
        
        query_count = len(metadata['QueriesMetadata'])
        print(f"\n✅ QueriesMetadata: {query_count} queries")
        
        for query in metadata['QueriesMetadata']:
            if 'QueryId' not in query or 'QueryName' not in query:
                print(f"❌ Invalid query metadata: {query}")
                return False
        
        # Validate M code exists
        m_code = zipf.read('MashupDocument.pq').decode('utf-8')
        if len(m_code) == 0:
            print("\n❌ MashupDocument.pq is empty")
            return False
        
        print(f"\n✅ MashupDocument.pq: {len(m_code)} characters")
        
    print("\n✅ .pqt file validation passed")
    return True
```

---

## Skill Category: Workspace ID Management

### Skill: Extract Workspace IDs from .platform Files

**When to Use:**
- Tracking source workspaces
- Planning migrations
- Documenting dependencies

**How to Execute:**

```python
import json

def extract_platform_metadata(platform_file_path):
    """Extract workspace and item metadata from .platform file"""
    
    with open(platform_file_path, 'r', encoding='utf-8') as f:
        platform_data = json.load(f)
    
    metadata = {}
    
    if 'metadata' in platform_data:
        meta = platform_data['metadata']
        metadata['workspace_id'] = meta.get('workspaceId', 'N/A')
        metadata['item_id'] = meta.get('itemId', 'N/A')
        metadata['item_type'] = meta.get('itemType', 'N/A')
        metadata['display_name'] = meta.get('displayName', 'N/A')
    
    return metadata

# Usage
metadata = extract_platform_metadata('.platform')
print(f"Workspace ID: {metadata['workspace_id']}")
print(f"Item ID: {metadata['item_id']}")
print(f"Name: {metadata['display_name']}")
```

### Skill: Sanitize Workspace IDs for Public Sharing

**When to Use:**
- Preparing code for GitHub/public repos
- Creating documentation examples
- Protecting sensitive information

**How to Execute:**

```python
import re
import os

def sanitize_workspace_ids(directory, replace_mapping=None):
    """
    Replace real workspace/item IDs with dummy values
    
    Args:
        directory: Path to search
        replace_mapping: Dict of {real_id: dummy_id} or None for auto-generation
    """
    
    if replace_mapping is None:
        # Generate dummy IDs
        replace_mapping = {
            # Workspace IDs
            '10ee8e5c-0129-463f-8ea4-3da613e9987c': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
            '22b3514d-31fa-45db-83aa-fd61b708baf3': 'ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj',
            # Item IDs
            '2523106f-1e93-41fa-b25d-1d03475e1d73': '11111111-2222-3333-4444-555555555555',
            '5fce0e6a-f440-4a26-9ece-71f07af751a4': '66666666-7777-8888-9999-aaaaaaaaaaaa',
        }
    
    # File extensions to process
    extensions = ['.md', '.json', '.txt', '.py']
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if any(filename.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace IDs
                modified = content
                for real_id, dummy_id in replace_mapping.items():
                    modified = modified.replace(real_id, dummy_id)
                
                # Write back if changed
                if modified != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(modified)
                    print(f"Sanitized: {filepath}")
```

**Dummy ID Patterns:**
- Workspace 1: `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee`
- Workspace 2: `ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj`
- Item 1: `11111111-2222-3333-4444-555555555555`
- Item 2: `66666666-7777-8888-9999-aaaaaaaaaaaa`

---

## Skill Category: Batch Processing and Automation

### Skill: Process Multiple Export Directories

**When to Use:**
- Migrating multiple workspaces
- Bulk .pqt generation
- Automated workflows

**How to Execute:**

```python
import os
import subprocess

def batch_process_workspaces(root_dir, output_base_dir):
    """
    Process all workspace export directories
    
    Structure:
    root_dir/
    ├── workspace_A/
    ├── workspace_B/
    └── workspace_C/
    """
    
    workspace_dirs = [
        d for d in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, d))
    ]
    
    results = []
    
    for workspace in workspace_dirs:
        workspace_path = os.path.join(root_dir, workspace)
        output_path = os.path.join(output_base_dir, workspace)
        
        print(f"\n{'='*60}")
        print(f"Processing: {workspace}")
        print(f"{'='*60}")
        
        # Run process_dataflows.py
        cmd = [
            'python',
            'process_dataflows.py',
            '--all',
            workspace_path,
            '--output',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        results.append({
            'workspace': workspace,
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })
    
    # Summary report
    print(f"\n{'='*60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r['success'])
    print(f"Total workspaces: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    
    # List failures
    failures = [r for r in results if not r['success']]
    if failures:
        print("\nFailed workspaces:")
        for failure in failures:
            print(f"  - {failure['workspace']}")
            print(f"    Error: {failure['error'][:200]}")
    
    return results
```

### Skill: Generate Item Mapping Summary

**When to Use:**
- Tracking processed dataflows
- Documentation
- Migration planning

**How to Execute:**

```python
import os

def consolidate_item_mappings(root_dir, output_file):
    """
    Consolidate all item_mapping.txt files into one summary
    """
    
    all_mappings = []
    
    for root, dirs, files in os.walk(root_dir):
        if 'item_mapping.txt' in files:
            mapping_path = os.path.join(root, 'item_mapping.txt')
            workspace_name = os.path.basename(os.path.dirname(mapping_path))
            
            with open(mapping_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                all_mappings.append(f"{workspace_name} | {line.strip()}")
    
    # Write consolidated file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Workspace | Item | WorkspaceID | ItemID | Name | Type | File\n")
        f.write("=" * 120 + "\n")
        for mapping in sorted(all_mappings):
            f.write(mapping + "\n")
    
    print(f"Consolidated {len(all_mappings)} mappings to {output_file}")
```

---

## Skill Application Examples

### Example 1: Complete .pqt Creation from Fabric Export

```python
import base64
import json
import os

# Step 1: Decode export file
export_path = 'WS__workspace-id__item-id__DataflowName__Dataflow.json'
output_dir = 'item_001'

with open(export_path, 'r', encoding='utf-8') as f:
    export_data = json.load(f)

os.makedirs(output_dir, exist_ok=True)

for part in export_data['definition']['parts']:
    decoded = base64.b64decode(part['payload']).decode('utf-8')
    with open(os.path.join(output_dir, part['path']), 'w', encoding='utf-8') as f:
        f.write(decoded)

# Step 2: Validate queryMetadata
with open(os.path.join(output_dir, 'queryMetadata.json'), 'r') as f:
    qm = json.load(f)

if 'queriesMetadata' not in qm:
    print("ERROR: Missing queriesMetadata object")
    exit(1)

# Step 3: Create pqtzip structure
pqtzip_dir = os.path.join(output_dir, 'pqtzip')
os.makedirs(pqtzip_dir, exist_ok=True)

# Copy MashupDocument.pq
import shutil
shutil.copy(
    os.path.join(output_dir, 'mashup.pq'),
    os.path.join(pqtzip_dir, 'MashupDocument.pq')
)

# Create MashupMetadata.json
mashup_meta = {
    "QueryGroups": [],
    "QueriesMetadata": [
        {
            "QueryId": info['queryId'],
            "QueryName": info['queryName']
        }
        for name, info in qm['queriesMetadata'].items()
    ]
}

with open(os.path.join(pqtzip_dir, 'MashupMetadata.json'), 'w') as f:
    json.dump(mashup_meta, f, indent=2)

# Create Metadata.json
with open(os.path.join(output_dir, '.platform'), 'r') as f:
    platform = json.load(f)

metadata = {
    "Name": platform['metadata']['displayName'],
    "Version": "1.0.0.0"
}

with open(os.path.join(pqtzip_dir, 'Metadata.json'), 'w') as f:
    json.dump(metadata, f, indent=2)

# Create [Content_Types].xml
xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="pq" ContentType="application/x-ms-m" />
    <Default Extension="json" ContentType="application/json" />
</Types>'''

with open(os.path.join(pqtzip_dir, '[Content_Types].xml'), 'w') as f:
    f.write(xml_content)

# Step 4: Create .pqt ZIP
import zipfile

pqt_path = os.path.join(output_dir, 'item_001.pqt')
with zipfile.ZipFile(pqt_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filename in os.listdir(pqtzip_dir):
        zipf.write(
            os.path.join(pqtzip_dir, filename),
            arcname=filename
        )

print(f"✅ Created: {pqt_path}")
```

### Example 2: Analyze Dataflow Portability

```python
def assess_dataflow_portability(item_dir):
    """Assess if dataflow is portable across workspaces"""
    
    mashup_path = os.path.join(item_dir, 'mashup.pq')
    
    with open(mashup_path, 'r', encoding='utf-8') as f:
        m_code = f.read()
    
    # Check for blocking patterns
    blocking_patterns = {
        'Lakehouse': r'Lakehouse\.Contents',
        'Workspace ID': r'[0-9a-f]{8}-[0-9a-f]{4}',
        'SQL Server': r'Sql\.(Database|Databases)',
        'SharePoint': r'SharePoint\.',
        'Web Service': r'Web\.Contents'
    }
    
    issues = []
    for name, pattern in blocking_patterns.items():
        if re.search(pattern, m_code, re.IGNORECASE):
            issues.append(name)
    
    # Assessment
    if not issues:
        print("✅ PORTABLE - No workspace-specific dependencies")
        return 'portable'
    else:
        print(f"⚠️  WORKSPACE-SPECIFIC - Found: {', '.join(issues)}")
        print("   Can only be imported into workspace with matching resources")
        return 'workspace-specific'
```

## Quick Reference: Common Patterns

### Workspace ID Pattern (GUID)
```regex
[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}
```

### Export Filename Pattern
```
WS__<workspace-prefix>__<item-prefix>__<name>__Dataflow.json
```

### Valid M Code Section Delimiter
```m
section Section1;
```

### Self-Contained Table Pattern
```m
Table.FromRows(Json.Document("[{...}]"), type table [...])
```

## Version History

- **Version 1.0** (2026-01-09): Initial skills compilation
  - 25+ technical skills documented
  - Code examples for common operations
  - Validation and troubleshooting patterns
