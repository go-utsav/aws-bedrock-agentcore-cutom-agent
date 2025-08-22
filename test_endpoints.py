import boto3
import json

agent_core_client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# Test different payload formats and endpoints
test_cases = [
    {
        "name": "Test 1: Simple prompt format",
        "payload": json.dumps({"prompt": "Hello, how are you?"})
    },
    {
        "name": "Test 2: Input wrapper format",
        "payload": json.dumps({"input": {"prompt": "Hello, how are you?"}})
    },
    {
        "name": "Test 3: Direct message format",
        "payload": json.dumps({"message": "Hello, how are you?"})
    }
]

for i, test_case in enumerate(test_cases, 1):
    print(f"\n{'='*50}")
    print(f"Test {i}: {test_case['name']}")
    print(f"Payload: {test_case['payload']}")
    print(f"{'='*50}")
    
    try:
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:540737535723:runtime/strands_agent-7kPP2NCKny",
            payload=test_case['payload'],
            qualifier="DEFAULT"
        )
        
        response_body = response['response'].read()
        response_data = json.loads(response_body)
        print(f"✅ SUCCESS!")
        print(f"Response: {response_data}")
        break
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        if "500" in str(e):
            print("   → 500 error suggests the endpoint is reachable but there's a processing error")
        elif "502" in str(e):
            print("   → 502 error suggests the endpoint is not reachable")
        else:
            print(f"   → Other error: {type(e).__name__}")
        
        if i < len(test_cases):
            print("   → Trying next test case...")
        else:
            print("   → All test cases failed")
