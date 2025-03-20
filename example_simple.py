#!/usr/bin/env python3
"""
Example of how to use the File Ranking Tool.
This script demonstrates various commands to interact with the tool.
"""

import os
import json
import subprocess
import tempfile

# Helper function to run a command
def run_command(cmd_dict):
    # Convert the command to JSON
    cmd_json = json.dumps(cmd_dict)
    
    # Run the tool and pipe the command to it
    proc = subprocess.Popen(
        ["python", "file_rank_simple.py"],
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
simple_file = os.path.abspath("file_rank_simple.py")

# Example 0: Get tool capabilities
print_section("Discovering tool capabilities")
response = run_command({
    "action": "get_capabilities"
})
print("Tool name:", response.get("tool_info", {}).get("name"))
print("Supported languages:", response.get("dependency_tracking", {}).get("supported_languages"))
print("\nAvailable command categories:")
for category, commands in response.get("commands", {}).items():
    print(f"- {category}: {', '.join(commands.keys())}")

# Example 0.1: Get help for a specific command
print_section("Getting help for the rank_file command")
response = run_command({
    "action": "get_command_help",
    "command": "rank_file"
})
print_response(response)

# Example 1: Rank this example file
print_section("Ranking this example file")
response = run_command({
    "action": "rank_file",
    "file_path": this_file,
    "rank": 3,
    "summary": "Example script demonstrating how to use the File Ranking Tool"
})
print_response(response)

# Example 2: Rank the simple file itself
print_section("Ranking the simple implementation file")
response = run_command({
    "action": "rank_file",
    "file_path": simple_file,
    "rank": 1,
    "summary": "Core implementation for file ranking"
})
print_response(response)

# Example 3: Update dependencies for this file
print_section("Updating dependencies for this file")
response = run_command({
    "action": "update_dependencies",
    "file_path": this_file
})
print_response(response)

# Example 4: Update dependencies for the simple implementation file
print_section("Updating dependencies for the implementation file")
response = run_command({
    "action": "update_dependencies",
    "file_path": simple_file
})
print_response(response)

# Example 5: Get dependencies for this file
print_section("Getting dependencies for this file")
response = run_command({
    "action": "get_dependencies",
    "file_path": this_file
})
print_response(response)

# Example 6: Get dependents of a file
print_section("Getting files that depend on the implementation file")
response = run_command({
    "action": "get_dependents",
    "file_path": simple_file
})
print_response(response)

# Example 7: Scan all dependencies
print_section("Scanning dependencies for all ranked files")
response = run_command({
    "action": "scan_all_dependencies"
})
print_response(response)

# Example 8: Get a summary for a file
print_section("Getting a summary for this file")
response = run_command({
    "action": "generate_summary",
    "file_path": this_file
})
print_response(response)

# Example 9: View all ranked files with dependencies
print_section("Viewing all ranked files with dependencies")
response = run_command({
    "action": "get_all_files"
})
print_response(response)

# Example 10: View a specific file's ranking and dependencies
print_section("Viewing specific file ranking with dependencies")
response = run_command({
    "action": "get_file",
    "file_path": this_file
})
print_response(response)

# Example 11: View files in a directory
print_section("Viewing files in the current directory")
current_dir = os.path.dirname(os.path.abspath(__file__))
response = run_command({
    "action": "get_files_by_dir",
    "directory": current_dir
})
print_response(response)

# Example 12: Visualize dependencies
print_section("Visualizing file dependencies")
response = run_command({
    "action": "visualize_dependencies",
    "file_path": simple_file,
    "max_depth": 2
})
print("Dependency tree:")
for line in response.get("dependency_tree", []):
    print(line)
    
print("\nDependents:")
for line in response.get("dependents", []):
    print(line)
    
print("\nDependency statistics:")
stats = response.get("stats", {})
print(f"- Certain dependencies: {stats.get('certain_dependencies', 0)}")
print(f"- Possible imports: {stats.get('possible_imports', 0)}")
print(f"- Files that depend on this: {stats.get('dependents_count', 0)}")

# Example 13: Remove a file from rankings
print_section("Removing a file from rankings")
response = run_command({
    "action": "delete_file",
    "file_path": this_file
})
print_response(response)

# Example 14: Try an invalid command to see help suggestion
print_section("Trying an invalid command")
response = run_command({
    "action": "unknown_command"
})
print_response(response)

print("\nExample script completed.") 