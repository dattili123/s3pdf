import os
import json
import base64
import boto3
import streamlit as st
import pdfplumber
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# AWS Bedrock client
brt = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")
PDF_DIR = "./pdf_dir"

LOGO_PATH = "./logo.png"
BANNER_PATH = "./chatbot.png"

# Function: Read and Chunk PDF using pdfplumber
def read_and_chunk_pdf(pdf_path, chunk_size=800, chunk_overlap=25):
    """
    Reads a PDF and extracts text chunks using pdfplumber.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    all_chunks = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                extracted_text = page.extract_text()

                if extracted_text:
                    split_docs = text_splitter.create_documents(
                        texts=[extracted_text],
                        metadatas=[{"page": page_num + 1}]
                    )
                    all_chunks.extend(split_docs)

    except Exception as e:
        print(f"Error reading {pdf_path}: {str(e)}")

    return all_chunks


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
def store_embeddings_in_chromadb(pdf_dir, embedding_function):
    client = chromadb.PersistentClient("/path/to/chromadb")
    collection = client.get_or_create_collection(name="my_collection", embedding_function=embedding_function)

    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            print(f"Processing PDF: {pdf_file}")
            try:
                chunks = read_and_chunk_pdf(pdf_path)
                for chunk in chunks:
                    chunk_id = str(hash(chunk.page_content))
                    collection.add(
                        documents=[chunk.page_content],
                        metadatas={"id": chunk_id, "source": pdf_file, **chunk.metadata},
                        ids=[chunk_id]
                    )
            except Exception as e:
                print(f"Error processing PDF {pdf_file}: {str(e)}")

    return collection


# Step 4: Generate Answer Using AWS Bedrock with Enhanced Prompt
def generate_answer_with_bedrock(prompt, model_id, region="us-east-1"):
    client = boto3.client("bedrock-runtime", region_name=region)
    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(
                {
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
                                        f"{prompt}\n\n"
                                        "### Instructions:\n"
                                        "1. Analyze the given context thoroughly.\n"
                                        "2. Identify the key details relevant to the user's question.\n"
                                        "3. Provide a clear, structured, and step-by-step explanation.\n"
                                        "4. Summarize key takeaways for clarity.\n\n"
                                        "### Expected Output:\n"
                                        "- A detailed, insightful, and highly relevant answer.\n"
                                        "- Use professional and technical language where needed.\n"
                                        "- Ensure factual correctness and logical flow."
                                    )
                                }
                            ]
                        }
                    ],
                    "max_tokens": 600,
                    "temperature": 0.5,
                    "top_p": 0.85
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


# Step 5: RAG - Query ChromaDB and Generate Response
def query_chromadb_and_generate_response(user_query, embedding_function, collection, model_id, region="us-east-1"):
    query_embedding = embedding_function([user_query])[0]
    results = collection.query(query_embedding, n_results=5)

    if not results or "documents" not in results or not results["documents"]:
        return "No relevant data found in the database."

    # Retrieve relevant chunks
    documents = [doc for sublist in results["documents"] for doc in sublist]
    relevant_text = " ".join(documents)

    # RAG Augmentation: Provide better structured context
    full_prompt = f"Relevant Information: {relevant_text}\n\nUser Query: {user_query}\n\nAnswer:"
    return generate_answer_with_bedrock(full_prompt, model_id, region)


# Streamlit Interface
st.set_page_config(page_title="Advanced RAG Chatbot", page_icon="🤖", layout="wide")

if "collection" not in st.session_state:
    with st.spinner("Initializing ChromaDB..."):
        embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text-v2:0")
        client = chromadb.PersistentClient(path="./chromadb")
        collection = store_embeddings_in_chromadb(PDF_DIR, embedding_function)
        st.session_state.collection = collection
        st.success("Embeddings generated and stored!")
else:
    st.success("Existing embeddings found. Ready to use!")

if st.button("Clear Cache"):
    st.session_state.clear()
    st.success("Cache cleared!")

# Chatbot UI Layout
col1, col2, col3 = st.columns([1, 2, 1])

# Left Banner
with col1:
    st.image(BANNER_PATH, use_column_width=True)

# Chatbot Interface
with col2:
    st.image(LOGO_PATH, width=150)
    st.title("Enhanced RAG Chatbot with AWS Bedrock & ChromaDB")
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
            st.session_state["conversation"].append(("User", user_query))
            st.session_state["conversation"].append(("Bot", response))
            st.text_area("Chatbot Response:", value=response, height=200)

# Conversation History
with col3:
    st.subheader("Conversation History")
    for speaker, message in st.session_state["conversation"]:
        st.write(f"**{speaker}:** {message}")

import streamlit as st
import time
from PIL import Image

# Image Paths
image_paths = ["image1.jpg", "image2.jpg", "image3.jpg"]  # Replace with actual image file paths

# Inject Custom CSS for Smooth Transitions
st.markdown("""
    <style>
        .image-container {
            text-align: center;
            transition: opacity 1.5s ease-in-out;
            opacity: 0;
        }
        .image-container.show {
            opacity: 1;
        }
    </style>
""", unsafe_allow_html=True)

# Placeholder for Image
image_placeholder = st.empty()

# Infinite Loop with Smooth Transition
while True:
    for img_path in image_paths:
        img = Image.open(img_path)

        # Display Image with CSS Animation
        image_placeholder.markdown(f'<div class="image-container show"><img src="data:image/png;base64,{st.image(img, use_column_width=True)}" /></div>',
                                   unsafe_allow_html=True)
        time.sleep(2)  # Wait for 2 seconds before switching images


