import streamlit as st

# Sample images (replace with actual logo and chatbot UI image paths)
logo = "https://via.placeholder.com/150"  # Replace with actual chatbot logo
chatbot_image = "https://via.placeholder.com/150"  # Replace with actual chatbot UI image

# Title
st.markdown("<h3 style='text-align: center;'>Chatbot Flow</h3>", unsafe_allow_html=True)

# Creating columns for layout
col1, col2, col3, col4 = st.columns([1.5, 1, 0.2, 1])

with col1:
    st.markdown("<h2 style='text-align: left;'>Chatbot</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: left; font-size: 16px;'>"
        "An AI-powered chatbot that queries Jira and Confluence sources "
        "to generate responses to user questions.</p>",
        unsafe_allow_html=True,
    )

with col2:
    st.image(logo, caption="Chatbot Logo", use_column_width=True)

with col3:
    st.markdown("<h1 style='text-align: center;'>↔️</h1>", unsafe_allow_html=True)  # Bidirectional arrow

with col4:
    st.image(chatbot_image, caption="User Interaction", use_column_width=True)
