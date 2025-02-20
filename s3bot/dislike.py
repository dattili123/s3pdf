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
LOGO_PATH = "./logo.png"
BANNER_PATH = "./chatbot.png"
LIKED_RESPONSES_FILE = "liked_responses.txt"

def save_liked_response(response):
    """Saves the liked response to a text file."""
    with open(LIKED_RESPONSES_FILE, "a") as file:
        file.write(response + "\n" + "-" * 50 + "\n")

def regenerate_response_with_improvements(user_query, model_id, region="us-east-1"):
    """Generates a refined response based on user feedback."""
    client = boto3.client("bedrock-runtime", region_name=region)
    additional_instructions = (
        "Carefully refine the response to be more precise, logical, and informative.\n"
        "Ensure technical depth and clarity suitable for an expert audience.\n"
        "Improve structuring to include step-by-step guidance, actionable insights, and advanced explanations where applicable."
    )
    full_prompt = f"User Query: {user_query}\n\n{additional_instructions}\n\nAnswer:"
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": full_prompt
                    }]
                }],
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.9
            }),
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response["body"].read().decode("utf-8"))
        return "".join(item.get("text", "") for item in response_body["content"]).strip()
    except Exception as e:
        return f"Error generating response: {e}"

# Streamlit Interface Configuration
st.set_page_config(page_title="Ask SRE Infra Assist", page_icon="🛠️", layout="wide")

st.header("Chatbot Interface")

with st.form(key="question_form", clear_on_submit=False):
    user_query = st.text_input("Ask your question:", key="user_input", help="Press Enter to submit.")
    submit_button = st.form_submit_button("Submit")

if submit_button and user_query:
    with st.spinner("Generating response..."):
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        response = regenerate_response_with_improvements(user_query, model_id)
        st.session_state["latest_response"] = response
        st.text_area("Chatbot Response:", response, height=300)

    col1, col2 = st.columns([0.2, 0.2])
    with col1:
        if st.button("👍 Like", key="like_button"):
            save_liked_response(st.session_state["latest_response"])
            st.success("Response saved to liked responses!")
    with col2:
        if st.button("👎 Dislike", key="dislike_button"):
            with st.spinner("Refining response..."):
                refined_response = regenerate_response_with_improvements(user_query, model_id)
                st.session_state["latest_response"] = refined_response
                st.text_area("Refined Response:", refined_response, height=300)

if st.button("Clear Cache"):
    st.session_state.clear()
    st.success("Cache Cleared")
