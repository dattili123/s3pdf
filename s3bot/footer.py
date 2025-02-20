import streamlit as st

# Injecting CSS for a fixed footer
st.markdown("""
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f8f9fa;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            color: #333;
        }
    </style>
    <div class="footer">
        © 2025 Your Company | Built with Streamlit
    </div>
""", unsafe_allow_html=True)

# Main content
st.title("Streamlit App with Fixed Footer")
st.write("Scroll down to see the footer.")

# Adding some content for scrolling effect
for i in range(50):
    st.write(f"Line {i+1}")
