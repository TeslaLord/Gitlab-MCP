import os
import asyncio
import logging
from typing import Any
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt.chat_agent_executor import AgentState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# === Structured Output Schema ===
class GitLabAgentOutput(BaseModel):
    """Structured output for GitLab agent responses."""
    user_output: str = Field(description="The main response to the user")
    action_taken: str | None = Field(default=None, description="Description of any action taken (issue created, MR created, etc.)")
    resource_url: str | None = Field(default=None, description="URL to the created/modified resource")
    insights_summary: str | None = Field(default=None, description="Key insights or analysis from the response")


# === System Prompt ===
GITLAB_SYSTEM_PROMPT = """You are a GitLab assistant with access to live GitLab API tools.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. ALWAYS use tools to get real data - NEVER provide generic responses
2. You CANNOT access GitLab data without using the tools
3. If a user asks about GitLab, you MUST call the appropriate tool first
4. Do NOT say "I cannot access" or "I don't have access" - you DO have access via tools

Available tools:
- get_project: Get project details by ID
- list_issues: List issues in a project  
- create_issue: Create a new issue
- list_merge_requests: List MRs in a project
- create_merge_request: Create a new MR
- get_file_content: Read file from repository
- list_branches: List all branches
- list_commits: List commits

EXAMPLES OF CORRECT BEHAVIOR:
User: "Show me my projects"
You: [Call appropriate tool to list projects] then provide the results

User: "What's in project 123?"
You: [Call get_project with ID 123] then show the data

User: "Show my user info"
You: [Call tool to get user data] then display it

NEVER respond without calling tools first. You have full access via the tools."""


# === Test Prompts ===
TEST_PROMPTS = {
    "list_projects": "Show me my GitLab projects",
    "get_project": "Get details about project ID 12345",
    "list_issues": "List open issues in project 12345",
    "create_issue": "Create an issue titled 'Fix login bug' in project 12345 with description 'Users cannot log in with special characters in password'",
    "list_mrs": "Show me open merge requests in project 12345",
    "create_mr": "Create a merge request from feature-branch to main in project 12345 titled 'Add new feature'",
    "get_file": "Show me the contents of README.md from project 12345",
    "list_branches": "List all branches in project 12345",
    "list_commits": "Show recent commits in project 12345",
}


class GitLabAgent:
    """
    GitLabAgent integrates LangGraph's ReAct agent with GitLab MCP server
    to interact with GitLab repositories, issues, merge requests, and more.
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        gitlab_server_path: str | None = None,
        model_name: str = "gpt-5",
        max_context_tokens: int = 2000,
    ):
        logger.info("🚀 Initializing GitLabAgent...")
        logger.info(f"📊 Model: {model_name}")
        
        # === API keys and model setup ===
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.model = ChatOpenAI(model=model_name, api_key=self.openai_api_key)
        logger.info("✅ OpenAI model initialized")
        
        # === GitLab MCP Server Setup ===
        # Determine the server path
        if gitlab_server_path is None:
            # Default to the server.py in the same directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            gitlab_server_path = os.path.join(current_dir, "server.py")
        
        if not os.path.exists(gitlab_server_path):
            raise FileNotFoundError(f"GitLab MCP server not found at: {gitlab_server_path}")
        
        logger.info(f"📁 GitLab server path: {gitlab_server_path}")
        
        # Check for GitLab token
        gitlab_token = os.getenv("GITLAB_TOKEN")
        if not gitlab_token:
            logger.warning("⚠️ GITLAB_TOKEN environment variable not set. Some operations may fail.")
        
        mcp_servers = {
            "gitlab": {
                "command": "python",
                "args": [gitlab_server_path],
                "transport": "stdio",
                "env": {
                    "GITLAB_TOKEN": gitlab_token or "",
                    "GITLAB_URL": os.getenv("GITLAB_URL", "https://gitlab.com"),
                }
            }
        }
        
        logger.info(f"🔌 Configuring GitLab MCP server")
        self.client = MultiServerMCPClient(mcp_servers)

        # === State and checkpointing setup ===
        self.checkpointer = InMemorySaver()

        # === Initialize agent lazily ===
        self.agent = None

    async def initialize(self):
        """Initializes the agent asynchronously (loads tools)."""
        logger.info("⚙️ Initializing agent and loading tools...")
        tools = []
        
        try:
            logger.info("📡 Connecting to GitLab MCP server...")
            tools = await self.client.get_tools()
            logger.info(f"✅ Loaded {len(tools)} tools from GitLab MCP server")
            
            if len(tools) == 0:
                logger.error("❌ No tools loaded! Check if GITLAB_TOKEN is set and server.py is working.")
                raise ValueError("No tools loaded from GitLab MCP server")
            
            for i, tool in enumerate(tools, 1):
                logger.info(f"  {i}. {tool.name} - {tool.description[:80]}...")
        except Exception as e:
            logger.error(f"❌ Error loading tools: {e}")
            logger.exception("Full error:")
            raise

        self.agent = create_react_agent(
            model=self.model,
            tools=tools,
            checkpointer=self.checkpointer,
        )
        logger.info("✅ Agent initialized successfully")

    async def invoke(self, user_prompt: str, thread_id: str = "1") -> Any:
        """Invokes the ReAct agent asynchronously."""
        logger.info("=" * 80)
        logger.info(f"💬 USER PROMPT (Thread: {thread_id}):")
        logger.info(f"   {user_prompt}")
        logger.info("=" * 80)
        
        if not self.agent:
            await self.initialize()

        config = {"configurable": {"thread_id": thread_id}}
        
        # Enhanced prompt to force tool usage
        enhanced_prompt = f"""{user_prompt}

