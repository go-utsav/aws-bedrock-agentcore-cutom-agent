import boto3
import json

# Create IAM client
iam_client = boto3.client('iam', region_name='us-east-1')

# Role name
role_name = 'AgentRuntimeRole'

# Updated trust policy for Bedrock AgentCore in us-east-1
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock-agentcore.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "540737535723"
                },
                "ArnLike": {
                    "aws:SourceArn": "arn:aws:bedrock-agentcore:us-east-1:540737535723:*"
                }
            }
        }
    ]
}

try:
    print(f"Updating trust policy for role: {role_name}")
    
    # Update the role's trust policy
    response = iam_client.update_assume_role_policy(
        RoleName=role_name,
        PolicyDocument=json.dumps(trust_policy)
    )
    
    print("✅ Trust policy updated successfully!")
    
    # Verify the update
    print("\nVerifying updated trust policy...")
    response = iam_client.get_role(RoleName=role_name)
    updated_policy = response['Role']['AssumeRolePolicyDocument']
    
    print("Updated Trust Policy:")
    print(json.dumps(updated_policy, indent=2))
    
    print(f"\n🎉 Role '{role_name}' is now ready for us-east-1!")
    
except Exception as e:
    print(f"❌ Error updating trust policy: {e}")
    raise
