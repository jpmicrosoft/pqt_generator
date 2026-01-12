# Fabric Dataflow Agent Configuration

This directory contains configuration files for AI agents working with Microsoft Fabric Dataflow projects. These files provide comprehensive knowledge, skills, and tooling definitions to enable AI assistants to effectively help with dataflow development, migration, and troubleshooting.

## Files Overview

### 1. `fabric_dataflow_instructions.md`

**Purpose:** Comprehensive instruction file providing guidance for working with Fabric Dataflow Gen2 exports and Power Query Templates (.pqt).

**Contents:**
- Core concepts (export structure, queryMetadata requirements, workspace IDs)
- Workflow guidelines (export → decode → convert → import)
- Common issues and solutions
- Best practices for production migrations, demos, and multi-tenant scenarios
- File naming conventions
- Security and compliance guidance
- Advanced topics (M code patterns, batch processing, version control)
- Troubleshooting checklists
- Reference resources with documentation URLs

**When to Use:**
- Starting a new Fabric dataflow project
- Troubleshooting .pqt import failures
- Planning workspace migrations
- Creating portable demo dataflows
- Preparing code for public sharing

**How to Use:**
```markdown
1. Read "Core Concepts" section for foundational understanding
2. Follow "Workflow Guidelines" for step-by-step procedures
3. Reference "Common Issues and Solutions" when encountering errors
4. Apply "Best Practices" for your specific use case
5. Use "Troubleshooting Checklist" for systematic debugging
```

---

### 2. `fabric_dataflow_skills.md`

**Purpose:** Technical skills library with executable code examples and step-by-step procedures for common Fabric dataflow tasks.

**Contents:**
- Reference resources (all documentation URLs)
- Export structure analysis skills
- queryMetadata validation and transformation
- M code dependency analysis
- .pqt file creation and validation
- Workspace metadata extraction
- Self-contained M code generation
- Batch processing operations
- ID sanitization for public sharing
- Git workflow integration

**When to Use:**
- Need working code examples for specific tasks
- Learning how to perform technical operations
- Building automation scripts
- Understanding expected inputs and outputs
- Training AI agents on specific procedures

**How to Use:**
```markdown
1. Find the relevant "Skill Category" for your task
2. Read the "When to Use" section to confirm applicability
3. Follow "How to Execute" with provided code examples
4. Review "Expected Output" to validate results
5. Apply "Key Points" for best practices
```

**Skill Categories:**
- Fabric Export Structure Analysis
- Query Metadata Management
- M Code Analysis and Generation
- .pqt File Operations
- Workspace Migration Tools
- Batch Processing
- Security and Sanitization
- Version Control Integration

---

### 3. `fabric_dataflow_mcp.json`

**Purpose:** Model Context Protocol (MCP) configuration file defining tools, resources, prompts, and knowledge base for AI agents.

**Contents:**
- **Tools:** 9 executable tools for dataflow operations
  - decode_fabric_export
  - validate_query_metadata
  - analyze_m_code_dependencies
  - create_pqt_file
  - validate_pqt_file
  - extract_workspace_metadata
  - generate_self_contained_m_code
  - batch_process_exports
  - sanitize_workspace_ids

- **Resources:** 6 documentation resources
  - Fabric export structure guide
  - Query metadata requirements
  - .pqt file format specification
  - Workspace migration guide
  - M code patterns library
  - Troubleshooting checklist

- **Prompts:** 4 guided workflows
  - analyze_dataflow_export
  - create_portable_dataflow
  - troubleshoot_pqt_import
  - plan_workspace_migration

- **Configuration:** Toolkit settings, dummy IDs, encoding preferences

- **Knowledge Base:** Critical facts about exports, workspace specificity, .pqt structure, common issues

- **Documentation:** All 11 official Microsoft documentation URLs

**When to Use:**
- Configuring AI agents for Fabric dataflow work
- Building automated workflows
- Creating interactive prompts for guided processes
- Providing structured knowledge to AI systems

**How to Use:**

**For AI Agent Configuration:**
```json
{
  "mcpServers": {
    "fabric-dataflow-toolkit": {
      // Use this configuration in your AI agent settings
      // Points to fabric_dataflow_server implementation
    }
  }
}
```

**For Tool Invocation:**
```json
// Example: Decode a Fabric export
{
  "tool": "decode_fabric_export",
  "parameters": {
    "export_file_path": "exports/WS__workspace-id__item-id__DataflowName__Dataflow.json",
    "output_directory": "output/decoded"
  }
}
```

**For Prompt Usage:**
```json
// Example: Analyze dataflow export
{
  "prompt": "analyze_dataflow_export",
  "arguments": {
    "export_file_path": "exports/WS__workspace-id__item-id__DataflowName__Dataflow.json"
  }
}
```

---

## Quick Start Guide

### Scenario 1: Learning Fabric Dataflow Basics

1. **Read:** `fabric_dataflow_instructions.md` → "Core Concepts" section
2. **Reference:** "Fabric Export Structure" and "queryMetadata Requirements"
3. **Practice:** Use skills in `fabric_dataflow_skills.md` → "Identify Fabric Export File Structure"

### Scenario 2: Troubleshooting .pqt Import Failure

1. **Check:** `fabric_dataflow_instructions.md` → "Common Issues and Solutions" → "Issue 1"
2. **Use:** `fabric_dataflow_skills.md` → "Validate queryMetadata Structure"
3. **Analyze:** Run `analyze_m_code_dependencies` tool (defined in `fabric_dataflow_mcp.json`)
4. **Follow:** Troubleshooting checklist in instructions file

### Scenario 3: Building Automation Script

