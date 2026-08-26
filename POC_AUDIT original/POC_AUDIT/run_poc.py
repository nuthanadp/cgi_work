#!/usr/bin/env python3
"""
Quick start script for the APS POC demonstration
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import pandas
        import groq
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install dependencies:")
        print("   pip install -r requirements.txt")
        return False

def run_tests():
    """Run basic tests to validate functionality"""
    print("🧪 Running basic tests...")
    
    test_file = Path("tests/test_basic.py")
    if not test_file.exists():
        print("❌ Test file not found")
        return False
    
    try:
        result = subprocess.run([sys.executable, str(test_file)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Tests passed")
            return True
        else:
            print("❌ Tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_demo():
    """Run the main demonstration"""
    print("🚀 Starting APS POC demonstration...")
    
    try:
        # Import and run the main demo
        from main import main
        result = main()
        print("✅ Demo completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

def start_api_server():
    """Start the API server"""
    print("🌐 Starting API server...")
    print("   Access the API at: http://localhost:8000")
    print("   API documentation: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop")
    
    try:
        from main import APSDemo
        demo = APSDemo()
        app = demo.run_api_demo()
        
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ API server failed: {e}")
        return False

def main():
    """Main entry point for quick start"""
    print("🏦 APS (Automatic Payment System) POC")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Show options
    print("\nWhat would you like to do?")
    print("1. Run tests only")
    print("2. Run complete demo")  
    print("3. Start API server")
    print("4. Run tests + demo + API")
    print("0. Exit")
    
    try:
        choice = input("\nEnter your choice (0-4): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            return
        
        elif choice == "1":
            run_tests()
        
        elif choice == "2":
            run_demo()
        
        elif choice == "3":
            start_api_server()
        
        elif choice == "4":
            print("🎯 Running complete demonstration...")
            
            if run_tests():
                if run_demo():
                    print("\n🌐 Starting API server (Ctrl+C to exit)...")
                    start_api_server()
        
        else:
            print("❌ Invalid choice")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()