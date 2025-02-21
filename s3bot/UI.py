import streamlit as st

st.markdown("""
    <style>
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #f8f9fa;
            padding: 10px 20px;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            box-shadow: 0px 4px 2px -2px gray;
        }
        .header img {
            height: 50px;
        }
        .header h1 {
            flex-grow: 1;
            text-align: center;
            margin: 0;
            font-size: 24px;
            color: #333;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header">
        <img src="https://your-logo-url.com/logo.png" alt="Logo">
        <h1>Your Title Here</h1>
        <img src="https://your-right-image-url.com/pic.png" alt="Right Image">
    </div>
""", unsafe_allow_html=True)

st.write("\n\n\n\n")  # To create space after fixed header
