"""
Example usage of the GitLab Agent with various GitLab operations.

Before running:
1. Install dependencies: pip install -r requirements-agent.txt
2. Set environment variables:
   - OPENAI_API_KEY=your-openai-key
   - GITLAB_TOKEN=your-gitlab-token
   - GITLAB_URL=https://gitlab.com (optional, defaults to gitlab.com)
"""

import asyncio
import os
from gitlab_agent import GitLabAgent


async def example_list_projects():
    """Example: List all accessible GitLab projects."""
    print("\n" + "="*80)
    print("EXAMPLE: List Projects")
    print("="*80)
    
    agent = GitLabAgent()
    
    try:
        response = await agent.invoke("Show me all my GitLab projects")
        print("\n✅ Success! Check logs above for details.")
    finally:
        await agent.aclose()


async def example_get_project_info():
    """Example: Get detailed information about a specific project."""
    print("\n" + "="*80)
    print("EXAMPLE: Get Project Information")
    print("="*80)
    
    # Replace with your actual project ID or path
    project_id = input("Enter project ID or path (e.g., 'username/repo'): ").strip()
    
    if not project_id:
        print("❌ Project ID is required")
        return
    
    agent = GitLabAgent()
    
    try:
        response = await agent.invoke(f"Get details about project {project_id}")
        print("\n✅ Success! Check logs above for details.")
    finally:
        await agent.aclose()


async def example_list_issues():
    """Example: List issues in a project."""
    print("\n" + "="*80)
    print("EXAMPLE: List Issues")
    print("="*80)
    
    project_id = input("Enter project ID: ").strip()
    
    if not project_id:
        print("❌ Project ID is required")
        return
    
    agent = GitLabAgent()
    
    try:
        response = await agent.invoke(
            f"List all open issues in project {project_id}"
        )
        print("\n✅ Success! Check logs above for details.")
    finally:
        await agent.aclose()


async def example_create_issue():
    """Example: Create a new issue."""
    print("\n" + "="*80)
    print("EXAMPLE: Create Issue")
    print("="*80)
    
    project_id = input("Enter project ID: ").strip()
    title = input("Enter issue title: ").strip()
    description = input("Enter issue description (optional): ").strip()
    
    if not project_id or not title:
        print("❌ Project ID and title are required")
        return
    
    agent = GitLabAgent()
    
    try:
        prompt = f"Create an issue in project {project_id} with title '{title}'"
        if description:
            prompt += f" and description '{description}'"
        
        response = await agent.invoke_structured(prompt)
        
        print("\n✅ Issue created successfully!")
        print(f"Response: {response.user_output}")
        if response.resource_url:
            print(f"Issue URL: {response.resource_url}")
            
    finally:
        await agent.aclose()


async def example_list_merge_requests():
    """Example: List merge requests in a project."""
    print("\n" + "="*80)
    print("EXAMPLE: List Merge Requests")
    print("="*80)
    
    project_id = input("Enter project ID: ").strip()
    
    if not project_id:
        print("❌ Project ID is required")
        return
    
    agent = GitLabAgent()
    
    try:
        response = await agent.invoke(
            f"Show me all open merge requests in project {project_id}"
        )
        print("\n✅ Success! Check logs above for details.")
    finally:
        await agent.aclose()


async def example_create_merge_request():
    """Example: Create a new merge request."""
    print("\n" + "="*80)
    print("EXAMPLE: Create Merge Request")
    print("="*80)
    
    project_id = input("Enter project ID: ").strip()
    source_branch = input("Enter source branch: ").strip()
    target_branch = input("Enter target branch (e.g., main): ").strip()
    title = input("Enter MR title: ").strip()
    description = input("Enter MR description (optional): ").strip()
    
    if not all([project_id, source_branch, target_branch, title]):
        print("❌ All fields except description are required")
        return
    
    agent = GitLabAgent()
    
    try:
        prompt = f"Create a merge request in project {project_id} from {source_branch} to {target_branch} with title '{title}'"
        if description:
            prompt += f" and description '{description}'"
        
        response = await agent.invoke_structured(prompt)
        
        print("\n✅ Merge request created successfully!")
        print(f"Response: {response.user_output}")
        if response.resource_url:
            print(f"MR URL: {response.resource_url}")
            
    finally:
        await agent.aclose()


async def example_get_file_content():
    """Example: Get content of a file from repository."""
    print("\n" + "="*80)
    print("EXAMPLE: Get File Content")
    print("="*80)
    
    project_id = input("Enter project ID: ").strip()
    file_path = input("Enter file path (e.g., README.md): ").strip()
    ref = input("Enter branch/tag (default: main): ").strip() or "main"
    
    if not project_id or not file_path:
        print("❌ Project ID and file path are required")
        return
    
    agent = GitLabAgent()
    
    try:
        response = await agent.invoke(
            f"Show me the contents of {file_path} from project {project_id} on branch {ref}"
        )
        print("\n✅ Success! Check logs above for details.")
    finally:
        await agent.aclose()


async def example_list_branches():
    """Example: List all branches in a project."""
    print("\n" + "="*80)
    print("EXAMPLE: List Branches")
    print("="*80)
    
    project_id = input("Enter project ID: ").strip()
    
    if not project_id:
        print("❌ Project ID is required")
        return
    
    agent = GitLabAgent()
    
    try:
        response = await agent.invoke(
            f"List all branches in project {project_id}"
        )
        print("\n✅ Success! Check logs above for details.")
    finally:
        await agent.aclose()


async def example_conversational():
    """Example: Have a conversation with the GitLab agent."""
    print("\n" + "="*80)
    print("EXAMPLE: Conversational Mode")
    print("="*80)
    print("Type 'quit' to exit\n")
    
    agent = GitLabAgent()
    thread_id = "conversational-session"
    
    try:
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = await agent.invoke(user_input, thread_id=thread_id)
            
            # Print just the final message
            if response and "messages" in response:
                final_msg = response["messages"][-1]
                print(f"\n🤖 Agent: {final_msg.content}\n")
                
    finally:
        await agent.aclose()


async def main():
    """Main menu for example selection."""
    print("""
    ╔════════════════════════════════════════════╗
    ║     GitLab Agent - Example Usage           ║
    ╚════════════════════════════════════════════╝
    
    Choose an example to run:
    
    1.  List Projects
    2.  Get Project Information
    3.  List Issues
    4.  Create Issue
    5.  List Merge Requests
    6.  Create Merge Request
    7.  Get File Content
    8.  List Branches
    9.  Conversational Mode
    0.  Exit
    """)
    
    choice = input("Enter choice (0-9): ").strip()
    
    examples = {
        "1": example_list_projects,
        "2": example_get_project_info,
        "3": example_list_issues,
        "4": example_create_issue,
        "5": example_list_merge_requests,
        "6": example_create_merge_request,
        "7": example_get_file_content,
        "8": example_list_branches,
        "9": example_conversational,
    }
    
    if choice == "0":
        print("👋 Goodbye!")
        return
    
    if choice in examples:
        await examples[choice]()
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your-key")
        exit(1)
    
    if not os.getenv("GITLAB_TOKEN"):
        print("⚠️  Warning: GITLAB_TOKEN environment variable not set")
        print("Some operations may fail without it")
        print("Set it with: export GITLAB_TOKEN=your-token\n")
    
    asyncio.run(main())
