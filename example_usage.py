#!/usr/bin/env python3
"""
Example of how to use the File Ranking MCP.
This script demonstrates various commands to interact with the MCP.
"""

import os
import json
import subprocess
import tempfile

# Helper function to run MCP commands
def run_mcp_command(cmd_dict):
    # Convert the command to JSON
    cmd_json = json.dumps(cmd_dict)
    
    # Run the MCP and pipe the command to it
    proc = subprocess.Popen(
        ["python", "file_rank_mcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send the command and get the response
    stdout, stderr = proc.communicate(cmd_json + "\n")
    
    # Parse and return the JSON response
    try:
        response = json.loads(stdout)
        return response
    except json.JSONDecodeError:
        print(f"Error parsing response: {stdout}")
        print(f"Stderr: {stderr}")
        return {"error": "Failed to parse response"}

def print_section(title):
    """Helper to print section titles"""
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50)

def print_response(response):
    """Helper to pretty print JSON responses"""
    print(json.dumps(response, indent=2))

# Get the path of this example script to use in examples
this_file = os.path.abspath(__file__)
mcp_file = os.path.abspath("file_rank_mcp.py")

# Example 1: Rank this example file
print_section("Ranking this example file")
response = run_mcp_command({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "call_tool",
    "params": {
        "name": "rank_file",
        "params": {
            "file_path": this_file,
            "rank": 3,
            "summary": "Example script demonstrating how to use the File Ranking MCP"
        }
    }
})
print_response(response)

# Example 2: Rank the MCP file itself
print_section("Ranking the MCP file")
response = run_mcp_command({
    "jsonrpc": "2.0",
    "id": 2,
    "method": "call_tool",
    "params": {
        "name": "rank_file",
        "params": {
            "file_path": mcp_file,
            "rank": 1,
            "summary": "Core MCP implementation for file ranking"
        }
    }
})
print_response(response)

# Example 3: Get a summary for a file
print_section("Getting an LLM summary for this file")
response = run_mcp_command({
    "jsonrpc": "2.0",
    "id": 3,
    "method": "call_tool",
    "params": {
        "name": "summarize_file",
        "params": {
            "file_path": this_file
        }
    }
})
print_response(response)

# Example 4: View all ranked files
print_section("Viewing all ranked files")
response = run_mcp_command({
    "jsonrpc": "2.0",
    "id": 4,
    "method": "read_resource",
    "params": {
        "path": "/files"
    }
})
print_response(response)

# Example 5: View a specific file's ranking
print_section("Viewing specific file ranking")
response = run_mcp_command({
    "jsonrpc": "2.0",
    "id": 5,
    "method": "read_resource",
    "params": {
        "path": f"/files/{this_file}"
    }
})
print_response(response)

# Example 6: View files in a directory
print_section("Viewing files in the current directory")
current_dir = os.path.dirname(os.path.abspath(__file__))
response = run_mcp_command({
    "jsonrpc": "2.0",
    "id": 6,
    "method": "read_resource",
    "params": {
        "path": f"/directory/{current_dir}"
    }
})
print_response(response)

# Example 7: Remove a file from rankings
print_section("Removing a file from rankings")
response = run_mcp_command({
    "jsonrpc": "2.0",
    "id": 7,
    "method": "call_tool",
    "params": {
        "name": "remove_file",
        "params": {
            "file_path": this_file
        }
    }
})
print_response(response)

print("\nExample script completed.") 