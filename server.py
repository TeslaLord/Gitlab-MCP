import os
import json
from typing import Any
import asyncio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import AnyUrl
import httpx

# GitLab API configuration
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "")

server = Server("gitlab-mcp-server")

async def make_gitlab_request(
    endpoint: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None
) -> dict[str, Any] | list[dict[str, Any]]:
    """Make a request to the GitLab API."""
    if not GITLAB_TOKEN:
        raise ValueError("GITLAB_TOKEN environment variable is required")
    
    url = f"{GITLAB_URL}/api/v4/{endpoint}"
    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data, params=params)
        elif method == "PUT":
            response = await client.put(url, headers=headers, json=data, params=params)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        if response.status_code == 204:
            return {}
        
        return response.json()


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available GitLab resources."""
    return [
        Resource(
            uri=AnyUrl(f"gitlab://projects"),
            name="GitLab Projects",
            description="List of accessible GitLab projects",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl(f"gitlab://user"),
            name="Current User",
            description="Information about the authenticated user",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific GitLab resource."""
    uri_str = str(uri)
    
    if uri_str == "gitlab://projects":
        projects = await make_gitlab_request("projects", params={"membership": True, "per_page": 20})
        return json.dumps(projects, indent=2)
    
    elif uri_str == "gitlab://user":
        user = await make_gitlab_request("user")
        return json.dumps(user, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available GitLab tools."""
    return [
        Tool(
            name="list_projects",
            description="List all GitLab projects accessible to the current user",
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {
                        "type": "integer",
                        "description": "Number of projects to return (default: 20, max: 100)",
                    },
                },
            },
        ),
        Tool(
            name="get_project",
            description="Get details about a specific GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_issues",
            description="List issues in a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state: opened, closed, or all",
                        "enum": ["opened", "closed", "all"],
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="create_issue",
            description="Create a new issue in a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the issue",
                    },
                    "description": {
                        "type": "string",
                        "description": "The description of the issue",
                    },
                    "labels": {
                        "type": "string",
                        "description": "Comma-separated list of label names",
                    },
                },
                "required": ["project_id", "title"],
            },
        ),
        Tool(
            name="list_merge_requests",
            description="List merge requests in a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                    "state": {
                        "type": "string",
                        "description": "Filter by state: opened, closed, merged, or all",
                        "enum": ["opened", "closed", "merged", "all"],
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="create_merge_request",
            description="Create a new merge request in a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                    "source_branch": {
                        "type": "string",
                        "description": "The source branch name",
                    },
                    "target_branch": {
                        "type": "string",
                        "description": "The target branch name",
                    },
                    "title": {
                        "type": "string",
                        "description": "The title of the merge request",
                    },
                    "description": {
                        "type": "string",
                        "description": "The description of the merge request",
                    },
                },
                "required": ["project_id", "source_branch", "target_branch", "title"],
            },
        ),
        Tool(
            name="get_file_content",
            description="Get the content of a file from a GitLab repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file in the repository",
                    },
                    "ref": {
                        "type": "string",
                        "description": "The branch, tag, or commit SHA (default: main)",
                    },
                },
                "required": ["project_id", "file_path"],
            },
        ),
        Tool(
            name="list_branches",
            description="List branches in a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_commits",
            description="List commits in a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID or URL-encoded path of the project",
                    },
                    "ref_name": {
                        "type": "string",
                        "description": "The name of a branch, tag, or commit SHA",
                    },
                },
                "required": ["project_id"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool execution requests."""
    if arguments is None:
        arguments = {}
    
    try:
        if name == "list_projects":
            params = {
                "membership": True,
                "per_page": arguments.get("per_page", 20)
            }
            result = await make_gitlab_request("projects", params=params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_project":
            project_id = arguments["project_id"]
            result = await make_gitlab_request(f"projects/{project_id}")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "list_issues":
            project_id = arguments["project_id"]
            params = {}
            if "state" in arguments:
                params["state"] = arguments["state"]
            result = await make_gitlab_request(f"projects/{project_id}/issues", params=params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "create_issue":
            project_id = arguments["project_id"]
            data = {
                "title": arguments["title"],
            }
            if "description" in arguments:
                data["description"] = arguments["description"]
            if "labels" in arguments:
                data["labels"] = arguments["labels"]
            result = await make_gitlab_request(f"projects/{project_id}/issues", method="POST", data=data)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "list_merge_requests":
            project_id = arguments["project_id"]
            params = {}
            if "state" in arguments:
                params["state"] = arguments["state"]
            result = await make_gitlab_request(f"projects/{project_id}/merge_requests", params=params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "create_merge_request":
            project_id = arguments["project_id"]
            data = {
                "source_branch": arguments["source_branch"],
                "target_branch": arguments["target_branch"],
                "title": arguments["title"],
            }
            if "description" in arguments:
                data["description"] = arguments["description"]
            result = await make_gitlab_request(f"projects/{project_id}/merge_requests", method="POST", data=data)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_file_content":
            project_id = arguments["project_id"]
            file_path = arguments["file_path"]
            params = {"ref": arguments.get("ref", "main")}
            result = await make_gitlab_request(f"projects/{project_id}/repository/files/{file_path}", params=params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "list_branches":
            project_id = arguments["project_id"]
            result = await make_gitlab_request(f"projects/{project_id}/repository/branches")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "list_commits":
            project_id = arguments["project_id"]
            params = {}
            if "ref_name" in arguments:
                params["ref_name"] = arguments["ref_name"]
            result = await make_gitlab_request(f"projects/{project_id}/repository/commits", params=params)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gitlab-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
