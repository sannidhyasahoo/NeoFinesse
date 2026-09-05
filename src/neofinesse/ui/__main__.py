"""
CLI entry point for running the NeoFinesse Phase 8 Demo & Audit UI server.
Usage: python -m neofinesse.ui [--port 8080] [--open-browser]
"""
from neofinesse.ui.server import main

if __name__ == "__main__":
    main()
