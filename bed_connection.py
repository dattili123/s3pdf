import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def check_bedrock_connectivity(region="us-east-1"):
    """
    Check connectivity to the AWS Bedrock Runtime service.

    Args:
        region (str): The AWS region to use for the Bedrock service.

    Returns:
        None
    """
    try:
        # Create a Bedrock client
        client = boto3.client("bedrock-runtime", region_name=region)
        
        # List available models (a harmless API call to test connectivity)
        response = client.list_models()
        print("Successfully connected to AWS Bedrock!")
        print("Available Models:")
        for model in response.get("models", []):
            print(f"- Model ID: {model.get('modelId')}")
    except NoCredentialsError:
        print("AWS credentials not found. Please configure your credentials.")
    except PartialCredentialsError:
        print("AWS credentials are incomplete. Please check your configuration.")
    except Exception as e:
        print(f"Error connecting to AWS Bedrock: {e}")

# Example Usage
check_bedrock_connectivity()
