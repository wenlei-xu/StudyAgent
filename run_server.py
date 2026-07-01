"""Windows-compatible launcher: ensures SelectorEventLoop for psycopg compatibility.

Run from anywhere — auto-chdirs to the project root.
Usage:  python run_server.py
"""
import os
import sys
import asyncio
import selectors

# Ensure CWD is the project root (where .env lives)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
