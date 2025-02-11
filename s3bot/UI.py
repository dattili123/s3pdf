import streamlit as st
import base64
import time

# Set Streamlit page config
st.set_page_config(page_title="Ask InfoSphere", page_icon="🤖", layout="wide")

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
BANNER_PATH = "./chatbot.png"  # Replace with your image file
set_background(BANNER_PATH)

# Custom CSS to fix layout and align elements
st.markdown("""
    <style>
        .header-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 20px;
            margin: 0px !important;
        }
        .header-title {
            font-size: 30px;
            font-weight: bold;
            color: black;
            margin-left: 10px;
        }
        .conversation-history {
            max-height: 300px;
            overflow-y: auto;
            border-radius: 10px;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.8);
        }
        .chat-input {
            width: 100%;
        }
        .stButton button {
            background-color: black !important;
            color: white !important;
            font-size: 16px !important;
        }
        .chat-response {
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Layout: Logo + Title
col1, col2 = st.columns([0.2, 0.8])  # Adjust width ratio

with col1:
    LOGO_PATH = "./logo.png"  # Replace with your image file
    st.image(LOGO_PATH, width=120)

with col2:
    st.markdown('<h1 class="header-title">InfoSphere</h1>', unsafe_allow_html=True)

# Divider
st.markdown("<hr style='border:1px solid black;'>", unsafe_allow_html=True)

# Two-column Layout: Chatbot & Conversation History
col1, col2 = st.columns([1.5, 1.5])

# Chatbot Interface
with col1:
    st.subheader("Chatbot Interface")

    # Input with Enter key submission using st.form
    with st.form(key="question_form", clear_on_submit=False):
        user_query = st.text_input("Ask your question:", key="user_input", help="Press Enter to submit.")
        submit_button = st.form_submit_button("Submit")

    # Process Query
    if submit_button and user_query:
        st.write(f"🔎 **You asked:** {user_query}")

        # Simulated AI Response (Replace with actual function)
        time.sleep(1)  # Simulate processing time
        response = f"🤖 AI Response to '{user_query}'..."  # Replace with actual response logic
        st.markdown(f'<div class="chat-response">{response}</div>', unsafe_allow_html=True)

# Conversation History
with col2:
    st.subheader("Conversation History ↩️")
    st.markdown('<div class="conversation-history">', unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state["conversation"] = []

    if user_query:
        st.session_state["conversation"].append(("User", user_query))
        st.session_state["conversation"].append(("Bot", response))

    # Display conversation history
    for speaker, message in reversed(st.session_state["conversation"][-6:]):  # Show last 6 messages
        with st.expander(f"**{speaker}:** {message[:30]}..."):
            st.write(f"{message}")

    st.markdown('</div>', unsafe_allow_html=True)
