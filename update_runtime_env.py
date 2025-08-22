import boto3
import json

# Create Bedrock AgentCore control client
client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')

try:
    print("Updating agent runtime with AWS credentials environment variables...")
    
    # Update the agent runtime with environment variables
    response = client.update_agent_runtime(
        agentRuntimeId='strands_agent-7kPP2NCKny',
        agentRuntimeArtifact={
            'containerConfiguration': {
                'containerUri': '540737535723.dkr.ecr.us-east-1.amazonaws.com/my-strands-agent:latest'
            }
        },
        roleArn='arn:aws:iam::540737535723:role/AgentRuntimeRole',
        networkConfiguration={"networkMode": "PUBLIC"},
        environmentVariables={
            'AWS_DEFAULT_REGION': 'us-east-1',
            'AWS_REGION': 'us-east-1'
        }
    )
    
    print("✅ Agent runtime updated successfully!")
    print(f"Status: {response.get('status', 'UPDATING')}")
    print("The runtime will restart with the new environment variables. This may take a few minutes.")
    
except Exception as e:
    print(f"❌ Error updating runtime: {e}")
    raise
