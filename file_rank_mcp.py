#!/usr/bin/env python3
import json
import os
import sys
from typing import Dict, List, Any, Optional
import mcp
from mcp.types import Resource, Tool

# DataManager: Handles data storage and manipulation
class DataManager:
    def __init__(self, data_file="file_rankings.json"):
        """Initialize with a path to the JSON data file."""
        self.data_file = data_file
        self.load_data()

    def load_data(self):
        """Load data from the JSON file, or initialize an empty structure."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {"files": {}}
        
    def save_data(self):
        """Save the current data to the JSON file."""
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def add_file(self, file_path: str, rank: int, summary: Optional[str] = None) -> Dict[str, Any]:
        """Add or update a file's ranking and summary."""
        if not os.path.exists(file_path):
            return {"error": f"File {file_path} not found."}
        
        if rank < 1 or rank > 10:
            return {"error": "Rank must be between 1 (most important) and 10 (least important)."}
        
        # Default summary if none provided
        if summary is None:
            summary = "No summary provided."
            
        self.data["files"][file_path] = {
            "rank": rank,
            "summary": summary
        }
        self.save_data()
        return {"success": f"Added/updated file {file_path} with rank {rank}"}
    
    def get_file(self, file_path: str) -> Dict[str, Any]:
        """Get a specific file's ranking and summary."""
        if file_path in self.data["files"]:
            return self.data["files"][file_path]
        return {"error": f"File {file_path} not found in rankings."}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Remove a file from rankings."""
        if file_path in self.data["files"]:
            del self.data["files"][file_path]
            self.save_data()
            return {"success": f"Removed file {file_path} from rankings."}
        return {"error": f"File {file_path} not found in rankings."}
    
    def get_files_by_dir(self, directory: str) -> Dict[str, Any]:
        """Get all ranked files in a directory."""
        if not os.path.exists(directory):
            return {"error": f"Directory {directory} not found."}
        
        result = {}
        for file_path, info in self.data["files"].items():
            if file_path.startswith(directory):
                result[file_path] = info
        
        if not result:
            return {"info": f"No ranked files found in directory {directory}."}
        return result
    
    def get_all_files(self) -> Dict[str, Any]:
        """Get all ranked files."""
        if not self.data["files"]:
            return {"info": "No ranked files found."}
        return self.data["files"]

# Main MCP implementation using server session
def main():
    print("Starting File Ranking MCP service...", file=sys.stderr)
    data_manager = DataManager()
    
    # Create server session
    session = mcp.ServerSession()
    
    # Register resources
    session.register_resource(
        path="/files",
        get=lambda: data_manager.get_all_files()
    )
    
    session.register_resource(
        path="/files/<file_path>",
        get=lambda file_path: data_manager.get_file(file_path)
    )
    
    session.register_resource(
        path="/directory/<directory>",
        get=lambda directory: data_manager.get_files_by_dir(directory)
    )
    
    # Register tools
    session.register_tool(
        name="rank_file",
        description="Rank a file's importance (1-10) and provide a summary",
        parameters={
            "file_path": {"type": "string", "description": "Full path to the file"},
            "rank": {"type": "integer", "description": "Importance rank (1-10, 1 is most important)"},
            "summary": {"type": "string", "optional": True, "description": "Brief summary of the file's purpose"}
        },
        function=lambda params: data_manager.add_file(
            params["file_path"], 
            params["rank"], 
            params.get("summary")
        )
    )
    
    session.register_tool(
        name="remove_file",
        description="Remove a file from the rankings",
        parameters={
            "file_path": {"type": "string", "description": "Full path to the file to remove"}
        },
        function=lambda params: data_manager.delete_file(params["file_path"])
    )
    
    session.register_tool(
        name="summarize_file",
        description="Request an LLM to generate a summary for a file",
        parameters={
            "file_path": {"type": "string", "description": "Full path to the file to summarize"}
        },
        function=lambda params: generate_summary(params["file_path"])
    )
    
    # Start the server
    session.start(mcp.StdioServerParameters())

def generate_summary(file_path: str) -> Dict[str, Any]:
    """Generate a summary for a file using LLM capabilities."""
    if not os.path.exists(file_path):
        return {"error": f"File {file_path} not found."}
    
    try:
        # In a real implementation, this would call the LLM
        # Since we're in Cursor, we can assume the LLM will handle this
        # For now, we'll just return a placeholder
        return {
            "summary": "This is a placeholder for LLM-generated summary. In actual use, this will be replaced with a real summary.",
            "file_path": file_path
        }
    except Exception as e:
        return {"error": f"Failed to generate summary: {str(e)}"}

if __name__ == "__main__":
    main()
