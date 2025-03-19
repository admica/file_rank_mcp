# File Rank Tool

A simple tool for ranking files in your codebase by importance and providing summaries.

## Overview

This tool helps you keep track of which files in your project are most important, giving them a rating between 1 (most important) to 10 (least important). It also allows you to generate and store file summaries.

## Features

- Rank files on a scale from 1-10 (1 being most important)
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

## How It Works

The tool stores file rankings and summaries in a JSON file (`file_rankings.json`) which is automatically created in the same directory. This file is updated whenever you add, update, or remove file rankings.

### Data Structure

The rankings are stored in a simple JSON structure:

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
  }
}
```

## Integration with LLMs

The current implementation includes a placeholder for LLM integration. In a production environment, the `generate_summary` function would call an LLM to analyze the file and produce a meaningful summary.
