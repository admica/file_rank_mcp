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
    def detect_dependencies(file_path: str) -> Dict[str, List[str]]:
        """Detect all imports in a file with confidence levels.
        
        Returns a dictionary with:
        - "certain": List of dependencies we're highly confident about
        - "possible": List of potential dependencies that might exist
        """
        if not os.path.exists(file_path):
            return {"certain": [], "possible": []}
            
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == '.py':
                # Python AST parsing gives high confidence imports
                certain, possible = DependencyDetector._detect_python_imports(file_path)
                return {"certain": certain, "possible": possible}
                
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                # JavaScript/TypeScript regex parsing
                certain, possible = DependencyDetector._detect_js_imports(file_path)
                return {"certain": certain, "possible": possible}
                
            # Add other language detectors as needed
            return {"certain": [], "possible": []}
            
        except Exception as e:
            print(f"Error detecting dependencies in {file_path}: {str(e)}", file=sys.stderr)
            return {"certain": [], "possible": []}
    
    @staticmethod
    def _detect_python_imports(file_path: str) -> Tuple[List[str], List[str]]:
        """Parse Python file and extract imports.
        
        Returns (certain_imports, possible_imports)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            module_imports = []
            
            for node in ast.walk(tree):
                # Handle regular imports
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_imports.append(name.name)
                # Handle from ... import ...
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_imports.append(node.module)
            
            # Convert module names to potential file paths
            dir_path = os.path.dirname(file_path)
            certain_imports = []
            possible_imports = []
            
            for imp in module_imports:
                # Skip standard library modules
                if imp in sys.builtin_module_names:
                    continue
                    
                # Convert dots to directory separators
                path_parts = imp.split('.')
                
                # Try both direct .py file and __init__.py in directory
                potential_paths = [
                    os.path.join(dir_path, *path_parts) + '.py',
                    os.path.join(dir_path, *path_parts, '__init__.py')
                ]
                
                found = False
                for path in potential_paths:
                    if os.path.exists(path):
                        certain_imports.append(os.path.abspath(path))
                        found = True
                        break
                
                if not found:
                    # Keep the module name as a possible import
                    possible_imports.append(imp)
            
            return certain_imports, possible_imports
            
        except Exception as e:
            print(f"Error parsing Python imports in {file_path}: {str(e)}", file=sys.stderr)
            return [], []
    
    @staticmethod
    def _detect_js_imports(file_path: str) -> Tuple[List[str], List[str]]:
        """Parse JavaScript/TypeScript file and extract imports.
        
        Returns (certain_imports, possible_imports)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for import statements and require calls
            import_regex = r'(?:import\s+.+\s+from\s+[\'"](.+?)[\'"])|(?:require\s*\(\s*[\'"](.+?)[\'"]\s*\))'
            matches = re.findall(import_regex, content)
            
            certain_imports = []
            possible_imports = []
            dir_path = os.path.dirname(file_path)
            
            for match in matches:
                # Each match is a tuple with groups for import or require
                import_path = match[0] or match[1]
                if not import_path:
                    continue
                    
                # Skip package imports
                if import_path.startswith('@') or not ('/' in import_path or '.' in import_path):
                    possible_imports.append(import_path)
                    continue
                
                # Handle relative imports
                if import_path.startswith('.'):
                    import_path = os.path.normpath(os.path.join(dir_path, import_path))
                
                # Try different extensions
                extensions = ['.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.ts']
                
                # If import already has an extension, just check if it exists
                if os.path.splitext(import_path)[1]:
                    if os.path.exists(import_path):
                        certain_imports.append(os.path.abspath(import_path))
                    else:
                        possible_imports.append(import_path)
                    continue
                
                # Try different extensions
                found = False
                for ext in extensions:
                    full_path = import_path + ext
                    if os.path.exists(full_path):
                        certain_imports.append(os.path.abspath(full_path))
                        found = True
                        break
                
                if not found:
                    possible_imports.append(import_path)
            
            return certain_imports, possible_imports
            
        except Exception as e:
            print(f"Error parsing JS imports in {file_path}: {str(e)}", file=sys.stderr)
            return [], []

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
        
        # Detect dependencies with confidence levels
        deps = DependencyDetector.detect_dependencies(abs_file_path)
        
        # Update the dependencies data
        if abs_file_path not in self.data["dependencies"]:
            self.data["dependencies"][abs_file_path] = {}
            
        # Store certain imports as the main dependency list
        self.data["dependencies"][abs_file_path]["imports"] = deps["certain"]
        
        # Also store possible imports for reference
        if deps["possible"]:
            self.data["dependencies"][abs_file_path]["possible_imports"] = deps["possible"]
        elif "possible_imports" in self.data["dependencies"][abs_file_path]:
            # Clean up possible imports if there are none
            del self.data["dependencies"][abs_file_path]["possible_imports"]
            
        self.save_data()
        
        return {
            "success": f"Updated dependencies for {abs_file_path}",
            "imports_count": len(deps["certain"]),
            "imports": deps["certain"],
            "possible_count": len(deps["possible"]),
            "possible_imports": deps["possible"]
        }
    
    def scan_all_dependencies(self) -> Dict[str, Any]:
        """Scan all ranked files and update their dependencies."""
        updated_files = []
        total_imports = 0
        total_possible = 0
        
        for file_path in self.data["files"]:
            if os.path.exists(file_path):
                result = self.update_dependencies(file_path)
                if "success" in result:
                    updated_files.append(file_path)
                    total_imports += result.get("imports_count", 0)
                    total_possible += result.get("possible_count", 0)
        
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
                "supported_languages": ["Python", "JavaScript", "TypeScript"],
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
                            "error": "Error message if unsuccessful"
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
                            "error": "Error message if unsuccessful"
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
            
        elif action == "visualize_dependencies":
            file_path = command_data.get("file_path")
            max_depth = command_data.get("max_depth", 3)
            
            if not file_path:
                return {"error": "Missing required parameter: file_path"}
                
            return manager.visualize_dependencies(file_path, max_depth)
            
        elif action == "get_capabilities":
            return manager.get_capabilities()
            
        elif action == "get_command_help":
            command_name = command_data.get("command")
            
            if not command_name:
                return {"error": "Missing required parameter: command"}
                
            return manager.get_command_help(command_name)
            
        else:
            # If command not recognized, suggest using get_capabilities
            return {
                "error": f"Unknown action: {action}",
                "help": "Use the 'get_capabilities' action to see all available commands."
            }
            
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