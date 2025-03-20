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
from datetime import datetime

# Force unbuffered stdout
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Add debug output to stderr (won't interfere with stdout JSON responses)
print(f"File Ranking MCP server starting up from {__file__}...", file=sys.stderr)
print(f"Python executable: {sys.executable}", file=sys.stderr)
print(f"Arguments: {sys.argv}", file=sys.stderr)
print(f"Working directory: {os.getcwd()}", file=sys.stderr)
print(f"Ready to receive commands...", file=sys.stderr)

# Global log file definition
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, "mcp_debug.log")

def log_debug(message):
    """Log a debug message to the log file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

class DependencyDetector:
    """Detects and tracks dependencies between files."""
    
    def __init__(self):
        """Initialize the dependency detector."""
        # Mapping of file extensions to their language-specific detection functions
        self.language_handlers = {
            '.py': self._detect_python_dependencies,
            '.js': self._detect_js_dependencies,
            '.jsx': self._detect_js_dependencies,
            '.ts': self._detect_js_dependencies,
            '.tsx': self._detect_js_dependencies,
            '.c': self._detect_cpp_dependencies,
            '.cpp': self._detect_cpp_dependencies,
            '.cc': self._detect_cpp_dependencies,
            '.cxx': self._detect_cpp_dependencies,
            '.h': self._detect_cpp_dependencies,
            '.hpp': self._detect_cpp_dependencies,
            '.hxx': self._detect_cpp_dependencies,
            '.rs': self._detect_rust_dependencies
        }
        
    def detect_dependencies(self, file_path: str, tracked_files: List[str] = None) -> Dict[str, List[str]]:
        """Detect dependencies for a file.
        
        Args:
            file_path: Path to the file to analyze
            tracked_files: List of files already being tracked in the system
            
        Returns:
            Dictionary with 'imports' and 'possible_imports' lists
        """
        if tracked_files is None:
            tracked_files = []
            
        abs_file_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_file_path):
            return {"imports": [], "possible_imports": []}
            
        file_ext = os.path.splitext(abs_file_path)[1].lower()
        
        # Default to empty results
        certain_dependencies = []
        possible_dependencies = []
        
        # Use language-specific handler if available
        if file_ext in self.language_handlers:
            try:
                certain, possible = self.language_handlers[file_ext](abs_file_path)
                certain_dependencies.extend(certain)
                possible_dependencies.extend(possible)
            except Exception as e:
                print(f"Error parsing {file_ext} imports in {abs_file_path}: {str(e)}")
                
        # Cross-language matching: check if any possible dependencies match tracked files
        enhanced_certain = certain_dependencies.copy()
        remaining_possible = []
        
        for dep in possible_dependencies:
            # See if this possible import matches any tracked file
            matched = False
            
            for tracked_file in tracked_files:
                # Check if the import name appears in the tracked file path
                # This is a simplistic approach that could be improved
                tracked_basename = os.path.basename(tracked_file)
                tracked_stem = os.path.splitext(tracked_basename)[0]
                
                # For Python/JS-style imports that might match directory structures
                parts = dep.split('.')
                last_part = parts[-1] if parts else ""
                
                if (tracked_stem == dep or  # Direct match
                    tracked_stem == last_part):  # Match the last part of a dotted import
                    enhanced_certain.append(tracked_file)
                    matched = True
                    break
                    
                # Handle path-style imports (for JS/TS relative imports and C/C++ includes)
                if dep.endswith(tracked_basename) or dep == tracked_basename:
                    enhanced_certain.append(tracked_file)
                    matched = True
                    break
            
            if not matched:
                remaining_possible.append(dep)
                
        return {
            "imports": sorted(list(set(enhanced_certain))),
            "possible_imports": sorted(list(set(remaining_possible)))
        }
    
    def _detect_python_dependencies(self, file_path: str) -> Tuple[List[str], List[str]]:
        """Detect dependencies in a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Tuple of (certain_dependencies, possible_dependencies)
        """
        certain_dependencies = []
        possible_dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Handle standard imports
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_path = name.name
                        possible_dependencies.append(module_path)
                        
                # Handle from X import Y
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module_path = node.module
                    possible_dependencies.append(module_path)
                    
            # Try to resolve local imports to absolute file paths
            for module in possible_dependencies.copy():
                # Convert dots to directory separators
                rel_path = module.replace('.', os.sep)
                
                # Try different file extensions
                for ext in ['.py']:
                    # Check if the file exists relative to the current file
                    current_dir = os.path.dirname(file_path)
                    abs_import_path = os.path.abspath(os.path.join(current_dir, rel_path + ext))
                    
                    if os.path.exists(abs_import_path):
                        certain_dependencies.append(abs_import_path)
                        possible_dependencies.remove(module)
                        break
                        
        except Exception as e:
            print(f"Error parsing Python imports in {file_path}: {str(e)}")
            
        return certain_dependencies, possible_dependencies
    
    def _detect_js_dependencies(self, file_path: str) -> Tuple[List[str], List[str]]:
        """Detect dependencies in a JavaScript/TypeScript file.
        
        Args:
            file_path: Path to the JavaScript/TypeScript file
            
        Returns:
            Tuple of (certain_dependencies, possible_dependencies)
        """
        certain_dependencies = []
        possible_dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Pattern for both require() and ES6 imports
            # Captures the module path in the first group
            import_patterns = [
                r'(?:import|require)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',  # require('./module')
                r'from\s+[\'"]([^\'"]+)[\'"]',  # from './module'
                r'import\s+(?:[^;]*\s+from\s+)?[\'"]([^\'"]+)[\'"]'  # import './module'
            ]
            
            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    module_path = match.group(1)
                    if module_path:
                        # Assume it's a possible dependency first
                        possible_dependencies.append(module_path)
                        
                        # Try to resolve relative imports
                        if module_path.startswith(('./', '../', '/')):
                            # Remove leading ./ if present
                            if module_path.startswith('./'):
                                module_path = module_path[2:]
                            
                            # Get the directory of the current file
                            current_dir = os.path.dirname(file_path)
                            
                            # List of possible extensions to try
                            extensions = ['', '.js', '.jsx', '.ts', '.tsx', '.json']
                            
                            # Also try index files in directories
                            index_files = [
                                os.path.join(module_path, 'index.js'),
                                os.path.join(module_path, 'index.jsx'),
                                os.path.join(module_path, 'index.ts'),
                                os.path.join(module_path, 'index.tsx')
                            ]
                            
                            # Try all possible file paths
                            for ext in extensions:
                                abs_import_path = os.path.abspath(os.path.join(current_dir, module_path + ext))
                                if os.path.exists(abs_import_path):
                                    certain_dependencies.append(abs_import_path)
                                    possible_dependencies.remove(match.group(1))
                                    break
                                    
                            # If not found, try index files
                            if match.group(1) in possible_dependencies:
                                for index_file in index_files:
                                    abs_import_path = os.path.abspath(os.path.join(current_dir, index_file))
                                    if os.path.exists(abs_import_path):
                                        certain_dependencies.append(abs_import_path)
                                        possible_dependencies.remove(match.group(1))
                                        break
            
        except Exception as e:
            print(f"Error parsing JavaScript/TypeScript imports in {file_path}: {str(e)}")
            
        return certain_dependencies, possible_dependencies
            
    def _detect_cpp_dependencies(self, file_path: str) -> Tuple[List[str], List[str]]:
        """Detect dependencies in C/C++ files.
        
        Args:
            file_path: Path to the C/C++ file
            
        Returns:
            Tuple of (certain_dependencies, possible_dependencies)
        """
        certain_dependencies = []
        possible_dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Pattern for system includes: #include <header.h>
            system_include_pattern = r'#\s*include\s*<([^>]+)>'
            
            # Pattern for local includes: #include "header.h"
            local_include_pattern = r'#\s*include\s*"([^"]+)"'
            
            # Find system includes (standard libraries, etc.)
            for match in re.finditer(system_include_pattern, content):
                header = match.group(1)
                if header:
                    possible_dependencies.append(header)
                    
            # Find and resolve local includes
            for match in re.finditer(local_include_pattern, content):
                header = match.group(1)
                if header:
                    # First mark as possible
                    possible_dependencies.append(header)
                    
                    # Try to resolve to a file path
                    current_dir = os.path.dirname(file_path)
                    abs_include_path = os.path.abspath(os.path.join(current_dir, header))
                    
                    if os.path.exists(abs_include_path):
                        certain_dependencies.append(abs_include_path)
                        possible_dependencies.remove(header)
                        continue
                    
                    # If not found directly, try common include directories
                    # For a real implementation, you'd want to extract include paths from build files
                    include_dirs = [
                        os.path.join(os.path.dirname(current_dir), 'include'),
                        os.path.join(current_dir, 'include')
                    ]
                    
                    for include_dir in include_dirs:
                        abs_include_path = os.path.abspath(os.path.join(include_dir, header))
                        if os.path.exists(abs_include_path):
                            certain_dependencies.append(abs_include_path)
                            possible_dependencies.remove(header)
                            break
                    
        except Exception as e:
            print(f"Error parsing C/C++ includes in {file_path}: {str(e)}")
            
        return certain_dependencies, possible_dependencies

    def _detect_rust_dependencies(self, file_path: str) -> Tuple[List[str], List[str]]:
        """Detect dependencies in a Rust file.
        
        Args:
            file_path: Path to the Rust file
            
        Returns:
            Tuple of (certain_dependencies, possible_dependencies)
        """
        certain_dependencies = []
        possible_dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Pattern for use statements
            use_pattern = r'use\s+([^;]+);'
            
            # Pattern for extern crate statements
            extern_crate_pattern = r'extern\s+crate\s+([^;]+);'
            
            # Pattern for mod statements
            mod_pattern = r'mod\s+([^{;]+)[{;]'
            
            # Find all use statements
            for match in re.finditer(use_pattern, content):
                import_path = match.group(1).strip()
                if import_path:
                    # Handle paths like std::io, crate::module, etc.
                    possible_dependencies.append(import_path)
            
            # Find all extern crate statements
            for match in re.finditer(extern_crate_pattern, content):
                crate_name = match.group(1).strip()
                if crate_name:
                    possible_dependencies.append(crate_name)
            
            # Find all mod statements
            for match in re.finditer(mod_pattern, content):
                module_name = match.group(1).strip()
                if module_name:
                    # Rust modules can be in the same directory with module_name.rs
                    # or in a subdirectory module_name/mod.rs
                    current_dir = os.path.dirname(file_path)
                    
                    # Check for module_name.rs
                    module_file = os.path.join(current_dir, f"{module_name}.rs")
                    if os.path.exists(module_file):
                        certain_dependencies.append(os.path.abspath(module_file))
                        continue
                    
                    # Check for module_name/mod.rs
                    module_dir_file = os.path.join(current_dir, module_name, "mod.rs")
                    if os.path.exists(module_dir_file):
                        certain_dependencies.append(os.path.abspath(module_dir_file))
                        continue
                    
                    # If we couldn't find the file, add as a possible dependency
                    possible_dependencies.append(module_name)
                    
        except Exception as e:
            print(f"Error parsing Rust imports in {file_path}: {str(e)}")
            
        return certain_dependencies, possible_dependencies

class FileRankManager:
    def __init__(self, data_file="file_rankings.json"):
        """Initialize with a path to the JSON data file."""
        self.data_file = data_file
        self.load_data()
        self.exit_requested = False  # Flag for MCP exit request

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
        """Analyze a file and update its dependencies.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with the results
        """
        abs_file_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_file_path):
            return {"error": f"File {abs_file_path} not found"}
            
        # Initialize the dependencies structure if needed
        if abs_file_path not in self.data["dependencies"]:
            self.data["dependencies"][abs_file_path] = {}
            
        # Get all tracked files to help with cross-file matching
        tracked_files = list(self.data["files"].keys())
        
        # Create an instance of DependencyDetector if needed
        if not hasattr(self, 'dependency_detector'):
            self.dependency_detector = DependencyDetector()
            
        # Detect dependencies
        result = self.dependency_detector.detect_dependencies(abs_file_path, tracked_files)
        
        # Update our data structure
        self.data["dependencies"][abs_file_path]["imports"] = result["imports"]
        self.data["dependencies"][abs_file_path]["possible_imports"] = result["possible_imports"]
        
        # Save the updated data
        self.save_data()
        
        return {
            "success": f"Updated dependencies for {abs_file_path}",
            "imports_count": len(result["imports"]),
            "imports": result["imports"],
            "possible_count": len(result["possible_imports"]),
            "possible_imports": result["possible_imports"]
        }
        
    def scan_all_dependencies(self) -> Dict[str, Any]:
        """Scan all ranked files and update their dependencies.
        
        Returns:
            Dictionary with the results
        """
        if not self.data["files"]:
            return {"info": "No files to scan"}
            
        # Get all tracked files for better cross-file matching
        tracked_files = list(self.data["files"].keys())
        
        # Create an instance of DependencyDetector if needed
        if not hasattr(self, 'dependency_detector'):
            self.dependency_detector = DependencyDetector()
            
        updated_files = []
        total_imports = 0
        total_possible = 0
        
        for file_path in self.data["files"].keys():
            if not os.path.exists(file_path):
                continue
                
            # Initialize the dependencies structure if needed
            if file_path not in self.data["dependencies"]:
                self.data["dependencies"][file_path] = {}
                
            # Detect dependencies
            result = self.dependency_detector.detect_dependencies(file_path, tracked_files)
            
            # Update our data structure
            self.data["dependencies"][file_path]["imports"] = result["imports"]
            self.data["dependencies"][file_path]["possible_imports"] = result["possible_imports"]
            
            updated_files.append(file_path)
            total_imports += len(result["imports"])
            total_possible += len(result["possible_imports"])
            
        # Save the updated data
        self.save_data()
        
        return {
            "success": f"Updated dependencies for {len(updated_files)} files",
            "updated_files": updated_files,
            "total_imports": total_imports,
            "total_possible_imports": total_possible
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
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Return all supported commands and their descriptions.
        
        This discovery endpoint helps LLMs understand what the tool can do.
        """
        capabilities = {
            "tool_info": {
                "name": "File Ranking Tool",
                "version": "1.0.0",
                "description": "Tool for ranking files by importance and tracking dependencies"
            },
            "ranking_system": {
                "scale": "1-10",
                "interpretation": "Lower numbers (1) indicate more important files, higher numbers (10) indicate less important files"
            },
            "dependency_tracking": {
                "supported_languages": ["Python", "JavaScript", "TypeScript", "C", "C++", "Rust"],
                "confidence_levels": {
                    "certain": "File paths that exist and are confirmed dependencies",
                    "possible": "Import statements that couldn't be resolved to existing files"
                }
            },
            "commands": {
                "file_operations": {
                    "rank_file": {
                        "description": "Assign an importance rank to a file",
                        "parameters": {
                            "file_path": "Path to the file to rank (required)",
                            "rank": "Importance rank from 1-10, lower is more important (required)",
                            "summary": "Brief description of the file's purpose (optional)"
                        },
                        "example": {
                            "action": "rank_file",
                            "file_path": "/path/to/file.py",
                            "rank": 1,
                            "summary": "Main entry point for the application"
                        },
                        "returns": {
                            "success": "Confirmation message if successful",
                            "error": "Error message if unsuccessful"
                        }
                    },
                    "delete_file": {
                        "description": "Remove a file from the rankings",
                        "parameters": {
                            "file_path": "Path to the file to remove (required)"
                        },
                        "example": {
                            "action": "delete_file",
                            "file_path": "/path/to/file.py"
                        },
                        "returns": {
                            "success": "Confirmation message if successful",
                            "error": "Error message if unsuccessful"
                        }
                    },
                    "generate_summary": {
                        "description": "Generate a summary for a file (placeholder for LLM integration)",
                        "parameters": {
                            "file_path": "Path to the file to summarize (required)"
                        },
                        "example": {
                            "action": "generate_summary",
                            "file_path": "/path/to/file.py"
                        },
                        "returns": {
                            "file_path": "Path to the summarized file",
                            "summary": "Generated summary text",
                            "error": "Error message if unsuccessful"
                        }
                    }
                },
                "query_operations": {
                    "get_file": {
                        "description": "Get information about a specific file",
                        "parameters": {
                            "file_path": "Path to the file to query (required)"
                        },
                        "example": {
                            "action": "get_file",
                            "file_path": "/path/to/file.py"
                        },
                        "returns": {
                            "file_info": "File ranking and summary",
                            "dependencies": "Files this file imports (if available)",
                            "imported_by": "Files that import this file (if any)",
                            "error": "Error message if unsuccessful"
                        }
                    },
                    "get_files_by_dir": {
                        "description": "Get all ranked files in a directory",
                        "parameters": {
                            "directory": "Path to the directory to query (required)"
                        },
                        "example": {
                            "action": "get_files_by_dir",
                            "directory": "/path/to/dir"
                        },
                        "returns": {
                            "file_list": "Dictionary of files with their rankings and summaries",
                            "error": "Error message if unsuccessful"
                        }
                    },
                    "get_all_files": {
                        "description": "Get all ranked files in the system",
                        "parameters": {},
                        "example": {
                            "action": "get_all_files"
                        },
                        "returns": {
                            "files": "Dictionary of all files with their rankings and summaries",
                            "info": "Informational message if no files found"
                        }
                    }
                },
                "dependency_operations": {
                    "update_dependencies": {
                        "description": "Analyze a file and update its dependencies",
                        "parameters": {
                            "file_path": "Path to the file to analyze (required)"
                        },
                        "example": {
                            "action": "update_dependencies",
                            "file_path": "/path/to/file.py"
                        },
                        "returns": {
                            "success": "Confirmation message if successful",
                            "imports_count": "Number of certain dependencies found",
                            "imports": "List of certain dependencies",
                            "possible_count": "Number of possible imports found",
                            "possible_imports": "List of imports that couldn't be resolved",
                            "error": "Error message if unsuccessful"
                        }
                    },
                    "scan_all_dependencies": {
                        "description": "Scan all ranked files and update their dependencies",
                        "parameters": {},
                        "example": {
                            "action": "scan_all_dependencies"
                        },
                        "returns": {
                            "success": "Confirmation message with count of updated files",
                            "updated_files": "List of files that were updated",
                            "total_imports": "Total number of certain dependencies found",
                            "total_possible_imports": "Total number of possible imports found"
                        }
                    },
                    "get_dependencies": {
                        "description": "Get dependencies for a specific file",
                        "parameters": {
                            "file_path": "Path to the file to query (required)"
                        },
                        "example": {
                            "action": "get_dependencies",
                            "file_path": "/path/to/file.py"
                        },
                        "returns": {
                            "file": "Path to the queried file",
                            "dependencies": "Dictionary with imports and possible_imports",
                            "error": "Error message if unsuccessful or file not found"
                        }
                    },
                    "get_dependents": {
                        "description": "Get files that depend on a specific file",
                        "parameters": {
                            "file_path": "Path to the file to query (required)"
                        },
                        "example": {
                            "action": "get_dependents",
                            "file_path": "/path/to/file.py"
                        },
                        "returns": {
                            "file": "Path to the queried file",
                            "dependents": "List of files that import this file",
                            "error": "Error message if unsuccessful or file not found"
                        }
                    },
                    "visualize_dependencies": {
                        "description": "Generate a text-based tree visualization of a file's dependencies",
                        "parameters": {
                            "file_path": "Path to the file to visualize (required)",
                            "max_depth": "Maximum depth to traverse in the dependency tree (optional, default: 3)"
                        },
                        "example": {
                            "action": "visualize_dependencies",
                            "file_path": "/path/to/file.py",
                            "max_depth": 3
                        },
                        "returns": {
                            "file": "Path to the queried file",
                            "dependency_tree": "Lines of ASCII tree visualization",
                            "dependents": "List of files that depend on this file",
                            "stats": "Statistics about dependencies",
                            "error": "Error message if unsuccessful"
                        }
                    }
                },
                "discovery": {
                    "get_capabilities": {
                        "description": "Get information about all available commands",
                        "parameters": {},
                        "example": {
                            "action": "get_capabilities"
                        },
                        "returns": "This capabilities document"
                    },
                    "get_command_help": {
                        "description": "Get detailed help for a specific command",
                        "parameters": {
                            "command": "Name of the command to get help for (required)"
                        },
                        "example": {
                            "action": "get_command_help",
                            "command": "rank_file"
                        },
                        "returns": {
                            "command_info": "Detailed documentation for the specified command",
                            "error": "Error message if command not found"
                        }
                    }
                }
            },
            "usage_workflow": {
                "basic_workflow": [
                    "1. Use rank_file to assign importance to files",
                    "2. Use update_dependencies or scan_all_dependencies to detect file relationships",
                    "3. Use query commands to explore the codebase structure",
                    "4. Use visualize_dependencies to see dependency trees"
                ],
                "important_notes": [
                    "File ranking and dependency scanning are separate operations",
                    "Rankings are subjective (1-10) with 1 being most important",
                    "Only certain dependencies are used for relationship tracking",
                    "All paths should be absolute or relative to current directory"
                ]
            }
        }
        
        return capabilities
        
    def get_command_help(self, command: str) -> Dict[str, Any]:
        """Get detailed help for a specific command."""
        # Define help data for each command
        command_help = {
            "rank_file": {
                "command": "rank_file",
                "description": "Assign an importance rank to a file",
                "detailed_description": (
                    "This command lets you rank a file's importance on a scale from 1 to 10, "
                    "where 1 is the most important and 10 is the least important. "
                    "You can also provide a summary describing what the file does."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to rank",
                        "required": True,
                        "type": "string"
                    },
                    "rank": {
                        "description": "Importance rank from 1 (most important) to 10 (least important)",
                        "required": True,
                        "type": "integer",
                        "constraints": "Must be between 1 and 10"
                    },
                    "summary": {
                        "description": "Brief description of the file's purpose",
                        "required": False,
                        "type": "string",
                        "default": "No summary provided."
                    }
                },
                "examples": [
                    {
                        "description": "Rank a file as very important with a summary",
                        "command": {
                            "action": "rank_file",
                            "file_path": "/path/to/main.py",
                            "rank": 1,
                            "summary": "Main application entry point"
                        }
                    },
                    {
                        "description": "Rank a file as less important without a summary",
                        "command": {
                            "action": "rank_file",
                            "file_path": "/path/to/utils.py",
                            "rank": 7
                        }
                    }
                ],
                "return_values": {
                    "success": "String confirming the file was ranked successfully",
                    "error": "String explaining what went wrong if the command failed"
                },
                "related_commands": ["get_file", "update_dependencies"]
            },
            "update_dependencies": {
                "command": "update_dependencies",
                "description": "Analyze a file and update its dependencies",
                "detailed_description": (
                    "This command analyzes the source code of a file to detect import statements "
                    "and categorizes dependencies into 'certain' (verified file paths) and "
                    "'possible' (imports that couldn't be resolved to existing files). "
                    "Currently supports Python, JavaScript, and TypeScript files."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to analyze",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Update dependencies for a Python file",
                        "command": {
                            "action": "update_dependencies",
                            "file_path": "/path/to/module.py"
                        }
                    }
                ],
                "return_values": {
                    "success": "Confirmation message if successful",
                    "imports_count": "Number of certain dependencies found",
                    "imports": "List of certain dependencies (verified file paths)",
                    "possible_count": "Number of possible imports found",
                    "possible_imports": "List of imports that couldn't be resolved to files",
                    "error": "Error message if unsuccessful"
                },
                "related_commands": ["scan_all_dependencies", "get_dependencies", "get_dependents"]
            },
            "delete_file": {
                "command": "delete_file", 
                "description": "Remove a file from the rankings",
                "detailed_description": (
                    "This command removes a file from the rankings and cleans up any dependency "
                    "references to it. The file itself is not deleted from the filesystem, "
                    "only its entry in the rankings database."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to remove from rankings",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Remove a file from rankings",
                        "command": {
                            "action": "delete_file",
                            "file_path": "/path/to/obsolete_file.py"
                        }
                    }
                ],
                "return_values": {
                    "success": "Confirmation message if successful",
                    "error": "Error message if unsuccessful or file not found in rankings"
                },
                "related_commands": ["rank_file", "get_all_files"]
            },
            "get_file": {
                "command": "get_file",
                "description": "Get information about a specific file",
                "detailed_description": (
                    "This command retrieves the ranking, summary, and dependency information "
                    "for a specific file. It includes both the files this file imports and "
                    "the files that import it (dependents)."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to query",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Get information about a file",
                        "command": {
                            "action": "get_file",
                            "file_path": "/path/to/file.py"
                        }
                    }
                ],
                "return_values": {
                    "file_info": "Dictionary containing the file's rank and summary",
                    "dependencies": "Dictionary of files this file imports (if scanned)",
                    "imported_by": "List of files that import this file (if any)",
                    "error": "Error message if unsuccessful or file not found"
                },
                "related_commands": ["get_dependencies", "get_dependents"]
            },
            "get_all_files": {
                "command": "get_all_files",
                "description": "Get all ranked files in the system",
                "detailed_description": (
                    "This command retrieves information about all files that have been ranked, "
                    "including their rankings, summaries, and dependency information if available."
                ),
                "parameters": {},
                "examples": [
                    {
                        "description": "Get all ranked files",
                        "command": {
                            "action": "get_all_files"
                        }
                    }
                ],
                "return_values": {
                    "files": "Dictionary of all files with their rankings and summaries",
                    "info": "Informational message if no files found"
                },
                "related_commands": ["get_files_by_dir", "get_file"]
            },
            "get_files_by_dir": {
                "command": "get_files_by_dir",
                "description": "Get all ranked files in a directory",
                "detailed_description": (
                    "This command retrieves information about all ranked files within a specific "
                    "directory, including their rankings, summaries, and dependency information "
                    "if available."
                ),
                "parameters": {
                    "directory": {
                        "description": "Path to the directory to query",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Get all ranked files in a directory",
                        "command": {
                            "action": "get_files_by_dir",
                            "directory": "/path/to/src"
                        }
                    }
                ],
                "return_values": {
                    "file_list": "Dictionary of files with their rankings and summaries",
                    "info": "Informational message if no ranked files found in directory",
                    "error": "Error message if directory not found"
                },
                "related_commands": ["get_all_files", "get_file"]
            },
            "generate_summary": {
                "command": "generate_summary",
                "description": "Generate a summary for a file",
                "detailed_description": (
                    "This command generates a summary for a file. In the current implementation, "
                    "it returns a placeholder message, but in a production environment, this would "
                    "call an LLM to analyze the file and generate a meaningful summary."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to summarize",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Generate a summary for a file",
                        "command": {
                            "action": "generate_summary",
                            "file_path": "/path/to/file.py"
                        }
                    }
                ],
                "return_values": {
                    "file_path": "Path to the summarized file",
                    "summary": "Generated summary text",
                    "error": "Error message if unsuccessful or file not found"
                },
                "related_commands": ["rank_file"]
            },
            "scan_all_dependencies": {
                "command": "scan_all_dependencies",
                "description": "Scan all ranked files and update their dependencies",
                "detailed_description": (
                    "This command iterates through all ranked files and updates their dependencies "
                    "by analyzing import statements. It's a convenient way to build a complete "
                    "dependency graph for the entire codebase."
                ),
                "parameters": {},
                "examples": [
                    {
                        "description": "Scan dependencies for all ranked files",
                        "command": {
                            "action": "scan_all_dependencies"
                        }
                    }
                ],
                "return_values": {
                    "success": "Confirmation message with count of updated files",
                    "updated_files": "List of files that were updated",
                    "total_imports": "Total number of certain dependencies found",
                    "total_possible_imports": "Total number of possible imports found"
                },
                "related_commands": ["update_dependencies"]
            },
            "get_dependencies": {
                "command": "get_dependencies",
                "description": "Get dependencies for a specific file",
                "detailed_description": (
                    "This command retrieves the dependencies for a specific file, including both "
                    "'certain' dependencies (verified file paths) and 'possible' imports that "
                    "couldn't be resolved to existing files."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to query",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Get dependencies for a file",
                        "command": {
                            "action": "get_dependencies",
                            "file_path": "/path/to/file.py"
                        }
                    }
                ],
                "return_values": {
                    "file": "Path to the queried file",
                    "dependencies": "Dictionary with imports and possible_imports",
                    "info": "Informational message if no dependencies found",
                    "error": "Error message if unsuccessful or file not found"
                },
                "related_commands": ["get_dependents", "update_dependencies"]
            },
            "get_dependents": {
                "command": "get_dependents",
                "description": "Get files that depend on a specific file",
                "detailed_description": (
                    "This command finds all files that import or depend on a specific file. "
                    "It helps identify which parts of the codebase rely on a given file, "
                    "which is useful for understanding impact when making changes."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to query",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Find files that depend on a specific file",
                        "command": {
                            "action": "get_dependents",
                            "file_path": "/path/to/util.py"
                        }
                    }
                ],
                "return_values": {
                    "file": "Path to the queried file",
                    "dependents": "List of files that import this file",
                    "info": "Informational message if no files depend on this file",
                    "error": "Error message if unsuccessful or file not found"
                },
                "related_commands": ["get_dependencies", "update_dependencies"]
            },
            "get_capabilities": {
                "command": "get_capabilities",
                "description": "Get information about all available commands",
                "detailed_description": (
                    "This discovery endpoint returns comprehensive information about the tool, "
                    "including all available commands, their parameters, expected return values, "
                    "and example usage. It helps LLMs understand what the tool can do."
                ),
                "parameters": {},
                "examples": [
                    {
                        "description": "Get all capabilities",
                        "command": {
                            "action": "get_capabilities"
                        }
                    }
                ],
                "return_values": {
                    "tool_info": "Basic information about the tool",
                    "ranking_system": "Explanation of the ranking scale",
                    "dependency_tracking": "Information about supported languages and confidence levels",
                    "commands": "Detailed information about all available commands",
                    "usage_workflow": "Suggested workflow for using the tool"
                },
                "related_commands": ["get_command_help"]
            },
            "get_command_help": {
                "command": "get_command_help",
                "description": "Get detailed help for a specific command",
                "detailed_description": (
                    "This command provides detailed documentation for a specific command, "
                    "including parameter descriptions, examples, and related commands. "
                    "It's useful for learning how to use a particular command."
                ),
                "parameters": {
                    "command": {
                        "description": "Name of the command to get help for",
                        "required": True,
                        "type": "string"
                    }
                },
                "examples": [
                    {
                        "description": "Get help for the rank_file command",
                        "command": {
                            "action": "get_command_help",
                            "command": "rank_file"
                        }
                    }
                ],
                "return_values": {
                    "command": "Name of the command",
                    "description": "Brief description of the command",
                    "detailed_description": "Detailed explanation of the command's purpose and behavior",
                    "parameters": "Dictionary of parameters with descriptions",
                    "examples": "Example usage of the command",
                    "return_values": "Description of what the command returns",
                    "related_commands": "List of related commands",
                    "error": "Error message if command not found"
                },
                "related_commands": ["get_capabilities"]
            },
            "visualize_dependencies": {
                "command": "visualize_dependencies",
                "description": "Generate a text-based tree visualization of a file's dependencies",
                "detailed_description": (
                    "This command creates an ASCII tree visualization of a file's dependencies, "
                    "showing the hierarchical relationship between files. It includes file ranks "
                    "where available and lists files that depend on the queried file. The tree "
                    "is limited to a specified maximum depth to avoid excessive output for "
                    "large dependency chains."
                ),
                "parameters": {
                    "file_path": {
                        "description": "Path to the file to visualize",
                        "required": True,
                        "type": "string"
                    },
                    "max_depth": {
                        "description": "Maximum depth to traverse in the dependency tree",
                        "required": False,
                        "type": "integer",
                        "default": 3
                    }
                },
                "examples": [
                    {
                        "description": "Visualize file dependencies with default depth",
                        "command": {
                            "action": "visualize_dependencies",
                            "file_path": "/path/to/file.py"
                        }
                    },
                    {
                        "description": "Visualize deeper dependency chain",
                        "command": {
                            "action": "visualize_dependencies",
                            "file_path": "/path/to/file.py",
                            "max_depth": 5
                        }
                    }
                ],
                "return_values": {
                    "file": "Path to the queried file",
                    "dependency_tree": "Lines of ASCII tree visualization showing dependencies",
                    "dependents": "List of files that depend on this file with their ranks",
                    "stats": "Statistics about dependencies including counts and depth",
                    "info": "Informational message if no dependencies found",
                    "error": "Error message if unsuccessful"
                },
                "related_commands": ["get_dependencies", "get_dependents", "update_dependencies"]
            }
        }
        
        # If we don't have specific help for this command, generate basic help from capabilities
        if command not in command_help:
            # Look through all command categories in get_capabilities result
            capabilities = self.get_capabilities()
            for category_name, category in capabilities["commands"].items():
                if command in category:
                    cmd_info = category[command]
                    return {
                        "command": command,
                        "description": cmd_info.get("description", "No description available"),
                        "parameters": cmd_info.get("parameters", {}),
                        "example": cmd_info.get("example", {}),
                        "returns": cmd_info.get("returns", {})
                    }
            
            # Command not found in any category
            return {"error": f"No help available for command: {command}"}
            
        # Return detailed help for this command
        return command_help[command]

    def visualize_dependencies(self, file_path: str, max_depth: int = 3) -> Dict[str, Any]:
        """Generate a text-based visualization of a file's dependencies.
        
        Args:
            file_path: Path to the file to visualize
            max_depth: Maximum depth to traverse (default: 3)
            
        Returns:
            Dictionary with visualization results
        """
        abs_file_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_file_path):
            return {"error": f"File {abs_file_path} not found."}
            
        if abs_file_path not in self.data["dependencies"]:
            return {"info": f"No dependencies found for {abs_file_path}. Run update_dependencies first."}
        
        # Track visited files to avoid cycles
        visited = set()
        
        def build_tree(path, depth=0, prefix=""):
            if depth > max_depth or path in visited:
                return []
                
            visited.add(path)
            
            # Get file importance info
            importance = ""
            if path in self.data["files"]:
                rank = self.data["files"][path]["rank"]
                importance = f" [rank: {rank}]"
            
            # Get path relative to current directory for cleaner display
            try:
                rel_path = os.path.relpath(path)
            except ValueError:
                # Fall back to the original path if relpath fails
                rel_path = path
                
            result = [f"{prefix}├── {rel_path}{importance}"]
            
            # Get dependencies
            if path in self.data["dependencies"] and "imports" in self.data["dependencies"][path]:
                deps = self.data["dependencies"][path]["imports"]
                
                # Sort dependencies by importance if available
                def get_rank(dep_path):
                    if dep_path in self.data["files"]:
                        return self.data["files"][dep_path]["rank"]
                    return 999  # High rank (low importance) for unranked files
                
                deps.sort(key=get_rank)
                
                for i, dep in enumerate(deps):
                    is_last = (i == len(deps) - 1)
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    connector = "└── " if is_last else "├── "
                    
                    # Only recurse if not creating a cycle
                    if dep not in visited:
                        dep_tree = build_tree(dep, depth + 1, prefix + new_prefix)
                        if dep_tree:
                            result.extend(dep_tree)
                        else:
                            # If we hit max depth or a cycle, just show the dependency without recursing
                            try:
                                rel_dep = os.path.relpath(dep)
                            except ValueError:
                                rel_dep = dep
                                
                            dep_importance = ""
                            if dep in self.data["files"]:
                                dep_rank = self.data["files"][dep]["rank"]
                                dep_importance = f" [rank: {dep_rank}]"
                                
                            result.append(f"{prefix}{new_prefix}{connector}{rel_dep}{dep_importance}")
            
            return result
            
        # Build the dependency tree
        tree_lines = build_tree(abs_file_path)
        
        # Build the reverse dependency tree (files that depend on this file)
        dependent_lines = []
        dependents = []
        
        for dep_file, deps in self.data["dependencies"].items():
            if "imports" in deps and abs_file_path in deps["imports"]:
                dependents.append(dep_file)
        
        if dependents:
            dependent_lines.append("Files that depend on this file:")
            for dep in dependents:
                try:
                    rel_dep = os.path.relpath(dep)
                except ValueError:
                    rel_dep = dep
                
                dep_importance = ""
                if dep in self.data["files"]:
                    dep_rank = self.data["files"][dep]["rank"]
                    dep_importance = f" [rank: {dep_rank}]"
                
                dependent_lines.append(f"  → {rel_dep}{dep_importance}")
        
        # Count certain and possible dependencies
        certain_count = 0
        possible_count = 0
        
        if abs_file_path in self.data["dependencies"]:
            if "imports" in self.data["dependencies"][abs_file_path]:
                certain_count = len(self.data["dependencies"][abs_file_path]["imports"])
            if "possible_imports" in self.data["dependencies"][abs_file_path]:
                possible_count = len(self.data["dependencies"][abs_file_path]["possible_imports"])
        
        return {
            "file": abs_file_path,
            "dependency_tree": tree_lines,
            "dependents": dependent_lines,
            "stats": {
                "depth": max_depth,
                "certain_dependencies": certain_count,
                "possible_imports": possible_count,
                "dependents_count": len(dependents)
            }
        }

