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
PDF_DIR = "./pdf_dir"  # Directory where PDFs are stored

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

# Function to retrieve references from stored PDFs and provide Confluence links
def get_references_from_pdf(user_query, collection):
    query_results = collection.query(user_query, n_results=3)  # Retrieve top 3 references
    references = []
    
    if "metadatas" in query_results:
        for metadata in query_results["metadatas"]:
            source = metadata.get("source", "Unknown Source")
            page_id = source.split("_")[0] if "_" in source else "Unknown"
            page_title = source.split("_")[1] if "_" in source else "Unknown Title"
            confluence_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
            references.append(f"[{page_title}]({confluence_url})")
    
    return references if references else ["No references found"]

# Function to generate context-aware answer
def generate_context_aware_answer(user_query, model_id, region="us-east-1"):
    client = boto3.client("bedrock-runtime", region_name=region)
    
    # Retrieve conversation history
    conversation_history = st.session_state.get("conversation", [])
    
    # Construct the prompt using recent conversation history (last 3 interactions)
    history_context = "\n".join(
        [f"{speaker}: {message}" for speaker, message in conversation_history[-3:]]
    )
    
    full_prompt = (
        f"Context:\n{history_context}\n\n"
        f"User: {user_query}\nBot:"
    )
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": [{"type": "text", "text": full_prompt}]}],
                    "max_tokens": 300,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            ),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read().decode("utf-8"))
        response_text = "".join(item.get("text", "") for item in response_body["content"])
        return response_text.strip() if response_text.strip() else "No response generated."
    except Exception as e:
        return f"Error generating response: {e}"

# Streamlit UI
st.set_page_config(page_title="AWS Bedrock Chatbot with Context Awareness", page_icon="🤖", layout="wide")
st.title("AWS Bedrock Chatbot with Context Awareness")

if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Initialize ChromaDB
if "collection" not in st.session_state:
    with st.spinner("Initializing ChromaDB..."):
        client = chromadb.PersistentClient(path="./chromadb")
        collection = client.get_or_create_collection(name="knowledge_base")
        st.session_state.collection = collection
        st.success("ChromaDB initialized!")

user_query = st.text_input("Ask your question:")
if st.button("Submit"):
    with st.spinner("Generating response..."):
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        response = generate_context_aware_answer(user_query, model_id)
        references = get_references_from_pdf(user_query, st.session_state.collection)
        
        # Store conversation history
        st.session_state["conversation"].append(("User", user_query))
        st.session_state["conversation"].append(("Bot", response))
        
        # Display chatbot response
        st.text_area("Chatbot Response:", value=response, height=200)
        
        # Display references
        st.subheader("References")
        for ref in references:
            st.markdown(f"- {ref}")

# Show conversation history
st.subheader("Conversation History")
for i, (speaker, message) in enumerate(st.session_state["conversation"][-6:]):
    with st.expander(f"{speaker}: {message[:30]}..."):
        st.write(f"{message}")
