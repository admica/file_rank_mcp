# File Rank Tool

A simple tool for ranking files in your codebase by importance and providing summaries with dependency tracking.

## Overview

This tool helps you keep track of which files in your project are most important, giving them a rating between 1 (most important) to 10 (least important). It also tracks file dependencies and provides summaries, helping you understand the codebase structure.

## Features

- Rank files on a scale from 1-10 (1 being most important)
- Track and visualize file dependencies (which files import which)
- Get summaries of files (with placeholder for LLM integration)
- Query rankings for individual files, directories, or the entire codebase
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

#### File Ranking

1. **Rank a file**:
   ```json
   {"action": "rank_file", "file_path": "/path/to/file.py", "rank": 1, "summary": "Main entry point"}
   ```

2. **Get a file summary**:
   ```json
   {"action": "generate_summary", "file_path": "/path/to/file.py"}
   ```

3. **Get all ranked files**:
   ```json
   {"action": "get_all_files"}
   ```

4. **Get files in a directory**:
   ```json
   {"action": "get_files_by_dir", "directory": "/path/to/dir"}
   ```

5. **Remove a file from rankings**:
   ```json
   {"action": "delete_file", "file_path": "/path/to/file.py"}
   ```

#### Dependency Tracking

6. **Update dependencies for a file**:
   ```json
   {"action": "update_dependencies", "file_path": "/path/to/file.py"}
   ```

7. **Scan dependencies for all ranked files**:
   ```json
   {"action": "scan_all_dependencies"}
   ```

8. **Get dependencies for a file**:
   ```json
   {"action": "get_dependencies", "file_path": "/path/to/file.py"}
   ```

9. **Get files that depend on a specific file**:
   ```json
   {"action": "get_dependents", "file_path": "/path/to/file.py"}
   ```

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
      "imports": ["/path/to/file2.py", "/path/to/file3.py"]
    },
    "/path/to/file2.py": {
      "imports": []
    }
  }
}
```

### Dependency Detection

The tool analyzes source code to detect dependencies automatically:

- For Python files: Uses AST parsing to analyze imports
- For JavaScript/TypeScript: Uses regex to detect import/require statements

When you get a file's information, its dependencies and the files that depend on it are included in the response.

## Integration with LLMs

The current implementation includes a placeholder for LLM integration. In a production environment, the `generate_summary` function would call an LLM to analyze the file and produce a meaningful summary.

LLMs can use the dependency information to better understand the project structure, providing more accurate suggestions about file importance and relationships.
