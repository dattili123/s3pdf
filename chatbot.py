import os
import boto3
import json
import numpy as np
import tensorflow as tf
import sentencepiece as spm
from PyPDF2 import PdfReader
from tqdm import tqdm


def sanitize_filename(name):
    """
    Sanitize a string to make it safe for use as a filename.
    """
    return re.sub(r'[^\w\-_\. ]', '_', name)


def split_pdf_logically(pdf_path, output_dir):
    """
    Splits a PDF document logically into sections and saves them as text files.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_dir (str): Directory where the split parts will be saved.
    """
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(pdf_path)
    sections = {"Introduction": []}  # Default section
    current_section = "Introduction"

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue  # Skip pages without text

        lines = text.split('\n')
        for line in lines:
            # Detect headings (lines starting with "1.", "2.", etc.)
            if line.strip().isdigit() or line.strip().startswith(('1.', '2.', '3.')):
                current_section = sanitize_filename(line.strip())  # Update the current section safely
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line)

    # Write each section to a separate file
    for section, content in sections.items():
        filename = os.path.join(output_dir, f"{sanitize_filename(section)}.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))

    print(f"PDF split into {len(sections)} sections. Files saved in {output_dir}")



def train_embedding_model(split_files_dir, embedding_size=128, model_path="embedding_model"):
    """
    Train a TensorFlow-based embedding model on split files.

    Args:
        split_files_dir (str): Directory of split files.
        embedding_size (int): Size of the embeddings.
        model_path (str): Path to save the trained model.
    """
    texts = []
    for file_name in os.listdir(split_files_dir):
        file_path = os.path.join(split_files_dir, file_name)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            texts.append(f.read())
    
    # Simple text preprocessing
    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(sequences, padding="post")

    # Define a simple embedding model
    model = tf.keras.Sequential([
        tf.keras.layers.Embedding(input_dim=len(tokenizer.word_index) + 1,
                                   output_dim=embedding_size, input_length=padded_sequences.shape[1]),
        tf.keras.layers.GlobalAveragePooling1D()
    ])
    model.compile(optimizer='adam', loss='mse')

    # Train model (dummy labels for unsupervised embeddings)
    model.fit(padded_sequences, np.zeros((len(padded_sequences), embedding_size)), epochs=5, batch_size=2)

    # Save the model with `tf.saved_model.save` for compatibility
    tf.saved_model.save(model, model_path)
    print(f"Embedding model trained and saved at {model_path}")
    return model, tokenizer


def find_relevant_section(question, split_files_dir, model, tokenizer):
    """
    Finds the most relevant section for a question using embeddings.

    Args:
        question (str): User query.
        split_files_dir (str): Directory of split text files.
        model: Trained TensorFlow embedding model.
        tokenizer: Tokenizer used for embedding generation.

    Returns:
        str: Content of the most relevant section.
    """
    question_sequence = tokenizer.texts_to_sequences([question])
    question_embedding = model(tf.keras.preprocessing.sequence.pad_sequences(
        question_sequence, maxlen=model.input_shape[1], padding="post"))

    max_similarity = -1
    relevant_content = ""

    for file_name in os.listdir(split_files_dir):
        file_path = os.path.join(split_files_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content_sequence = tokenizer.texts_to_sequences([content])
        content_embedding = model(tf.keras.preprocessing.sequence.pad_sequences(
            content_sequence, maxlen=model.input_shape[1], padding="post"))
        
        # Calculate cosine similarity
        similarity = np.dot(question_embedding, content_embedding.T) / (
            np.linalg.norm(question_embedding) * np.linalg.norm(content_embedding))
        if similarity > max_similarity:
            max_similarity = similarity
            relevant_content = content

    return relevant_content


def generate_answer_with_bedrock(prompt, model_id):
    """
    Use AWS Bedrock to generate an answer using the provided prompt.

    Args:
        prompt (str): Context and question for the model.
        model_id (str): AWS Bedrock model ID.

    Returns:
        str: Generated answer.
    """
    client = boto3.client('bedrock-runtime')
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps({"input": prompt}),
        contentType='application/json'
    )
    return json.loads(response['body'].read().decode('utf-8'))['generated_text']


def chatbot_response(question, split_files_dir, model, tokenizer, model_id):
    """
    Generate chatbot response for a user question.

    Args:
        question (str): User query.
        split_files_dir (str): Directory of split files.
        model: Trained TensorFlow embedding model.
        tokenizer: Tokenizer used for embedding generation.
        model_id (str): AWS Bedrock model ID.

    Returns:
        str: Chatbot response.
    """
    relevant_content = find_relevant_section(question, split_files_dir, model, tokenizer)
    prompt = f"Context:\n{relevant_content}\n\nQuestion:\n{question}\nAnswer:"
    return generate_answer_with_bedrock(prompt, model_id)


# Example Usage
if __name__ == "__main__":
    pdf_path = "/mnt/data/your_document.pdf"
    split_files_dir = "/mnt/data/split_sections"
    model_id = "amazon.titan-text-v1"
    model_path = "embedding_model"

    # Step 1: Split the PDF
    split_pdf_logically(pdf_path, split_files_dir)

    # Step 2: Train an embedding model
    model, tokenizer = train_embedding_model(split_files_dir, model_path=model_path)

    # Step 3: Generate chatbot response
    question = "What are the main features of Amazon S3?"
    print(chatbot_response(question, split_files_dir, model, tokenizer, model_id))
