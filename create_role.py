import boto3
import json

# Create IAM client
iam_client = boto3.client('iam', region_name='us-east-1')

# Role name
role_name = 'AgentRuntimeRole'

# Trust policy for Bedrock AgentCore
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock-agentcore.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

# Permission policy for the role
permission_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:*",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }
    ]
}

try:
    # Create the role
    print(f"Creating IAM role: {role_name}")
    response = iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Role for Bedrock AgentCore runtime'
    )
    print(f"✅ Role created successfully: {response['Role']['Arn']}")
    
    # Attach the permission policy
    print("Attaching permission policy...")
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName='BedrockAgentCorePolicy',
        PolicyDocument=json.dumps(permission_policy)
    )
    print("✅ Permission policy attached successfully")
    
    # Wait a moment for the role to propagate
    import time
    print("Waiting for role to propagate...")
    time.sleep(10)
    
    print(f"\n🎉 IAM Role '{role_name}' is ready!")
    print(f"Role ARN: {response['Role']['Arn']}")
    
except Exception as e:
    if "EntityAlreadyExists" in str(e):
        print(f"✅ Role '{role_name}' already exists")
        # Get the existing role ARN
        response = iam_client.get_role(RoleName=role_name)
        print(f"Role ARN: {response['Role']['Arn']}")
    else:
        print(f"❌ Error creating role: {e}")
        raise
