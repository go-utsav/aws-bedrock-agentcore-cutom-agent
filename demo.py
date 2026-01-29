#!/usr/bin/env python3
"""
AppBank Twin System - Quick Demo Launcher
Perfect for showing the system to stakeholders
"""

import subprocess
import sys
import time
import requests
from threading import Thread
import os

def check_twin_system_running():
    """Check if twin system is running"""
    try:
        response = requests.get("http://localhost:8080/ping", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_twin_system():
    """Start the twin system in background"""
    print("🚀 Starting AppBank Twin System...")
    try:
        # Start twin system in background
        process = subprocess.Popen([
            sys.executable, "twin_system.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for it to start
        for i in range(10):
            if check_twin_system_running():
                print("✅ Twin System is running!")
                return process
            time.sleep(1)
            print(f"⏳ Waiting for system to start... ({i+1}/10)")
        
        print("❌ Failed to start twin system")
        return None
    except Exception as e:
        print(f"❌ Error starting twin system: {e}")
        return None

def run_proof_of_concept():
    """Run the proof of concept tests"""
    print("\n🧪 Running Proof of Concept Demo...")
    try:
        result = subprocess.run([sys.executable, "test_twin_system.py"], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def start_interactive_chat():
    """Start the interactive chat"""
    print("\n💬 Starting Interactive Chat Interface...")
    try:
        subprocess.run([sys.executable, "interactive_chat.py"])
    except KeyboardInterrupt:
        print("\n👋 Chat session ended.")
    except Exception as e:
        print(f"❌ Error starting chat: {e}")

def main():
    """Main demo function"""
    print("🏦 AppBank Twin System - Demo Launcher")
    print("="*60)
    print("This will:")
    print("1. Start the Twin System server")
    print("2. Run proof of concept tests")
    print("3. Launch interactive chat interface")
    print("="*60)
    
    input("Press Enter to start the demo...")
    
    # Check if already running
    if check_twin_system_running():
        print("✅ Twin System is already running!")
    else:
        # Start twin system
        process = start_twin_system()
        if not process:
            print("❌ Cannot start twin system. Please check your setup.")
            return
    
    # Run proof of concept
    print("\n" + "="*60)
    success = run_proof_of_concept()
    
    if success:
        print("\n" + "="*60)
        print("🎉 Proof of concept completed successfully!")
        print("Ready to start interactive demo...")
        
        choice = input("\nStart interactive chat? (y/n): ").lower().strip()
        if choice in ['y', 'yes', '']:
            start_interactive_chat()
        else:
            print("Demo completed. Twin system is still running on localhost:8080")
            print("You can start the chat anytime with: python interactive_chat.py")
    else:
        print("❌ Proof of concept tests failed. Please check the system.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
