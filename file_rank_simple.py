#!/usr/bin/env python3
"""
File Ranking Tool

A simple command-line tool for ranking files in a codebase by importance
and providing summaries.
"""

import json
import os
import sys
import argparse
from typing import Dict, List, Any, Optional

class FileRankManager:
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
    
    def rank_file(self, file_path: str, rank: int, summary: Optional[str] = None) -> Dict[str, Any]:
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
            return {file_path: self.data["files"][file_path]}
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
        return {"files": self.data["files"]}

    def generate_summary(self, file_path: str) -> Dict[str, Any]:
        """Generate a summary for a file."""
        if not os.path.exists(file_path):
            return {"error": f"File {file_path} not found."}
        
        try:
            # In a real implementation, this would call an LLM
            # For now, we just return a placeholder
            summary = "This is a placeholder for a generated summary."
            
            # Update the file's summary if it exists in our data
            if file_path in self.data["files"]:
                self.data["files"][file_path]["summary"] = summary
                self.save_data()
                
            return {
                "file_path": file_path,
                "summary": summary
            }
        except Exception as e:
            return {"error": f"Failed to generate summary: {str(e)}"}

def process_command(manager, command):
    """Process a command from stdin and return a result."""
    try:
        command_data = json.loads(command)
        action = command_data.get("action")
        
        if action == "rank_file":
            file_path = command_data.get("file_path")
            rank = command_data.get("rank")
            summary = command_data.get("summary")
            
            if not file_path or not rank:
                return {"error": "Missing required parameters: file_path and rank"}
                
            return manager.rank_file(file_path, rank, summary)
            
        elif action == "get_file":
            file_path = command_data.get("file_path")
            
            if not file_path:
                return {"error": "Missing required parameter: file_path"}
                
            return manager.get_file(file_path)
            
        elif action == "delete_file":
            file_path = command_data.get("file_path")
            
            if not file_path:
                return {"error": "Missing required parameter: file_path"}
                
            return manager.delete_file(file_path)
            
        elif action == "get_files_by_dir":
            directory = command_data.get("directory")
            
            if not directory:
                return {"error": "Missing required parameter: directory"}
                
            return manager.get_files_by_dir(directory)
            
        elif action == "get_all_files":
            return manager.get_all_files()
            
        elif action == "generate_summary":
            file_path = command_data.get("file_path")
            
            if not file_path:
                return {"error": "Missing required parameter: file_path"}
                
            return manager.generate_summary(file_path)
            
        else:
            return {"error": f"Unknown action: {action}"}
            
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}
    except Exception as e:
        return {"error": f"Error processing command: {str(e)}"}

def main():
    """Main function to run the file ranking tool."""
    manager = FileRankManager()
    
    # Process one command per line from stdin
    for line in sys.stdin:
        if not line.strip():
            continue
            
        result = process_command(manager, line)
        print(json.dumps(result))
        sys.stdout.flush()

if __name__ == "__main__":
    print("Starting File Ranking service...", file=sys.stderr)
    main() 