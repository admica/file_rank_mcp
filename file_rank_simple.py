#!/usr/bin/env python3
"""
File Ranking Tool

A simple command-line tool for ranking files in a codebase by importance
and providing summaries, with dependency tracking.
"""

import json
import os
import sys
import re
import ast
from typing import Dict, List, Any, Optional, Set, Tuple

class DependencyDetector:
    """Detects dependencies between files in different languages."""
    
    @staticmethod
    def detect_dependencies(file_path: str) -> List[str]:
        """Detect all imports in a file based on its extension."""
        if not os.path.exists(file_path):
            return []
            
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.py':
                return DependencyDetector._detect_python_imports(file_path)
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                return DependencyDetector._detect_js_imports(file_path)
            # Add other language detectors as needed
            return []
        except Exception as e:
            print(f"Error detecting dependencies in {file_path}: {str(e)}", file=sys.stderr)
            return []
    
    @staticmethod
    def _detect_python_imports(file_path: str) -> List[str]:
        """Parse Python file and extract imports."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                # Handle regular imports
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                # Handle from ... import ...
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # Convert module names to potential file paths
            dir_path = os.path.dirname(file_path)
            file_imports = []
            
            for imp in imports:
                # Convert dots to directory separators
                path_parts = imp.split('.')
                
                # Try both direct .py file and __init__.py in directory
                potential_paths = [
                    os.path.join(dir_path, *path_parts) + '.py',
                    os.path.join(dir_path, *path_parts, '__init__.py')
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        file_imports.append(os.path.abspath(path))
                        break
            
            return file_imports
        except Exception as e:
            print(f"Error parsing Python imports in {file_path}: {str(e)}", file=sys.stderr)
            return []
    
    @staticmethod
    def _detect_js_imports(file_path: str) -> List[str]:
        """Parse JavaScript/TypeScript file and extract imports."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for import statements and require calls
            import_regex = r'(?:import\s+.+\s+from\s+[\'"](.+?)[\'"])|(?:require\s*\(\s*[\'"](.+?)[\'"]\s*\))'
            matches = re.findall(import_regex, content)
            
            imports = []
            dir_path = os.path.dirname(file_path)
            
            for match in matches:
                # Each match is a tuple with groups for import or require
                import_path = match[0] or match[1]
                if not import_path or import_path.startswith('@'): 
                    # Skip package imports starting with @
                    continue
                
                # Handle relative imports
                if import_path.startswith('.'):
                    import_path = os.path.normpath(os.path.join(dir_path, import_path))
                
                # Try different extensions
                extensions = ['.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.ts']
                
                # If import already has an extension, just check if it exists
                if os.path.splitext(import_path)[1]:
                    if os.path.exists(import_path):
                        imports.append(os.path.abspath(import_path))
                    continue
                
                # Try different extensions
                for ext in extensions:
                    full_path = import_path + ext
                    if os.path.exists(full_path):
                        imports.append(os.path.abspath(full_path))
                        break
            
            return imports
        except Exception as e:
            print(f"Error parsing JS imports in {file_path}: {str(e)}", file=sys.stderr)
            return []

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
            self.data = {"files": {}, "dependencies": {}}
        
        # Ensure dependencies structure exists
        if "dependencies" not in self.data:
            self.data["dependencies"] = {}
        
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
            
        # Use absolute path for consistency
        abs_file_path = os.path.abspath(file_path)
        
        self.data["files"][abs_file_path] = {
            "rank": rank,
            "summary": summary
        }
        self.save_data()
        return {"success": f"Added/updated file {abs_file_path} with rank {rank}"}
    
    def get_file(self, file_path: str) -> Dict[str, Any]:
        """Get a specific file's ranking and summary."""
        abs_file_path = os.path.abspath(file_path)
        if abs_file_path in self.data["files"]:
            result = {abs_file_path: self.data["files"][abs_file_path]}
            
            # Add dependency information if available
            if abs_file_path in self.data["dependencies"]:
                result[abs_file_path]["dependencies"] = self.data["dependencies"][abs_file_path]
                
            # Find files that depend on this file
            dependents = []
            for dep_file, deps in self.data["dependencies"].items():
                if "imports" in deps and abs_file_path in deps["imports"]:
                    dependents.append(dep_file)
            
            if dependents:
                result[abs_file_path]["imported_by"] = dependents
                
            return result
        return {"error": f"File {abs_file_path} not found in rankings."}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Remove a file from rankings and dependencies."""
        abs_file_path = os.path.abspath(file_path)
        
        if abs_file_path in self.data["files"]:
            del self.data["files"][abs_file_path]
            
            # Also clean up dependencies
            if abs_file_path in self.data["dependencies"]:
                del self.data["dependencies"][abs_file_path]
            
            # Remove this file from other files' imports
            for _, deps in self.data["dependencies"].items():
                if "imports" in deps and abs_file_path in deps["imports"]:
                    deps["imports"].remove(abs_file_path)
            
            self.save_data()
            return {"success": f"Removed file {abs_file_path} from rankings."}
        return {"error": f"File {abs_file_path} not found in rankings."}
    
    def get_files_by_dir(self, directory: str) -> Dict[str, Any]:
        """Get all ranked files in a directory."""
        abs_dir = os.path.abspath(directory)
        if not os.path.exists(abs_dir):
            return {"error": f"Directory {abs_dir} not found."}
        
        result = {}
        for file_path, info in self.data["files"].items():
            if file_path.startswith(abs_dir):
                result[file_path] = info.copy()
                
                # Add dependency information if available
                if file_path in self.data["dependencies"]:
                    result[file_path]["dependencies"] = self.data["dependencies"][file_path]
        
        if not result:
            return {"info": f"No ranked files found in directory {abs_dir}."}
        return result
    
    def get_all_files(self) -> Dict[str, Any]:
        """Get all ranked files."""
        if not self.data["files"]:
            return {"info": "No ranked files found."}
        
        # Create a copy to avoid modifying the original data
        result = {"files": {}}
        
        for file_path, info in self.data["files"].items():
            result["files"][file_path] = info.copy()
            
            # Add dependency information if available
            if file_path in self.data["dependencies"]:
                result["files"][file_path]["dependencies"] = self.data["dependencies"][file_path]
        
        return result
    
    def generate_summary(self, file_path: str) -> Dict[str, Any]:
        """Generate a summary for a file."""
        abs_file_path = os.path.abspath(file_path)
        if not os.path.exists(abs_file_path):
            return {"error": f"File {abs_file_path} not found."}
        
        try:
            # In a real implementation, this would call an LLM
            # For now, we just return a placeholder
            summary = "This is a placeholder for a generated summary."
            
            # Update the file's summary if it exists in our data
            if abs_file_path in self.data["files"]:
                self.data["files"][abs_file_path]["summary"] = summary
                self.save_data()
                
            return {
                "file_path": abs_file_path,
                "summary": summary
            }
        except Exception as e:
            return {"error": f"Failed to generate summary: {str(e)}"}
    
    def update_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Update dependencies for a specific file."""
        abs_file_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_file_path):
            return {"error": f"File {abs_file_path} not found."}
        
        # Detect dependencies
        imports = DependencyDetector.detect_dependencies(abs_file_path)
        
        # Update the dependencies data
        if abs_file_path not in self.data["dependencies"]:
            self.data["dependencies"][abs_file_path] = {}
            
        self.data["dependencies"][abs_file_path]["imports"] = imports
        self.save_data()
        
        return {
            "success": f"Updated dependencies for {abs_file_path}",
            "imports_count": len(imports),
            "imports": imports
        }
    
    def scan_all_dependencies(self) -> Dict[str, Any]:
        """Scan all ranked files and update their dependencies."""
        updated_files = []
        for file_path in self.data["files"]:
            if os.path.exists(file_path):
                result = self.update_dependencies(file_path)
                if "success" in result:
                    updated_files.append(file_path)
        
        return {
            "success": f"Updated dependencies for {len(updated_files)} files",
            "updated_files": updated_files
        }
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Get all dependencies for a specific file."""
        abs_file_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_file_path):
            return {"error": f"File {abs_file_path} not found."}
            
        if abs_file_path not in self.data["dependencies"]:
            return {"info": f"No dependencies found for {abs_file_path}"}
            
        return {
            "file": abs_file_path,
            "dependencies": self.data["dependencies"][abs_file_path]
        }
    
    def get_file_dependents(self, file_path: str) -> Dict[str, Any]:
        """Get all files that depend on a specific file."""
        abs_file_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_file_path):
            return {"error": f"File {abs_file_path} not found."}
            
        dependents = []
        for dep_file, deps in self.data["dependencies"].items():
            if "imports" in deps and abs_file_path in deps["imports"]:
                dependent_info = {
                    "file": dep_file
                }
                
                # Add rank and summary if available
                if dep_file in self.data["files"]:
                    dependent_info.update(self.data["files"][dep_file])
                    
                dependents.append(dependent_info)
        
        if not dependents:
            return {"info": f"No files depend on {abs_file_path}"}
            
        return {
            "file": abs_file_path,
            "dependents": dependents
        }

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
        
        elif action == "update_dependencies":
            file_path = command_data.get("file_path")
            
            if not file_path:
                return {"error": "Missing required parameter: file_path"}
                
            return manager.update_dependencies(file_path)
            
        elif action == "scan_all_dependencies":
            return manager.scan_all_dependencies()
            
        elif action == "get_dependencies":
            file_path = command_data.get("file_path")
            
            if not file_path:
                return {"error": "Missing required parameter: file_path"}
                
            return manager.get_file_dependencies(file_path)
            
        elif action == "get_dependents":
            file_path = command_data.get("file_path")
            
            if not file_path:
                return {"error": "Missing required parameter: file_path"}
                
            return manager.get_file_dependents(file_path)
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