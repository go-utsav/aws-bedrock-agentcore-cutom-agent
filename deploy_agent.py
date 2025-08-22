import boto3

# Bedrock AgentCore is available in us-east-1, us-west-2, and ap-southeast-1
# Using us-east-1 (N. Virginia) as it's the primary region for this service
client = boto3.client('bedrock-agentcore-control', region_name='us-east-1')

response = client.create_agent_runtime(
    agentRuntimeName='strands_agent',
    agentRuntimeArtifact={
        'containerConfiguration': {
            'containerUri': '540737535723.dkr.ecr.us-east-1.amazonaws.com/my-strands-agent:latest'
        }
    },
    networkConfiguration={"networkMode": "PUBLIC"},
    roleArn='arn:aws:iam::540737535723:role/AgentRuntimeRole'  # Updated with your actual account ID
)

print(f"Agent Runtime created successfully!")
print(f"Agent Runtime ARN: {response['agentRuntimeArn']}")
print(f"Status: {response['status']}")