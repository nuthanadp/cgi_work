#!/usr/bin/env python
"""
APS Frontend Launcher
Starts the Streamlit web interface for the Automatic Payment System
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("🏦 APS - Automatic Payment System")
    print("=" * 50)
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def launch_streamlit():
    """Launch the Streamlit application"""
    print("\n🚀 Launching Streamlit app...")
    print("📱 Open your browser and go to: http://localhost:8501")
    print("🛑 To stop the app, press Ctrl+C")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 APS Frontend stopped. Thank you!")
    except Exception as e:
        print(f"❌ Error launching Streamlit: {e}")

def main():
    """Main launcher function"""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Install dependencies
    if install_dependencies():
        # Launch app
        launch_streamlit()
    else:
        print("❌ Cannot start app due to dependency installation failure")
        sys.exit(1)

if __name__ == "__main__":
    main()