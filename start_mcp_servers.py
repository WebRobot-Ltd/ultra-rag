#!/usr/bin/env python3
"""
UltraRAG MCP Servers Launcher
Starts all available MCP servers for AI agent access
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# List of all available MCP servers
MCP_SERVERS = [
    "sayhello",
    "corpus", 
    "custom",
    "evaluation",
    "generation",
    "prompt",
    "reranker",
    "retriever",
    "benchmark"
]

class MCPServerManager:
    def __init__(self):
        self.processes = []
        self.base_path = Path(__file__).parent
        
        # Authentication configuration
        self.enable_auth = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'
        self.auth_config = {
            'database_url': os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/strapi'),
            'jwt_secret': os.environ.get('JWT_SECRET', 'your-secret-key'),
            'api_key_header': 'X-API-Key'
        }
        
        if self.enable_auth:
            print("🔐 Authentication enabled for MCP servers")
            print(f"   Database URL: {self.auth_config['database_url']}")
        else:
            print("⚠️  Authentication disabled for MCP servers")
        
    def start_server(self, server_name):
        """Start a single MCP server"""
        server_path = self.base_path / "servers" / server_name / "src" / f"{server_name}.py"
        
        if not server_path.exists():
            print(f"❌ Server {server_name} not found at {server_path}")
            return None
            
        try:
            print(f"🚀 Starting MCP server: {server_name}")
            
            # Prepare environment variables
            env = os.environ.copy()
            env['ENABLE_AUTH'] = str(self.enable_auth).lower()
            env['DATABASE_URL'] = self.auth_config['database_url']
            env['JWT_SECRET'] = self.auth_config['jwt_secret']
            
            process = subprocess.Popen(
                [sys.executable, str(server_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            self.processes.append((server_name, process))
            print(f"✅ Server {server_name} started with PID {process.pid}")
            return process
        except Exception as e:
            print(f"❌ Failed to start server {server_name}: {e}")
            return None
    
    def start_all_servers(self):
        """Start all available MCP servers"""
        print("🎯 UltraRAG MCP Servers Launcher")
        print("=" * 50)
        
        for server_name in MCP_SERVERS:
            self.start_server(server_name)
            time.sleep(1)  # Small delay between starts
        
        print(f"\n🎉 Started {len(self.processes)} MCP servers")
        print("\nAvailable servers:")
        for server_name, process in self.processes:
            status = "🟢 Running" if process.poll() is None else "🔴 Stopped"
            print(f"  - {server_name}: {status} (PID: {process.pid})")
    
    def stop_all_servers(self):
        """Stop all running MCP servers"""
        print("\n🛑 Stopping all MCP servers...")
        for server_name, process in self.processes:
            if process.poll() is None:  # Process is still running
                print(f"Stopping {server_name} (PID: {process.pid})")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Force killing {server_name}")
                    process.kill()
        print("✅ All servers stopped")
    
    def monitor_servers(self):
        """Monitor server health and restart if needed"""
        print("\n👀 Monitoring servers... (Press Ctrl+C to stop)")
        try:
            while True:
                time.sleep(10)
                for server_name, process in self.processes:
                    if process.poll() is not None:  # Process has stopped
                        print(f"⚠️  Server {server_name} stopped unexpectedly, restarting...")
                        self.start_server(server_name)
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested")
            self.stop_all_servers()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    manager.stop_all_servers()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    manager = MCPServerManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            print("Available MCP servers:")
            for server in MCP_SERVERS:
                print(f"  - {server}")
        elif sys.argv[1] in MCP_SERVERS:
            print(f"Starting single server: {sys.argv[1]}")
            manager.start_server(sys.argv[1])
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_all_servers()
        else:
            print(f"Unknown server: {sys.argv[1]}")
            print("Available servers:", ", ".join(MCP_SERVERS))
    else:
        # Start all servers
        manager.start_all_servers()
        manager.monitor_servers()
