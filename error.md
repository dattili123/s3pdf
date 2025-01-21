Error invoking AWS Bedrock: An error occurred (ValidationException) when calling the InvokeModel operation: Malformed input request: #: required key [prompt] not found#: required key [max_tokens_to_sample] not found#: extraneous key [input] is not permitted, please reformat your input and try again.
Chatbot Response:
Error generating response.

def generate_answer_with_bedrock(prompt, model_id, region="us-east-1"):
    """
    Use AWS Bedrock to generate an answer using the prompt.

    Args:
        prompt (str): Context and question as the prompt.
        model_id (str): AWS Bedrock model ID.
        region (str): AWS region for Bedrock service.

    Returns:
        str: The generated response from the model.
    """
    client = boto3.client("bedrock-runtime", region_name=region)
    try:
        # Corrected request body format
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "prompt": prompt,
                "max_tokens_to_sample": 300,  # Adjust based on your needs
                "temperature": 0.7,
                "top_p": 0.9
            }),
            contentType="application/json",
        )
        # Parse and return the response
        response_body = json.loads(response["body"].read().decode("utf-8"))
        return response_body.get("completion", "No response generated.")
    except Exception as e:
        print(f"Error invoking AWS Bedrock: {e}")
        return "Error generating response."
