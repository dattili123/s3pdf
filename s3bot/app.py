import os
import json
import boto3
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.config import Settings
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from chromadb.utils import embedding_functions
from chromadb import PersistentClient


# Step 1: Read and Chunk PDF
def read_and_chunk_pdf(pdf_path, chunk_size=800, chunk_overlap=25):
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    pdf_reader = PdfReader(pdf_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chunks = []
    for page_num, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text:
            # Pass metadata explicitly for each text
            split_docs = text_splitter.create_documents(
                texts=[text],
                metadatas=[{"page": page_num + 1}]
            )
            chunks.extend(split_docs)
    return chunks


# Step 2: Embedding Function using AWS Bedrock
class TitanEmbeddingFunction:
    def __init__(self, model_id, region="us-east-1"):
        self.model_id = model_id
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

    def __call__(self, input):
        # `input` is the new parameter name expected by ChromaDB
        embeddings = []
        for text in input:  # Process each input text
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({"inputText": text})
            )
            embedding = json.loads(response["body"].read())["embedding"]
            embeddings.append(embedding)
        return embeddings


# Step 3: Store Embeddings in ChromaDB
def store_embeddings_in_chromadb(chunks, embedding_function):
    client = PersistentClient(path="./chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    # Fetch existing metadata to identify already added embeddings
    existing_data = collection.get(include=["metadatas"])
    existing_ids = {metadata.get("id") for metadata in existing_data["metadatas"] if "id" in metadata}

    # Add new chunks to the collection only if the ID does not already exist
    for idx, chunk in enumerate(chunks):
        chunk_id = str(idx)
        if chunk_id in existing_ids:
            print(f"Skipping existing embedding ID: {chunk_id}")
            continue  # Skip already existing embeddings

        collection.add(
            documents=[chunk.page_content],
            metadatas=[{"id": chunk_id, **chunk.metadata}],
            ids=[chunk_id]
        )
        print(f"Added new embedding ID: {chunk_id}")




# Step 4: Generate Answer Using AWS Bedrock
def generate_answer_with_bedrock(prompt, model_id, region="us-east-1"):
    client = boto3.client("bedrock-runtime", region_name=region)
    try:
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
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read().decode("utf-8"))
        if "content" in response_body and isinstance(response_body["content"], list):
            response_text = "".join(item.get("text", "") for item in response_body["content"])
            return response_text.strip() if response_text.strip() else "No response generated."
        else:
            return "No valid content in response."
    except client.exceptions.ValidationException as e:
        print(f"Validation error: {e}")
        return "Error: Input size exceeds model limits. Please shorten the context or input."
    except Exception as e:
        print(f"Error invoking AWS Bedrock: {e}")
        return "Error generating response."

# Step 5: Query ChromaDB and Generate Response
def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    # Generate embedding for the query
    query_embedding = embedding_function([user_query])[0]

    # Search in ChromaDB collection
    results = collection.query(query_embedding, n_results=5)
    print("Query results:", results)  # Debugging output

    # Check if results contain any matches
    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database. Please refine your query or ensure embeddings are correctly added."

    # Flatten the list of documents
    documents = [doc for sublist in results["documents"] for doc in sublist]

    # Concatenate relevant documents
    relevant_text = " ".join(documents)

    # Generate response using AWS Bedrock
    full_prompt = f"Relevant context: {relevant_text}\n\nUser question: {user_query}"
    response = generate_answer_with_bedrock(full_prompt, model_id, region)
    return response



# Main Script
if __name__ == "__main__":
    # Step 1: Extract and chunk the PDF
    pdf_path = "./s3-api.pdf"
    #chunks = read_and_chunk_pdf(pdf_path)

    # Step 2: Generate embeddings
    embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")

    # Initialize ChromaDB client
    client = PersistentClient(path="./chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    # Check if collection has existing embeddings
    existing_data = collection.get(include=["metadatas"])
    if not existing_data["metadatas"]:
        print("Collection is empty. Generating embeddings...")
        chunks = read_and_chunk_pdf(pdf_path)
        store_embeddings_in_chromadb(chunks, embedding_function)
    else:
        print("Collection already populated. Skipping embedding generation.")

    # Step 4: Chatbot loop
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    region = "us-east-1"
    while True:
        user_query = input("Ask your question (or type 'exit' to quit): ")
        if user_query.lower() == "exit":
            print("Exiting chatbot. Goodbye!")
            break
        response = query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region)
        print("Chatbot Response:", response)
