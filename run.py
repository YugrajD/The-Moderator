#!/usr/bin/env python3
"""
Simple startup script for the UN Diplomatic Simulation
"""
import os
import sys
import time
import webbrowser
import threading
from server import app

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

def main():
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ No .env file found!")
        print("📝 Please copy .env.template to .env and add your Claude API key:")
        print("   cp .env.template .env")
        print("   # Then edit .env with your ANTHROPIC_API_KEY")
        sys.exit(1)
    
    # Check if API key is set
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your_claude_api_key_here":
        print("❌ ANTHROPIC_API_KEY not set in .env file!")
        print("📝 Please edit .env and add your Claude API key")
        sys.exit(1)
    
    print("🌍 Starting UN Diplomatic Simulation...")
    print("🚀 Server will start on http://localhost:5000")
    print("🌐 Browser will open automatically...")
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start Flask app
    try:
        app.run(debug=True, port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    main() 