#!/usr/bin/env python3
"""
FastMCP Server Entrypoint for Antigravity & MCP Clients
(Cursor, VS Code Cline/Roo, Claude Desktop, Antigravity)
"""

import sys
import os

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_dispatcher import mcp, logger

if __name__ == "__main__":
    logger.info("Starting Local AI & Token Auditor FastMCP Server via stdio...")
    mcp.run(transport="stdio")
