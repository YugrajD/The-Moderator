#!/usr/bin/env python3
"""
Launcher for the text-based UN Diplomatic Simulation interface
"""

import subprocess
import sys
import time
import requests

def check_server():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:5001/api/tts/status", timeout=3)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start the Flask server"""
    print("Starting Flask server...")
    try:
        # Start server in background
        process = subprocess.Popen([sys.executable, "server.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for server to start
        for i in range(10):
            if check_server():
                print("✅ Server started successfully!")
                return process
            time.sleep(1)
            print(f"Waiting for server... ({i+1}/10)")
        
        print("❌ Server failed to start")
        return None
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def main():
    print("🌍 UN Diplomatic Simulation - Text Interface Launcher")
    print("=" * 50)
    
    # Check if server is already running
    if check_server():
        print("✅ Server is already running!")
    else:
        print("🔄 Starting server...")
        server_process = start_server()
        if not server_process:
            print("❌ Failed to start server. Please start it manually with: python server.py")
            return
    
    print("\n🎮 Starting text interface...")
    print("📝 All game messages will be written to message.txt")
    print("🔊 TTS audio will be generated and noted in the logs")
    print("=" * 50)
    
    # Start the text interface
    try:
        subprocess.run([sys.executable, "text_interface.py"])
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error running text interface: {e}")

if __name__ == "__main__":
    main() 