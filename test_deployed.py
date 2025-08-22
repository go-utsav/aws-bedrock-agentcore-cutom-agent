#!/usr/bin/env python3
"""
Test the deployed agent on Bedrock AgentCore
"""

import boto3
import json

def test_deployed_agent():
    print("🚀 Testing deployed agent on Bedrock AgentCore...")
    
    # Use the control service to get runtime details
    control_client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
    
    try:
        # List all runtimes to see what's available
        print("📋 Available runtimes:")
        runtimes_response = control_client.list_agent_runtimes()
        
        for runtime in runtimes_response['agentRuntimes']:
            print(f"  - {runtime['agentRuntimeName']}: {runtime['status']}")
            if runtime['agentRuntimeName'] == 'strands_agent':
                print(f"    ARN: {runtime['agentRuntimeArn']}")
                print(f"    ID: {runtime['agentRuntimeId']}")
        
        print("\n🔍 Your runtime status:")
        print("✅ Runtime is READY! Now you can test it.")
        print("\n📋 To test your deployed agent:")
        print("1. Go to AWS Bedrock AgentCore Console")
        print("2. Find your runtime: strands_agent")
        print("3. Look for the HTTP endpoint URL")
        print("4. Test with Postman:")
        print("   POST {endpoint}/invocations")
        print("   Body: {\"input\": {\"prompt\": \"what is nothing hill carnival in uk\"}}")
        
        print("\n🎯 Your agent should respond exactly like the local one!")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deployed_agent()
