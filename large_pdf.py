import os
import chromadb
import boto3
import json
import pdfplumber  # More efficient for text extraction
from langchain.text_splitter import RecursiveCharacterTextSplitter

# AWS Bedrock Client
brt = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

# Initialize ChromaDB Client
CHROMADB_PATH = "./chromadb"
if not os.path.exists(CHROMADB_PATH):
    os.makedirs(CHROMADB_PATH)
chroma_client = chromadb.PersistentClient(path=CHROMADB_PATH)

# Get or create collection
embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
collection = chroma_client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

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

# Store Embeddings Efficiently
def store_embeddings_in_chromadb(batch):
    documents = [item["text"] for item in batch]
    metadatas = [item["metadata"] for item in batch]
    ids = [str(hash(item["text"])) for item in batch]

    # Store in ChromaDB (Chunked)
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"✅ Added {len(batch)} chunks to ChromaDB.")

# Process the PDF efficiently
process_large_pdf("large_file.pdf")
print("✅ PDF Processing Complete!")
