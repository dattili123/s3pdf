import os
import json
import re
import numpy as np
import boto3
import redis
import pdfplumber
import requests
import streamlit as st
from PyPDF2 import PdfReader
from concurrent.futures import ThreadPoolExecutor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

# AWS Bedrock client
brt = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

# Redis Cache for Storing Extracted PDF Text
cache = redis.StrictRedis(host="localhost", port=6379, db=0)

# Path Constants
PDF_PATH = "./s3-api.pdf"
PROCESSED_PDFS_FILE = "./processed_pdfs.json"

# Base URLs
JIRA_BASE_URL = "https://8443/browse/"
CONFLUENCE_BASE_URL = "https://confluence.url/pages/viewpage.action?pageId="

# Load Processed PDFs
def load_processed_pdfs():
    if os.path.exists(PROCESSED_PDFS_FILE):
        with open(PROCESSED_PDFS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_processed_pdfs(processed_pdfs):
    with open(PROCESSED_PDFS_FILE, "w") as f:
        json.dump(processed_pdfs, f)

# Extract Text from PDFs (Faster with pdfplumber)
def extract_text_from_pdf(pdf_path):
    cached_text = cache.get(pdf_path)
    if cached_text:
        return cached_text.decode("utf-8")  # Retrieve from cache

    with pdfplumber.open(pdf_path) as pdf:
        extracted_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    cache.set(pdf_path, extracted_text)  # Store in cache
    return extracted_text

# Read and Chunk PDF (Optimized for Speed)
def read_and_chunk_pdf(pdf_path, chunk_size=500, chunk_overlap=50):
    text = extract_text_from_pdf(pdf_path)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.create_documents([text])

# Store PDF Embeddings (Parallel Processing)
def process_pdf(pdf_path, embedding_function):
    pdf_file = os.path.basename(pdf_path)
    processed_pdfs = load_processed_pdfs()

    if pdf_file in processed_pdfs:
        print(f"Skipping already processed PDF: {pdf_file}")
        return

    print(f"Processing new PDF: {pdf_file}")
    process_large_pdf(pdf_path, batch_size=10)
    processed_pdfs[pdf_file] = True
    save_processed_pdfs(processed_pdfs)

def store_all_pdfs_in_chromadb(pdf_dir, embedding_function):
    pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    with ThreadPoolExecutor() as executor:
        executor.map(lambda pdf: process_pdf(pdf, embedding_function), pdf_files)
    return collection

# Extract Jira Keys from Bedrock Response
def extract_jira_keys_from_response(response_text):
    return list(set(re.findall(r'\b[A-Z]+-\d+\b', response_text)))

# Parallel API Calls for Jira & Confluence
def fetch_url(session, url):
    with session.get(url) as response:
        return response.text

def fetch_multiple(urls):
    with ThreadPoolExecutor() as executor:
        return list(executor.map(requests.get, urls))

# Query ChromaDB & Generate Response
def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=2)  # Reduced from 5 to 2

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database.", [], []

    documents = [doc for sublist in results["documents"] for doc in sublist]
    metadata = results.get("metadatas", [])
    print(f"Metadata: {metadata}")

    confluence_links = []
    other_pdf_sources = set()

    for meta in metadata[0]:
        if isinstance(meta, dict):
            source = meta.get("source", "Unknown Source")
            page = meta.get("page", "Unknown Page")

            match = re.match(r".*/(\d+)_.*\.pdf", source)
            if match:
                confluence_links.append(f"{CONFLUENCE_BASE_URL}{match.group(1)}")
            else:
                other_pdf_sources.add(f"File: {source} Page: {page}")

    relevant_text = " ".join(documents)
    full_prompt = f"Relevant Information:\n\n{relevant_text}\n\nUser Query: {user_query}\n\nAnswer:"

    response = generate_answer_with_bedrock(full_prompt, model_id, region)
    jira_keys = extract_jira_keys_from_response(response)
    jira_links = [f"{JIRA_BASE_URL}{key}" for key in jira_keys]

    return response, confluence_links, jira_links, other_pdf_sources

# Bedrock API with Streaming
def generate_answer_with_bedrock(prompt, model_id, region="us-east-1"):
    client = boto3.client("bedrock-runtime", region_name=region)
    conversation_history = st.session_state.get("conversation", [])[-2:]  # Last 2 exchanges

    history_context = "\n".join(
        [f"{speaker}: {message}" for speaker, message in conversation_history]
    )

    try:
        response = client.invoke_model_with_response_stream(  # Streaming Response
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{"role": "user", "content": [{"type": "text", "text": f"{history_context}\n\n{prompt}"}]}],
                "max_tokens": 1024,  # Reduced from 4096
                "temperature": 0.7,
                "top_p": 0.9
            }),
            contentType="application/json",
            accept="application/json"
        )

        response_body = response["body"]
        response_text = ""

        for event in response_body:
            response_text += event["text"] if "text" in event else ""

        return response_text.strip() if response_text.strip() else "No response generated."

    except Exception as e:
        return f"Error generating response: {e}"

# Streamlit UI Setup
st.set_page_config(page_title="Ask SRE Infra Assist", layout="wide")
st.header("Chatbot Interface")

with st.form(key="question_form", clear_on_submit=False):
    user_query = st.text_input("Ask your question:", key="user_input", help="Press Enter to submit.")
    submit_button = st.form_submit_button("Submit")

if submit_button and user_query:
    if "conversation" not in st.session_state:
        st.session_state["conversation"] = []

    with st.spinner("Generating response..."):
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        response, confluence_links, jira_links, other_pdf_sources = query_chromadb_and_generate_response(
            user_query, TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0"), st.session_state.collection, model_id
        )

        references = "\n\n🔗 References:\n" + "\n".join(jira_links + confluence_links + list(other_pdf_sources))
        st.text_area("Chatbot Response:", response + references, height=600)

if st.button("Clear Cache"):
    st.session_state.clear()
    st.success("Cache Cleared")
