import boto3
import json

agent_core_client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# Test with the simplest possible payload
payload = json.dumps({
    "input": {
        "prompt": "Hello"
    }
})

print("Testing with simplest payload:")
print(f"Payload: {payload}")
print("=" * 50)

try:
    response = agent_core_client.invoke_agent_runtime(
        agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:540737535723:runtime/strands_agent-7kPP2NCKny",
        payload=payload,
        qualifier="DEFAULT"
    )
    
    response_body = response['response'].read()
    response_data = json.loads(response_body)
    print("✅ SUCCESS!")
    print(f"Response: {response_data}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    
    # Check what type of error we're getting
    if "500" in str(e):
        print("   → 500 error: Agent is reachable but has internal error")
        print("   → This means Bedrock CAN reach your agent!")
    elif "422" in str(e):
        print("   → 422 error: Validation error - wrong payload format")
    elif "502" in str(e):
        print("   → 502 error: Agent not reachable")
    else:
        print(f"   → Other error: {type(e).__name__}")