IMPORTANT: You must use the available GitLab tools to answer this. Do not provide a generic response."""

        try:
            logger.info("🤖 Invoking agent...")
            response = await self.agent.ainvoke(
                {
                    "messages": [
                        {"role": "system", "content": GITLAB_SYSTEM_PROMPT},
                        {"role": "user", "content": enhanced_prompt}
                    ]
                },
                config=config,
            )
            
            # Log the response
            if response and "messages" in response:
                logger.info(f"📨 Received {len(response['messages'])} messages")
                
                # Count tool calls
                tool_call_count = 0
                
                # Log tool calls if any
                for i, msg in enumerate(response["messages"]):
                    msg_type = getattr(msg, 'type', 'unknown')
                    if msg_type == 'ai' and hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_call_count += len(msg.tool_calls)
                        logger.info(f"   🔧 AI Message {i} used {len(msg.tool_calls)} tool(s):")
                        for tc in msg.tool_calls:
                            logger.info(f"      - {tc.get('name', 'unknown')} with args: {tc.get('args', {})}")
                    elif msg_type == 'tool':
                        logger.info(f"   📊 Tool Message {i}: {getattr(msg, 'name', 'unknown')}")
                
                # Warn if no tools were called
                if tool_call_count == 0:
                    logger.warning("⚠️  WARNING: Agent did NOT call any tools!")
                    logger.warning("⚠️  The response may be generic/hallucinated.")
                else:
                    logger.info(f"✅ Agent called {tool_call_count} tool(s) total")
                
                final_message = response["messages"][-1]
                logger.info(f"✅ AGENT RESPONSE:")
                logger.info(f"   Role: {getattr(final_message, 'type', 'unknown')}")
                content_str = str(final_message.content)
                logger.info(f"   Content: {content_str[:500]}..." if len(content_str) > 500 else f"   Content: {content_str}")
            
            logger.info("=" * 80)
            return response
            
        except Exception as e:
            logger.error(f"❌ Error during agent invocation: {e}")
            logger.exception("Full traceback:")
            raise

    async def invoke_structured(self, user_prompt: str, thread_id: str = "1") -> GitLabAgentOutput:
        """Invokes the agent and returns structured output."""
        logger.info("📋 Requesting structured output...")
        
        # First get the regular response
        response = await self.invoke(user_prompt, thread_id)
        
        # Extract the final message content
        final_message = response["messages"][-1].content
        logger.info("🔄 Parsing response into structured format...")
        
        # Use structured output model to parse the response
        structured_model = self.model.with_structured_output(GitLabAgentOutput)
        
        # Create a parsing prompt
        parsing_prompt = f"""
        Please extract the following information from this GitLab agent response and format it according to the schema:
        
        Agent Response: {final_message}
        
        Extract:
        - user_output (mandatory): The main response to the user
        - action_taken (optional): Description of any action taken (e.g., "Created issue #123", "Listed 5 merge requests")
        - resource_url (optional): Any GitLab URLs mentioned (issues, MRs, projects, files)
        - insights_summary (optional): Any key insights or analysis
        """
        
        try:
            structured_response = await structured_model.ainvoke([{"role": "user", "content": parsing_prompt}])
            logger.info("✅ STRUCTURED OUTPUT:")
            logger.info(f"   📝 User Output: {structured_response.user_output[:200]}..." if len(structured_response.user_output) > 200 else f"   📝 User Output: {structured_response.user_output}")
            if structured_response.action_taken:
                logger.info(f"   ⚡ Action: {structured_response.action_taken}")
            if structured_response.resource_url:
                logger.info(f"   🔗 Resource URL: {structured_response.resource_url}")
            if structured_response.insights_summary:
                logger.info(f"   💡 Insights: {structured_response.insights_summary}")
            logger.info("=" * 80)
            return structured_response
        except Exception as e:
            logger.error(f"❌ Error parsing structured output: {e}")
            raise

    async def aclose(self):
        """Closes the MCP client gracefully."""
        logger.info("🔌 Closing MCP client connections...")
        if self.client:
            # As per langchain-mcp-adapters 0.11.0, no explicit cleanup needed
            # The client will clean up automatically when the object is destroyed
            logger.info("✅ MCP client cleanup complete")


# === Example Usage ===
if __name__ == "__main__":
    
    async def main():
        # Initialize the agent
        agent = GitLabAgent()
        
        # Example 1: List projects
        print("\n" + "="*80)
        print("EXAMPLE 1: List Projects")
        print("="*80)
        response1 = await agent.invoke(TEST_PROMPTS["list_projects"])
        print(response1)
        
        # Example 2: Get project details (replace with your project ID)
        # print("\n" + "="*80)
        # print("EXAMPLE 2: Get Project Details")
        # print("="*80)
        # response2 = await agent.invoke("Get details about project ID YOUR_PROJECT_ID")
        
        # Example 3: Structured output
        print("\n" + "="*80)
        print("EXAMPLE 3: Structured Output")
        print("="*80)
        structured_response = await agent.invoke_structured("List all users in the projects")
        print(f"\nStructured Output: {structured_response.model_dump_json(indent=2)}")
        
        # Clean up
        await agent.aclose()

    asyncio.run(main())
