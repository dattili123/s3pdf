import os
import boto3
import json
import logging
from PyPDF2 import PdfReader
import re

# Set up the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Logs to the console
    ]
)
logger = logging.getLogger(__name__)


def split_pdf_logically(pdf_path, output_dir):
    """
    Splits a PDF document logically into sections and saves them as text files.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory where split parts will be saved.
    """
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(pdf_path)
    sections = {"Introduction": []}
    current_section = "Introduction"

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue

        lines = text.split("\n")
        for line in lines:
            if re.match(r"^\d+\.", line.strip()):  # Detect headings like "1.", "2."
                current_section = line.strip()
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line)

    for section, content in sections.items():
        sanitized_name = re.sub(r'[^\w\-_\. ]', '_', section)
        filename = os.path.join(output_dir, f"{sanitized_name}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

    logger.info(f"PDF split into {len(sections)} sections. Files saved in {output_dir}")


def find_relevant_section(question, split_files_dir):
    """
    Finds the most relevant section for a question using basic keyword matching.

    Args:
        question (str): The user's question.
        split_files_dir (str): Directory of split text files.

    Returns:
        str: The most relevant section content.
    """
    max_score = -1
    relevant_content = ""

    for file_name in os.listdir(split_files_dir):
        file_path = os.path.join(split_files_dir, file_name)

        if os.path.isdir(file_path):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Basic keyword matching for relevance
        score = sum(1 for word in question.split() if word.lower() in content.lower())
        if score > max_score:
            max_score = score
            relevant_content = content

    logger.info(f"Most relevant section identified for question: '{question}'")
    return relevant_content


def generate_answer_with_bedrock(prompt, model_id="amazon.titan-text-v1"):
    """
    Use AWS Bedrock to generate an answer using the prompt.

    Args:
        prompt (str): Context and question as the prompt.
        model_id (str): AWS Bedrock model ID.

    Returns:
        str: The generated response from the model.
    """
    client = boto3.client("bedrock-runtime")
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps({"input": prompt}),
        contentType="application/json",
    )
    logger.info(f"Answer generated successfully for the provided prompt.")
    return json.loads(response["body"].read().decode("utf-8"))["generated_text"]


def chatbot_response(question, split_files_dir, model_id="amazon.titan-text-v1"):
    """
    Generate a chatbot response using AWS Bedrock LLM.

    Args:
        question (str): The user's query.
        split_files_dir (str): Directory containing split files.
        model_id (str): AWS Bedrock model ID.

    Returns:
        str: The chatbot response.
    """
    # Find the most relevant section
    relevant_content = find_relevant_section(question, split_files_dir)

    # Create the prompt with context
    prompt = f"Context:\n{relevant_content}\n\nQuestion:\n{question}\nAnswer:"
    return generate_answer_with_bedrock(prompt, model_id)


# Example Usage
if __name__ == "__main__":
    # Paths
    pdf_path = "/mnt/data/your_document.pdf"  # Replace with your PDF path
    split_files_dir = "/mnt/data/split_sections"

    # Step 1: Split the PDF into sections
    try:
        split_pdf_logically(pdf_path, split_files_dir)
    except Exception as e:
        logger.error(f"Failed to split PDF: {e}")

    # Step 2: Generate a response using AWS Bedrock
    question = "What are the main features of Amazon S3?"
    try:
        response = chatbot_response(question, split_files_dir)
        logger.info(f"Chatbot Response: {response}")
    except Exception as e:
        logger.error(f"Failed to generate chatbot response: {e}")
