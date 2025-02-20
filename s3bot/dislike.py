import os
import json
import base64
import boto3
import streamlit as st
from PyPDF2 import PdfReader
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from atlassian import Jira, Confluence
from langchain.text_splitter import RecursiveCharacterTextSplitter

# AWS Bedrock client
brt = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
PDF_PATH = "./s3-api.pdf"

LOGO_PATH = "./logo.png"  # Update with your logo filename
BANNER_PATH = "./chatbot.png"  # Update with your banner filename

base_url = "https://confluence.org.com"
username = "gbudfa"
password = "$2025"
parent_page_ids = [1524851522, 1588779324]

# Set your JIRA credentials and base URL
JIRA_URL = "https://jira.org.com"
USERNAME = "gbudfa"
API_TOKEN = "$2025"  # Use API token for authentication
PROJECT_KEY = "PANTHER"  # Replace with your Jira project key

# Initialize Jira Connection
jira = Jira(
    url=JIRA_URL,
    username=USERNAME,
    password=API_TOKEN,
    verify_ssl=False
)

# Initialize Confluence instance
confluence = Confluence(
    url=base_url,
    username=username,
    password=password,
    verify_ssl=False
)

# Streamlit Interface Configuration
st.set_page_config(page_title="Ask SRE Infra Assist", page_icon="🛠️", layout="wide")

# Initialize ChromaDB Collection
if "collection" not in st.session_state:
    with st.spinner("Loading FannieAstra..."):
        embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
        client = chromadb.PersistentClient(path="./knowledge_base")
        collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)
        st.session_state.collection = store_all_pdfs_in_chromadb(PDF_PATH, embedding_function)

# Chatbot Section
embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")

st.header("Chatbot Interface")

with st.form(key="question_form", clear_on_submit=False):
    user_query = st.text_input("Ask your question:", key="user_input", help="Press Enter to submit.")
    submit_button = st.form_submit_button("Submit")

if submit_button and user_query:
    if "conversation" not in st.session_state:
        st.session_state["conversation"] = []

    with st.spinner("Generating response..."):
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        response, confluence_links, other_pdf_sources = query_chromadb_and_generate_response(
            user_query,
            TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0"),
            st.session_state.collection,
            model_id,
        )

        references = get_references_from_pdf(user_query, st.session_state.collection, embedding_function)
        reference_section = "\n\n References:\n"
        if confluence_links:
            reference_section += "🔗 Confluence Sources:\n" + "\n".join(confluence_links) + "\n"
        if other_pdf_sources:
            reference_section += "📄 Other PDF Sources:\n" + "\n".join(other_pdf_sources) + "\n"

        final_response = f"{response}{reference_section}"
        st.session_state["conversation"].append((user_query, final_response))
        st.text_area("Chatbot Response:", final_response, height=600)

        # Like/Dislike buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("👍 Like"):
                st.success("Glad you liked it.")
        with col2:
            if st.button("👎 Dislike"):
                with st.spinner("Regenerating response..."):
                    improved_response = regenerate_answer_with_bedrock(user_query, model_id)
                    improved_final_response = f"{improved_response}{reference_section}"
                    st.session_state["conversation"].append((user_query, improved_final_response))
                    st.text_area("Updated Chatbot Response:", improved_final_response, height=600)

if st.button("Clear Cache"):
    st.session_state.clear()
    st.success("Cache Cleared")

with st.sidebar:
    st.header("Conversation History")
    if "conversation" in st.session_state:
        for i, (speaker, message) in enumerate(st.session_state["conversation"]):
            with st.expander(f"{speaker}: {message[:30]}..."):
                st.write(f"{message}")
