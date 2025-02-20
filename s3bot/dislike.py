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
LIKED_RESPONSES_FILE = "liked_responses.txt"

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

# Function to store liked responses
def store_liked_response(response):
    try:
        with open(LIKED_RESPONSES_FILE, "a") as file:
            file.write(response + "\n\n")
        st.success("Response saved as liked!")
    except Exception as e:
        st.error(f"Error saving liked response: {str(e)}")

# Function to generate response with Bedrock
def generate_answer_with_bedrock(prompt, model_id, region="us-east-1", improve=False):
    client = boto3.client("bedrock-runtime", region_name=region)
    conversation_history = st.session_state.get("conversation", [])
    history_context = "\n".join(
        [f"{speaker}: {message}" for speaker, message in conversation_history[-3:]]
    )

    additional_instructions = ""
    if improve:
        additional_instructions = (
            "6. Carefully refine the response to be more precise, logical, and informative.\n"
            "7. Ensure technical depth and clarity suitable for an expert audience.\n"
            "8. Improve structuring to include step-by-step guidance, actionable insights, and advanced explanations where applicable.\n"
        )

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Think deeply and generate the most accurate, well-structured, and logically sound response.\n\n"
                                    "### Context Provided:\n"
                                    f"{history_context}\n\n"
                                    f"{prompt}\n\n"
                                    "### Instructions:\n"
                                    "1. Analyze the given context thoroughly.\n"
                                    "2. Identify the key details relevant to the user's question.\n"
                                    "3. Provide a clear, structured, and step-by-step explanation.\n"
                                    "4. Summarize key takeaways for clarity.\n"
                                    "5. If a user asks about any questions in the context of JIRA, then look at the JIRA issues you have in the embeddings and generate a perfect response, including the key numbers of the referenced JIRA issues.\n\n"
                                    f"{additional_instructions}"
                                    "### Expected Output:\n"
                                    "- A detailed, insightful, and highly relevant answer.\n"
                                    "- Use professional and technical language where needed.\n"
                                    "- Ensure factual correctness and logical flow."
                                )
                            }
                        ]
                    }
                ],
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.9
            }),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read().decode("utf-8"))
        response_text = "".join(item.get("text", "") for item in response_body["content"])
        return response_text.strip() if response_text.strip() else "No response generated."

    except Exception as e:
        return f"Error generating response: {e}"

# Function to regenerate response on dislike
def regenerate_response(user_query):
    st.warning("Generating a better response...")
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    improved_response = generate_answer_with_bedrock(user_query, model_id, improve=True)
    st.session_state["conversation"].append((user_query, improved_response))
    st.text_area("Improved Response:", improved_response, height=600)

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
        response = generate_answer_with_bedrock(user_query, model_id)
        st.session_state["conversation"].append((user_query, response))
        st.text_area("Chatbot Response:", response, height=600)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Like"):
                store_liked_response(response)
        with col2:
            if st.button("👎 Dislike"):
                regenerate_response(user_query)
