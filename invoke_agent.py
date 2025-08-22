import boto3
import json

agent_core_client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# Use the correct payload format according to Bedrock AgentCore contract
payload = json.dumps({
    "input": {
        "prompt": "Explain machine learning in simple terms"
    }
})

print("Sending payload:", payload)

response = agent_core_client.invoke_agent_runtime(
    agentRuntimeArn="arn:aws:bedrock-agentcore:us-east-1:540737535723:runtime/strands_agent-7kPP2NCKny",
    payload=payload,
    qualifier="DEFAULT"
)

response_body = response['response'].read()
response_data = json.loads(response_body)
print("Agent Response:", response_data)