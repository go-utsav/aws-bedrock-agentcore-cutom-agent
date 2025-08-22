#!/usr/bin/env python3
"""
AWS Bedrock Setup and Test Script
This script helps you set up and test your AWS Bedrock configuration
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def check_aws_credentials():
    """Check if AWS credentials are properly configured"""
    print("Checking AWS credentials...")
    
    try:
        # Try to get credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials:
            print("✅ AWS credentials found")
            print(f"   Access Key: {credentials.access_key[:10]}...")
            print(f"   Secret Key: {credentials.secret_key[:10]}...")
            print(f"   Token: {'Yes' if credentials.token else 'No'}")
            return True
        else:
            print("❌ No AWS credentials found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        return False

def check_bedrock_access(region="eu-west-2"):
    """Check if Bedrock is accessible in the specified region"""
    print(f"\nChecking Bedrock access in {region}...")
    
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        
        # Try to list models
        response = bedrock.list_foundation_models()
        print(f"✅ Bedrock accessible in {region}")
        print(f"   Found {len(response['modelSummaries'])} models")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnauthorizedOperation':
            print(f"❌ Unauthorized to access Bedrock in {region}")
            print("   Check your IAM permissions")
        elif error_code == 'InvalidParameterValue':
            print(f"❌ Invalid region: {region}")
        else:
            print(f"❌ Error accessing Bedrock: {e}")
        return False
        
    except NoCredentialsError:
        print("❌ No AWS credentials configured")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def list_available_models(region="eu-west-2"):
    """List all available models in the specified region"""
    print(f"\nListing available models in {region}...")
    
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        response = bedrock.list_foundation_models()
        
        print("Available Models:")
        print("=" * 80)
        
        for model in response['modelSummaries']:
            print(f"Model ID: {model['modelId']}")
            print(f"Name: {model['modelName']}")
            print(f"Provider: {model['providerName']}")
            print(f"Input: {', '.join(model['inputModalities'])}")
            print(f"Output: {', '.join(model['outputModalities'])}")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")

def test_model_invocation(model_id, region="eu-west-2"):
    """Test if a specific model can be invoked"""
    print(f"\nTesting model invocation for {model_id} in {region}...")
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # Simple test prompt
        prompt = "Hello, this is a test message."
        
        if "claude" in model_id.lower():
            # Claude format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": prompt}]
            }
        elif "titan" in model_id.lower():
            # Titan format
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 100,
                    "temperature": 0.7
                }
            }
        else:
            print(f"⚠️  Unknown model type, skipping invocation test")
            return False
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        print(f"✅ Model {model_id} is accessible and can be invoked")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ValidationException':
            print(f"❌ Model {model_id} is not valid or accessible")
        elif error_code == 'AccessDeniedException':
            print(f"❌ Access denied to model {model_id}")
        else:
            print(f"❌ Error testing model: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error testing model: {e}")
        return False

def main():
    """Main setup function"""
    print("AWS Bedrock Setup and Test")
    print("=" * 40)
    
    # Check credentials
    if not check_aws_credentials():
        print("\nTo fix this, set up your AWS credentials:")
        print("1. Install AWS CLI: pip install awscli")
        print("2. Run: aws configure")
        print("3. Or set environment variables:")
        print("   export AWS_ACCESS_KEY_ID=your_key")
        print("   export AWS_SECRET_ACCESS_KEY=your_secret")
        print("   export AWS_DEFAULT_REGION=eu-west-2")
        return
    
    # Check Bedrock access
    if not check_bedrock_access():
        print("\nTo fix this:")
        print("1. Ensure Bedrock is available in eu-west-2")
        print("2. Check your IAM permissions include bedrock:*")
        print("3. Request access to Bedrock models in AWS console")
        return
    
    # List available models
    list_available_models()
    
    # Test specific model
    test_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    test_model_invocation(test_model)
    
    print("\nSetup complete! Check the output above for any issues.")

if __name__ == "__main__":
    import json
    main()
