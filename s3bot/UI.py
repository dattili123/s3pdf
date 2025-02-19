import streamlit as st

# Sample images (replace with your image URLs or local file paths)
image1 = "https://via.placeholder.com/150"  # Replace with actual image path
image2 = "https://via.placeholder.com/150"
image3 = "https://via.placeholder.com/150"

# Display images in a row with arrows between them
st.markdown("<h3 style='text-align: center;'>Process Flow</h3>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns([1, 0.2, 1, 0.2, 1])

with col1:
    st.image(image1, caption="Step 1", use_column_width=True)
with col2:
    st.markdown("<h1 style='text-align: center;'>➡️</h1>", unsafe_allow_html=True)
with col3:
    st.image(image2, caption="Step 2", use_column_width=True)
with col4:
    st.markdown("<h1 style='text-align: center;'>➡️</h1>", unsafe_allow_html=True)
with col5:
    st.image(image3, caption="Step 3", use_column_width=True)
