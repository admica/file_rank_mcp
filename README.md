# File Rank MCP (Model Context Protocol) Server

A simple tool for ranking files in your codebase by importance and providing summaries with dependency tracking.

## Overview

This tool helps you keep track of which files in your project are most important, giving them a rating between 1 (most important) to 10 (least important). It also tracks file dependencies and provides summaries, helping you understand the codebase structure.

## Features

- Rank files on a scale from 1-10 (1 being most important)
- Track and visualize file dependencies (which files import which)
- Confidence-based dependency detection to minimize false positives
- Get summaries of files (with placeholder for LLM integration)
- Query rankings for individual files, directories, or the entire codebase
- Self-documenting API with discovery endpoints
- Simple stdio JSON interface

## Setup

1. Clone this repository
2. No special requirements - just uses standard Python libraries

## Usage

The tool communicates via JSON over stdio. You can use it directly or through the provided example script.

### Running the Example

```bash
python example_simple.py
```

### Manual Commands

#### Discovery Operations

1. **Get all capabilities**:
   ```json
   {"action": "get_capabilities"}
   ```
   This discovery endpoint returns comprehensive information about all available commands, their parameters, expected return values, and example usage.

2. **Get help for a specific command**:
   ```json
   {"action": "get_command_help", "command": "rank_file"}
   ```
   Returns detailed documentation for a specific command, including parameter descriptions, examples, and related commands.

#### File Ranking

3. **Rank a file**:
   ```json
   {"action": "rank_file", "file_path": "/path/to/file.py", "rank": 1, "summary": "Main entry point"}
   ```

4. **Get a file summary**:
   ```json
   {"action": "generate_summary", "file_path": "/path/to/file.py"}
   ```

5. **Get all ranked files**:
   ```json
   {"action": "get_all_files"}
   ```

6. **Get files in a directory**:
   ```json
   {"action": "get_files_by_dir", "directory": "/path/to/dir"}
   ```

7. **Remove a file from rankings**:
   ```json
   {"action": "delete_file", "file_path": "/path/to/file.py"}
   ```

#### Dependency Tracking

8. **Update dependencies for a file**:
   ```json
   {"action": "update_dependencies", "file_path": "/path/to/file.py"}
   ```

9. **Scan dependencies for all ranked files**:
   ```json
   {"action": "scan_all_dependencies"}
   ```

10. **Get dependencies for a file**:
    ```json
    {"action": "get_dependencies", "file_path": "/path/to/file.py"}
    ```

11. **Get files that depend on a specific file**:
    ```json
    {"action": "get_dependents", "file_path": "/path/to/file.py"}
    ```

12. **Visualize file dependencies as a tree**:
    ```json
    {"action": "visualize_dependencies", "file_path": "/path/to/file.py", "max_depth": 3}
    ```
    Returns an ASCII tree visualization of the dependency hierarchy, showing which files are imported at each level along with their importance rank.

## How It Works

The tool stores file rankings, summaries, and dependencies in a JSON file (`file_rankings.json`) which is automatically created in the same directory. This file is updated whenever you add, update, or remove file rankings.

### Data Structure

The rankings and dependencies are stored in a simple JSON structure:

```json
{
  "files": {
    "/path/to/file1.py": {
      "rank": 1,
      "summary": "This file is the main entry point."
    },
    "/path/to/file2.py": {
      "rank": 5,
      "summary": "This file contains utility functions."
    }
  },
  "dependencies": {
    "/path/to/file1.py": {
      "imports": ["/path/to/file2.py"],
      "possible_imports": ["some_external_package"]
    },
    "/path/to/file2.py": {
      "imports": []
    }
  }
}
```

### Dependency Detection

The tool analyzes source code to detect dependencies with a confidence-based approach:

- **Certain dependencies**: File paths the tool can verify with high confidence
- **Possible dependencies**: Imports the tool can detect but cannot resolve to actual files

This approach ensures that only verified dependencies are used for relationship tracking, avoiding false positives while still providing information about all detected imports.

Currently supported languages:
- Python: AST parsing for accurate import detection
- JavaScript/TypeScript: Regex patterns to detect import/require statements

When you get a file's information, its dependencies and the files that depend on it are included in the response.

### LLM Integration with Discovery Endpoints

The discovery endpoints (`get_capabilities` and `get_command_help`) make it easy for LLMs to understand:

1. **Available commands**: All commands are documented with parameters and return values
2. **Expected data formats**: Examples show exactly how to construct requests
3. **Command relationships**: Usage workflows show how commands work together
4. **Dependency tracking details**: Clear explanation of confidence levels
5. **Ranking system**: Explains the 1-10 ranking scale and its interpretation

This self-documenting API design means that LLMs can discover and learn how to use the tool effectively without prior knowledge.

## Integration with LLMs

The current implementation includes a placeholder for LLM integration. In a production environment, the `generate_summary` function would call an LLM to analyze the file and produce a meaningful summary.

LLMs can use the dependency information to better understand the project structure, providing more accurate suggestions about file importance and relationships.
