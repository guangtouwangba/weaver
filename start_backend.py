#!/usr/bin/env python3
"""Simple script to start the backend API server."""
import subprocess
import sys
import os

# Change to project root
os.chdir('/Users/siqiuchen/Documents/opensource/research-agent-rag')

# Start uvicorn
cmd = ['uv', 'run', 'uvicorn', 'app:app', '--reload', '--host', '0.0.0.0', '--port', '8000']
print(f"Starting backend: {' '.join(cmd)}")
subprocess.run(cmd)

