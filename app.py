import os
import boto3
import json
from PyPDF2 import PdfReader, PdfWriter


def split_pdf_by_size(input_pdf_path, output_dir, size_limit_mb=1):
    """
    Splits a PDF file into smaller PDFs, each approximately size_limit_mb in size.

    Args:
        input_pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory where split PDFs will be saved.
        size_limit_mb (int): Maximum size of each split PDF in megabytes.
    """
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    current_size = 0
    part_number = 1

    for i, page in enumerate(reader.pages):
        writer.add_page(page)
        
        # Add the estimated size of the current page
        page_size = len(page.extract_text().encode("utf-8")) / (1024 * 1024)  # Size in MB
        current_size += page_size

        # If the current size exceeds the limit or it's the last page, save the file
        if current_size >= size_limit_mb or i == len(reader.pages) - 1:
            output_path = os.path.join(output_dir, f"part_{part_number}.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            print(f"Saved: {output_path} (Size: {current_size:.2f} MB)")
            writer = PdfWriter()  # Reset the writer for the next part
            current_size = 0
            part_number += 1

    print(f"PDF split into {part_number - 1} parts and saved in {output_dir}.")


def find_relevant_pdf(question, split_files_dir):
    """
    Finds the most relevant PDF part for a question using basic keyword matching.

    Args:
        question (str): The user's question.
        split_files_dir (str): Directory containing split PDF files.

    Returns:
        str: Path to the most relevant PDF part.
    """
    max_score = -1
    relevant_pdf = ""

    for file_name in os.listdir(split_files_dir):
        file_path = os.path.join(split_files_dir, file_name)

        if not file_name.endswith(".pdf"):
            continue

        reader = PdfReader(file_path)
        content = " ".join([page.extract_text() for page in reader.pages])

        # Basic keyword matching for relevance
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
    if not prompt.startswith('"'):
        prompt = f'"{prompt}'
    if not prompt.endswith('"'):
        prompt = f'{prompt}"'
    try:
        # Corrected request body format
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}],}],
                    "max_tokens": 300,  # Adjust based on your needs
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            ),
        )
        # Parse and return the response
        response_body = json.loads(response["body"].read().decode("utf-8"))
        return response_body.get("completion", "No response generated.")
    except Exception as e:
        print(f"Error invoking AWS Bedrock: {e}")
        return "Error generating response."


def chatbot_response(question, split_files_dir, model_id, region="us-east-1"):
    """
    Generate a chatbot response using AWS Bedrock LLM.

    Args:
        question (str): The user's query.
        split_files_dir (str): Directory containing split PDF files.
        model_id (str): AWS Bedrock model ID.
        region (str): AWS region for Bedrock service.

    Returns:
        str: The chatbot response.
    """
    #relevant_pdf_path = find_relevant_pdf(question, split_files_dir)
    relevant_pdf_path = "split_pdfs/part_2.pdf"

    # Read the relevant PDF content
    reader = PdfReader(relevant_pdf_path)
    content = " ".join([page.extract_text() for page in reader.pages])

    # Create the prompt with context
    prompt = f"Context:\n{content}\n\nQuestion:\n{question}\nAnswer:"
    return generate_answer_with_bedrock(prompt, model_id, region)


# Example Usage
if __name__ == "__main__":
    # Paths
    input_pdf_path = "docs/s3-api.pdf"  # Replace with your PDF path
    split_files_dir = "split_pdfs"
    bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"  # Replace with your Bedrock model ID
    aws_region = "us-east-1"

    # Step 1: Split the PDF into parts
    split_pdf_by_size(input_pdf_path, split_files_dir, size_limit_mb=1)

    # Step 2: Generate a response using AWS Bedrock
    question = "What are the main features of Amazon S3?"
    response = chatbot_response(question, split_files_dir, bedrock_model_id, aws_region)
    print("Chatbot Response:")
    print(response)
