#!/usr/bin/env python3
"""
Install and setup Context 7 MCP server for Prime Agent advanced tools.
"""

import subprocess
import sys
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_context7():
    """Install Context 7 MCP server."""
    try:
        logger.info("Installing Context 7 MCP server...")

        # Install standard MCP package
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "mcp", "--upgrade"
        ])

        logger.info("✅ Context 7 MCP server installed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install Context 7: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def create_context7_config():
    """Create Context 7 configuration file."""
    config = {
        "mcpServers": {
            "context7-prime-agent": {
                "command": "python",
                "args": ["-m", "app.mcp.context7_server"],
                "env": {
                    "PORT": "5012"
                }
            }
        }
    }

    config_path = "agen911/context7_config.json"
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"✅ Context 7 config created at {config_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create config: {e}")
        return False

def main():
    """Main installation process."""
    logger.info("🚀 Setting up Context 7 MCP server for Prime Agent...")

    # Step 1: Install Context 7
    if not install_context7():
        logger.error("❌ Installation failed!")
        return False

    # Step 2: Create configuration
    if not create_context7_config():
        logger.error("❌ Configuration failed!")
        return False

    logger.info("🎉 Context 7 setup completed successfully!")
    logger.info("📋 Next steps:")
    logger.info("   1. Run the Context 7 server: python -m app.mcp.context7_server")
    logger.info("   2. Test the new Prime Agent tools")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
