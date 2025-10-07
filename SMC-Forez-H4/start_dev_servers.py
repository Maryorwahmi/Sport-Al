#!/usr/bin/env python3
"""
SMC Forez Development Launcher
Easily start both API server and frontend for development
"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    try:
        import uvicorn
        import fastapi
        print("✅ Python dependencies: uvicorn, fastapi")
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("Run: pip install uvicorn fastapi")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found. Please install Node.js")
        return False
    
    # Check npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    return True

def install_frontend_dependencies():
    """Install frontend dependencies if needed"""
    frontend_dir = Path("frontend")
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install frontend dependencies")
            return False
    else:
        print("✅ Frontend dependencies already installed")
    
    return True

def start_api_server():
    """Start the API server"""
    print("🚀 Starting API server on http://localhost:3001...")
    
    # Use the virtual environment Python if available
    venv_python = Path(".venv/Scripts/python.exe")
    python_cmd = str(venv_python) if venv_python.exists() else "python"
    
    try:
        process = subprocess.Popen([
            python_cmd, "-m", "uvicorn", 
            "api_server:app", 
            "--host", "127.0.0.1", 
            "--port", "3001", 
            "--reload"
        ])
        return process
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def start_frontend_server():
    """Start the frontend development server"""
    print("🎨 Starting frontend development server on http://localhost:5173...")
    
    try:
        process = subprocess.Popen([
            'npm', 'run', 'dev'
        ], cwd='frontend')
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend server: {e}")
        return None

def main():
    """Main launcher function"""
    print("=" * 60)
    print("🚀 SMC FOREZ DEVELOPMENT LAUNCHER")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Please install missing dependencies.")
        return
    
    # Install frontend dependencies
    if not install_frontend_dependencies():
        print("❌ Frontend setup failed.")
        return
    
    print("\n🌟 Starting development servers...")
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        return
    
    # Wait a moment for API server to start
    time.sleep(3)
    
    # Start frontend server
    frontend_process = start_frontend_server()
    if not frontend_process:
        api_process.terminate()
        return
    
    # Wait for servers to start
    print("\n⏳ Waiting for servers to start...")
    time.sleep(5)
    
    print("\n" + "=" * 60)
    print("🎉 SERVERS STARTED SUCCESSFULLY!")
    print("=" * 60)
    print("🌐 Frontend: http://localhost:5173")
    print("🔌 API Server: http://localhost:3001")
    print("📚 API Docs: http://localhost:3001/docs")
    print("🔌 WebSocket: ws://localhost:3001/ws")
    print("=" * 60)
    
    # Open browser
    try:
        webbrowser.open('http://localhost:5173')
        print("🌐 Opening frontend in your browser...")
    except:
        print("💡 Please open http://localhost:5173 in your browser")
    
    print("\n💡 To stop servers, press Ctrl+C")
    print("💡 Both servers support hot-reloading for development")
    
    try:
        # Keep the launcher running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        if api_process:
            api_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main()