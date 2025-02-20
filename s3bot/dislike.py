import streamlit as st
import boto3
from chromadb import Client
from my_bedrock_module import query_bedrock

# Initialize AWS Bedrock Client
bedrock_client = boto3.client('bedrock-runtime')

# Initialize ChromaDB client
chroma_client = Client()

# Session State Initialization
if "liked_responses" not in st.session_state:
    st.session_state["liked_responses"] = []
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Define function to query AWS Bedrock with RAG approach
def query_with_rag(user_query, rethink=False):
    """ Queries AWS Bedrock with enhanced RAG-based retrieval."""
    
    # Retrieve relevant context from ChromaDB
    retrieved_docs = chroma_client.query(user_query)
    context = "\n".join(retrieved_docs)
    
    # Adjust prompt based on user feedback
    prompt = (
        f"You are an advanced AI assistant using Retrieval-Augmented Generation (RAG).\n"
        f"User query: {user_query}\n"
    )
    
    if rethink:
        prompt += (
            "The user was not satisfied with the previous answer. Please rethink the response "
            "by considering alternative perspectives and improving relevance. Use the retrieved context below:\n"
            f"Context:\n{context}\n"
        )
    else:
        prompt += f"Use the following retrieved context to provide an accurate response:\n{context}\n"
    
    # Query AWS Bedrock
    response = query_bedrock(prompt)
    return response

# Streamlit UI
st.title("Chatbot with Like/Dislike Feedback")
user_input = st.text_input("Ask me anything:")

if st.button("Submit"):
    with st.spinner("Generating response..."):
        response = query_with_rag(user_input)
        st.session_state["conversation"].append(("User", user_input))
        st.session_state["conversation"].append(("Bot", response))

# Display conversation with Like/Dislike buttons
for i, (speaker, message) in enumerate(st.session_state["conversation"]):
    if speaker == "Bot":
        with st.expander(f"Bot: {message[:30]}..."):
            st.write(message)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"👍 Like {i}", key=f"like_{i}"):
                    st.session_state["liked_responses"].append(message)
                    st.success("Response saved as liked!")
            
            with col2:
                if st.button(f"👎 Dislike {i}", key=f"dislike_{i}"):
                    with st.spinner("Rethinking response..."):
                        new_response = query_with_rag(user_input, rethink=True)
                        st.session_state["conversation"][-1] = ("Bot", new_response)  # Replace response
                        st.warning("New approach generated!")
