#!/usr/bin/env python3
"""
Start script for AuroRag - Agentic RAG Text-to-SQL System
Runs both backend (Streamlit) and frontend (React/Vite)
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            has_model = any("llama3.1" in m.get("name", "").lower() for m in models)
            return True, has_model
    except:
        pass
    return False, False

def main():
    print("🚀 Starting AuroRag System...")
    print("=" * 50)
    
    # Get project root and directories
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "frontend"
    
    # Check Ollama
    ollama_running, model_available = check_ollama()
    if ollama_running:
        print("✅ Ollama service is running")
        if model_available:
            print("✅ llama3.1:8b model is available")
        else:
            print("⚠️  Warning: llama3.1:8b model not found")
            print("   Download it with: ollama pull llama3.1:8b")
    else:
        print("⚠️  Warning: Ollama service not detected")
        print("   Make sure Ollama is running: ollama serve")
    
    print("\nStarting services...\n")
    
    processes = []
    
    try:
        # Start FastAPI
        print("🚀 Starting FastAPI backend (port 8000)...")
        api = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api_server:app", 
             "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(api)
        time.sleep(3)
        
        # Check if node_modules exists in frontend
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=False)
        
        # Start Vite
        print("⚛️  Starting React frontend (port 5173)...")
        vite = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(vite)
        time.sleep(3)
        
        print("\n✅ Services started!")
        print("=" * 50)
        print("\nBackend (FastAPI):   http://localhost:8000")
        print("Frontend (React):    http://localhost:5173")
        print("\nPress Ctrl+C to stop all services\n")
        
        # Wait for processes
        for p in processes:
            p.wait()
            
    except KeyboardInterrupt:
        print("\n\nShutting down services...")
        for p in processes:
            p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
