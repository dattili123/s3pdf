import streamlit as st

# Inject custom CSS to move the sidebar to the right
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            position: fixed;
            right: 0;
            top: 0;
            height: 100%;
            background-color: #f8f9fa;  /* Change background color if needed */
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    st.title("Right Sidebar")
    st.write("This sidebar is moved to the right.")
    st.slider("Adjust value", 0, 100, 50)

# Main content
st.title("Streamlit App with Right Sidebar")
st.write("This is a demo where we shift the sidebar to the right using CSS.")

# Adding some content
for i in range(10):
    st.write(f"Line {i+1}")
