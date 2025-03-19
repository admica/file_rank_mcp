#!/bin/bash
# PATH: ./file_rank_mcp.py
import json
import os
import argparse
from mcp import Server, Resource, Tool
from mcp.types import ResourceResponse, ToolResponse

# DataManager: Handles data storage and manipulation
class DataManager:
    def __init__(self, data_file="file_rank_mcp.json"):
        """Initialize with a path to the JSON data file."""
        self.data_file = data_file
        self.load_data()

    def load_data(self):
        """Load data from the JSON file, or initialize an empty structure."""
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {"groups": []}

    def save_data(self):
        """Save the current data to the JSON file."""
        with open(self.data_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def get_groups_summary(self):
        """Return a summary of all groups."""
        result = []
        for group in self.data["groups"]:
            files = group["files"]
            group_info = {
                "group": group["name"],
                "path": group.get("path", ""),
                "files": len(files)
            }
            if files:
                priorities = [file["priority"] for file in files]
                group_info["pri_min"] = min(priorities)
                group_info["pri_max"] = max(priorities)
            result.append(group_info)
        return result

    def get_group(self, group_name):
        """Return details of a specific group, or an error if not found."""
        group = next((g for g in self.data["groups"] if g["name"] == group_name), None)
        if group:
            return group
        return {"error": f"Group {group_name} not found"}

    def add_file(self, group_name, file_path, priority, summary=None):
        """Add a file to a group or update its priority if it exists."""
        group = next((g for g in self.data["groups"] if g["name"] == group_name), None)
        if group is None:
            group_path = os.path.dirname(file_path)
            group = {"name": group_name, "path": group_path, "files": []}
            self.data["groups"].append(group)
        for file in group["files"]:
            if file["path"] == file_path:
                file["priority"] = priority
                break
        else:
            if summary is None:
                summary = "No summary provided"
            group["files"].append({"path": file_path, "priority": priority, "summary": summary})
        self.save_data()
        return {"success": f"Added/updated file {file_path} in group {group_name}"}

    def remove_file(self, group_name, file_path):
        """Remove a file from a group."""
        group = next((g for g in self.data["groups"] if g["name"] == group_name), None)
        if group is None:
            return {"error": f"Group {group_name} not found"}
        original_count = len(group["files"])
        group["files"] = [f for f in group["files"] if f["path"] != file_path]
        if len(group["files"]) == original_count:
            return {"error": f"File {file_path} not found in group {group_name}"}
        self.save_data()
        return {"success": f"Removed file {file_path} from group {group_name}"}

    def remove_group(self, group_name):
        """Remove an entire group."""
        original_count = len(self.data["groups"])
        self.data["groups"] = [g for g in self.data["groups"] if g["name"] != group_name]
        if len(self.data["groups"]) == original_count:
            return {"error": f"Group {group_name} not found"}
        self.save_data()
        return {"success": f"Removed group {group_name}"}

    def set_group_path(self, group_name, path):
        """Set the path for a group."""
        group = next((g for g in self.data["groups"] if g["name"] == group_name), None)
        if group is None:
            return {"error": f"Group {group_name} not found"}
        group["path"] = path
        self.save_data()
        return {"success": f"Set path for group {group_name} to {path}"}

# FilePriorityServer: Defines MCP resources and tools
class FilePriorityServer(Server):
    def __init__(self, data_manager):
        """Initialize the server with a data manager."""
        super().__init__()
        self.data_manager = data_manager

        # Resource: Fetch all group summaries
        groups_resource = Resource(
            path="/groups",
            get=lambda: ResourceResponse(data=self.data_manager.get_groups_summary())
        )
        self.add_resource(groups_resource)

        # Resource: Fetch details of a specific group
        group_detail_resource = Resource(
            path="/groups/<group_name>",
            get=lambda group_name: ResourceResponse(data=self.data_manager.get_group(group_name))
        )
        self.add_resource(group_detail_resource)

        # Tool: Add or update a file
        add_file_tool = Tool(
            name="add_file",
            description="Add or update a file in a group with priority and summary",
            parameters={
                "group": {"type": "string", "description": "The group name"},
                "file": {"type": "string", "description": "The file path"},
                "priority": {"type": "integer", "description": "Priority (1-10)"},
                "summary": {"type": "string", "optional": True, "description": "File summary"}
            },
            function=lambda group, file, priority, summary=None: ToolResponse(
                output=self.data_manager.add_file(group, file, priority, summary)
            )
        )
        self.add_tool(add_file_tool)

        # Tool: Remove a file from a group
        remove_file_tool = Tool(
            name="remove_file",
            description="Remove a file from a group",
            parameters={
                "group": {"type": "string", "description": "The group name"},
                "file": {"type": "string", "description": "The file path"}
            },
            function=lambda group, file: ToolResponse(output=self.data_manager.remove_file(group, file))
        )
        self.add_tool(remove_file_tool)

        # Tool: Remove an entire group
        remove_group_tool = Tool(
            name="remove_group",
            description="Remove an entire group and its files",
            parameters={
                "group": {"type": "string", "description": "The group name"}
            },
            function=lambda group: ToolResponse(output=self.data_manager.remove_group(group))
        )
        self.add_tool(remove_group_tool)

        # Tool: Set the path for a group
        set_group_path_tool = Tool(
            name="set_group_path",
            description="Set the path for a group",
            parameters={
                "group": {"type": "string", "description": "The group name"},
                "path": {"type": "string", "description": "The new path for the group"}
            },
            function=lambda group, path: ToolResponse(output=self.data_manager.set_group_path(group, path))
        )
        self.add_tool(set_group_path_tool)

# Main script to run the server
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the File Rank MCP Server")
    parser.add_argument("--data-file", default="file_rank_mcp.json", help="Path to the data file")
    parser.add_argument("--http", action="store_true", help="Run server on HTTP instead of STDIO")
    args = parser.parse_args()

    print("Setting up...")
    data_manager = DataManager(data_file=args.data_file)
    server = FilePriorityServer(data_manager)

    if args.http:
        from mcp.transports import HttpTransport
        transport = HttpTransport(host="0.0.0.0", port=8000)
        print("Starting HTTP server on port 8000...")
        server.run(transport=transport)
    else:
        print("Starting server on STDIO...")
        server.run()
