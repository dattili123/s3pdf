import os
import json
import base64
import boto3
import streamlit as st
from PyPDF2 import PdfReader
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

# AWS Bedrock client
brt = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
PDF_PATH = "./s3-api.pdf"

LOGO_PATH = "./logo.png"  # Update with your logo filename
BANNER_PATH = "./chatbot.png"  # Update with your banner filename


# Utility to load images as base64 for Streamlit
def load_image_as_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


# Step 1: Read and Chunk PDF
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


# Step 2: Embedding Function using AWS Bedrock
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


# Step 3: Store Embeddings in ChromaDB
def store_embeddings_in_chromadb(chunks, embedding_function):
    client = chromadb.PersistentClient(path="./chromadb")
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
    return collection


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
        response_text = "".join(item.get("text", "") for item in response_body["content"])
        return response_text.strip() if response_text.strip() else "No response generated."
    except Exception as e:
        return f"Error generating response: {e}"


# Step 5: Query ChromaDB and Generate Response
def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database."

    documents = [doc for sublist in results["documents"] for doc in sublist]
    relevant_text = " ".join(documents)
    full_prompt = f"Relevant context: {relevant_text}\n\nUser question: {user_query}"
    return generate_answer_with_bedrock(full_prompt, model_id, region)


# Streamlit Interface
st.set_page_config(page_title="AWS Bedrock Chatbot", page_icon="🤖", layout="wide")


if "collection" not in st.session_state:
    with st.spinner("Initializing chromadb...."):
        embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
        client = chromadb.PersistentClient(path="./chromadb")
        collection = client.get_or_create_collection(name="mycollection", embedding_function=embedding_function)
        existing_data = collection.get(include=["metadatas"])

        if not existing_data["metadatas"]:
            st.info("Embeddings not found. Generating new embeddings.....")
            chunks = read_and_chunk_pdf(PDF_PATH)
            st.session_state.collection = store_embeddings_in_chromadb(chunks, embedding_function)
            st.success("Embeddings have generated and stored!")
        else:
            st.session_state.collection = collection
            st.success("Existing embeddings found. Ready to use!")

# Updated CSS for Full Page Background
st.markdown(
    """
    <style>
        html, body {
            background-color: #f4f7fc; /* Light blue-gray background for the entire page */
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
            background-color: #ffffff; /* White background for banner */
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .chatbot-container {
            margin-top: 20px;
            background-color: #ffffff; /* White background for chatbot */
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .conversation-history {
            padding-top: 20px;
            padding-left: 10px;
            padding-right: 10px;
            background-color: #ffffff; /* White background for conversation history */
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3, h4 {
            color: #2c3e50; /* Dark blue-gray for all headings */
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .stButton button {
            background-color: #2c3e50; /* Dark blue-gray for buttons */
            color: white;
            border-radius: 5px;
            font-size: 16px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 10px 20px;
        }
        .stButton button:hover {
            background-color: #34495e; /* Slightly darker blue-gray on hover */
            color: white;
        }
        .stTextArea textarea {
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .conversation-history h2 {
            margin-bottom: 15px;
            color: #2c3e50;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Layout with Columns
col1, col2, col3 = st.columns([1, 2, 1])  # Adjust column proportions

# Left Banner
with col1:
    st.markdown('<div class="left-banner">', unsafe_allow_html=True)
    st.image(BANNER_PATH, use_column_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Center: Chatbot Interface
with col2:
    st.image(LOGO_PATH, width=150)  # Logo at the top
    st.title("AWS Bedrock Chatbot with ChromaDB")
    st.subheader("Chatbot Interface")
    user_query = st.text_input("Ask your question:")
    if st.button("Submit"):
        if "conversation" not in st.session_state:
            st.session_state["conversation"] = []
        with st.spinner("Generating response..."):
            model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
            response = query_chromadb_and_generate_response(
                user_query,
                TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0"),
                st.session_state.collection,
                model_id,
            )
            # Add to conversation history
            st.session_state["conversation"].append(("User", user_query))
            st.session_state["conversation"].append(("Bot", response))
            st.text_area("Chatbot Response:", value=response, height=200)

# Right: Conversation History
with col3:
    st.markdown('<div class="conversation-history">', unsafe_allow_html=True)
    st.subheader("Conversation History")
    if "conversation" in st.session_state:
        for i, (speaker, message) in enumerate(st.session_state["conversation"]):
            with st.expander(f"{speaker}: {message[:30]}..."):  # Display first 30 chars in expander title
                st.write(f"{message}")
    st.markdown('</div>', unsafe_allow_html=True)
