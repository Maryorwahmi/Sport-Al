#!/usr/bin/env python3
"""
SMC Forez API Server
This is a lightweight wrapper around main.py for compatibility with existing task configurations
"""

from main import app

# This file exists for compatibility with existing VS Code tasks
# The actual server logic is in main.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=3001, reload=True)