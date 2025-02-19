import streamlit as st
import base64
import chromadb
from titan import TitanEmbeddingFunction

# Page configuration
st.set_page_config(page_title="Ask SRE Infra Assist", page_icon="🤖", layout="wide")

# Function to set background image
def set_background(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    page_bg_css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded_string}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(page_bg_css, unsafe_allow_html=True)

# Set background image
BANNER_PATH = "your_background_image.png"
set_background(BANNER_PATH)

# Initialize session state for conversation if not present
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Sidebar for conversation history
with st.sidebar:
    st.header("Conversation History")
    for i, (speaker, message) in enumerate(st.session_state["conversation"]):
        with st.expander(f"{speaker}: {message[:30]}..."):
            st.write(message)

# Main Chatbot Interface
st.title("Chatbot Interface")

# Embedding function
embedding_function = TitanEmbeddingFunction(model_id="amazon.titan-embed-text:v2.0")

# Chat input using st.chat_input
user_query = st.chat_input("Ask your question...")
if user_query:
    with st.spinner("Generating response..."):
        # Generate response using predefined function
        model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        response = query_chromadb_and_generate_response(
            user_query, embedding_function, st.session_state.collection, model_id
        )
        
        # Store conversation history
        st.session_state["conversation"].append(("User", user_query))
        st.session_state["conversation"].append(("Bot", response))

    # Display conversation using st.chat_message
    with st.chat_message("user"):
        st.markdown(f"**User:** {user_query}")
    with st.chat_message("assistant"):
        st.markdown(f"**Bot:** {response}")

# Clear cache button
if st.button("Clear Cache", use_container_width=True):
    st.session_state["conversation"].clear()
    st.success("Cache Cleared")
