import os
import json
import base64
import boto3
import streamlit as st
from PyPDF2 import PdfReader
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from atlassian import Confluence  # Confluence API

# AWS Bedrock Client
brt = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

# Confluence Settings
CONFLUENCE_BASE_URL = "https://confluence.organization.com"
CONFLUENCE_USERNAME = "abc123"
CONFLUENCE_PASSWORD = "$2025"
PAGE_IDS = ["124524340", "1223218285", "129384750"]  # List of Confluence page IDs
PDF_DIR = "./pdfs"  # Directory for storing PDFs

LOGO_PATH = "./logo.png"
BANNER_PATH = "./chatbot.png"

# Initialize Confluence API client
confluence = Confluence(
    url=CONFLUENCE_BASE_URL,
    username=CONFLUENCE_USERNAME,
    password=CONFLUENCE_PASSWORD,
    verify_ssl=False
)

# Function: Export a single Confluence Page to PDF (if missing)
def export_page_to_pdf(page_id, output_dir=PDF_DIR):
    try:
        page_info = confluence.get_page_by_id(page_id)
        page_title = page_info['title'].replace("/", "_")
        file_path = f"{output_dir}/{page_title}.pdf"

        # Skip if the PDF already exists
        if os.path.exists(file_path):
            print(f'Skipping existing PDF: {file_path}')
            return

        print(f'Fetching page "{page_title}" from Confluence...')
        pdf_export = confluence.export_page(page_id)

        # Save the PDF
        os.makedirs(output_dir, exist_ok=True)
        with open(file_path, "wb") as pdf_file:
            pdf_file.write(pdf_export)
        print(f'Saved page "{page_title}" to {file_path}')

    except Exception as e:
        print(f'Failed to export page [{page_id}] to PDF: {str(e)}')

# Function: Export All Confluence Pages (if missing)
def export_all_confluence_pages():
    for page_id in PAGE_IDS:
        export_page_to_pdf(page_id)

# Run Confluence PDF Export
export_all_confluence_pages()

# Function: Read and Chunk PDF
def read_and_chunk_pdf(pdf_path, chunk_size=800, chunk_overlap=25):
    from langchain.text_splitter import RecursiveCharacterTextSplitter

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

# Function: Embedding using AWS Bedrock
class TitanEmbeddingFunction:
    def __init__(self, model_id, region="us-east-1"):
        self.model_id = model_id
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            response = brt.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({"inputText": text})
            )
            embedding = json.loads(response["body"].read())["embedding"]
            embeddings.append(embedding)
        return embeddings

# Initialize ChromaDB
embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
client = chromadb.PersistentClient(path="./chromadb")
collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

# Check if embeddings exist
existing_data = collection.get(include=["metadatas"])
if not existing_data["metadatas"]:
    st.info("Embeddings not found. Generating new embeddings...")

    for pdf_file in os.listdir(PDF_DIR):
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        chunks = read_and_chunk_pdf(pdf_path)
        for chunk in chunks:
            collection.add(
                documents=[chunk.page_content],
                metadatas=[chunk.metadata],
                ids=[str(hash(chunk.page_content))]
            )

    st.success("Embeddings have been generated and stored!")

else:
    st.success("Existing embeddings found. Ready to use!")

# Styling & Layout for Streamlit UI
st.set_page_config(page_title="AWS Bedrock Chatbot", page_icon="🤖", layout="wide")

st.markdown(
    """
    <style>
        html, body {
            background-color: #f4f7fc;
        }
        .main {
            padding-top: 0 !important;
        }
        .block-container {
            padding-top: 10px !important;
        }
        .left-banner {
            text-align: center;
            padding: 20px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .chatbot-container {
            margin-top: 20px;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Layout with Columns
col1, col2, col3 = st.columns([1, 2, 1])

# Left Banner
with col1:
    st.markdown('<div class="left-banner">', unsafe_allow_html=True)
    st.image(BANNER_PATH, use_column_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Center: Chatbot Interface
with col2:
    st.image(LOGO_PATH, width=150)
    st.title("AWS Bedrock Chatbot with Confluence Integration")
    st.subheader("Chatbot Interface")
    user_query = st.text_input("Ask your question:")
    if st.button("Submit"):
        with st.spinner("Processing..."):
            response = collection.query(
                embedding_function([user_query])[0], n_results=5
            )
            if response["documents"]:
                context = " ".join([doc for doc_list in response["documents"] for doc in doc_list])
                final_response = f"Context: {context}\n\nUser question: {user_query}\n\nAnswer: {generate_answer_with_bedrock(context, 'anthropic.claude-3-5-sonnet-20240620-v1:0')}"
                st.text_area("Chatbot Response:", value=final_response, height=200)
            else:
                st.warning("No relevant data found.")
