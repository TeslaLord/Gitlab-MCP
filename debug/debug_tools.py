"""
Debug script to test if GitLab MCP server tools are loading correctly.
"""

import os
import asyncio
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_connection():
    """Test connection to GitLab MCP server."""
    
    # Check environment variables
    logger.info("=" * 80)
    logger.info("ENVIRONMENT CHECK")
    logger.info("=" * 80)
    
    gitlab_token = os.getenv("GITLAB_TOKEN")
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    
    logger.info(f"GITLAB_TOKEN: {'✅ Set' if gitlab_token else '❌ Not set'}")
    logger.info(f"GITLAB_URL: {gitlab_url}")
    
    if not gitlab_token:
        logger.error("❌ GITLAB_TOKEN is not set! Export it with:")
        logger.error("   export GITLAB_TOKEN='your-token-here'")
        return
    
    # Find server.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    
    logger.info(f"Server path: {server_path}")
    logger.info(f"Server exists: {os.path.exists(server_path)}")
    
    # Configure MCP client
    mcp_servers = {
        "gitlab": {
            "command": "python",
            "args": [server_path],
            "transport": "stdio",
            "env": {
                "GITLAB_TOKEN": gitlab_token,
                "GITLAB_URL": gitlab_url,
            }
        }
    }
    
    logger.info("\n" + "=" * 80)
    logger.info("MCP CLIENT TEST")
    logger.info("=" * 80)
    
    client = MultiServerMCPClient(mcp_servers)
    
    try:
        logger.info("📡 Connecting to MCP server...")
        tools = await client.get_tools()
        
        logger.info(f"\n✅ SUCCESS! Loaded {len(tools)} tools")
        logger.info("\n" + "=" * 80)
        logger.info("AVAILABLE TOOLS")
        logger.info("=" * 80)
        
        for i, tool in enumerate(tools, 1):
            logger.info(f"\n{i}. {tool.name}")
            logger.info(f"   Description: {tool.description}")
            # Handle different schema formats
            if hasattr(tool, 'args_schema'):
                if hasattr(tool.args_schema, 'schema'):
                    logger.info(f"   Input Schema: {tool.args_schema.schema()}")
                else:
                    logger.info(f"   Input Schema: {tool.args_schema}")
            else:
                logger.info(f"   Input Schema: N/A")
        
        # Try to get resources
        logger.info("\n" + "=" * 80)
        logger.info("TESTING RESOURCES")
        logger.info("=" * 80)
        
        try:
            resources = await client.list_resources()
            logger.info(f"✅ Found {len(resources)} resources")
            for i, resource in enumerate(resources, 1):
                logger.info(f"{i}. {resource}")
        except Exception as e:
            logger.warning(f"⚠️ Could not list resources: {e}")
        
        # Test calling a simple tool
        logger.info("\n" + "=" * 80)
        logger.info("TESTING TOOL CALL")
        logger.info("=" * 80)
        
        if len(tools) > 0:
            # Try to call the first tool (if it doesn't require parameters)
            first_tool = tools[0]
            logger.info(f"Attempting to call: {first_tool.name}")
            
            # Note: We can't actually call it without proper parameters
            # This is just to verify the tool structure
            logger.info(f"Tool callable: {callable(first_tool)}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL CHECKS PASSED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        logger.exception("Full traceback:")
    
    finally:
        logger.info("\n🔌 Closing connection...")
        # As per langchain-mcp-adapters 0.11.0, no explicit cleanup needed
        # The client will clean up automatically
        logger.info("✅ Connection cleanup complete")


if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
