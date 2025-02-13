import os
import chromadb
import boto3
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdfplumber
import json

# AWS Bedrock Client
brt = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

# Efficient PDF Processing (Read & Process in Batches)
def process_large_pdf(pdf_path, batch_size=10, chunk_size=800, chunk_overlap=25):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    batch = []  # Store chunks before adding to ChromaDB
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                chunks = text_splitter.split_text(text)  # Split the text into smaller chunks
                for chunk in chunks:
                    batch.append({"text": chunk, "metadata": {"source": pdf_path, "page": page_num + 1}})
                
                # Process in batches to avoid memory overflow
                if len(batch) >= batch_size:
                    store_embeddings_in_chromadb(batch)
                    batch = []  # Clear batch from memory

        # Process any remaining chunks
        if batch:
            store_embeddings_in_chromadb(batch)

# Store Embeddings Efficiently in ChromaDB
def store_embeddings_in_chromadb(pdf_dir, embedding_function, batch_size=10):
    client = chromadb.PersistentClient("/path/to/chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    # Get existing metadata for all stored chunks
    existing_data = collection.get(include=["metadatas"])
    existing_files = {metadata.get("source") for metadata in existing_data["metadatas"] if "source" in metadata}

    # Iterate over all PDFs in the directory and process in batches
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            if pdf_file in existing_files:  # Skip if already processed
                print(f"Skipping existing PDF: {pdf_file}")
                continue

            pdf_path = os.path.join(pdf_dir, pdf_file)
            print(f"Processing new PDF: {pdf_file}")

            try:
                process_large_pdf(pdf_path, batch_size=batch_size)
            except Exception as e:
                print(f"Error processing PDF {pdf_file}: {str(e)}")

    return collection
