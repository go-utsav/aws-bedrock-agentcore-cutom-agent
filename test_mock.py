#!/usr/bin/env python3
"""
Test the mock agent locally
"""

import json
import asyncio
from agent_simple import InvocationRequest, invoke_agent_logic

async def test_mock_agent():
    # Test with the same payload that Bedrock is sending
    test_payload = {
        "input": {
            "prompt": "Hello, how are you?"
        }
    }

    print("Testing mock agent locally with Bedrock payload format:")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    print("=" * 60)

    try:
        # Create the request object
        request = InvocationRequest(**test_payload)
        
        # Test the agent logic
        result = await invoke_agent_logic(request)
        
        print("✅ SUCCESS!")
        print(f"Response: {result}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mock_agent())
