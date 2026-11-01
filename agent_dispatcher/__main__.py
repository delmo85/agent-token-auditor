"""
Module entrypoint for `python -m agent_dispatcher`.
"""

from agent_dispatcher.config import mcp, logger

if __name__ == "__main__":
    logger.info("Starting Local AI MCP Server via stdio...")
    mcp.run(transport="stdio")