1. **Review:** `fabric_dataflow_mcp.json` → "tools" section for available operations
2. **Copy:** Code examples from `fabric_dataflow_skills.md` relevant skills
3. **Apply:** Best practices from `fabric_dataflow_instructions.md`
4. **Reference:** Documentation URLs in all three files

### Scenario 4: Planning Workspace Migration

1. **Read:** `fabric_dataflow_instructions.md` → "Best Practices" → "For Production Migrations"
2. **Use:** `plan_workspace_migration` prompt from `fabric_dataflow_mcp.json`
3. **Execute:** Batch processing skills from `fabric_dataflow_skills.md`
4. **Validate:** Use validation tools defined in MCP configuration

### Scenario 5: Creating Portable Demo Dataflows

1. **Read:** `fabric_dataflow_instructions.md` → "Best Practices" → "For Demos and Presentations"
2. **Use:** `create_portable_dataflow` prompt from `fabric_dataflow_mcp.json`
3. **Generate:** Self-contained M code using skills from `fabric_dataflow_skills.md`
4. **Reference:** M Code Patterns in instructions file

---

## Integration with AI Agents

### VS Code Copilot / GitHub Copilot

1. **Add to workspace settings:**
   ```json
   {
     "github.copilot.chat.codeGeneration.instructions": [
       {
         "file": "agent/fabric_dataflow_instructions.md"
       }
     ]
   }
   ```

2. **Reference in prompts:**
   ```
   @workspace Using the fabric dataflow instructions, help me decode this export file.
   ```

### Custom AI Agents

1. **Load instructions as system prompt:**
   ```python
   with open('fabric_dataflow_instructions.md', 'r') as f:
       instructions = f.read()
   
   system_prompt = f"You are an expert in Fabric dataflows.\n\n{instructions}"
   ```

2. **Use skills for code generation:**
   ```python
   with open('fabric_dataflow_skills.md', 'r') as f:
       skills = f.read()
   
   # Extract relevant skill for current task
   ```

3. **Implement MCP tools:**
   ```python
   import json
   
   with open('fabric_dataflow_mcp.json', 'r') as f:
       mcp_config = json.load(f)
   
   # Implement tools defined in mcp_config['mcpServers']['fabric-dataflow-toolkit']['tools']
   ```

### Claude Desktop / MCP Servers

1. **Configure MCP server:**
   ```json
   {
     "mcpServers": {
       "fabric-dataflow-toolkit": {
         "command": "python",
         "args": ["-m", "fabric_dataflow_server"],
         "env": {
           "TOOLKIT_PATH": "./"
         }
       }
     }
   }
   ```

2. **Reference in conversations:**
   ```
   Use the fabric-dataflow-toolkit to analyze this export file.
   ```

---

## File Maintenance

### Updating Instructions

When you discover new patterns, issues, or solutions:

1. Add to appropriate section in `fabric_dataflow_instructions.md`
2. Update "Version History" at bottom
3. Cross-reference in `fabric_dataflow_mcp.json` → "knowledgeBase"

### Adding New Skills

When you develop reusable procedures:

1. Create new skill in `fabric_dataflow_skills.md` under appropriate category
2. Include: When to Use, How to Execute, Expected Output, Key Points
3. Add corresponding tool to `fabric_dataflow_mcp.json` if applicable

### Updating MCP Configuration

When you add tools or resources:

1. Define tool schema in `fabric_dataflow_mcp.json` → "tools"
2. Add documentation resource if needed
3. Create corresponding skill in `fabric_dataflow_skills.md`
4. Update instructions with usage guidance

---

## Documentation URL Index

All three files reference these official resources:

### Microsoft Fabric & Power BI
- **Fabric Documentation**: https://learn.microsoft.com/fabric/
- **Power Query M Language**: https://learn.microsoft.com/powerquery-m/
- **Power BI REST API**: https://learn.microsoft.com/rest/api/power-bi/
- **Power BI Admin API**: https://api.powerbi.com/v1.0/myorg/admin
- **Scanner API**: https://learn.microsoft.com/rest/api/power-bi/admin/workspace-info-get-scan-result
- **Dataflow Definition API**: https://learn.microsoft.com/rest/api/fabric/dataflow/items/get-dataflow-definition
- **Scanner Setup Guide**: https://learn.microsoft.com/power-bi/admin/service-admin-metadata-scanning
- **Service Principal Setup**: https://learn.microsoft.com/power-bi/developer/embedded/embed-service-principal
- **Admin API Reference**: https://learn.microsoft.com/rest/api/power-bi/admin

### Development Tools
- **Git Credential Manager**: https://github.com/git-ecosystem/git-credential-manager
- **Python zipfile Module**: https://docs.python.org/3/library/zipfile.html

---

## Related Resources

### Toolkit Repository
- **GitHub**: https://github.com/jpmicrosoft/pqt_generator

### Related Projects
- **pbi_helper**: Power BI helper utilities and Scanner API tools
- **fabric_queries**: SQL queries and notebooks for Fabric workspaces

---

## Support and Contributions

### Getting Help

1. **Check instructions file** for conceptual guidance
2. **Check skills file** for code examples
3. **Review MCP configuration** for available tools
4. **Search documentation URLs** for official Microsoft guidance

### Contributing

When you develop new skills, patterns, or solutions:

1. Document in appropriate file (instructions, skills, or MCP)
2. Include working code examples
3. Add troubleshooting tips
4. Update this README if adding new file types

---

## Version History

- **Version 1.0** (2026-01-12): Initial release
  - Created comprehensive instruction file from session learnings
  - Developed technical skills library with code examples
  - Built MCP configuration with tools, prompts, and knowledge base
  - Added complete documentation URL references
  - Integrated all three files for cohesive AI agent support

---

## License

These configuration files are intended for use with the Fabric Dataflow Toolkit and related projects. Refer to individual project repositories for license information.
