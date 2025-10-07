# GitLab MCP Server

A Model Context Protocol (MCP) server for interacting with GitLab repositories, issues, merge requests, and more.

## Features

- List and get project details
- Manage issues (list, create)
- Manage merge requests (list, create)
- Access repository files
- List branches and commits
- User information

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your GitLab access token:

```bash
export GITLAB_TOKEN="your-gitlab-token"
# Optional: for self-hosted GitLab
export GITLAB_URL="https://gitlab.example.com"
```

## Usage

### Option 1: Run as MCP Server

Run the server directly:

```bash
python server.py
```

### Option 2: Use with LangGraph Agent (Recommended)

The `gitlab_agent.py` provides a high-level interface using LangGraph's ReAct agent:

```python
import asyncio
from gitlab_agent import GitLabAgent

async def main():
    # Initialize the agent
    agent = GitLabAgent()
    
    # Simple invoke
    response = await agent.invoke("Show me my GitLab projects")
    
    # Structured output
    structured = await agent.invoke_structured(
        "Create an issue titled 'Fix bug' in project 12345"
    )
    print(structured.user_output)
    print(structured.action_taken)
    print(structured.resource_url)
    
    # Clean up
    await agent.aclose()

asyncio.run(main())
```

### Option 3: Interactive Examples

Run the interactive example script:

```bash
python example_usage.py
```

This provides a menu with various examples:
- List projects
- Create issues
- Manage merge requests
- Browse repository files
- Conversational mode

## Available Tools

### get_project
Get details about a specific GitLab project.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project

### list_issues
List issues in a GitLab project.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project
- `state` (optional): Filter by state (opened, closed, all)

### create_issue
Create a new issue in a GitLab project.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project
- `title` (required): The title of the issue
- `description` (optional): The description of the issue
- `labels` (optional): Comma-separated list of label names

### list_merge_requests
List merge requests in a GitLab project.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project
- `state` (optional): Filter by state (opened, closed, merged, all)

### create_merge_request
Create a new merge request in a GitLab project.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project
- `source_branch` (required): The source branch name
- `target_branch` (required): The target branch name
- `title` (required): The title of the merge request
- `description` (optional): The description of the merge request

### get_file_content
Get the content of a file from a GitLab repository.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project
- `file_path` (required): The path to the file in the repository
- `ref` (optional): The branch, tag, or commit SHA (default: main)

### list_branches
List branches in a GitLab project.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project

### list_commits
List commits in a GitLab project.

**Parameters:**
- `project_id` (required): The ID or URL-encoded path of the project
- `ref_name` (optional): The name of a branch, tag, or commit SHA

## Resources

- `gitlab://projects`: List of accessible GitLab projects
- `gitlab://user`: Information about the authenticated user

## Configuration

Set the following environment variables:

- `GITLAB_TOKEN` (required): Your GitLab personal access token
- `GITLAB_URL` (optional): GitLab instance URL (default: https://gitlab.com)
- `OPENAI_API_KEY` (required for agent): Your OpenAI API key

## Getting a GitLab Token

1. Go to your GitLab instance (gitlab.com or your self-hosted instance)
2. Navigate to Settings > Access Tokens
3. Create a personal access token with the following scopes:
   - `api` - Access the API
   - `read_repository` - Read repository content
   - `write_repository` - Write to repository (if needed)

## Agent Architecture

The GitLab Agent uses:
- **LangGraph**: For the ReAct agent framework
- **LangChain**: For LLM integration (OpenAI)
- **MCP Client**: To connect to the GitLab MCP server
- **Structured Outputs**: Using Pydantic models for reliable response parsing

### Agent Features

- 🔄 **Conversational**: Maintains context across multiple interactions
- 🎯 **Tool Selection**: Automatically selects the right GitLab tools
- 📊 **Structured Outputs**: Returns typed, validated responses
- 🔍 **Logging**: Detailed logging of all operations
- 💾 **Checkpointing**: Saves conversation state

## Example Agent Interactions

```python
# List projects
await agent.invoke("What GitLab projects do I have access to?")

# Get project info
await agent.invoke("Tell me about project 12345")

# Create an issue
await agent.invoke_structured(
    "Create a bug report in project myuser/myrepo titled 'Login fails'"
)

# List merge requests
await agent.invoke("Show me open merge requests in project 12345")

# Get file content
await agent.invoke("Show me the README.md file from project 12345")
```

## Files

- `server.py` - Main MCP server implementation
- `gitlab_agent.py` - LangGraph agent wrapper
- `example_usage.py` - Interactive examples
- `requirements.txt` - MCP server dependencies
- `requirements-agent.txt` - Agent dependencies
- `.env.example` - Environment variable template

## License

MIT
