import boto3
from botocore.exceptions import ClientError

def list_available_models():
    """List all available Bedrock models in eu-west-2 region"""
    try:
        bedrock = boto3.client('bedrock', region_name='eu-west-2')
        
        # List foundation models
        response = bedrock.list_foundation_models()
        
        print("Available Foundation Models in eu-west-2:")
        print("=" * 50)
        
        for model in response['modelSummaries']:
            print(f"Model ID: {model['modelId']}")
            print(f"Model Name: {model['modelName']}")
            print(f"Provider: {model['providerName']}")
            print(f"Input Modalities: {model['inputModalities']}")
            print(f"Output Modalities: {model['outputModalities']}")
            print("-" * 30)
            
    except ClientError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    list_available_models()
