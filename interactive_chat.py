#!/usr/bin/env python3
"""
Interactive Terminal Chat Interface for AppBank Twin System
Perfect for demos and proof of concept presentations
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Optional

class AppBankChat:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session_history = []
        self.available_agents = {}
        self.current_mode = "orchestrator"
        self.current_agent = None
        
        # Load available agents
        self._load_agents()
        
    def _load_agents(self):
        """Load available agents from the twin system"""
        try:
            response = requests.get(f"{self.base_url}/agents")
            if response.status_code == 200:
                agents_data = response.json()
                for agent in agents_data["agents"]:
                    self.available_agents[agent["id"]] = {
                        "name": agent["name"],
                        "role": agent["role"],
                        "expertise": agent["expertise"]
                    }
                print(f"✅ Connected to AppBank Twin System - {len(self.available_agents)} agents available")
            else:
                print(f"❌ Failed to load agents: {response.status_code}")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Cannot connect to twin system: {e}")
            print("💡 Make sure your twin system is running: uv run twin_system.py")
            sys.exit(1)
    
    def display_welcome(self):
        """Display welcome message and instructions"""
        print("\n" + "="*80)
        print("🏦 Welcome to AppBank AI Twin System - Interactive Chat")
        print("="*80)
        print("\n🎯 Available Chat Modes:")
        print("  1. 🤝 ORCHESTRATOR (default) - Team Coordinator routes your request")
        print("  2. 🎯 DIRECT - Talk directly to a specific agent")
        print("\n👥 Available Agents:")
        for agent_id, agent_info in self.available_agents.items():
            print(f"  • {agent_info['name']} ({agent_info['role']})")
            print(f"    Expertise: {', '.join(agent_info['expertise'])}")
        
        print("\n🔧 Commands:")
        print("  /mode orchestrator  - Switch to orchestrator mode")
        print("  /mode direct        - Switch to direct agent mode")
        print("  /agent <agent_name> - Set target agent for direct mode")
        print("  /agents             - List all agents")
        print("  /history            - Show chat history")
        print("  /clear              - Clear chat history")
        print("  /help               - Show this help")
        print("  /quit or /exit      - Exit the chat")
        print("\n💬 Just type your message to start chatting!")
        print("-"*80)
    
    def display_status(self):
        """Display current chat status"""
        mode_emoji = "🤝" if self.current_mode == "orchestrator" else "🎯"
        agent_info = f" → {self.current_agent}" if self.current_agent else ""
        print(f"\n{mode_emoji} Mode: {self.current_mode.upper()}{agent_info}")
    
    def handle_command(self, command: str) -> bool:
        """Handle chat commands. Returns True if command was processed, False otherwise"""
        parts = command.strip().split()
        cmd = parts[0].lower()
        
        if cmd in ['/quit', '/exit']:
            print("\n👋 Thanks for using AppBank Twin System! Goodbye!")
            return True
            
        elif cmd == '/help':
            self.display_welcome()
            
        elif cmd == '/mode':
            if len(parts) > 1:
                mode = parts[1].lower()
                if mode in ['orchestrator', 'direct']:
                    self.current_mode = mode
                    if mode == 'orchestrator':
                        self.current_agent = None
                    print(f"✅ Switched to {mode.upper()} mode")
                else:
                    print("❌ Invalid mode. Use 'orchestrator' or 'direct'")
            else:
                print("❌ Please specify mode: /mode orchestrator or /mode direct")
                
        elif cmd == '/agent':
            if len(parts) > 1:
                agent_name = ' '.join(parts[1:]).lower()
                # Find agent by name (case insensitive)
                found_agent = None
                for agent_id, agent_info in self.available_agents.items():
                    if agent_info['name'].lower() == agent_name:
                        found_agent = agent_id
                        break
                
                if found_agent:
                    self.current_agent = found_agent
                    self.current_mode = 'direct'
                    agent_info = self.available_agents[found_agent]
                    print(f"✅ Set target agent to {agent_info['name']} ({agent_info['role']})")
                else:
                    print(f"❌ Agent '{agent_name}' not found")
                    print("Available agents:", [info['name'] for info in self.available_agents.values()])
            else:
                print("❌ Please specify agent name: /agent <name>")
                
        elif cmd == '/agents':
            print("\n👥 Available Agents:")
            for agent_id, agent_info in self.available_agents.items():
                memory_count = self._get_agent_memory_count(agent_id)
                print(f"  • {agent_info['name']} ({agent_info['role']}) - {memory_count} memories")
                
        elif cmd == '/history':
            self._display_history()
            
        elif cmd == '/clear':
            self.session_history.clear()
            print("✅ Chat history cleared")
            
        else:
            print(f"❌ Unknown command: {cmd}")
            print("Type /help for available commands")
            
        return False
    
    def _get_agent_memory_count(self, agent_id: str) -> int:
        """Get memory count for an agent"""
        try:
            response = requests.get(f"{self.base_url}/agent/{agent_id}/memory")
            if response.status_code == 200:
                return response.json()["memory_entries"]
        except:
            pass
        return 0
    
    def _display_history(self):
        """Display chat history"""
        if not self.session_history:
            print("📝 No chat history yet")
            return
            
        print("\n📝 Chat History:")
        print("-"*60)
        for i, entry in enumerate(self.session_history, 1):
            timestamp = entry['timestamp']
            mode = entry['mode']
            agent = entry.get('agent', 'Team Coordinator')
            user_msg = entry['user_message'][:100] + "..." if len(entry['user_message']) > 100 else entry['user_message']
            
            print(f"{i}. [{timestamp}] {mode.upper()}")
            print(f"   👤 You: {user_msg}")
            print(f"   🤖 {agent}: Response received")
            print()
    
    def send_message(self, message: str) -> Optional[Dict]:
        """Send message to the twin system"""
        try:
            if self.current_mode == "orchestrator":
                payload = {
                    "user_message": message,
                    "collaboration_mode": "orchestrator",
                    "context": {"interactive_session": True, "timestamp": datetime.now().isoformat()}
                }
                endpoint = "/twin-system"
            else:  # direct mode
                if not self.current_agent:
                    print("❌ No agent selected for direct mode. Use /agent <name> first")
                    return None
                    
                payload = {
                    "user_message": message,
                    "target_agent": self.current_agent,
                    "collaboration_mode": "direct",
                    "context": {"interactive_session": True, "timestamp": datetime.now().isoformat()}
                }
                endpoint = "/twin-system"
            
            response = requests.post(f"{self.base_url}{endpoint}", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"❌ Request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None
    
    def display_response(self, result: Dict, user_message: str):
        """Display agent response in a formatted way"""
        output = result["output"]
        agent_name = output.get("agent", "Team Coordinator")
        role = output.get("role", "Orchestrator")
        response_text = output["message"]["content"][0]["text"]
        timestamp = output.get("timestamp", datetime.now().isoformat())
        
        # Store in history
        history_entry = {
            "timestamp": timestamp,
            "mode": self.current_mode,
            "agent": agent_name,
            "user_message": user_message,
            "response": response_text
        }
        self.session_history.append(history_entry)
        
        # Display response
        print(f"\n🤖 {agent_name} ({role}) responds:")
        print("="*60)
        print(response_text)
        print("="*60)
        print(f"⏰ {timestamp}")
    
    def run(self):
        """Run the interactive chat loop"""
        self.display_welcome()
        
        while True:
            try:
                self.display_status()
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if self.handle_command(user_input):
                        break
                    continue
                
                # Send message to twin system
                print("\n🔄 Processing your request...")
                result = self.send_message(user_input)
                
                if result:
                    self.display_response(result, user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break

def main():
    """Main function to run the interactive chat"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AppBank Twin System Interactive Chat")
    parser.add_argument("--url", default="http://localhost:8080", 
                       help="Twin system URL (default: http://localhost:8080)")
    args = parser.parse_args()
    
    chat = AppBankChat(args.url)
    chat.run()

if __name__ == "__main__":
    main()
