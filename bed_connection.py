import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def check_bedrock_connectivity(region="us-east-1", model_id="amazon.titan-text-v1"):
    """
    Check connectivity to the AWS Bedrock Runtime service by invoking a dummy prompt.

    Args:
        region (str): The AWS region to use for the Bedrock service.
        model_id (str): The AWS Bedrock model ID to test.

    Returns:
        None
    """
    try:
        # Create a Bedrock Runtime client
        client = boto3.client("bedrock-runtime", region_name=region)
        
        # Send a basic test request
        response = client.invoke_model(
            modelId=model_id,
            body='{"input": "Test connectivity to AWS Bedrock."}',
            contentType="application/json",
        )
        print("Successfully connected to AWS Bedrock!")
        print("Response:")
        print(response)
    except NoCredentialsError:
        print("AWS credentials not found. Please configure your credentials.")
    except PartialCredentialsError:
        print("AWS credentials are incomplete. Please check your configuration.")
    except Exception as e:
        print(f"Error connecting to AWS Bedrock: {e}")

# Example Usage
check_bedrock_connectivity()
