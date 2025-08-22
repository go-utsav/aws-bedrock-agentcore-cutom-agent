#!/usr/bin/env python3
"""
Test the deployed agent via HTTP endpoint
"""

import json

def test_deployed_agent_http():
    # The agent should be accessible via HTTP on the Bedrock AgentCore runtime
    # We'll test the same payload that worked locally
    
    payload = {
        "input": {
            "prompt": "what is nothing hill carnival in uk"
        }
    }
    
    print("🚀 Testing deployed agent via HTTP...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("=" * 60)

    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

    response = client.invoke_agent_runtime(
    agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:540737535723:runtime/strands_agent-qPj2H261Xl",
    qualifier="<Endpoint Name>",
    payload=input_text
)
    
    # Note: The actual HTTP endpoint URL would be provided by AWS
    # For now, let's check if we can get the runtime details
    print("ℹ️ To test the deployed agent, you need to:")
    print("1. Get the HTTP endpoint URL from AWS Bedrock AgentCore console")
    print("2. Use that URL with /invocations endpoint")
    print("3. Send the same payload that worked locally")
    
    print("\n📋 Your working local test:")
    print("POST http://localhost:8080/invocations")
    print(f"Body: {json.dumps(payload, indent=2)}")
    
    print("\n🔍 To find your deployed agent endpoint:")
    print("1. Go to AWS Bedrock AgentCore console")
    print("2. Find your runtime: strands_agent-qPj2H261Xl")
    print("3. Look for the HTTP endpoint URL")
    print("4. Test with: POST {endpoint}/invocations")

if __name__ == "__main__":
    test_deployed_agent_http()