def process_command(manager, command):
    """Process a command from stdin and return a result."""
    try:
        command_data = json.loads(command)
        # Extract JSON-RPC fields
        jsonrpc = command_data.get("jsonrpc", "2.0")
        req_id = command_data.get("id")
        method = command_data.get("method")
        params = command_data.get("params", {})
        
        # For backward compatibility, try to get action from params or root
        action = params.get("action") if isinstance(params, dict) else None
        if not action:
            action = command_data.get("action")
        
        # If method is provided but no action, use method as action
        if method and not action:
            action = method
        
        log_debug(f"Processing command: action={action}, id={req_id}, method={method}, params={params}")
        
        # Handle MCP notifications (no id, no response needed)
        if req_id is None and method is not None and method.startswith("notifications/"):
            log_debug(f"Received notification: {method}")
            # Don't respond to notifications
            return None
        
        result = None
        error = None
        
        # Handle MCP protocol initialization
        if action == "initialize":
            log_debug(f"Handling initialization request: {params}")
            # This is the MCP handshake, respond with our capabilities
            # Strictly follow the MCP protocol specification format
            result = {
                "serverInfo": {
                    "name": "File Ranking MCP Server",
                    "version": "1.0.0"
                },
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                }
            }
            log_debug(f"Initialize response: {result}")
        elif action == "tools/list":
            # List available tools in MCP format
            result = {
                "tools": [
                    {
                        "name": "rank_file",
                        "description": "Assign an importance rank to a file",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to rank"
                                },
                                "rank": {
                                    "type": "integer",
                                    "description": "Importance rank (1-10, lower is more important)"
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "Brief description of the file's purpose"
                                }
                            },
                            "required": ["file_path", "rank"]
                        }
                    },
                    {
                        "name": "update_dependencies",
                        "description": "Analyze a file and update its dependencies",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to analyze"
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "get_file",
                        "description": "Get information about a file's ranking and dependencies",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to query"
                                }
                            },
                            "required": ["file_path"]
                        }
                    },
                    {
                        "name": "get_all_files",
                        "description": "Get all ranked files and their information",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "visualize_dependencies",
                        "description": "Generate a text visualization of file dependencies",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to visualize"
                                },
                                "max_depth": {
                                    "type": "integer",
                                    "description": "Maximum depth to traverse in the dependency tree"
                                }
                            },
                            "required": ["file_path"]
                        }
                    }
                ]
            }
            log_debug(f"Tools list response: {result}")
        elif action == "shutdown":
            # Handle MCP shutdown request
            log_debug("Received shutdown request")
            result = {}
        elif action == "exit":
            # Handle MCP exit request
            log_debug("Received exit request, will exit after response")
            result = {}
            # Signal to exit after responding
            manager.exit_requested = True
        # Add standard MCP tools/call method
        elif action == "tools/call":
            # This is the standard MCP way to execute tools
            log_debug(f"Executing tool call: {params}")
            
            # Extract the tool call parameters
            tool_name = params.get("name", "")
            tool_params = params.get("parameters", {})
            tool_id = params.get("id", "")
            
            log_debug(f"Tool name: {tool_name}, params: {tool_params}")
            
            # Map tool names to our actions
            if tool_name == "rank_file":
                file_path = tool_params.get("file_path")
                rank = tool_params.get("rank")
                summary = tool_params.get("summary")
                
                if not file_path or not isinstance(rank, int):
                    error = {"code": -32602, "message": "Missing required parameters: file_path and rank"}
                else:
                    cmd_result = manager.rank_file(file_path, rank, summary)
                    result = cmd_result
            elif tool_name == "update_dependencies":
                file_path = tool_params.get("file_path")
                
                if not file_path:
                    error = {"code": -32602, "message": "Missing required parameter: file_path"}
                else:
                    cmd_result = manager.update_dependencies(file_path)
                    result = cmd_result
            elif tool_name == "get_file":
                file_path = tool_params.get("file_path")
                
                if not file_path:
                    error = {"code": -32602, "message": "Missing required parameter: file_path"}
                else:
                    cmd_result = manager.get_file(file_path)
                    result = cmd_result
            elif tool_name == "get_all_files":
                cmd_result = manager.get_all_files()
                result = cmd_result
            elif tool_name == "visualize_dependencies":
                file_path = tool_params.get("file_path")
                max_depth = tool_params.get("max_depth", 3)
                
                if not file_path:
                    error = {"code": -32602, "message": "Missing required parameter: file_path"}
                else:
                    cmd_result = manager.visualize_dependencies(file_path, max_depth)
                    result = cmd_result
            else:
                error = {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
        # Legacy direct action handlers
        elif action == "rank_file":
            # Extract parameters from params or root for backward compatibility
            file_path = params.get("file_path") if isinstance(params, dict) else command_data.get("file_path")
            rank = params.get("rank") if isinstance(params, dict) else command_data.get("rank")
            summary = params.get("summary") if isinstance(params, dict) else command_data.get("summary")
            
            if not file_path or not rank:
                error = {"code": -32602, "message": "Missing required parameters: file_path and rank"}
            else:
                result = manager.rank_file(file_path, rank, summary)
            
        elif action == "get_files_by_dir":
            directory = params.get("directory") if isinstance(params, dict) else command_data.get("directory")
            
            if not directory:
                error = {"code": -32602, "message": "Missing required parameter: directory"}
            else:
                result = manager.get_files_by_dir(directory)
            
        elif action == "generate_summary":
            file_path = params.get("file_path") if isinstance(params, dict) else command_data.get("file_path")
            
            if not file_path:
                error = {"code": -32602, "message": "Missing required parameter: file_path"}
            else:
                result = manager.generate_summary(file_path)
        
        elif action == "update_dependencies":
            file_path = params.get("file_path") if isinstance(params, dict) else command_data.get("file_path")
            
            if not file_path:
                error = {"code": -32602, "message": "Missing required parameter: file_path"}
            else:
                result = manager.update_dependencies(file_path)
            
        elif action == "scan_all_dependencies":
            result = manager.scan_all_dependencies()
            
        elif action == "get_dependencies":
            file_path = params.get("file_path") if isinstance(params, dict) else command_data.get("file_path")
            
            if not file_path:
                error = {"code": -32602, "message": "Missing required parameter: file_path"}
            else:
                result = manager.get_file_dependencies(file_path)
            
        elif action == "get_dependents":
            file_path = params.get("file_path") if isinstance(params, dict) else command_data.get("file_path")
            
            if not file_path:
                error = {"code": -32602, "message": "Missing required parameter: file_path"}
            else:
                result = manager.get_file_dependents(file_path)
            
        elif action == "visualize_dependencies":
            file_path = params.get("file_path") if isinstance(params, dict) else command_data.get("file_path")
            max_depth = params.get("max_depth", 3) if isinstance(params, dict) else command_data.get("max_depth", 3)
            
            if not file_path:
                error = {"code": -32602, "message": "Missing required parameter: file_path"}
            else:
                result = manager.visualize_dependencies(file_path, max_depth)
            
        elif action == "get_capabilities":
            result = manager.get_capabilities()
            
        elif action == "get_command_help":
            command_name = params.get("command") if isinstance(params, dict) else command_data.get("command")
            
            if not command_name:
                error = {"code": -32602, "message": "Missing required parameter: command"}
            else:
                result = manager.get_command_help(command_name)
            
        else:
            error = {
                "code": -32601, 
                "message": f"Unknown action: {action}",
                "data": {
                    "help": "Use the 'get_capabilities' action to see all available commands."
                }
            }
        
        # Skip response if None (for notifications)
        if result is None and error is None:
            return None
            
        # Format response according to JSON-RPC 2.0
        response = {"jsonrpc": "2.0"}
        
        # Add ID if it was provided
        if req_id is not None:
            response["id"] = req_id
        
        if error and not result:  # Don't add error if we've already formatted a result with error status
            response["error"] = error
        else:
            response["result"] = result
        
        return response
            
    except json.JSONDecodeError:
        return {
            "jsonrpc": "2.0", 
            "id": None, 
            "error": {"code": -32700, "message": "Invalid JSON format"}
        }
    except Exception as e:
        print(f"Error processing command: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return {
            "jsonrpc": "2.0", 
            "id": None, 
            "error": {"code": -32603, "message": f"Error processing command: {str(e)}"}
        }

def main():
    """Main function to run the file ranking tool."""
    # Log server startup info
    log_debug(f"=== Starting MCP Server ===")
    log_debug(f"Python executable: {sys.executable}")
    log_debug(f"Arguments: {sys.argv}")
    log_debug(f"Working directory: {os.getcwd()}")
    log_debug(f"Log file: {log_file}")
    
    print("Starting main function...", file=sys.stderr)
    manager = FileRankManager()
    print("FileRankManager initialized", file=sys.stderr)
    
    print("Entering command processing loop...", file=sys.stderr)
    log_debug("Entering command processing loop")
    
    # Process one command per line from stdin
    try:
        for line in sys.stdin:
            line = line.strip()
            log_debug(f"STDIN RECEIVED: '{line}'")
            
            if not line:
                log_debug("Empty line received, skipping")
                print("Empty line received, skipping", file=sys.stderr)
                continue
                
            print(f"Received command: {line}", file=sys.stderr)
            result = process_command(manager, line)
            
            # Skip response for notifications (result is None)
            if result is None:
                log_debug("Skipping response for notification")
                continue
                
            # Ensure the response is valid JSON
            json_response = json.dumps(result)
            log_debug(f"RESPONSE: {json_response}")
            
            print(f"Sending response: {json_response[:100]}{'...' if len(json_response) > 100 else ''}", file=sys.stderr)
            print(json_response)
            sys.stdout.flush()
            print("Response flushed to stdout", file=sys.stderr)
            
            # Check if we should exit (in response to an exit request)
            if manager.exit_requested:
                log_debug("Exiting due to exit request")
                break
                
    except KeyboardInterrupt:
        log_debug("Received KeyboardInterrupt, shutting down")
        print("Received KeyboardInterrupt, shutting down...", file=sys.stderr)
    except Exception as e:
        error_msg = f"Unexpected error in main loop: {str(e)}"
        log_debug(error_msg)
        import traceback
        tb = traceback.format_exc()
        log_debug(f"Traceback:\n{tb}")
        print(error_msg, file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    print("Starting File Ranking service...", file=sys.stderr)
    main() 
