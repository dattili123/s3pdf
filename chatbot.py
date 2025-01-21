import os
import boto3
import json
import sentencepiece as spm
from PyPDF2 import PdfReader


def split_pdf_logically(pdf_path, output_dir):
    """
    Splits a PDF document logically into sections based on headings or structure.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory where the split parts will be saved.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    reader = PdfReader(pdf_path)
    sections = {}
    current_section = "Introduction"  # Default section
    sections[current_section] = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        
        # Detect headings (example: lines starting with "1.", "2.", etc.)
        lines = text.split('\n')
        for line in lines:
            if line.strip().isdigit() or line.strip().startswith(('1.', '2.', '3.')):
                current_section = line.strip()
                sections[current_section] = []
            else:
                sections[current_section].append(line)
    
    # Save each section to a file
    for section, content in sections.items():
        filename = f"{output_dir}/{section.replace(' ', '_')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
    
    print(f"PDF has been split into {len(sections)} sections. Check the directory: {output_dir}")


def train_sentencepiece_model(split_files_dir, model_prefix="mymodel"):
    """
    Train a SentencePiece model on the split files.
    """
    input_files = [os.path.join(split_files_dir, file) for file in os.listdir(split_files_dir)]
    combined_text = ""
    for file in input_files:
        with open(file, 'r', encoding='utf-8') as f:
            combined_text += f.read() + "\n"
    
    training_file = "combined_text.txt"
    with open(training_file, 'w', encoding='utf-8') as f:
        f.write(combined_text)
    
    spm.SentencePieceTrainer.train(
        input=training_file,
        model_prefix=model_prefix,
        vocab_size=2000,
        model_type="bpe"
    )

    print(f"SentencePiece model trained with prefix: {model_prefix}")


def find_relevant_section_with_sentencepiece(question, split_files_dir, model_prefix="mymodel"):
    """
    Find the most relevant section for a given question using SentencePiece for tokenization and similarity matching.
    """
    sp = spm.SentencePieceProcessor(model_file=f"{model_prefix}.model")
    question_tokens = sp.encode(question, out_type=str)
    
    relevant_content = ""
    max_score = 0

    for file_name in os.listdir(split_files_dir):
        file_path = os.path.join(split_files_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content_tokens = sp.encode(content, out_type=str)
        common_tokens = set(question_tokens) & set(content_tokens)
        score = len(common_tokens)

        if score > max_score:
            max_score = score
            relevant_content = content

    return relevant_content


def generate_answer_with_bedrock(prompt, model_id):
    """
    Use AWS Bedrock to generate an answer using the prompt.
    """
    client = boto3.client('bedrock-runtime')
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps({"input": prompt}),
        contentType='application/json'
    )
    return json.loads(response['body'].read().decode('utf-8'))['generated_text']


def chatbot_response(question, split_files_dir, model_id, model_prefix="mymodel"):
    """
    Main function to handle chatbot interaction.
    """
    relevant_content = find_relevant_section_with_sentencepiece(question, split_files_dir, model_prefix)
    prompt = f"Context:\n{relevant_content}\n\nQuestion:\n{question}\nAnswer:"
    answer = generate_answer_with_bedrock(prompt, model_id)
    return answer


# Example Usage
if __name__ == "__main__":
    # Path to the PDF file and output directory for split sections
    pdf_path = "/mnt/data/your_document.pdf"
    split_files_dir = "/mnt/data/split_sections"
    model_id = "amazon.titan-text-v1"  # Replace with your Bedrock model ID

    # Step 1: Split the PDF
    split_pdf_logically(pdf_path, split_files_dir)
    
    # Step 2: Train the SentencePiece model
    train_sentencepiece_model(split_files_dir)
    
    # Step 3: Answer a question
    question = "What are the main features of Amazon S3?"
    response = chatbot_response(question, split_files_dir, model_id)
    print(response)
