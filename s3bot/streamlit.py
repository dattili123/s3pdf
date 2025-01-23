import os
import json
import boto3
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb import PersistentClient

# Step 1: Read and Chunk PDF
def read_and_chunk_pdf(pdf_path, chunk_size=800, chunk_overlap=25):
    pdf_reader = PdfReader(pdf_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chunks = []
    for page_num, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text:
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
        embeddings = []
        for text in input:
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

    existing_data = collection.get(include=["metadatas"])
    existing_ids = {metadata.get("id") for metadata in existing_data["metadatas"] if "id" in metadata}

    for idx, chunk in enumerate(chunks):
        chunk_id = str(idx)
        if chunk_id in existing_ids:
            continue
        collection.add(
            documents=[chunk.page_content],
            metadatas=[{"id": chunk_id, **chunk.metadata}],
            ids=[chunk_id]
        )

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
            return "".join(item.get("text", "") for item in response_body["content"]).strip()
        else:
            return "No valid content in response."
    except Exception as e:
        return f"Error generating response: {e}"

# Step 5: Query ChromaDB and Generate Response
def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found."

    documents = [doc for sublist in results["documents"] for doc in sublist]
    relevant_text = " ".join(documents)

    full_prompt = f"Relevant context: {relevant_text}\n\nUser question: {user_query}"
    return generate_answer_with_bedrock(full_prompt, model_id, region)

# Streamlit UI
st.title("AWS Knowledge Base Chatbot")
st.write("Ask questions about AWS services based on the processed knowledge base.")

# PDF Path
pdf_path = "./s3-api.pdf"
if os.path.exists(pdf_path):
    st.write("📄 Found local PDF file. Processing...")
    chunks = read_and_chunk_pdf(pdf_path)
    st.success("PDF processed successfully!")

    # Initialize ChromaDB and Store Embeddings
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    region = "us-east-1"
    embedding_function = TitanEmbeddingFunction(model_id=model_id, region=region)

    client = PersistentClient(path="./chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    existing_data = collection.get(include=["metadatas"])
    if not existing_data["metadatas"]:
        st.write("Storing embeddings...")
        store_embeddings_in_chromadb(chunks, embedding_function)
        st.success("Embeddings stored successfully!")
    else:
        st.write("Embeddings already exist. Ready to chat.")

    # Chat Interface
    user_query = st.text_input("Ask your question:")
    if user_query:
        response = query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region)
        st.subheader("Chatbot Response:")
        st.write(response)
else:
    st.error("❌ PDF file not found. Please ensure 's3-api.pdf' is available in the current directory.")
