import os
import boto3
import json
from PyPDF2 import PdfReader, PdfWriter
import logging

def split_pdf_by_size(input_pdf_path, output_dir, size_limit_mb=1):
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    current_size = 0
    part_number = 1

    for i, page in enumerate(reader.pages):
        writer.add_page(page)
        page_size = len(page.extract_text().encode("utf-8")) / (1024 * 1024)
        current_size += page_size

        if current_size >= size_limit_mb or i == len(reader.pages) - 1:
            output_path = os.path.join(output_dir, f"part_{part_number}.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            print(f"Saved: {output_path} (Size: {current_size:.2f} MB)")
            writer = PdfWriter()
            current_size = 0
            part_number += 1

    print(f"PDF split into {part_number - 1} parts and saved in {output_dir}.")

def find_relevant_pdf(question, split_files_dir):
    max_score = -1
    relevant_pdf = ""

    for file_name in os.listdir(split_files_dir):
        file_path = os.path.join(split_files_dir, file_name)

        if not file_name.endswith(".pdf"):
            continue

        reader = PdfReader(file_path)
        content = " ".join([page.extract_text() for page in reader.pages])
        score = sum(1 for word in question.split() if word.lower() in content.lower())
        if score > max_score:
            max_score = score
            relevant_pdf = file_path

    print(f"Most relevant PDF part: {relevant_pdf}")
    return relevant_pdf

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
        #print("Sending Request to Bedrock:")
        #print(json.dumps({"modelId": model_id, "prompt": prompt}, indent=2))

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                    "max_tokens": 300,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            ),
        )
        response_body = json.loads(response["body"].read().decode("utf-8"))
        #print("Response from Bedrock:")
        #print(json.dumps(response_body, indent=2))

        # Extract response content
        if "content" in response_body and isinstance(response_body["content"], list):
            response_text = "".join(item.get("text", "") for item in response_body["content"])
            return response_text if response_text.strip() else "No response generated."
        else:
            return "No valid content in response."
    except client.exceptions.ValidationException as e:
        print(f"Validation error: {e}")
        return "Error: Input size exceeds model limits. Please shorten the context or input."
    except Exception as e:
        print(f"Error invoking AWS Bedrock: {e}")
        return "Error generating response."


def chatbot_response(question, split_files_dir, model_id, region="us-east-1"):
    relevant_pdf_path = find_relevant_pdf(question, split_files_dir)
    reader = PdfReader(relevant_pdf_path)
    pages = [page.extract_text() for page in reader.pages]

    full_text = " ".join(pages)
    max_context_length = 3000
    truncated_context = full_text[:max_context_length]

    prompt = f"Context:\n{truncated_context}\n\nQuestion:\n{question}\nAnswer:"
    #print(f"Prompt length: {len(prompt)} characters")
    if len(prompt) > 5000:
        print("Prompt exceeds maximum size. Consider reducing context further.")

    response = generate_answer_with_bedrock(prompt, model_id, region)

    if response == "No response generated." or "Error" in response:
        print("Generating response failed. Trying a simpler prompt.")
        prompt = f"Question:\n{question}\nAnswer:"
        response = generate_answer_with_bedrock(prompt, model_id, region)

    return response

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)

    input_pdf_path = "docs/s3-api.pdf"
    split_files_dir = "split_pdfs"
    bedrock_model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    aws_region = "us-east-1"

    question = "What are the main features of Amazon S3?"
    response = chatbot_response(question, split_files_dir, bedrock_model_id, aws_region)
    print("Chatbot Response:")
    print(response)
