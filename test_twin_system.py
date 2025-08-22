#!/usr/bin/env python3
"""
Test the Twin System with different collaboration modes
"""

import json
import asyncio
import requests

def test_twin_system_local():
    """Test the twin system locally"""
    base_url = "http://localhost:8080"
    
    print("🚀 Testing AppBank Twin System Locally")
    print("=" * 60)
    
    # Test 1: List all agents
    print("\n📋 Test 1: List all agents")
    try:
        response = requests.get(f"{base_url}/agents")
        if response.status_code == 200:
            agents = response.json()
            print("✅ Available agents:")
            for agent in agents["agents"]:
                print(f"  - {agent['name']} ({agent['role']}) - {agent['memory_entries']} memory entries")
        else:
            print(f"❌ Failed to get agents: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Direct communication with Utsav
    print("\n🎯 Test 2: Direct communication with Utsav (Cloud Ops)")
    test_direct_communication(base_url, "utsav_fullstack", "What's the current AWS cost optimization strategy for AppBank?")
    
    # Test 3: Direct communication with Niyas
    print("\n🎯 Test 3: Direct communication with Niyas (AI Developer)")
    test_direct_communication(base_url, "niyas_ai", "What AI models should we consider for our mobile app's recommendation system?")
    
    # Test 4: Orchestrated collaboration
    print("\n🤝 Test 4: Orchestrated collaboration (Team Coordinator)")
    test_orchestrated_collaboration(base_url, "We need to build a new feature that combines mobile app development, database design, and AI capabilities. How should we approach this?")
    
    # Test 5: Business decision with Owner/CEO
    print("\n👑 Test 5: Business decision with Owner/CEO")
    test_direct_communication(base_url, "owner_ceo", "Should we prioritize mobile app development or AI features for Q4? What's the business impact?")
    
    # Test 6: Check agent memories
    print("\n💾 Test 6: Check agent memories")
    test_agent_memories(base_url, "utsav_fullstack")
    test_agent_memories(base_url, "team_coordinator")

def test_direct_communication(base_url: str, agent_id: str, message: str):
    """Test direct communication with a specific agent"""
    payload = {
        "user_message": message,
        "target_agent": agent_id,
        "collaboration_mode": "direct",
        "context": {"test_mode": True}
    }
    
    try:
        response = requests.post(f"{base_url}/twin-system", json=payload)
        if response.status_code == 200:
            result = response.json()
            agent_name = result["output"]["agent"]
            response_text = result["output"]["message"]["content"][0]["text"]
            print(f"✅ {agent_name} responded:")
            print(f"   {response_text[:200]}...")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_orchestrated_collaboration(base_url: str, message: str):
    """Test orchestrated collaboration through team coordinator"""
    payload = {
        "user_message": message,
        "collaboration_mode": "orchestrator",
        "context": {"test_mode": True, "priority": "high"}
    }
    
    try:
        response = requests.post(f"{base_url}/twin-system", json=payload)
        if response.status_code == 200:
            result = response.json()
            response_text = result["output"]["message"]["content"][0]["text"]
            print(f"✅ Team Coordinator orchestrated response:")
            print(f"   {response_text[:200]}...")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_agent_memories(base_url: str, agent_id: str):
    """Test retrieving agent memories"""
    try:
        response = requests.get(f"{base_url}/agent/{agent_id}/memory")
        if response.status_code == 200:
            memory = response.json()
            print(f"✅ {memory['agent_name']} memory: {memory['memory_entries']} entries")
        else:
            print(f"❌ Failed to get memory: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_standard_invocation(base_url: str):
    """Test standard Bedrock AgentCore invocation"""
    print("\n🔧 Test 7: Standard Bedrock AgentCore invocation")
    payload = {
        "input": {
            "prompt": "What is the current status of our mobile app development project?"
        }
    }
    
    try:
        response = requests.post(f"{base_url}/invocations", json=payload)
        if response.status_code == 200:
            result = response.json()
            response_text = result["output"]["message"]["content"][0]["text"]
            print(f"✅ Standard invocation response:")
            print(f"   {response_text[:200]}...")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Twin System Testing Suite")
    print("Make sure your twin system is running on localhost:8080")
    print("=" * 60)
    
    try:
        test_twin_system_local()
        test_standard_invocation("http://localhost:8080")
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        print("\n💡 Make sure to start your twin system first:")
        print("   uv run twin_system.py")
